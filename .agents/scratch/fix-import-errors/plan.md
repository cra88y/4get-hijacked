# Task: Fix Import Errors in Engine Files

## Plan
- [x] Map the directory structure to locate engine files.
- [x] Identify files with incorrect import statements.
- [x] Update import statements to use relative imports.
- [x] Verify the changes.

## Research Log
---
### Directory Structure
- The repository contains multiple directories, including `searxng-custom` and `searxng-repo`.
- The `searxng-repo` directory likely contains the engine files that need to be updated.
### Engine Files Located
- The engine files are located in the `searxng-repo/searx/engines` directory.
- The directory contains multiple engine files, including `google.py`, `brave.py`, `duckduckgo.py`, and `yandex.py`.
### Search Results
- No files with `fourget_hijacker_client` found in the `searxng-repo/searx/engines` directory.
- This suggests that the files may not exist or the import issue is elsewhere.
### Next Steps
- Check the `searxng-custom` directory for the engine files.
- Verify if the `fourget_hijacker_client.py` file exists in the `searxng-custom` directory.
### Engine Files Located in searxng-custom
- The engine files are located in the `searxng-custom/engines` directory.
- The directory contains the following files:
- fourget_hijacker_client.py
- brave-4get.py
- duckduckgo-4get.py
- google-4get.py
- google-4get_updated.py
- yandex-4get.py
### Files with Incorrect Imports
- Found 2 files with incorrect import statements:
- `searxng-custom/engines/google-4get.py`
- `searxng-custom/engines/duckduckgo-4get.py`
### Changes Made
- Updated import statements in the following files:
- `searxng-custom/engines/google-4get.py`
- `searxng-custom/engines/duckduckgo-4get.py`
- Changed from `from searxng.fourget_hijacker_client import FourgetHijackerClient` to `from ..fourget_hijacker_client import FourgetHijackerClient`.
### File Structure Verification
- The user has provided feedback indicating that the files should be structured as follows:
- `searx/engines/`
- +-- google-4get.py
- +-- brave-4get.py
- +-- duckduckgo-4get.py
- +-- yandex-4get.py
- +-- fourget_hijacker_client.py
- This structure is not currently present in the `searxng-repo/searx/engines` directory.
- The files are currently located in the `searxng-custom/engines` directory.
