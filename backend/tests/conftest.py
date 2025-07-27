"""
Pytest configuration and fixtures for YouTube Infographic Generator tests
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import tempfile
import os
from typing import Generator

# Import your main app
from main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    with patch('main.openai_client') as mock_client:
        # Mock the chat completion response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''
        {
            "mainTitle": "Test Video Title",
            "keyPoints": [
                "First key point",
                "Second key point",
                "Third key point",
                "Fourth key point",
                "Fifth key point"
            ],
            "statistics": [
                {"label": "Test Metric", "value": "75%", "percentage": 75}
            ],
            "quotes": ["Test quote from video"],
            "category": "business",
            "summary": "Test summary of the video content"
        }
        '''
        
        mock_client.chat.completions.create.return_value = mock_response
        yield mock_client


@pytest.fixture
def mock_youtube_transcript():
    """Mock YouTube transcript API."""
    with patch('main.YouTubeTranscriptApi') as mock_api:
        mock_api.get_transcript.return_value = [
            {"text": "This is a test transcript", "start": 0.0, "duration": 5.0},
            {"text": "with multiple segments", "start": 5.0, "duration": 3.0},
            {"text": "for testing purposes", "start": 8.0, "duration": 4.0}
        ]
        yield mock_api


@pytest.fixture
def mock_vector_service():
    """Mock vector database service."""
    with patch('services.vector_db.VectorIconService') as mock_service:
        mock_instance = Mock()
        mock_instance.find_relevant_icons.return_value = [
            {
                "id": "test_icon_1",
                "name": "TestIcon1",
                "category": "business",
                "keywords": ["test", "business"],
                "description": "Test icon for business",
                "svg_path": "M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z",
                "similarity_score": 0.85
            }
        ]
        yield mock_instance


@pytest.fixture
def mock_template_service():
    """Mock template service."""
    with patch('services.template_service.TemplateService') as mock_service:
        mock_instance = Mock()
        mock_instance.get_template_coordinates.return_value = {
            "template": {
                "id": "modern-business",
                "name": "Modern Business",
                "width": 1200,
                "height": 1800
            },
            "coordinates": {
                "key_point": [
                    {"index": 0, "x": 100, "y": 400, "width": 32, "height": 32}
                ]
            },
            "color_schemes": [
                {
                    "scheme_name": "Corporate Blue",
                    "primary_color": "#2563EB",
                    "secondary_color": "#1E40AF",
                    "accent_color": "#3B82F6",
                    "background_color": "#FFFFFF",
                    "text_color": "#1F2937"
                }
            ]
        }
        yield mock_instance


@pytest.fixture
def temp_image_file():
    """Create a temporary image file for testing."""
    from PIL import Image
    import io
    
    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='red')
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
        img.save(tmp_file, format='PNG')
        tmp_file.flush()
        yield tmp_file.name
    
    # Cleanup
    os.unlink(tmp_file.name)


@pytest.fixture
def sample_transcript_text():
    """Sample transcript text for testing."""
    return """
    Welcome to this amazing video about artificial intelligence and machine learning.
    In this video, we'll explore how AI is transforming businesses worldwide.
    Studies show that 85% of companies are investing in AI technologies.
    Machine learning algorithms can improve efficiency by up to 40%.
    As one expert said, "AI is not just the future, it's the present."
    The key takeaways from this discussion include understanding AI fundamentals,
    implementing machine learning in your business processes,
    and staying updated with the latest technological trends.
    """


@pytest.fixture
def sample_video_metadata():
    """Sample video metadata for testing."""
    return {
        "id": "test_video_id",
        "title": "Test Video Title",
        "duration": "10:30",
        "description": "Test video description",
        "thumbnailUrl": "https://img.youtube.com/vi/test_video_id/maxresdefault.jpg",
        "channelName": "Test Channel"
    }


@pytest.fixture
def sample_content_analysis():
    """Sample content analysis result for testing."""
    return {
        "mainTitle": "AI and Machine Learning in Business",
        "keyPoints": [
            "AI is transforming businesses worldwide",
            "85% of companies are investing in AI technologies",
            "Machine learning can improve efficiency by 40%",
            "Understanding AI fundamentals is crucial",
            "Stay updated with technological trends"
        ],
        "statistics": [
            {"label": "Companies investing in AI", "value": "85%", "percentage": 85},
            {"label": "Efficiency improvement", "value": "40%", "percentage": 40}
        ],
        "quotes": ["AI is not just the future, it's the present"],
        "category": "technology",
        "summary": "Video explores AI transformation in business",
        "wordCount": 150,
        "transcriptLength": 500,
        "icons": ["Brain", "TrendingUp", "Target", "Lightbulb", "Rocket"]
    }


# Environment variable fixtures
@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "test_db")
    monkeypatch.setenv("DB_USER", "test_user")
    monkeypatch.setenv("DB_PASSWORD", "test_password")
    monkeypatch.setenv("QDRANT_HOST", "localhost")
    monkeypatch.setenv("QDRANT_PORT", "6333")


# Database fixtures (if using real database for integration tests)
@pytest.fixture(scope="session")
def test_db():
    """Create test database for integration tests."""
    # This would set up a test database
    # Implementation depends on your database setup
    pass


@pytest.fixture
def clean_db(test_db):
    """Clean database before each test."""
    # Clean up database state before each test
    pass