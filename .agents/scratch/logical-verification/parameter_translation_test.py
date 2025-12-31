#!/usr/bin/env python3
"""
Parameter Translation Verification Script
Tests the stub-to-client parameter translation logic
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'searxng-custom'))

from engines.google_4get import request as google_request
from engines.duckduckgo_4get import request as duckduckgo_request
from fourget_hijacker_client import FourgetHijackerClient

def test_parameter_translation():
    """Test parameter translation for different engines"""
    print("=== Parameter Translation Verification ===")
    
    # Test cases for different scenarios
    test_cases = [
        {
            'name': 'German language test',
            'params': {
                'searxng_locale': 'de-DE',
                'safesearch': 0
            },
            'expected': {
                'lang': 'de',
                'country': 'de'
            }
        },
        {
            'name': 'French language test',
            'params': {
                'searxng_locale': 'fr-FR',
                'safesearch': 1
            },
            'expected': {
                'lang': 'fr',
                'country': 'fr',
                'nsfw': 'no'
            }
        },
        {
            'name': 'US English with safe search',
            'params': {
                'searxng_locale': 'en-US',
                'safesearch': 2
            },
            'expected': {
                'lang': 'en',
                'country': 'us',
                'nsfw': 'no'
            }
        }
    ]
    
    # Mock the client to capture the translated parameters
    class MockClient:
        def __init__(self):
            self.last_params = None
            self.last_engine = None
            
        def fetch(self, engine, params):
            self.last_engine = engine
            self.last_params = params
            return {'status': 'ok', 'web': []}
    
    # Test Google engine
    print("\n--- Testing Google Engine ---")
    mock_client = MockClient()
    
    # Monkey patch the client
    original_client = FourgetHijackerClient
    FourgetHijackerClient = lambda: mock_client
    
    try:
        for test_case in test_cases:
            print(f"\nTest: {test_case['name']}")
            result = google_request("test query", test_case['params'])
            
            print(f"Input params: {test_case['params']}")
            print(f"Translated params: {mock_client.last_params}")
            
            # Verify translation
            success = True
            for key, expected_value in test_case['expected'].items():
                actual_value = mock_client.last_params.get(key)
                if actual_value != expected_value:
                    print(f"❌ FAILED: {key} = {actual_value}, expected {expected_value}")
                    success = False
                else:
                    print(f"✅ OK: {key} = {actual_value}")
            
            if success:
                print("✅ Test passed")
            else:
                print("❌ Test failed")
    
    finally:
        # Restore original client
        FourgetHijackerClient = original_client
    
    # Test DuckDuckGo engine (should be similar)
    print("\n--- Testing DuckDuckGo Engine ---")
    mock_client = MockClient()
    FourgetHijackerClient = lambda: mock_client
    
    try:
        for test_case in test_cases:
            print(f"\nTest: {test_case['name']}")
            result = duckduckgo_request("test query", test_case['params'])
            
            print(f"Input params: {test_case['params']}")
            print(f"Translated params: {mock_client.last_params}")
            
            # Verify translation
            success = True
            for key, expected_value in test_case['expected'].items():
                actual_value = mock_client.last_params.get(key)
                if actual_value != expected_value:
                    print(f"❌ FAILED: {key} = {actual_value}, expected {expected_value}")
                    success = False
                else:
                    print(f"✅ OK: {key} = {actual_value}")
            
            if success:
                print("✅ Test passed")
            else:
                print("❌ Test failed")
    
    finally:
        # Restore original client
        FourgetHijackerClient = original_client

if __name__ == "__main__":
    test_parameter_translation()