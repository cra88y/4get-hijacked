<?php
// 1. Load 4get's HTML parser
require_once __DIR__ . '/4get-repo/lib/fuckhtml.php';

// 2. Load the Config (Patched by entrypoint.sh)
require_once __DIR__ . '/4get-repo/data/config.php';

/**
 * Smart Backend Implementation
 * Uses APCu for state storage and Env Vars for proxies.
 */
class backend {
    public function __construct($service) {
        if (!function_exists('apcu_store')) {
            error_log("CRITICAL: APCu is not enabled. State storage will fail.");
        }
    }

    /**
     * Selects a proxy from Environment Variable or Config
     */
    public function get_ip() {
        // 1. Check for Environment Variable (Easy Docker Config)
        $env_proxies = getenv('FOURGET_PROXIES');
        if ($env_proxies) {
            // Expect comma-separated list: "ip:port,ip:port:user:pass"
            $proxies = explode(',', $env_proxies);
            return trim($proxies[array_rand($proxies)]);
        }

        // 2. Fallback to 4get Config (SAFE CHECK ADDED)
        if (defined('config::PROXY_LIST') && !empty(config::PROXY_LIST)) {
            $proxies = config::PROXY_LIST;
            return $proxies[array_rand($proxies)];
        }

        // 3. Fallback to direct connection
        return '127.0.0.1';
    }

    /**
     * Configures cURL to use the selected proxy.
     */
    public function assign_proxy($curl, $proxy) {
        if ($proxy === '127.0.0.1' || empty($proxy)) {
            return;
        }

        $parts = explode(':', $proxy);
        $url = $parts[0] . ':' . $parts[1];
        
        curl_setopt($curl, CURLOPT_PROXY, $url);
        
        if (isset($parts[2]) && isset($parts[3])) {
            curl_setopt($curl, CURLOPT_PROXYUSERPWD, $parts[2] . ':' . $parts[3]);
        }
        
        curl_setopt($curl, CURLOPT_PROXYTYPE, CURLPROXY_HTTP);
    }

    /**
     * Stores state in RAM (APCu).
     */
    public function store($url, $type, $proxy) {
        $token = bin2hex(random_bytes(16));
        $data = [
            'url' => $url,
            'proxy' => $proxy,
            'cookies' => [] 
        ];
        apcu_store("4get_$token", $data, 3600);
        return $token;
    }

    /**
     * Retrieves state.
     */
    public function get($token, $type) {
        $data = apcu_fetch("4get_$token");
        if ($data === false) {
            return [null, '127.0.0.1'];
        }
        return [$data['url'], $data['proxy']];
    }

    public function detect_sorry($html = '') {
        if (stripos($html, 'captcha') !== false || 
            stripos($html, 'unusual traffic') !== false ||
            stripos($html, '429 too many requests') !== false) {
            return true;
        }
        return false;
    }
}

if (!defined('USER_AGENT')) {
    // Safe check for USER_AGENT constant as well
    if (defined('config::USER_AGENT')) {
        define('USER_AGENT', config::USER_AGENT);
    } else {
        // Fallback if config is totally broken
        define('USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36');
    }
}