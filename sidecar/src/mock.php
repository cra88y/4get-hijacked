<?php
putenv("CURL_IMPERSONATE_CHROME=/usr/local/bin/curl_chrome116");
putenv("CURL_IMPERSONATE_FF=/usr/local/bin/curl_ff117");
// 1. Load the REAL parsing tool from the 4get repo
// We need this to actually parse the HTML!
require_once __DIR__ . '/4get-repo/lib/fuckhtml.php';

// 2. Define our MOCK backend
// This replaces the heavy real backend.php
class backend {
    public function __construct($service) {}
    public function get_ip() { return 'raw_ip::::'; }
    public function assign_proxy($curl, $proxy) {
        // Scrapers expect this to exist, but we don't need real proxying for the sidecar
    }
    public function store($url, $type, $proxy) { return $url; }
    public function get($token, $type) { return [$token, 'raw_ip::::']; }
    public function detect_sorry() { return false; }
}

// 3. Import REAL config from 4get-repo, but PATCH the User Agent to be safe
// We can't modify the repo file directly, so we patch it in memory.
$configFile = __DIR__ . '/4get-repo/data/config.php';
$configContent = file_get_contents($configFile);

// Aggressive User Agent Rotation
$userAgents = [
    // Firefox 125.0 (Windows)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    // Chrome 124.0 (Windows)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    // Edge 124.0 (Windows)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    // Safari 17.4 (macOS)
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    // Chrome 124.0 (Linux)
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    // Firefox 125.0 (Linux)
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0"
];

$selectedUA = $userAgents[array_rand($userAgents)];

// Replace the futuristic/bad User Agent line entirely with our selected random one
$configContent = preg_replace(
    '/const USER_AGENT = ".*";/',
    'const USER_AGENT = "' . $selectedUA . '";',
    $configContent
);

// Remove the opening PHP tag so we can eval() the rest
$configContent = preg_replace('/^<\?php/', '', $configContent);

// Evaluate the patched config class definition
eval($configContent);

// Global constant expected by some legacy 4get logic
if (!defined('USER_AGENT')) {
    define('USER_AGENT', config::USER_AGENT);
}