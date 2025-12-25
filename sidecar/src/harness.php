<?php
// Increase memory for large HTML blobs
ini_set('memory_limit', '256M');

header('Content-Type: application/json');

// Load our Mock Classes first
require_once 'mock.php';

// HIJACK THE INCLUDE PATH
// This forces 'include "lib/backend.php"' to find our empty files
// instead of the real ones in 4get-repo, preventing class redefinition errors.
set_include_path(__DIR__ . '/dummy_lib' . PATH_SEPARATOR . get_include_path());

// Read raw JSON input ($_POST is empty for JSON payloads)
$raw_input = file_get_contents('php://input');
$input = json_decode($raw_input, true);

if (!$input || !isset($input['engine'])) {
    die(json_encode(['status' => 'error', 'message' => 'Invalid JSON input']));
}

$engine = preg_replace('/[^a-z0-9_]/', '', $input['engine']);
$params = $input['params'] ?? [];

// Load manifest.json to find the engine's file and class
$manifest_path = __DIR__ . '/manifest.json';
if (!file_exists($manifest_path)) {
    die(json_encode(['status' => 'error', 'message' => 'Manifest file not found']));
}

$manifest = json_decode(file_get_contents($manifest_path), true);
if (!isset($manifest[$engine])) {
    die(json_encode(['status' => 'error', 'message' => "Engine $engine not found in manifest"]));
}

$engine_config = $manifest[$engine];
$engine_file = $engine_config['file'];
$engine_class = $engine_config['class'];

// Load the Scraper
// It will now "include" our empty dummy files safely
chdir('4get-repo');
if (!file_exists($engine_file)) {
    die(json_encode(['status' => 'error', 'message' => "Engine file $engine_file not found"]));
}
require_once $engine_file;

class_alias($engine_class, 'TargetEngine');

class Hijacker extends TargetEngine {
    public function __construct() {
        // 4get scrapers don't have parents, but we wrap in try just in case
        try { @parent::__construct(); } catch (Throwable $t) {}
    }
    public function get($proxy, $url, $get = [], $alt_ua = false) {
        // Override the get method to prevent actual HTTP requests
        return '';
    }
}

// Robust Error Handling (Auditor Recommendation)
try {
    $instance = new Hijacker();
    $final_params = array_merge([
        's' => '', 'country' => 'us', 'nsfw' => 'yes', 'lang' => 'en',
        'older' => false, 'newer' => false, 'spellcheck' => 'yes', 'npt' => null
    ], $params);

    $method = $input['method'] ?? 'web';
    echo json_encode($instance->$method($final_params));

} catch (Throwable $e) {
    echo json_encode([
        'status' => 'error',
        'message' => $e->getMessage(),
        'file' => basename($e->getFile()),
        'line' => $e->getLine()
    ]);
}
