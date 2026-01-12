<?php
/**
 * Synchronizes sidecar manifest.json with 4get scrapers
 */

$root = __DIR__; // Expecting app root (/var/www/html inside container)
$scraperDir = $root . "/4get-repo/scraper";
$manifestPath = $root . "/manifest.json";

if (!is_dir($scraperDir)) {
    $scraperDir = $root . "/src/4get-repo/scraper";
    $manifestPath = $root . "/src/manifest.json";
}

if (!is_dir($scraperDir)) {
    echo "Error: Scraper directory not found at $scraperDir\n";
    exit(1);
}

$scrapers = [];
foreach (glob("$scraperDir/*.php") as $path) {
    if (basename($path) === 'sc.php' && !strpos(file_get_contents($path), 'class sc')) {
        continue;
    }

    $name = basename($path, ".php");
    $scrapers[$name] = [
        "file" => "scraper/" . basename($path),
        "class" => $name
    ];
}

if (isset($scrapers["ddg"])) {
    $scrapers["duckduckgo"] = $scrapers["ddg"];
    unset($scrapers["ddg"]);
}

ksort($scrapers);

$json = json_encode($scrapers, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
if (file_put_contents($manifestPath, $json)) {
    echo "Manifest successfully generated with " . count($scrapers) . " engines.\n";
} else {
    echo "Error: Failed to write manifest.json to $manifestPath\n";
    exit(1);
}
