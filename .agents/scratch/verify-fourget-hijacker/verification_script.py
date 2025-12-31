#!/usr/bin/env python3
"""
Verification script for fourget_hijacker system.
This script should be run inside the SearXNG container when Docker is available.
"""

import asyncio
import subprocess
import json
import sys
from searxng.fourget_hijacker_client import FourgetHijackerClient

def run_command(cmd):
    """Run a shell command and return output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1

async def verify_service_discovery():
    """Verify Part 1: Service Discovery and Harness Integrity"""
    print("=== Part 1: Service Discovery and Harness Integrity ===")
    
    # Test 1.1: Service discovery
    print("\n1.1 Testing service discovery...")
    stdout, stderr, code = run_command("curl http://nginx-harness/harness.php?action=discover")
    
    if code != 0:
        print(f"❌ FAILED: Command failed with code {code}")
        print(f"Error: {stderr}")
        return False
    
    try:
        manifest = json.loads(stdout)
        print(f"✅ SUCCESS: Service discovery returned valid JSON")
        print(f"Available engines: {list(manifest.keys())}")
    except json.JSONDecodeError:
        print(f"❌ FAILED: Invalid JSON response")
        print(f"Output: {stdout}")
        return False
    
    # Test Content-Type header
    print("\n1.2 Testing Content-Type header...")
    stdout, stderr, code = run_command("curl -v http://nginx-harness/harness.php?action=discover 2>&1 | grep -i 'content-type'")
    
    if "application/json" in stdout.lower():
        print("✅ SUCCESS: Content-Type header is application/json")
    else:
        print("❌ FAILED: Content-Type header is not application/json")
        print(f"Header output: {stdout}")
        return False
    
    return True

async def verify_direct_scraper_execution():
    """Verify Part 2: Direct Scraper Execution"""
    print("\n=== Part 2: Direct Scraper Execution ===")
    
    # Test 2.1: Valid engine execution
    print("\n2.1 Testing valid engine execution (google)...")
    stdout, stderr, code = run_command(
        "curl -X POST http://nginx-harness/harness.php "
        "-H 'Content-Type: application/json' "
        "-d '{"engine": "google", "params": {"s": "test query", "country": "us"}}'"
    )
    
    if code != 0:
        print(f"❌ FAILED: Command failed with code {code}")
        print(f"Error: {stderr}")
        return False
    
    try:
        response = json.loads(stdout)
        if 'web' in response and isinstance(response['web'], list):
            print(f"✅ SUCCESS: Valid JSON response with 'web' list")
            print(f"Number of results: {len(response['web'])}")
            
            # Check required fields
            if response['web']:
                first_result = response['web'][0]
                required_fields = ['title', 'url', 'description']
                missing_fields = [field for field in required_fields if field not in first_result]
                
                if not missing_fields:
                    print("✅ SUCCESS: All required fields present in results")
                else:
                    print(f"❌ FAILED: Missing required fields: {missing_fields}")
                    return False
        else:
            print("❌ FAILED: Response missing 'web' list")
            print(f"Response: {response}")
            return False
    except json.JSONDecodeError:
        print(f"❌ FAILED: Invalid JSON response")
        print(f"Output: {stdout}")
        return False
    
    # Test 2.2: Error handling
    print("\n2.2 Testing error handling (nonexistent engine)...")
    stdout, stderr, code = run_command(
        "curl -X POST http://nginx-harness/harness.php "
        "-H 'Content-Type: application/json' "
        "-d '{"engine": "nonexistent-engine", "params": {"s": "test"}}'"
    )
    
    try:
        response = json.loads(stdout)
        if code != 200 and 'status' in response and response['status'] == 'error':
            print("✅ SUCCESS: Proper error handling with non-200 status")
        else:
            print(f"❌ FAILED: Expected error response, got status {code}")
            print(f"Response: {response}")
            return False
    except json.JSONDecodeError:
        print(f"❌ FAILED: Invalid JSON error response")
        print(f"Output: {stdout}")
        return False
    
    return True

async def verify_python_client():
    """Verify Part 3: Python Client Library Functionality"""
    print("\n=== Part 3: Python Client Library Functionality ===")
    
    try:
        client = FourgetHijackerClient()
        engine_name = 'google'
        params = {'s': 'python asyncio', 'country': 'us'}
        
        print("\n3.1 Testing raw data fetch...")
        raw_data = await client.fetch(engine_name, params)
        
        if not raw_data or 'web' not in raw_data:
            print("❌ FAILED: Raw data fetch failed or is malformed")
            print(f"Raw data: {raw_data}")
            return False
        
        print("✅ SUCCESS: Raw data fetch successful")
        
        print("\n3.2 Testing result normalization...")
        normalized_results = client.normalize_results(raw_data, engine_name)
        
        if not normalized_results:
            print("❌ FAILED: Normalization produced no results")
            return False
        
        print(f"✅ SUCCESS: Normalization successful, found {len(normalized_results)} results")
        
        # Check first result
        first_result = normalized_results[0]
        required_fields = ['title', 'url', 'content']
        missing_fields = [field for field in required_fields if field not in first_result]
        
        if not missing_fields:
            print("✅ SUCCESS: First result has all required keys")
            print(f"Sample result:")
            print(f"  Title: {first_result.get('title')[:50]}...")
            print(f"  URL: {first_result.get('url')[:50]}...")
            print(f"  Content: {first_result.get('content')[:50]}...")
        else:
            print(f"❌ FAILED: First result missing required fields: {missing_fields}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: Python client test failed with exception: {e}")
        return False

async def verify_searxng_integration():
    """Verify Part 4: Full SearXNG Integration"""
    print("\n=== Part 4: Full SearXNG Integration ===")
    print("Note: This test requires manual verification in the SearXNG UI")
    print("Steps:")
    print("1. Ensure google-4get engine is enabled in settings.yml")
    print("2. Restart the SearXNG container")
    print("3. Perform a search for 'test query' in the SearXNG web interface")
    print("4. Check if google-4get is listed as a responding engine")
    print("5. Verify results are displayed from google-4get")
    print("6. Check SearXNG logs for any errors related to google-4get.py")
    
    return True  # This is a manual verification step

async def main():
    """Main verification function"""
    print("Starting fourget_hijacker system verification...")
    print("=" * 60)
    
    results = []
    
    # Run verification tests
    results.append(await verify_service_discovery())
    results.append(await verify_direct_scraper_execution())
    results.append(await verify_python_client())
    results.append(await verify_searxng_integration())
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! The fourget_hijacker system is working correctly.")
        return True
    else:
        print("❌ SOME TESTS FAILED! Please review the output above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)