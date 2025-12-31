<?php
// 1. Load 4get's HTML parser
require_once __DIR__ . '/4get-repo/lib/fuckhtml.php';

// 2. Load the Config
// This file was already patched by entrypoint.sh to have the correct UA
require_once __DIR__ . '/4get-repo/data/config.php';

// 3. Mock the Backend (Required for scraper instantiation)
class backend {
    public function __construct($service) {}
    public function get_ip() { return '127.0.0.1'; }
    public function assign_proxy($curl, $proxy) {}
    public function store($url, $type, $proxy) { return $url; }
    public function get($token, $type) { return [$token, '127.0.0.1']; }
    public function detect_sorry() { return false; }
}

// 4. Legacy support
if (!defined('USER_AGENT')) {
    define('USER_AGENT', config::USER_AGENT);
}