<?php
ob_start();

ini_set('memory_limit', '256M');
ini_set('display_errors', 0);
ini_set('log_errors', 1);

header('Content-Type: application/json');

require_once 'mock.php';

set_include_path(__DIR__ . '/dummy_lib' . PATH_SEPARATOR . __DIR__ . '/4get-repo' . PATH_SEPARATOR . get_include_path());

$raw_input = file_get_contents('php://input');
$input = json_decode($raw_input, true);

// Basic validation
if (!$input) {
    ob_end_clean();
    echo json_encode(['status' => 'error', 'message' => 'Invalid JSON payload received by sidecar']);
    exit;
}

$engine_input = str_replace('-', '_', $input['engine'] ?? '');
$engine = preg_replace('/[^a-z0-9_]/', '', $engine_input);

$manifest = apcu_fetch('hijacker_manifest');
if ($manifest === false) {
    $manifest = json_decode(file_get_contents(__DIR__ . '/manifest.json'), true);
    apcu_store('hijacker_manifest', $manifest, 0);
}

if (!isset($manifest[$engine])) {
    ob_end_clean();
    echo json_encode(['status' => 'error', 'message' => "Engine $engine not found in manifest"]);
    exit;
}

$engine_config = $manifest[$engine];

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

$defaults = [
    's' => '', 
    'country' => 'us', 
    'nsfw' => 'yes', 
    'lang' => 'en',
    'npt' => null,
    'older' => false,
    'newer' => false,
    'spellcheck' => 'yes',
    'focus' => 'any',
    'region' => 'any',
    'domain' => '1',
    'date' => 'any',
    'extendedsearch' => 'no',
    'intitle' => 'no',
    'format' => 'any',
    'file' => 'any',
    'javascript' => 'any',
    'trackers' => 'any',
    'cookies' => 'any',
    'affiliate' => 'any',
    'adtech' => 'yes',
    'recent' => 'no'
];

$input_params = $input['params'] ?? [];
$params = $input_params + $defaults;

backend::$context = [
    'engine' => $engine,
    's' => $params['s'] ?? '',
    'offset' => $params['offset'] ?? 0
];

if (($params['offset'] ?? 0) > 0 && empty($params['npt'])) {
    $det_key = md5($engine . ($params['s'] ?? '') . $params['offset']);
    $stored_token = apcu_fetch("4get_det_$det_key");
    
    if ($stored_token) {
        $params['npt'] = $stored_token;
    } else {
        ob_end_clean();
        exit('[]');
    }
}

try {
    $method = $input['category'] ?? 'web';

    if (!method_exists($instance, $method)) {
        throw new Exception("Method '$method' not supported by engine '$engine'");
    }

    $result = $instance->$method($params);

    $resultCount = 0;
    if (isset($result[$method]) && is_array($result[$method])) {
        $resultCount = count($result[$method]);
    } elseif (isset($result['web']) && $method === 'web') {
        $resultCount = count($result['web']);
    }
    
    if ($resultCount === 0) {
        error_log("Hijacker: Scraper '{$engine}' method '{$method}' returned 0 results.");
    }

    if (isset($result['npt'])) {
        // It's already there, do nothing
    } elseif (isset($instance->npt)) {
        $result['npt'] = $instance->npt;
    }

    ob_end_clean();
    echo json_encode($result);
} catch (Throwable $e) {
    ob_end_clean();
    error_log("Hijacker Error: " . $e->getMessage());
    echo json_encode(['status' => 'error', 'message' => $e->getMessage()]);
}