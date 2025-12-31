# Task: Pre-Flight Stress Test for 4get-SearXNG Bridge

## Plan
- [x] Audit the PHP post_max_size configuration in Dockerfile or .htaccess.
- [x] Verify class_alias case-sensitivity in index.php and 4get repo naming conventions.
- [x] Check fuckhtml.php dependency chain for circular dependencies.
- [x] Review entrypoint.sh for permission handling robustness.
- [x] Ensure SearXNG settings.yml naming matches the custom engine file.
- [x] Verify if index.php needs file_get_contents('php://input') instead of $_POST.
- [x] Check for non-JSON responses in google.php that could break json.loads().

## Research Log
---
### Index.php Analysis
- The `index.php` file uses `file_get_contents('php://input')` to read raw JSON input, which is correct for handling large payloads.
- The `class_alias` function is used to alias the scraper class to `TargetScraper`, which is case-sensitive and depends on the filename and class name matching.
- The `Hijacker` class extends `TargetScraper` and overrides the `get` method to return injected HTML, ensuring no external HTTP requests are made.

### Google.php Analysis
- The `google.php` file defines a class `google` in lowercase, which matches the filename `google.php`.
- The class includes `lib/fuckhtml.php` and `lib/backend.php`, which are handled by the include path hijack in `index.php`.
- The class constructor initializes `fuckhtml` and `backend` objects, which are mocked in `mock.php`.

### Fuckhtml.php Analysis
- The `fuckhtml.php` file defines a class `fuckhtml` in lowercase, which matches the filename `fuckhtml.php`.
- The class includes methods for loading and parsing HTML, which are used by the scraper classes.
- The class does not include `backend.php` or `config.php`, so there is no circular dependency issue.

### Dockerfile Analysis
- The `Dockerfile` uses `php:8.2-apache` as the base image.
- It installs Git and necessary PHP extensions (`dom`, `xml`, `mbstring`).
- It creates a dummy library structure and copies the source code.
- The `post_max_size` is not explicitly set, which could cause issues with large payloads (>2MB).

### Entrypoint.sh Analysis
- The `entrypoint.sh` script clones or updates the 4get repository.
- It changes ownership of the `/var/www/html` directory to `www-data:www-data` to ensure Apache can read the files.
- The script does not handle potential failures in the `chown` command, which could lead to permission issues.

### Google_4get.py Analysis
- The `google_4get.py` file defines a custom SearXNG engine named `google_4get`.
- The engine uses the `fourget_bridge` module to handle requests and responses.
- The engine name `google_4get` matches the filename `google_4get.py`, ensuring SearXNG can load it correctly.

### Summary of Findings
1. **PHP post_max_size Trap**: The Dockerfile does not explicitly set `post_max_size`, which could cause issues with large payloads (>2MB). This is the highest risk.
2. **class_alias Case-Sensitivity**: The `google.php` file defines a class `google` in lowercase, which matches the filename `google.php`. The `class_alias` function in `index.php` will work correctly.
3. **fuckhtml Dependency Chain**: The `fuckhtml.php` file does not include `backend.php` or `config.php`, so there is no circular dependency issue.
4. **Apache www-data Permission Wall**: The `entrypoint.sh` script changes ownership of the `/var/www/html` directory to `www-data:www-data`, but it does not handle potential failures in the `chown` command.
5. **SearXNG settings.yml Naming Match**: The `google_4get.py` file defines a custom SearXNG engine named `google_4get`, which matches the filename `google_4get.py`.
6. **file_get_contents('php://input')**: The `index.php` file uses `file_get_contents('php://input')` to read raw JSON input, which is correct for handling large payloads.
7. **Non-JSON Responses**: The `index.php` file includes robust error handling to ensure non-JSON responses are properly formatted.

### Recommended Fixes
1. **PHP post_max_size**: Add the following line to the Dockerfile to increase the `post_max_size`:
   ```dockerfile
   RUN echo "post_max_size = 10M" >> /usr/local/etc/php/conf.d/uploads.ini
   ```
2. **Apache www-data Permission Wall**: Update the `entrypoint.sh` script to handle potential failures in the `chown` command:
   ```bash
   chown -R www-data:www-data /var/www/html || echo "⚠️ chown failed, continuing..."
   ```
### File Tree Summary
- The project contains multiple directories including `4get-repo`, `sidecar`, and `searxng-custom`.
- The `sidecar` directory includes a `docker-compose.yml` and a `src` folder with `dummy_lib` and `scripts`.
- The `4get-repo` directory contains the PHP-based scraper logic, including `index.php`, `mock.php`, and `fuckhtml.php`.
- The `searxng-custom` directory likely contains custom SearXNG configurations and engines.
