<?php
require_once __DIR__ . '/4get-repo/lib/fuckhtml.php';
require_once __DIR__ . '/4get-repo/data/config.php';

class backend {
    public static $context = [];

    public function __construct($service) {
        if (!function_exists('apcu_store')) {
            error_log("CRITICAL: APCu is not enabled. State storage will fail.");
        }
    }

    public function get_ip() {
        $env_proxies = getenv('FOURGET_PROXIES');
        if ($env_proxies) {
            $proxies = explode(',', $env_proxies);
            return trim($proxies[array_rand($proxies)]);
        }

        if (defined('config::PROXY_LIST') && !empty(config::PROXY_LIST)) {
            $proxies = config::PROXY_LIST;
            return $proxies[array_rand($proxies)];
        }

        return '127.0.0.1';
    }

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

    public function store($url, $type, $proxy) {
        $token = bin2hex(random_bytes(16));
        $data = [
            'url' => $url,
            'proxy' => $proxy,
            'cookies' => [] 
        ];
        apcu_store("4get_$token", $data, 3600);

        if (!empty(self::$context)) {
            $ctx = self::$context;
            $current_offset = $ctx['offset'] ?? 0;
            $next_offset = $current_offset + 10; 
            
            $key = md5(($ctx['engine'] ?? '') . ($ctx['s'] ?? '') . $next_offset);
            apcu_store("4get_det_$key", $token, 3600);
        }

        return $token;
    }

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