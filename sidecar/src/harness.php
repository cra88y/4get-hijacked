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

// don't let 4get scraper warnings leak into the json response — kills all 4get engines if they do
$scraper_warnings = [];
$prev_handler = set_error_handler(function ($severity, $msg, $file, $line) use (&$scraper_warnings) {
    $scraper_warnings[] = ['severity' => $severity, 'msg' => $msg, 'file' => basename($file), 'line' => $line];
    return true;
});

try {
    $method = $input['category'] ?? 'web';

    if (!method_exists($instance, $method)) {
        throw new Exception("Method '$method' not supported by engine '$engine'");
    }

    $result = $instance->$method($params);

    // drain all levels — scrapers sometimes call ob_start() themselves
    while (ob_get_level() > 0) {
        ob_end_clean();
    }

    $resultCount = 0;
    if (isset($result[$method]) && is_array($result[$method])) {
        $resultCount = count($result[$method]);
    } elseif (isset($result['web']) && $method === 'web') {
        $resultCount = count($result['web']);
    }

    if ($resultCount === 0) {
        $warn_summary = !empty($scraper_warnings)
            ? ' (suppressed warnings: ' . $scraper_warnings[0]['file'] . ':' . $scraper_warnings[0]['line'] . ')'
            : '';
        error_log("Hijacker: Scraper '{$engine}' method '{$method}' returned 0 results{$warn_summary}");
    }

    if (!isset($result['npt']) && isset($instance->npt)) {
        $result['npt'] = $instance->npt;
    }

    echo json_encode($result) ?: '{"web":[]}';
} catch (Throwable $e) {
    // drain before writing error json
    while (ob_get_level() > 0) {
        ob_end_clean();
    }
    $msg = $e->getMessage();
    error_log("Hijacker Error [{$engine}]: {$msg}");

    $response = ['status' => 'error', 'message' => $msg];
    $msg_l = strtolower($msg);

    if (str_contains($msg_l, 'captcha') || str_contains($msg_l, 'pow')) {
        $response['suspend'] = 300;
    } elseif (str_contains($msg_l, 'too many request') || str_contains($msg_l, '429')) {
        $response['suspend'] = 60;
    } elseif (str_contains($msg_l, 'blocked') || str_contains($msg_l, 'forbidden') || str_contains($msg_l, '403')) {
        $response['suspend'] = 300;
    } elseif (str_contains($msg_l, 'not found') || str_contains($msg_l, 'not supported') || str_contains($msg_l, 'class ')) {
        $response['suspend'] = 300;
    } else {
        $response['suspend'] = 30;
    }

    echo json_encode($response);
} finally {
    restore_error_handler();
}