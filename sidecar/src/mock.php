<?php
// 1. Load 4get's HTML parser
require_once __DIR__ . '/4get-repo/lib/fuckhtml.php';

// 2. Load the Config (Patched by entrypoint.sh)
require_once __DIR__ . '/4get-repo/data/config.php';

/**
 * Smart Backend Implementation
 * Uses APCu for state storage (cookies/tokens) and Config for proxies.
 * This restores pagination and stealth features without needing MySQL/Redis.
 */
class backend {
    public function __construct($service) {
        // Ensure APCu is enabled
        if (!function_exists('apcu_store')) {
            error_log("CRITICAL: APCu is not enabled. State storage will fail.");
        }
    }

    /**
     * Selects a proxy from config::PROXY_LIST
     */
    public function get_ip() {
        if (!empty(config::PROXY_LIST)) {
            $proxies = config::PROXY_LIST;
            // Random rotation
            $selected = $proxies[array_rand($proxies)];
            return $selected;
        }
        // Fallback to direct connection
        return '127.0.0.1';
    }

    /**
     * Configures cURL to use the selected proxy.
     */
    public function assign_proxy($curl, $proxy) {
        if ($proxy === '127.0.0.1' || empty($proxy)) {
            return;
        }

        // Parse 4get proxy format (IP:PORT or IP:PORT:USER:PASS)
        $parts = explode(':', $proxy);
        $url = $parts[0] . ':' . $parts[1];
        
        curl_setopt($curl, CURLOPT_PROXY, $url);
        
        // Handle Authentication
        if (isset($parts[2]) && isset($parts[3])) {
            curl_setopt($curl, CURLOPT_PROXYUSERPWD, $parts[2] . ':' . $parts[3]);
        }
        
        curl_setopt($curl, CURLOPT_PROXYTYPE, CURLPROXY_HTTP);
    }

    /**
     * Stores state (Cookies, Pagination Tokens) in memory (APCu).
     */
    public function store($url, $type, $proxy) {
        // Generate a unique token
        $token = bin2hex(random_bytes(16));
        
        // Store data in RAM with 1 hour TTL
        $data = [
            'url' => $url,
            'proxy' => $proxy,
            'cookies' => [] 
        ];
        
        apcu_store("4get_$token", $data, 3600);
        
        return $token;
    }

    /**
     * Retrieves state for pagination.
     */
    public function get($token, $type) {
        $data = apcu_fetch("4get_$token");
        
        if ($data === false) {
            return [null, '127.0.0.1'];
        }
        
        return [$data['url'], $data['proxy']];
    }

    /**
     * Basic Bot Detection
     */
    public function detect_sorry($html = '') {
        if (stripos($html, 'captcha') !== false || 
            stripos($html, 'unusual traffic') !== false ||
            stripos($html, '429 too many requests') !== false) {
            return true;
        }
        return false;
    }
}

// Legacy support
if (!defined('USER_AGENT')) {
    define('USER_AGENT', config::USER_AGENT);
}