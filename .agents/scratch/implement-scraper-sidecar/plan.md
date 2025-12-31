# Task: Implement Scraper Sidecar and Bridge

## Plan
- [x] Create sidecar directory structure
- [x] Implement PHP Sidecar components (Dockerfile, entrypoint.sh, mock.php, index.php)
- [x] Create searxng-custom directory structure
- [x] Implement Python Bridge components (fourget_bridge.py and engine stubs)
- [x] Create docker-compose.yml
- [x] Verify implementation structure

## Research Log
---
### PHP Sidecar Implementation
- Created sidecar/Dockerfile with PHP 8.2 and required extensions
- Created sidecar/entrypoint.sh with auto-update logic for 4get repository
- Created sidecar/src/mock.php with mock backend and config classes
- Created sidecar/src/index.php with generic PHP bridge and dynamic scraper loading

### Python Bridge Implementation
- Created searxng-custom/engines/fourget_bridge.py with factory pattern for scraper integration
- Created searxng-custom/engines/google_4get.py engine stub for Google searches
- Created searxng-custom/engines/brave_4get.py engine stub for Brave searches
- Bridge communicates with sidecar via HTTP POST to http://4get-sidecar:80

### Docker Compose Orchestration
- Created docker-compose.yml with two services: 4get-sidecar and searxng
- Services communicate via shared bridge network (searxng-network)
- Sidecar exposes port 8080, SearXNG exposes port 8081
- Volume mounts for custom engines and 4get repository persistence

### Final Implementation Structure
- ✅ PHP Sidecar: Dockerized PHP 8.2 with auto-updating 4get scrapers
- ✅ Python Bridge: Factory-based engine integration with HTTP communication
- ✅ Engine Stubs: Google and Brave search engines using the bridge
- ✅ Docker Compose: Orchestrated multi-container setup with proper networking
- ✅ Architecture: Decoupled design with clear separation of concerns
