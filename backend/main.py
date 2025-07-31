from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import uuid
import json
from typing import Dict, Optional
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
import re
import asyncio
from datetime import datetime
import logging
from dotenv import load_dotenv
from services.vector_db import VectorIconService
from services.template_service import TemplateService
from services.infographic_generator import InfographicGenerator

# Try to import OpenAI, make it optional
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI package not available. Using fallback content analysis.")

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="YouTube to Infographic API", version="1.0.0")

# Initialize OpenAI client
openai_client = None
openai_api_key = os.getenv("OPENAI_API_KEY")
if OPENAI_AVAILABLE and openai_api_key and openai_api_key.startswith("sk-"):
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    logger.info("OpenAI client initialized successfully")
else:
    logger.info("OpenAI not available or API key not configured - using fallback analysis")

# Initialize services
vector_service = VectorIconService()
template_service = TemplateService()
infographic_generator = InfographicGenerator()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://localhost:3000",
        "https://exquisite-capybara-f02683.netlify.app",  # Your Netlify domain
        "https://*.netlify.app"  # Allow all Netlify subdomains
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for jobs (use Redis/database in production)
processing_jobs: Dict[str, dict] = {}
generated_infographics: Dict[str, dict] = {}

class YouTubeURLRequest(BaseModel):
    url: str

class ProcessingStatus(BaseModel):
    status: str
    stage: str
    progress: int
    message: str

def extract_video_id(url: str) -> str:
    """Extract video ID from YouTube URL"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
        r'youtube\.com\/watch\?.*v=([^&\n?#]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    raise ValueError("Invalid YouTube URL")

def get_video_metadata(video_id: str) -> dict:
    """Get basic video metadata (in production, use YouTube Data API)"""
    # For MVP, return mock metadata
    # In production, integrate with YouTube Data API v3
    return {
        "id": video_id,
        "title": f"YouTube Video {video_id}",
        "duration": "Unknown",
        "description": "Video description",
        "thumbnailUrl": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
        "channelName": "YouTube Channel"
    }

def get_content_icons(key_points: list, category: str = "business") -> list:
    """Generate appropriate icons for content based on key points and category"""
    
    # Icon mapping based on keywords and context
    icon_keywords = {
        # Business & Finance
        'growth': 'TrendingUp',
        'profit': 'DollarSign', 
        'revenue': 'BarChart3',
        'market': 'Target',
        'strategy': 'Lightbulb',
        'team': 'Users',
        'leadership': 'Crown',
        'success': 'Award',
        'goal': 'Flag',
        'performance': 'Activity',
        
        # Technology
        'ai': 'Brain',
        'data': 'Database',
        'digital': 'Smartphone',
        'automation': 'Zap',
        'innovation': 'Rocket',
        'software': 'Code',
        'security': 'Shield',
        'cloud': 'Cloud',
        
        # Education & Learning
        'learn': 'BookOpen',
        'education': 'GraduationCap',
        'skill': 'Star',
        'knowledge': 'Brain',
        'training': 'Users',
        'development': 'TrendingUp',
        
        # Health & Wellness
        'health': 'Heart',
        'fitness': 'Activity',
        'nutrition': 'Apple',
        'wellness': 'Smile',
        'exercise': 'Dumbbell',
        
        # Communication & Social
        'communication': 'MessageCircle',
        'social': 'Users',
        'network': 'Share2',
        'community': 'Users',
        'collaboration': 'Handshake',
        
        # Time & Productivity
        'time': 'Clock',
        'productivity': 'CheckCircle',
        'efficiency': 'Zap',
        'organization': 'Calendar',
        'planning': 'Map',
        
        # Default icons by category
        'business': ['Briefcase', 'TrendingUp', 'Target', 'Award', 'Users'],
        'education': ['BookOpen', 'GraduationCap', 'Lightbulb', 'Star', 'Brain'],
        'technology': ['Smartphone', 'Zap', 'Database', 'Code', 'Rocket'],
        'health': ['Heart', 'Activity', 'Shield', 'Smile', 'Apple'],
        'finance': ['DollarSign', 'BarChart3', 'TrendingUp', 'PieChart', 'CreditCard']
    }
    
    selected_icons = []
    
    # Try to match icons based on key point content
    for point in key_points:
        point_lower = point.lower()
        matched_icon = None
        
        # Look for keyword matches
        for keyword, icon in icon_keywords.items():
            if isinstance(icon, str) and keyword in point_lower:
                matched_icon = icon
                break
        
        # If no specific match, use category defaults
        if not matched_icon:
            category_icons = icon_keywords.get(category, icon_keywords['business'])
            matched_icon = category_icons[len(selected_icons) % len(category_icons)]
        
        selected_icons.append(matched_icon)
    
    return selected_icons

def analyze_transcript_content(transcript_text: str) -> dict:
    """Analyze transcript content using OpenAI for summarization and key points"""
    
    # Try OpenAI analysis first
    if openai_client:
        try:
            return analyze_with_openai(transcript_text)
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {str(e)}")
            # Fall back to basic analysis
    
    # Basic fallback analysis
    return analyze_basic_content(transcript_text)

def analyze_with_openai(transcript_text: str) -> dict:
    """Use OpenAI to analyze transcript and generate infographic content"""
    try:
        # Truncate transcript if too long (OpenAI token limits)
        max_chars = 12000
        if len(transcript_text) > max_chars:
            transcript_text = transcript_text[:max_chars] + "..."
        
        prompt = f"""
