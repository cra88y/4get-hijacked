# Task: Logical Bridge Verification for fourget_hijacker

## Plan
- [ ] Bridge 1: Stub-to-Client Parameter Translation
  - [ ] Add debug logging to harness.php
  - [ ] Create parameter translation test script
  - [ ] Verify language parameter translation (lang_de -> de)
  - [ ] Verify date filter parameter translation
  - [ ] Test with all engines in manifest
- [ ] Bridge 2: Harness-to-Scraper Engine Signature Consistency
  - [ ] Create engine compatibility test script
  - [ ] Test all engines from manifest.json
  - [ ] Verify 200 OK responses for all engines
  - [ ] Document any engine-specific issues
- [ ] Bridge 3: Scraper-to-Client Data Normalization
  - [ ] Create raw JSON capture script
  - [ ] Capture output from multiple engines
  - [ ] Create normalization unit test
  - [ ] Verify all required fields present
  - [ ] Test field name variations (description vs snippet)

## Research Log
---
