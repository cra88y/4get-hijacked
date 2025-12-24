<?php
// FIX 1: Increase memory for large HTML blobs
ini_set('memory_limit', '256M');

header('Content-Type: application/json');

// 1. Load our Mock Classes first
require_once 'mock.php';

// 2. HIJACK THE INCLUDE PATH
// This forces 'include "lib/backend.php"' to find our empty files
// instead of the real ones in 4get-repo, preventing class redefinition errors.
set_include_path(__DIR__ . '/dummy_lib' . PATH_SEPARATOR . get_include_path());
// FIX 2: Read raw JSON input ($_POST is empty for JSON payloads)
$raw_input = file_get_contents('php://input');
$input = json_decode($raw_input, true);

if (!$input || !isset($input['scraper'])) {
    die(json_encode(['status' => 'error', 'message' => 'Invalid JSON input']));
}

$scraper_name = preg_replace('/[^a-z0-9_]/', '', $input['scraper']);
$html = $input['html'] ?? '';
$params = $input['params'] ?? [];

if (!file_exists("4get-repo/scraper/$scraper.php")) {
    die(json_encode(['status' => 'error', 'message' => "Scraper $scraper not found"]));
}

// 3. Load the Scraper
// It will now "include" our empty dummy files safely
chdir('4get-repo');
require_once "scraper/$scraper.php";

class_alias($scraper, 'TargetScraper');

class Hijacker extends TargetScraper {
    private $injected_html;
    public function __construct($html) {
        $this->injected_html = $html;
        // 4get scrapers don't have parents, but we wrap in try just in case
        try { @parent::__construct(); } catch (Throwable $t) {}
    }
    public function get($proxy, $url, $get = [], $alt_ua = false) {
        return $this->injected_html;
    }
}

// 4. Robust Error Handling (Auditor Recommendation)
try {
    $instance = new Hijacker($html);
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