Analyze this YouTube video transcript and create infographic content:

REQUIREMENTS:
1. Create a compelling main title (max 80 characters)
2. Generate exactly 5-6 key takeaway points (each 15-25 words)
3. Extract 3-4 statistics or data points if available
4. Find 1-2 memorable quotes if present
5. Determine content category for icon selection

TRANSCRIPT:
{transcript_text}

Return ONLY valid JSON in this exact format:
{{
    "mainTitle": "Compelling title here",
    "keyPoints": [
        "First key takeaway point",
        "Second key takeaway point", 
        "Third key takeaway point",
        "Fourth key takeaway point",
        "Fifth key takeaway point"
    ],
    "statistics": [
        {{"label": "Metric name", "value": "Number/percentage", "percentage": 75}},
        {{"label": "Another metric", "value": "Value", "percentage": 60}}
    ],
    "quotes": [
        "Notable quote from the video"
    ],
    "category": "business|education|technology|health|finance|lifestyle",
    "summary": "2-3 sentence summary of the main topic"
}}
"""
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert content analyst specializing in creating infographic content. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1200,
            temperature=0.7
        )
        
        # Parse the JSON response
        content = response.choices[0].message.content.strip()
        
        # Clean up any markdown formatting
        if content.startswith('```json'):
            content = content[7:]
        if content.endswith('```'):
            content = content[:-3]
        
        result = json.loads(content)
        
        # Add metadata
        result["wordCount"] = len(transcript_text.split())
        result["transcriptLength"] = len(transcript_text)
        
        # Generate icons based on key points and category
        result["icons"] = get_content_icons(result["keyPoints"], result.get("category", "business"))
        
        # Ensure we have exactly 5-6 key points
        if len(result["keyPoints"]) < 5:
            # Pad with generic points if needed
            while len(result["keyPoints"]) < 5:
                result["keyPoints"].append("Additional insight from the video content")
        elif len(result["keyPoints"]) > 6:
            result["keyPoints"] = result["keyPoints"][:6]
        
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {str(e)}")
        raise Exception("Failed to parse OpenAI response")
    except Exception as e:
        logger.error(f"OpenAI analysis error: {str(e)}")
        raise e

def analyze_basic_content(transcript_text: str) -> dict:
    """Basic content analysis fallback when OpenAI is not available"""
    sentences = transcript_text.split('.')
    word_count = len(transcript_text.split())
    
    # Extract key points from sentences
    key_points = []
    statistics = []
    quotes = []
    
    # Process sentences for content
    for sentence in sentences[:30]:
        sentence = sentence.strip()
        if len(sentence) < 10:
            continue
            
        # Extract statistics
        if re.search(r'\d+%|\d+\s*percent', sentence, re.IGNORECASE):
            percentage_match = re.search(r'(\d+)%|(\d+)\s*percent', sentence, re.IGNORECASE)
            if percentage_match:
                percentage = int(percentage_match.group(1) or percentage_match.group(2))
                statistics.append({
                    "label": sentence[:40] + "..." if len(sentence) > 40 else sentence,
                    "value": f"{percentage}%",
                    "percentage": min(percentage, 100)
                })
        
        # Extract key points
        key_indicators = ['important', 'key', 'main', 'first', 'second', 'third', 'remember', 'crucial']
        if any(indicator in sentence.lower() for indicator in key_indicators):
            if len(sentence) <= 120:  # Keep points concise
                key_points.append(sentence)
        
        # Extract quotes
        if '"' in sentence:
            quotes.append(sentence.replace('"', ''))
    
    # Generate main title
    clean_sentences = [s.strip() for s in sentences[:5] if len(s.strip()) > 10]
    main_title = clean_sentences[0][:80] if clean_sentences else "Video Content Summary"
    
    # Ensure we have 5-6 key points
    if not key_points:
        # Use first meaningful sentences as key points
        meaningful_sentences = [s.strip() for s in sentences[1:8] if len(s.strip()) > 15 and len(s.strip()) <= 120]
        key_points = meaningful_sentences[:6]
    
    # Ensure exactly 5-6 points
    while len(key_points) < 5:
        key_points.append("Key insight extracted from video content")
    if len(key_points) > 6:
        key_points = key_points[:6]
    
    # Generate default statistics if none found
    if not statistics:
        statistics = [
            {"label": "Video Content Analysis", "value": f"{word_count} words", "percentage": min(word_count // 20, 100)},
            {"label": "Key Points Identified", "value": str(len(key_points)), "percentage": len(key_points) * 15}
        ]
    
    return {
        "mainTitle": main_title,
        "keyPoints": key_points,
        "statistics": statistics[:4],
        "quotes": quotes[:2],
        "category": "business",
        "summary": f"Analysis of video content covering {len(key_points)} main topics",
        "wordCount": word_count,
        "transcriptLength": len(transcript_text),
        "icons": get_content_icons(key_points, "business")
    }

async def process_youtube_video(job_id: str, url: str):
    """Background task to process YouTube video"""
    try:
        # Update status: Extracting video metadata
        processing_jobs[job_id] = {
            "status": "processing",
            "stage": "Extracting video metadata...",
            "progress": 10,
            "message": "Getting video information"
        }
        await asyncio.sleep(1)
        
        # Extract video ID
        video_id = extract_video_id(url)
        video_metadata = get_video_metadata(video_id)
        
        # Update status: Downloading transcript
        processing_jobs[job_id] = {
            "status": "processing",
            "stage": "Downloading transcript...",
            "progress": 25,
            "message": "Fetching video transcript"
        }
        await asyncio.sleep(1)
        
        # Get transcript
        try:
            # Try to get transcript with multiple language options and manual captions
            transcript_list = None
            
            # First, try to get available transcripts
            try:
                available_transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
                
                # Try to get English transcript first (auto-generated or manual)
                try:
                    transcript = available_transcripts.find_transcript(['en'])
                    transcript_list = transcript.fetch()
                except:
                    # Try any available transcript
                    for transcript in available_transcripts:
                        try:
                            transcript_list = transcript.fetch()
                            break
                        except:
                            continue
                            
            except Exception as list_error:
                logger.warning(f"Could not list transcripts: {str(list_error)}")
                
                # Fallback to direct transcript fetch
                try:
                    transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'en-US', 'en-GB'])
                except:
                    # Try without language specification
                    transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            
            if not transcript_list:
                raise Exception("No transcript data retrieved")
                
            formatter = TextFormatter()
            transcript_text = formatter.format_transcript(transcript_list)
            
            if not transcript_text.strip():
                raise Exception("Empty transcript received")
                
            logger.info(f"Successfully retrieved transcript with {len(transcript_text)} characters")
                
        except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable) as e:
            logger.error(f"YouTube transcript API error: {str(e)}")
            processing_jobs[job_id] = {
                "status": "error",
                "stage": "Transcript unavailable",
                "progress": 25,
                "message": f"This video doesn't have accessible transcripts. Please try a different video that has subtitles/captions enabled."
            }
            return
        except Exception as e:
            logger.error(f"Unexpected transcript error: {str(e)}")
            processing_jobs[job_id] = {
                "status": "error",
                "stage": "Transcript unavailable",
                "progress": 25,
                "message": f"Could not retrieve transcript. This might be due to: 1) Video has no subtitles/captions, 2) Video is private/restricted, 3) Geographic restrictions. Please try a different video."
            }
            return
        
        # Update status: Analyzing content
        processing_jobs[job_id] = {
            "status": "processing",
            "stage": "Analyzing content and generating key points...",
            "progress": 50,
            "message": "AI-powered content analysis in progress"
        }
        await asyncio.sleep(2)
        
        # Analyze content
        content_analysis = analyze_transcript_content(transcript_text)
        
        # Update status: Selecting template
        processing_jobs[job_id] = {
            "status": "processing",
            "stage": "Preparing infographic content...",
            "progress": 70,
            "message": "Organizing content for visualization"
        }
        await asyncio.sleep(1)
        
        # Update status: Generating infographic
        processing_jobs[job_id] = {
            "status": "processing",
            "stage": "Selecting icons and positioning elements...",
            "progress": 85,
            "message": "Mapping content to template coordinates"
        }
        await asyncio.sleep(1.5)
        
        # Update status: Finalizing
        processing_jobs[job_id] = {
            "status": "processing",
            "stage": "Finalizing and optimizing...",
            "progress": 100,
            "message": "Preparing download"
        }
        await asyncio.sleep(1)
        
        # Generate complete infographic with positioned icons
        # For now, use default template - user will select in frontend
        default_template_id = "modern-business"
        
        complete_infographic = infographic_generator.generate_infographic_data(
            content_analysis, 
            default_template_id
        )
        
        infographic_data = {
            "id": job_id,
            "videoMetadata": video_metadata,
            "analysis": content_analysis,
            "templateData": complete_infographic,
            "templateType": default_template_id,
            "createdAt": datetime.now().isoformat(),
            "transcriptText": transcript_text[:500] + "..." if len(transcript_text) > 500 else transcript_text
        }
        
        generated_infographics[job_id] = infographic_data
        
        # Mark as completed
        processing_jobs[job_id] = {
            "status": "completed",
            "stage": "Infographic generated successfully!",
            "progress": 100,
            "message": "Ready for download"
        }
        
    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        processing_jobs[job_id] = {
            "status": "error",
            "stage": "Processing failed",
            "progress": 0,
            "message": str(e)
        }

@app.post("/api/generate")
async def generate_infographic(request: YouTubeURLRequest, background_tasks: BackgroundTasks):
    """Start infographic generation process"""
    try:
        # Validate URL
        video_id = extract_video_id(request.url)
        
        # Create job
        job_id = str(uuid.uuid4())
        
        # Initialize job status
        processing_jobs[job_id] = {
            "status": "processing",
            "stage": "Starting analysis...",
            "progress": 0,
            "message": "Initializing"
        }
        
        # Start background processing
        background_tasks.add_task(process_youtube_video, job_id, request.url)
        
        return {"jobId": job_id, "message": "Processing started"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Generation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start processing")

@app.get("/api/status/{job_id}")
async def get_processing_status(job_id: str):
    """Get processing status for a job"""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return processing_jobs[job_id]

@app.get("/api/infographic/{job_id}")
async def get_infographic(job_id: str):
    """Get completed infographic data"""
    if job_id not in generated_infographics:
        raise HTTPException(status_code=404, detail="Infographic not found")
    
    return generated_infographics[job_id]

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "message": "YouTube to Infographic API is running",
        "services": {
            "vector_db": "connected",
            "template_service": "connected",
            "openai": "connected" if openai_client else "not configured"
        }
    }

@app.get("/api/templates")
async def get_templates():
    """Get all available templates"""
    templates = template_service.get_all_templates()
    return {"templates": templates}

@app.get("/api/templates/{template_id}/coordinates")
async def get_template_coordinates(template_id: str):
    """Get coordinates for a specific template"""
    coordinates = template_service.get_template_coordinates(template_id)
    return coordinates

@app.post("/api/icons/search")
async def search_icons(request: dict):
    """Search for relevant icons based on content"""
    content = request.get("content", "")
    category = request.get("category")
    limit = request.get("limit", 6)
    
    icons = vector_service.find_relevant_icons(content, category, limit)
    return {"icons": icons}

@app.post("/api/infographic/generate-with-template")
async def generate_with_template(request: dict):
    """Generate infographic with specific template"""
    job_id = request.get("job_id")
    template_id = request.get("template_id")
    
    if job_id not in generated_infographics:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get existing analysis
    job_data = generated_infographics[job_id]
    content_analysis = job_data["analysis"]
    
    # Generate with new template
    complete_infographic = infographic_generator.generate_infographic_data(
        content_analysis, 
        template_id
    )
    
    # Update job data
    job_data["templateData"] = complete_infographic
    job_data["templateType"] = template_id
    
    return {"message": "Infographic updated with new template", "data": complete_infographic}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)