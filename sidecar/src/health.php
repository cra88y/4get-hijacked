<?php
header('Content-Type: application/json');

$health = [
    'status' => 'ok',
    'timestamp' => time(),
    'checks' => []
];

// 1. Check APCu
if (function_exists('apcu_enabled') && apcu_enabled()) {
    $health['checks']['apcu'] = 'ok';
} else {
    $health['status'] = 'degraded';
    $health['checks']['apcu'] = 'disabled';
}

// 2. Check 4get repo
if (is_dir(__DIR__ . '/4get-repo/scraper')) {
    $health['checks']['4get_repo'] = 'ok';
} else {
    $health['status'] = 'error';
    $health['checks']['4get_repo'] = 'missing';
}

// 3. Check manifest
if (file_exists(__DIR__ . '/manifest.json')) {
    $manifest = json_decode(file_get_contents(__DIR__ . '/manifest.json'), true);
    $health['checks']['manifest'] = 'ok';
    $health['engine_count'] = count($manifest);
} else {
    $health['status'] = 'error';
    $health['checks']['manifest'] = 'missing';
}

// 4. APCu memory stats (if available)
if (function_exists('apcu_sma_info')) {
    $sma = apcu_sma_info();
    $health['apcu_memory'] = [
        'used_mb' => round($sma['seg_size'] - $sma['avail_mem'], 2) / 1024 / 1024,
        'total_mb' => round($sma['seg_size'] / 1024 / 1024, 2)
    ];
}

http_response_code($health['status'] === 'ok' ? 200 : 503);
echo json_encode($health, JSON_PRETTY_PRINT);
