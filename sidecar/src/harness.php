<?php
// Start output buffering immediately to catch any PHP warnings/notices
ob_start();

ini_set('memory_limit', '256M');
// Do not display errors to STDOUT, log them to STDERR instead
ini_set('display_errors', 0);
ini_set('log_errors', 1);

header('Content-Type: application/json');

require_once 'mock.php';

// Hijack include path
set_include_path(__DIR__ . '/dummy_lib' . PATH_SEPARATOR . __DIR__ . '/4get-repo' . PATH_SEPARATOR . get_include_path());

$raw_input = file_get_contents('php://input');
$input = json_decode($raw_input, true);

// Basic validation
if (!$input) {
    ob_end_clean();
    echo json_encode(['status' => 'error', 'message' => 'Invalid JSON payload received by sidecar']);
    exit;
}

$engine = preg_replace('/[^a-z0-9_]/', '', $input['engine'] ?? '');
$manifest = json_decode(file_get_contents(__DIR__ . '/manifest.json'), true);

if (!isset($manifest[$engine])) {
    ob_end_clean();
    echo json_encode(['status' => 'error', 'message' => "Engine $engine not found in manifest"]);
    exit;
}

$engine_config = $manifest[$engine];

// Change directory so internal includes work
chdir(__DIR__ . '/4get-repo');

if (!file_exists($engine_config['file'])) {
    ob_end_clean();
    echo json_encode(['status' => 'error', 'message' => "File not found: " . $engine_config['file']]);
    exit;
}

require_once $engine_config['file'];

$className = $engine_config['class'];
if (!class_exists($className)) {
    ob_end_clean();
    echo json_encode(['status' => 'error', 'message' => "Class $className not found"]);
    exit;
}

$instance = new $className();

$params = array_merge([
    's' => '', 'country' => 'us', 'nsfw' => 'yes', 'lang' => 'en'
], $input['params'] ?? []);

try {
    // 4get engines use the 'web' method for standard searches
    $result = $instance->web($params);
    
    // Clear the buffer (discard warnings) and send JSON
    ob_end_clean();
    echo json_encode($result);
} catch (Throwable $e) {
    // Clear buffer and send error JSON
    ob_end_clean();
    error_log("Hijacker Error: " . $e->getMessage());
    echo json_encode(['status' => 'error', 'message' => $e->getMessage()]);
}