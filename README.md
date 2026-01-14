# 4get-hijacked

4get that doesn't suck?

Routes [4get](https://git.lolcat.ca/lolcat/4get) engines through a PHP sidecar for fast and parallel use as SearXNG engines. (aka 4get results 4 Searxng)

Feats:

- Allows 4get engines to be used in parallel (not normally possible)
- Minimal overhead to stay fast, beat some of Searxng's own engine equivalents as well as tested 4get instances.
- 4get's rich meta data scraping is normalized into compatible Searxng result types. (answer boxes, info boxes, search suggestions, prepended directly into snippets, etc.)
- no core modifications to 4get/searxng
- 4get cloned during deployment for upstream engine fixes
- literally doesn't even run 4get itself
- Searxng search parameters preserved where possible, capabilities vary by 4get engine (time range, language, country, safe search)
- 4get engine specifc params are settable in Settings.yml for the given engine, blind injection to support any known 4get engine specific param. (eg. Brave engine can take a spellcheck parameter, `fg_spellcheck: true` in the Settings.yml engine block will enable it)
- containerized for super easy installing/updating

## Structure

```
searx/engines/
  *-4get.py                    # Searxng engine wrappers
  fourget_hijacker_client.py   # param/result normalization

sidecar/
  Dockerfile                   # clones 4get, installs curl-impersonate
  entrypoint.sh                # patches UA to match TLS fingerprint
  src/
    harness.php                # POST endpoint to return the 4get results
    mock.php                   # backend class, proxy, APCu state
    filters.php                # exposes 4get engine filters
    dummy_lib/                 # null includes for 4get paths

docker-compose.yml             # full stack example: searxng + valkey + hijacker sidecar
settings-additions.yml         # Engine configs blocks needed for Searxng's settings.yml
```

## Run

```bash
docker compose up -d
```

## Test The Sidecar

```bash
curl -X POST localhost:8081/harness.php \
  -d '{"engine":"google","params":{"s":"test"}}'
```

## Engines

google, brave, duckduckgo, yandex, wiby, marginalia, crowdview... (these I use frequently with no issues)
All of the current 4get engines, like 35 at the moment, some are broken. lolcat, pls fix.  

## Steal Even More 4get Engines Why Not

1. Ensure engine exists in 4get master repo scrapers folder, note exact name.
2. Copy another engine's stub to `searx/engines/{exact-engine-name}-4get.py`
3. Update the categories array with Searxng related categories that the 4get engine supports.
4. Add config to `settings-additions.yml`

## Notes

- 4get cloned at build from `git.lolcat.ca/lolcat/4get`
- curl-impersonate for additional stealth (method copied from 4get)
- supports pagination tokens using hash lookup in sidecar
- `FOURGET_PROXIES` env: `ip:port,ip:port:user:pass` (untested proxy rotation, my Hetzner deploy with a couple users doesn't really get engine blocks/captchas)
