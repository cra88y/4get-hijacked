<?php
// 1. Load the REAL parsing tool from the 4get repo
// We need this to actually parse the HTML!
require_once __DIR__ . '/4get-repo/lib/fuckhtml.php';

// 2. Define our MOCK backend
// This replaces the heavy real backend.php
class backend {
    public function __construct($service) {}
    public function get_ip() { return '127.0.0.1'; }
    public function assign_proxy($curl, $proxy) {}
    public function store($url, $type, $proxy) { return $url; }
    public function get($token, $type) { return [$token, null]; }
}

// 3. Define MOCK config
class config {
    const PROXY_GOOGLE = false;
    const USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36';
}