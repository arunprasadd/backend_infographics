"""
Tests for main FastAPI application
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
import json


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check_success(self, client: TestClient):
        """Test successful health check."""
        response = client.get("/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "message" in data
        assert "services" in data


class TestGenerateEndpoint:
    """Test infographic generation endpoint."""
    
    def test_generate_with_valid_url(self, client: TestClient, mock_youtube_transcript, mock_openai_client):
        """Test generation with valid YouTube URL."""
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        response = client.post("/api/generate", json={"url": test_url})
        assert response.status_code == 200
        
        data = response.json()
        assert "jobId" in data
        assert "message" in data
        assert data["message"] == "Processing started"
    
    def test_generate_with_invalid_url(self, client: TestClient):
        """Test generation with invalid URL."""
        test_url = "https://invalid-url.com"
        
        response = client.post("/api/generate", json={"url": test_url})
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
    
    def test_generate_with_missing_url(self, client: TestClient):
        """Test generation with missing URL."""
        response = client.post("/api/generate", json={})
        assert response.status_code == 422  # Validation error


class TestStatusEndpoint:
    """Test processing status endpoint."""
    
    def test_status_with_valid_job_id(self, client: TestClient):
        """Test status check with valid job ID."""
        # First create a job
        with patch('main.YouTubeTranscriptApi'), patch('main.openai_client'):
            response = client.post("/api/generate", json={"url": "https://www.youtube.com/watch?v=test"})
            job_data = response.json()
            job_id = job_data["jobId"]
        
        # Check status
        response = client.get(f"/api/status/{job_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "stage" in data
        assert "progress" in data
        assert "message" in data
    
    def test_status_with_invalid_job_id(self, client: TestClient):
        """Test status check with invalid job ID."""
        response = client.get("/api/status/invalid-job-id")
        assert response.status_code == 404
        
        data = response.json()
        assert data["detail"] == "Job not found"


class TestInfographicEndpoint:
    """Test infographic retrieval endpoint."""
    
    def test_get_infographic_with_invalid_job_id(self, client: TestClient):
        """Test getting infographic with invalid job ID."""
        response = client.get("/api/infographic/invalid-job-id")
        assert response.status_code == 404
        
        data = response.json()
        assert data["detail"] == "Infographic not found"


class TestTemplateEndpoints:
    """Test template-related endpoints."""
    
    def test_get_templates(self, client: TestClient, mock_template_service):
        """Test getting all templates."""
        with patch('main.template_service', mock_template_service):
            mock_template_service.get_all_templates.return_value = [
                {
                    "id": "modern-business",
                    "name": "Modern Business",
                    "category": "business"
                }
            ]
            
            response = client.get("/api/templates")
            assert response.status_code == 200
            
            data = response.json()
            assert "templates" in data
            assert len(data["templates"]) > 0
    
    def test_get_template_coordinates(self, client: TestClient, mock_template_service):
        """Test getting template coordinates."""
        template_id = "modern-business"
        
        with patch('main.template_service', mock_template_service):
            response = client.get(f"/api/templates/{template_id}/coordinates")
            assert response.status_code == 200
            
            data = response.json()
            assert "template" in data
            assert "coordinates" in data


class TestIconSearchEndpoint:
    """Test icon search endpoint."""
    
    def test_search_icons(self, client: TestClient, mock_vector_service):
        """Test icon search functionality."""
        search_request = {
            "content": "business growth",
            "category": "business",
            "limit": 5
        }
        
        with patch('main.vector_service', mock_vector_service):
            response = client.post("/api/icons/search", json=search_request)
            assert response.status_code == 200
            
            data = response.json()
            assert "icons" in data
            assert len(data["icons"]) > 0


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_extract_video_id_youtube_com(self):
        """Test video ID extraction from youtube.com URL."""
        from main import extract_video_id
        
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        video_id = extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"
    
    def test_extract_video_id_youtu_be(self):
        """Test video ID extraction from youtu.be URL."""
        from main import extract_video_id
        
        url = "https://youtu.be/dQw4w9WgXcQ"
        video_id = extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"
    
    def test_extract_video_id_invalid_url(self):
        """Test video ID extraction from invalid URL."""
        from main import extract_video_id
        
        with pytest.raises(ValueError):
            extract_video_id("https://invalid-url.com")
    
    def test_get_video_metadata(self):
        """Test video metadata retrieval."""
        from main import get_video_metadata
        
        video_id = "test_video_id"
        metadata = get_video_metadata(video_id)
        
        assert metadata["id"] == video_id
        assert "title" in metadata
        assert "thumbnailUrl" in metadata
    
    def test_analyze_basic_content(self, sample_transcript_text):
        """Test basic content analysis."""
        from main import analyze_basic_content
        
        result = analyze_basic_content(sample_transcript_text)
        
        assert "mainTitle" in result
        assert "keyPoints" in result
        assert "statistics" in result
        assert "quotes" in result
        assert "category" in result
        assert len(result["keyPoints"]) >= 5


class TestContentAnalysis:
    """Test content analysis functionality."""
    
    def test_analyze_transcript_with_openai(self, mock_openai_client, sample_transcript_text):
        """Test transcript analysis with OpenAI."""
        from main import analyze_transcript_content
        
        with patch('main.openai_client', mock_openai_client):
            result = analyze_transcript_content(sample_transcript_text)
            
            assert "mainTitle" in result
            assert "keyPoints" in result
            assert len(result["keyPoints"]) == 5
            assert "statistics" in result
            assert "category" in result
    
    def test_analyze_transcript_without_openai(self, sample_transcript_text):
        """Test transcript analysis without OpenAI (fallback)."""
        from main import analyze_transcript_content
        
        with patch('main.openai_client', None):
            result = analyze_transcript_content(sample_transcript_text)
            
            assert "mainTitle" in result
            assert "keyPoints" in result
            assert len(result["keyPoints"]) >= 5
            assert "category" in result
    
    def test_get_content_icons(self):
        """Test icon selection based on content."""
        from main import get_content_icons
        
        key_points = [
            "Business growth is important",
            "AI technology advancement",
            "Team collaboration matters"
        ]
        
        icons = get_content_icons(key_points, "business")
        
        assert len(icons) == len(key_points)
        assert all(isinstance(icon, str) for icon in icons)


class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_transcript_not_available(self, client: TestClient):
        """Test handling when transcript is not available."""
        with patch('main.YouTubeTranscriptApi') as mock_api:
            mock_api.get_transcript.side_effect = Exception("Transcript not available")
            
            response = client.post("/api/generate", json={"url": "https://www.youtube.com/watch?v=test"})
            assert response.status_code == 200  # Job starts successfully
            
            # The error should be reflected in the job status
            job_data = response.json()
            job_id = job_data["jobId"]
            
            # Wait a bit for processing
            import time
            time.sleep(1)
            
            status_response = client.get(f"/api/status/{job_id}")
            status_data = status_response.json()
            
            # Should eventually show error status
            assert status_data["status"] in ["processing", "error"]
    
    def test_openai_api_error(self, client: TestClient, mock_youtube_transcript):
        """Test handling OpenAI API errors."""
        with patch('main.openai_client') as mock_client:
            mock_client.chat.completions.create.side_effect = Exception("API Error")
            
            response = client.post("/api/generate", json={"url": "https://www.youtube.com/watch?v=test"})
            assert response.status_code == 200  # Should fall back to basic analysis