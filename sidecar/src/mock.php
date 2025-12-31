<?php
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

// 3. Import REAL config from 4get-repo
// This ensures we inherit all stealth/UA updates from 4get automatically.
require_once __DIR__ . '/4get-repo/data/config.php';

// Global constant expected by some legacy 4get logic
if (!defined('USER_AGENT')) {
    define('USER_AGENT', config::USER_AGENT);
}