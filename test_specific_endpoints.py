#!/usr/bin/env python3
"""
Specific endpoint testing for YouTube to Infographic API
Quick tests for individual endpoints
"""

import requests
import json
import sys

API_BASE = "https://api.videotoinfographics.com"

def test_health():
    """Quick health check"""
    try:
        response = requests.get(f"{API_BASE}/api/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Health Check: API is healthy")
            print(f"   Services: {list(data.get('services', {}).keys())}")
            return True
        else:
            print(f"❌ Health Check: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health Check: {e}")
        return False

def test_templates():
    """Test templates endpoint"""
    try:
        response = requests.get(f"{API_BASE}/api/templates", timeout=10)
        if response.status_code == 200:
            data = response.json()
            templates = data.get('templates', [])
            print(f"✅ Templates: Found {len(templates)} templates")
            for template in templates[:3]:
                print(f"   - {template.get('name')} ({template.get('category')})")
            return True
        else:
            print(f"❌ Templates: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Templates: {e}")
        return False

def test_icon_search():
    """Test icon search"""
    try:
        search_data = {
            "content": "business growth success",
            "category": "business",
            "limit": 5
        }
        response = requests.post(
            f"{API_BASE}/api/icons/search", 
            json=search_data, 
            timeout=15
        )
        if response.status_code == 200:
            data = response.json()
            icons = data.get('icons', [])
            print(f"✅ Icon Search: Found {len(icons)} icons")
            for icon in icons[:3]:
                print(f"   - {icon.get('name')} (category: {icon.get('category')})")
            return True
        else:
            print(f"❌ Icon Search: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Icon Search: {e}")
        return False

def test_generate():
    """Test generation endpoint (without waiting for completion)"""
    try:
        test_data = {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
        response = requests.post(
            f"{API_BASE}/api/generate", 
            json=test_data, 
            timeout=15
        )
        if response.status_code == 200:
            data = response.json()
            job_id = data.get('jobId')
            print(f"✅ Generate: Job started with ID {job_id}")
            return job_id
        else:
            print(f"❌ Generate: HTTP {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Generate: {e}")
        return None

def main():
    """Run quick tests"""
    print("🚀 Quick API Tests")
    print("=" * 40)
    
    # Run tests
    health_ok = test_health()
    templates_ok = test_templates()
    icons_ok = test_icon_search()
    job_id = test_generate()
    
    print("\n" + "=" * 40)
    
    if health_ok and templates_ok:
        print("✅ Core API functionality is working")
        if job_id:
            print("✅ Video processing can be started")
            print(f"💡 Monitor job: {API_BASE}/api/status/{job_id}")
        print(f"📚 Full API docs: {API_BASE}/docs")
    else:
        print("❌ Some core functionality is not working")
    
    return 0 if health_ok else 1

if __name__ == "__main__":
    sys.exit(main())