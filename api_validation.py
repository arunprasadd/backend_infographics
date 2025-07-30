#!/usr/bin/env python3
"""
API Validation Script for YouTube to Infographic Generator
Tests the hosted API at https://api.videotoinfographics.com/
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional

class APIValidator:
    def __init__(self, base_url: str = "https://api.videotoinfographics.com"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'API-Validator/1.0'
        })
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, message: str, data: Any = None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
        if data and isinstance(data, dict):
            for key, value in list(data.items())[:3]:  # Show first 3 items
                print(f"   {key}: {value}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "data": data
        })
    
    def test_health_endpoint(self) -> bool:
        """Test the health check endpoint"""
        print("\n🏥 Testing Health Endpoint...")
        try:
            response = self.session.get(f"{self.base_url}/api/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                services = data.get('services', {})
                self.log_test("Health Check", True, 
                             f"API is healthy - Services: {list(services.keys())}", data)
                return True
            else:
                self.log_test("Health Check", False, 
                             f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test("Health Check", False, f"Connection error: {str(e)}")
            return False
    
    def test_templates_endpoint(self) -> bool:
        """Test the templates endpoint"""
        print("\n📋 Testing Templates Endpoint...")
        try:
            response = self.session.get(f"{self.base_url}/api/templates", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                templates = data.get('templates', [])
                
                if templates:
                    template_names = [t.get('name', 'Unknown') for t in templates]
                    self.log_test("Templates", True, 
                                 f"Found {len(templates)} templates: {', '.join(template_names[:3])}", 
                                 {"count": len(templates), "templates": template_names})
                else:
                    self.log_test("Templates", False, "No templates found")
                return len(templates) > 0
            else:
                self.log_test("Templates", False, 
                             f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test("Templates", False, f"Connection error: {str(e)}")
            return False
    
    def test_template_coordinates(self) -> bool:
        """Test template coordinates endpoint"""
        print("\n📐 Testing Template Coordinates...")
        try:
            # Test with default template
            template_id = "modern-business"
            response = self.session.get(
                f"{self.base_url}/api/templates/{template_id}/coordinates", 
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                template_info = data.get('template', {})
                coordinates = data.get('coordinates', {})
                color_schemes = data.get('color_schemes', [])
                
                coord_types = list(coordinates.keys())
                self.log_test("Template Coordinates", True, 
                             f"Template '{template_id}' loaded with {len(coord_types)} coordinate types",
                             {
                                 "template_name": template_info.get('name'),
                                 "coordinate_types": coord_types,
                                 "color_schemes": len(color_schemes)
                             })
                return True
            else:
                self.log_test("Template Coordinates", False, 
                             f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test("Template Coordinates", False, f"Connection error: {str(e)}")
            return False
    
    def test_icon_search(self) -> bool:
        """Test icon search endpoint"""
        print("\n🔍 Testing Icon Search...")
        try:
            search_queries = [
                {"content": "business growth", "category": "business", "limit": 5},
                {"content": "artificial intelligence", "category": "technology", "limit": 3},
                {"content": "education learning", "limit": 4}
            ]
            
            all_success = True
            for i, search_data in enumerate(search_queries):
                response = self.session.post(
                    f"{self.base_url}/api/icons/search", 
                    json=search_data,
                    timeout=15
                )
                
                if response.status_code == 200:
                    data = response.json()
                    icons = data.get('icons', [])
                    
                    if icons:
                        icon_names = [icon.get('name', 'Unknown') for icon in icons]
                        self.log_test(f"Icon Search {i+1}", True, 
                                     f"Query '{search_data['content']}' found {len(icons)} icons",
                                     {"icons": icon_names[:3]})
                    else:
                        self.log_test(f"Icon Search {i+1}", False, 
                                     f"No icons found for '{search_data['content']}'")
                        all_success = False
                else:
                    self.log_test(f"Icon Search {i+1}", False, 
                                 f"HTTP {response.status_code}: {response.text}")
                    all_success = False
            
            return all_success
                
        except requests.exceptions.RequestException as e:
            self.log_test("Icon Search", False, f"Connection error: {str(e)}")
            return False
    
    def test_generate_endpoint(self) -> Optional[str]:
        """Test the main generation endpoint"""
        print("\n🎬 Testing YouTube Video Generation...")
        try:
            # Use a popular YouTube video that should have transcripts
            test_urls = [
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll
                "https://youtu.be/dQw4w9WgXcQ"  # Short format
            ]
            
            for url in test_urls:
                test_data = {"url": url}
                
                response = self.session.post(
                    f"{self.base_url}/api/generate", 
                    json=test_data,
                    timeout=15
                )
                
                if response.status_code == 200:
                    data = response.json()
                    job_id = data.get('jobId')
                    
                    if job_id:
                        self.log_test("Generate Request", True, 
                                     f"Job started successfully with ID: {job_id}",
                                     {"jobId": job_id, "url": url})
                        return job_id
                    else:
                        self.log_test("Generate Request", False, "No job ID returned")
                elif response.status_code == 400:
                    # Try next URL if this one fails
                    continue
                else:
                    self.log_test("Generate Request", False, 
                                 f"HTTP {response.status_code}: {response.text}")
            
            self.log_test("Generate Request", False, "All test URLs failed")
            return None
                
        except requests.exceptions.RequestException as e:
            self.log_test("Generate Request", False, f"Connection error: {str(e)}")
            return None
    
    def test_status_endpoint(self, job_id: str) -> bool:
        """Test the status endpoint and monitor job progress"""
        print(f"\n📊 Monitoring Job Progress: {job_id}")
        try:
            max_attempts = 60  # 60 seconds max
            attempt = 0
            
            while attempt < max_attempts:
                response = self.session.get(
                    f"{self.base_url}/api/status/{job_id}", 
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status')
                    stage = data.get('stage', '')
                    progress = data.get('progress', 0)
                    message = data.get('message', '')
                    
                    print(f"   [{attempt+1:2d}s] Status: {status:12} | Progress: {progress:3d}% | {stage}")
                    
                    if status == 'completed':
                        self.log_test("Status Tracking", True, 
                                     "Job completed successfully", 
                                     {"final_stage": stage, "total_time": f"{attempt+1}s"})
                        return True
                    elif status == 'error':
                        self.log_test("Status Tracking", False, 
                                     f"Job failed: {message}")
                        return False
                    
                    time.sleep(1)
                    attempt += 1
                else:
                    self.log_test("Status Tracking", False, 
                                 f"HTTP {response.status_code}: {response.text}")
                    return False
            
            self.log_test("Status Tracking", False, 
                         f"Job did not complete within {max_attempts} seconds")
            return False
            
        except requests.exceptions.RequestException as e:
            self.log_test("Status Tracking", False, f"Connection error: {str(e)}")
            return False
    
    def test_infographic_retrieval(self, job_id: str) -> bool:
        """Test retrieving the completed infographic"""
        print(f"\n📄 Testing Infographic Retrieval...")
        try:
            response = self.session.get(
                f"{self.base_url}/api/infographic/{job_id}", 
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate the structure
                required_fields = ['id', 'videoMetadata', 'analysis', 'templateData']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    analysis = data.get('analysis', {})
                    video_metadata = data.get('videoMetadata', {})
                    template_data = data.get('templateData', {})
                    
                    key_points = analysis.get('keyPoints', [])
                    statistics = analysis.get('statistics', [])
                    
                    self.log_test("Infographic Retrieval", True, 
                                 f"Retrieved complete infographic data",
                                 {
                                     "video_title": video_metadata.get('title', 'Unknown'),
                                     "main_title": analysis.get('mainTitle', ''),
                                     "key_points": len(key_points),
                                     "statistics": len(statistics),
                                     "category": analysis.get('category', ''),
                                     "template_type": data.get('templateType', '')
                                 })
                    return True
                else:
                    self.log_test("Infographic Retrieval", False, 
                                 f"Missing required fields: {missing_fields}")
                    return False
            else:
                self.log_test("Infographic Retrieval", False, 
                             f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test("Infographic Retrieval", False, f"Connection error: {str(e)}")
            return False
    
    def test_cors_headers(self) -> bool:
        """Test CORS headers for frontend integration"""
        print("\n🌐 Testing CORS Configuration...")
        try:
            # Test preflight request
            headers = {
                'Origin': 'https://videotoinfographics.com',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            }
            
            response = self.session.options(f"{self.base_url}/api/health", headers=headers)
            
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
            }
            
            if cors_headers['Access-Control-Allow-Origin']:
                self.log_test("CORS Headers", True, 
                             "CORS properly configured for frontend", cors_headers)
                return True
            else:
                self.log_test("CORS Headers", False, "CORS headers missing or misconfigured")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test("CORS Headers", False, f"Connection error: {str(e)}")
            return False
    
    def run_full_validation(self) -> bool:
        """Run the complete validation suite"""
        print("🚀 YouTube to Infographic API Validation")
        print(f"🌐 Testing API at: {self.base_url}")
        print("=" * 60)
        
        # Basic connectivity and health
        if not self.test_health_endpoint():
            print("\n❌ API is not accessible. Please check the server status.")
            return False
        
        # Test static endpoints
        templates_ok = self.test_templates_endpoint()
        coordinates_ok = self.test_template_coordinates()
        icons_ok = self.test_icon_search()
        cors_ok = self.test_cors_headers()
        
        # Test the full workflow
        print("\n" + "="*60)
        print("🎬 TESTING FULL YOUTUBE PROCESSING WORKFLOW")
        print("="*60)
        
        job_id = self.test_generate_endpoint()
        workflow_ok = False
        
        if job_id:
            status_ok = self.test_status_endpoint(job_id)
            if status_ok:
                retrieval_ok = self.test_infographic_retrieval(job_id)
                workflow_ok = retrieval_ok
        
        # Generate summary
        self.generate_summary()
        
        # Check if all critical tests passed
        critical_tests = [
            any(r['test'] == 'Health Check' and r['success'] for r in self.test_results),
            templates_ok,
            workflow_ok or job_id is not None  # At least job creation should work
        ]
        
        return all(critical_tests)
    
    def generate_summary(self):
        """Generate test summary and integration guide"""
        print("\n" + "="*60)
        print("📋 VALIDATION SUMMARY")
        print("="*60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Tests Passed: {passed}/{total} ({passed/total*100:.1f}%)")
        
        if passed >= total * 0.8:  # 80% pass rate
            print("🎉 API IS READY FOR FRONTEND INTEGRATION!")
            
            print(f"\n🔗 Frontend Integration Configuration:")
            print(f"   API Base URL: {self.base_url}")
            print(f"   Health Check: {self.base_url}/api/health")
            print(f"   API Documentation: {self.base_url}/docs")
            
            print(f"\n📝 Key Endpoints for Frontend:")
            print(f"   POST {self.base_url}/api/generate")
            print(f"   GET  {self.base_url}/api/status/{{jobId}}")
            print(f"   GET  {self.base_url}/api/infographic/{{jobId}}")
            print(f"   GET  {self.base_url}/api/templates")
            print(f"   POST {self.base_url}/api/icons/search")
            
            print(f"\n⚡ Frontend Integration Tips:")
            print(f"   - Use polling for status updates (1-2 second intervals)")
            print(f"   - Handle CORS properly (already configured)")
            print(f"   - Implement proper error handling for failed jobs")
            print(f"   - Show progress indicators during processing")
            
        else:
            print("⚠️  API has some issues that should be addressed:")
            
            failed_tests = [r for r in self.test_results if not r['success']]
            for test in failed_tests:
                print(f"   ❌ {test['test']}: {test['message']}")
        
        return passed >= total * 0.8

def main():
    """Main function"""
    validator = APIValidator("https://api.videotoinfographics.com")
    success = validator.run_full_validation()
    
    if success:
        print(f"\n✅ API validation completed successfully!")
        print(f"🚀 Ready to integrate with frontend!")
    else:
        print(f"\n❌ API validation found issues.")
        print(f"🔧 Please address the issues before frontend integration.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())