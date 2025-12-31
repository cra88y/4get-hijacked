<?php
// 1. Start output buffering immediately.
// This traps any PHP warnings, notices, or accidental whitespace from includes.
ob_start();

// 2. Disable display_errors so they don't break JSON. Log them instead.
ini_set('display_errors', 0);
ini_set('log_errors', 1);
header('Content-Type: application/json');

try {
    require_once 'mock.php';

    // Hijack include path
    set_include_path(__DIR__ . '/dummy_lib' . PATH_SEPARATOR . __DIR__ . '/4get-repo' . PATH_SEPARATOR . get_include_path());

    $raw_input = file_get_contents('php://input');
    $input = json_decode($raw_input, true);

    if (!$input) {
        throw new Exception('Invalid JSON payload');
    }

    $engine = preg_replace('/[^a-z0-9_]/', '', $input['engine'] ?? '');
    $page = $input['page'] ?? 'web';
    
    $manifestPath = __DIR__ . '/manifest.json';
    if (!file_exists($manifestPath)) {
        throw new Exception('Manifest not found');
    }

    $manifest = json_decode(file_get_contents($manifestPath), true);

    if (!isset($manifest[$engine])) {
        throw new Exception("Engine '$engine' not found in manifest");
    }

    $engine_config = $manifest[$engine];
    
    // Change directory so internal 4get includes work
    chdir(__DIR__ . '/4get-repo');
    
    if (!file_exists($engine_config['file'])) {
        throw new Exception("Engine file not found: " . $engine_config['file']);
    }

    require_once $engine_config['file'];
    $className = $engine_config['class'];
    
    if (!class_exists($className)) {
        throw new Exception("Class '$className' not found");
    }

    $instance = new $className();

    // 3. Safely get filters
    $result = [];
    if (method_exists($instance, 'getfilters')) {
        $result = $instance->getfilters($page);
    } elseif (isset($instance->filter)) {
        $result = $instance->filter;
    }

    // 4. Clean the buffer (discard warnings) and output ONLY the JSON
    ob_end_clean();
    echo json_encode($result);

} catch (Throwable $e) {
    // On error, clean buffer and return empty JSON to prevent SearXNG crash
    ob_end_clean();
    error_log("Filters.php Error for engine '$engine': " . $e->getMessage());
    echo json_encode([]); 
}