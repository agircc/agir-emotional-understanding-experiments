#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
from dotenv import load_dotenv

def main():
    """Check environment configuration and provide diagnostic information"""
    print("Environment Check Tool")
    print("======================")
    
    # Check Python version
    print(f"Python version: {sys.version}")
    
    # Check OPENAI_API_KEY
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        masked_key = api_key[:5] + "*" * (len(api_key) - 9) + api_key[-4:]
        print(f"OPENAI_API_KEY: {masked_key} (valid)")
    else:
        print("OPENAI_API_KEY: not set (please configure in .env file)")
    
    # Check environment variables that may affect OpenAI client
    proxy_vars = ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 
                  'OPENAI_PROXY', 'openai_proxy']
    
    found_proxies = False
    print("\nProxy settings that may affect OpenAI client:")
    for var in proxy_vars:
        if var in os.environ:
            found_proxies = True
            print(f"  - {var}: {os.environ[var]}")
    
    if not found_proxies:
        print("  No proxy settings detected")
    
    # Provide recommendations if proxy settings are found
    if found_proxies:
        print("\nProxy settings detected that may cause OpenAI client initialization issues. Recommendations:")
        print("1. Temporary solution: Clear these variables before running the code")
        print("   Example: unset HTTP_PROXY HTTPS_PROXY")
        print("2. Handle proxy settings explicitly in the code (already implemented in main.py)")
    
    print("\nDependency check:")
    try:
        import openai
        print(f"  openai version: {openai.__version__}")
    except ImportError:
        print("  openai library not installed")
    
    try:
        import tqdm
        print(f"  tqdm version: {tqdm.__version__}")
    except ImportError:
        print("  tqdm library not installed")

if __name__ == "__main__":
    main() 