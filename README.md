# 4get-hijacked

Routes [4get](https://git.lolcat.ca/lolcat/4get) scrapers through a PHP sidecar for use as SearXNG engines.

## Structure

```
searx/engines/
  *-4get.py                    # SearXNG engine wrappers
  fourget_hijacker_client.py   # param/result normalization

sidecar/
  Dockerfile                   # clones 4get, installs curl-impersonate
  entrypoint.sh                # patches UA to match TLS fingerprint
  src/
    harness.php                # POST endpoint, loads scrapers
    manifest.json              # engine → scraper mapping
    mock.php                   # backend class, proxy, APCu state
    filters.php                # exposes scraper filters
    dummy_lib/                 # null includes for 4get paths

crab-engine/
  google-crab.py               # ported 4get google engine (1/1/26)

docker-compose.yml             # full stack: searxng + valkey + sidecar
settings-additions.yml         # SearXNG engine config block
```

## Run

```bash
docker compose up -d
```

Engines copied into SearXNG container at startup.

## Test Sidecar Directly

```bash
curl -X POST localhost:8081/harness.php \
  -d '{"engine":"wiby","params":{"s":"test"}}'
```

## Add Engine

1. Add to `manifest.json`:

   ```json
   "name": {"file": "scraper/name.php", "class": "name"}
   ```
2. Copy engine template to `searx/engines/name-4get.py`
3. Add config to `settings-additions.yml`

## Engines

google, brave, duckduckgo, yandex, mojeek, wiby, yep, marginalia, curlie, baidu, crowdview

## Notes

- 4get cloned at build from `git.lolcat.ca/lolcat/4get`
- curl-impersonate Chrome 116 for TLS fingerprint
- APCu for pagination tokens (1hr TTL)
- `FOURGET_PROXIES` env: `ip:port,ip:port:user:pass`
