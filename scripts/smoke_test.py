#!/usr/bin/env python3
"""
Smoke test for Gemma 4 E4B via Ollama API
Tests basic connectivity, latency, and response quality
"""

import json
import time
import requests
from typing import Dict, Any

OLLAMA_API = "http://localhost:11434/api/generate"
MODEL = "gemma4:latest"

def test_query(prompt: str, max_tokens: int = 100, timeout: int = 30) -> Dict[str, Any]:
    """Send query to Ollama and measure latency"""
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "think": False,  # Disable thinking mode for Gemma 4
        "options": {
            "num_predict": max_tokens,
            "temperature": 0.1
        }
    }
    
    start = time.time()
    try:
        response = requests.post(OLLAMA_API, json=payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        elapsed = time.time() - start
        
        return {
            "success": True,
            "response": data.get("response", ""),
            "latency": round(elapsed, 2),
            "total_duration": round(data.get("total_duration", 0) / 1e9, 2),
            "load_duration": round(data.get("load_duration", 0) / 1e9, 2),
            "prompt_eval_count": data.get("prompt_eval_count", 0),
            "eval_count": data.get("eval_count", 0)
        }
    except requests.exceptions.Timeout:
        elapsed = time.time() - start
        return {
            "success": False,
            "error": "Timeout",
            "latency": round(elapsed, 2)
        }
    except Exception as e:
        elapsed = time.time() - start
        return {
            "success": False,
            "error": str(e),
            "latency": round(elapsed, 2)
        }

def main():
    print("=" * 60)
    print("Sub-Centre Mind — Gemma 4 Smoke Test")
    print("=" * 60)
    
    # Test 1: Simple arithmetic
    print("\n[Test 1] Simple query: '2+2'")
    result = test_query("What is 2+2?", max_tokens=10, timeout=20)
    if result["success"]:
        print(f"✅ Response: {result['response'].strip()}")
        print(f"   Latency: {result['latency']}s (load: {result['load_duration']}s)")
    else:
        print(f"❌ Failed: {result.get('error', 'Unknown')}")
        print(f"   Latency: {result['latency']}s")
    
    # Test 2: IFA protocol query (Gate 1 requirement)
    print("\n[Test 2] IFA protocol query")
    result = test_query(
        "IFA tablet dose for pregnant women per MoHFW guidelines?",
        max_tokens=50,
        timeout=30
    )
    if result["success"]:
        print(f"✅ Response: {result['response'].strip()}")
        print(f"   Latency: {result['latency']}s (Gate 1 target: <12s)")
        if result['latency'] > 12:
            print(f"   ⚠️  WARNING: Latency exceeds Gate 1 requirement!")
    else:
        print(f"❌ Failed: {result.get('error', 'Unknown')}")
        print(f"   Latency: {result['latency']}s")
    
    # Test 3: Hindi query (multilingual requirement)
    print("\n[Test 3] Hindi query")
    result = test_query(
        "गर्भवती महिलाओं के लिए IFA टैबलेट की खुराक क्या है?",
        max_tokens=50,
        timeout=30
    )
    if result["success"]:
        print(f"✅ Response: {result['response'].strip()}")
        print(f"   Latency: {result['latency']}s")
    else:
        print(f"❌ Failed: {result.get('error', 'Unknown')}")
        print(f"   Latency: {result['latency']}s")
    
    print("\n" + "=" * 60)
    print("Smoke test complete. Check latency against Gate 1 target (<12s).")
    print("=" * 60)

if __name__ == "__main__":
    main()
