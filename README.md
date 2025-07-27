# YouTube to Infographic Generator

A full-stack application that converts YouTube videos into beautiful infographics using real transcript data and AI-powered content analysis.

## 🏗️ Backend Architecture

The backend uses a modern microservices architecture with:
- **FastAPI**: High-performance Python web framework
- **Qdrant**: Vector database for semantic icon search
- **PostgreSQL**: Relational database for templates and coordinates
- **OpenAI**: AI-powered content analysis
- **S3**: Cloud storage for template files
- **Docker**: Containerized deployment

## 🚀 Live Demo

**Frontend Demo**: [https://exquisite-capybara-f02683.netlify.app](https://exquisite-capybara-f02683.netlify.app)

*Note: The live demo runs in frontend-only mode with simulated data. For full functionality with real YouTube transcript extraction, run the application locally with the Python backend.*

## 📋 Prerequisites

### System Requirements:
- **Python**: 3.8+ 
- **Node.js**: 18+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Git**: Latest version

### API Keys Required:
- **OpenAI API Key**: For content analysis (required)
- **AWS Credentials**: For S3 template storage (optional)
- **YouTube Data API**: For enhanced metadata (optional)

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone <your-repository-url>
cd youtube-infographic-generator
```

### 2. Backend Setup
```bash
cd backend

# Copy environment file
cp .env.example .env

# Edit .env with your API keys
nano .env

# Start all services with Docker
docker-compose up -d

# Check if services are running
docker-compose ps
```

### 3. Frontend Setup
```bash
cd ../  # Back to root directory

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Edit .env to point to your backend
echo "VITE_API_URL=http://localhost:8000" > .env

# Start development server
npm run dev
```

### 4. Load Icons (Optional)
```bash
# Load your icon images into Qdrant
cd backend
python scripts/load_images_to_qdrant.py
```

### 5. Test the Application
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Qdrant Dashboard**: http://localhost:6333/dashboard

## Features

- **Real YouTube Transcript Extraction**: Uses `youtube-transcript-api` to fetch actual video transcripts
- **AI-Powered Content Analysis**: Analyzes transcript content to extract key points, statistics, and quotes
- **Vector-Based Icon Search**: Semantic icon matching using Qdrant vector database
- **Template Coordinate System**: Precise icon positioning using PostgreSQL coordinates
- **Dynamic Infographic Generation**: Creates professional infographics based on analyzed content
- **Real-time Processing**: Live progress tracking with detailed status updates
- **Modern UI**: Beautiful, responsive interface built with React and Tailwind CSS
- **Template System**: Multiple professional templates with customizable color schemes
- **Export Options**: Multiple formats (PNG, JPG, PDF, SVG) with quality settings
- **Studio Interface**: Professional editing environment similar to infography.in

## 🏗️ Backend Services

### Core Services:
1. **FastAPI Server** (Port 8000)
   - Main API endpoints
   - YouTube transcript processing
   - Content analysis with OpenAI

2. **Qdrant Vector DB** (Port 6333)
   - Icon embeddings storage
   - Semantic similarity search
   - CLIP-based image vectors

3. **PostgreSQL** (Port 5432)
   - Template coordinates
   - Color schemes
   - Metadata storage

4. **Redis** (Port 6379)
   - Caching layer
   - Session management
   - Background job queue

### API Endpoints:
```
POST /api/generate                     # Start infographic generation
GET  /api/status/{job_id}             # Get processing status
GET  /api/infographic/{job_id}        # Get completed infographic
GET  /api/templates                   # Get all templates
GET  /api/templates/{id}/coordinates  # Get template coordinates
POST /api/icons/search                # Search relevant icons
GET  /api/health                      # Health check
```

## Architecture

### Frontend (React + TypeScript + Vite)
- Modern React application with TypeScript
- Tailwind CSS for styling
- Real-time status updates
- Responsive design
- Template selection and customization
- Professional studio interface

### Backend (Python + FastAPI)
- FastAPI for high-performance API
- `youtube-transcript-api` for transcript extraction
- Qdrant for vector-based icon search
- PostgreSQL for template management
- OpenAI for intelligent content analysis
- Content analysis and processing
- Background task processing

## 🔧 Development Setup

### Backend Development:
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run development server
python run.py
```

### Frontend Development:
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

### Database Management:
```bash
# Access PostgreSQL
docker-compose exec postgres psql -U postgres -d infographic_db

# View Qdrant collections
curl http://localhost:6333/collections

# Redis CLI
docker-compose exec redis redis-cli
```

## Deployment Options

### Option 1: Frontend-Only Demo (Current Netlify Deployment)
The current deployment at [https://exquisite-capybara-f02683.netlify.app](https://exquisite-capybara-f02683.netlify.app) runs in demo mode with:
- Simulated transcript processing
- Mock content analysis
- Full template and customization features
- All UI/UX functionality

### Option 2: Full-Stack Deployment
For production with real YouTube transcript processing:

**Frontend**: Deploy to Netlify/Vercel
**Backend**: Deploy to Railway/Heroku/DigitalOcean

#### Backend Deployment (Railway Example):
```bash
# 1. Create Railway project
# 2. Connect your repository
# 3. Set environment variables:
#    - PORT=8000
#    - PYTHON_VERSION=3.9
#    - OPENAI_API_KEY=your_key
# 4. Deploy backend/ directory
```

#### Frontend Deployment:
```bash
# Set environment variable for production:
# VITE_API_URL=https://your-backend-url.railway.app

npm run build
# Deploy dist/ folder to Netlify/Vercel
```

## 🔑 Environment Variables

### Backend (.env):
```bash
# Required
OPENAI_API_KEY=sk-your-openai-key-here

# Database
DB_HOST=postgres
DB_PORT=5432
DB_NAME=infographic_db
DB_USER=postgres
DB_PASSWORD=postgres

# Vector Database
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# Optional: AWS S3
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
S3_BUCKET_NAME=infographic-templates

# Optional: YouTube API
YOUTUBE_API_KEY=your_youtube_key
```

### Frontend (.env):
```bash
VITE_API_URL=http://localhost:8000
```

## Setup Instructions

### Prerequisites
- Node.js 18+ and npm
- Python 3.8+
- Docker and Docker Compose
- pip (Python package manager)

### 1. Clone and Install Frontend Dependencies
```bash
npm install
```

### 2. Setup Python Backend
```bash
cd backend
pip install -r requirements.txt
```

### 3. Environment Configuration
```bash
# Copy environment files
cp .env.example .env
cp backend/.env.example backend/.env

# Edit .env files with your configuration
```

### 4. Run the Application

#### Option 1: Run Both Frontend and Backend Together
```bash
npm run dev:full
```

#### Option 2: Run Separately
```bash
# Terminal 1: Start backend
npm run dev:backend
# or
cd backend && python run.py

# Terminal 2: Start frontend
npm run dev
```

#### Option 3: Docker Compose (Recommended)
```bash
cd backend
docker-compose up -d

# In another terminal
npm run dev
```

The application will be available at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## 🎨 Adding Custom Icons

### 1. Prepare Your Icons:
```bash
# Organize icons in folders by category
icons/
├── business/
│   ├── growth.png
│   ├── target.png
│   └── chart.png
├── education/
│   ├── book.png
│   └── graduation.png
└── technology/
    ├── ai.png
    └── code.png
```

### 2. Load Icons to Vector Database:
```bash
cd backend

# Edit the script with your icon path
nano scripts/load_images_to_qdrant.py

# Run the loading script
python scripts/load_images_to_qdrant.py
```

### 3. Verify Icons Loaded:
```bash
# Check Qdrant collection
curl http://localhost:6333/collections/image_icons

# Test icon search
curl -X POST http://localhost:8000/api/icons/search \
  -H "Content-Type: application/json" \
  -d '{"content": "business growth", "limit": 5}'
```

## How It Works

1. **URL Input**: User enters a YouTube URL
2. **Transcript Extraction**: Backend uses `youtube-transcript-api` to fetch the video transcript
3. **Content Analysis**: AI analyzes the transcript to extract:
   - Main title/theme
   - Key points and takeaways
   - Statistics and numerical data
   - Notable quotes
4. **Icon Selection**: Vector database finds relevant icons using semantic similarity
5. **Template Mapping**: System maps content to template coordinates
4. **Infographic Generation**: Creates a structured, visual representation of the content

## API Endpoints
## Studio Features

### Template System
- **6 Professional Templates**: Modern Business, Educational Flow, Data Visualization, Timeline Story, Social Media, Comparison Layout
- **Category Filtering**: Business, Education, Statistical, Timeline, Social Media
- **Color Schemes**: Multiple color variations per template
- **Premium Options**: Advanced templates with enhanced features

### Customization Options
- **Layout**: Portrait, Landscape, Square formats
- **Typography**: Small, Medium, Large font sizes
- **Content**: Custom titles and subtitles
- **Branding**: Toggle watermark visibility

### Export Features
- **Formats**: PNG, JPG, PDF, SVG
- **Quality**: Low, Medium, High settings
- **Sizes**: Small (800x1200), Medium (1200x1800), Large (1600x2400), Custom
- **Transparency**: PNG with transparent backgrounds
## Development

### Adding New Features
- Frontend components are in `src/components/`
- Backend logic is in `backend/main.py`
- Types are defined in `src/types/index.ts`
- Templates are managed in `src/hooks/useTemplates.ts`

### Content Analysis Enhancement
The current implementation includes basic content analysis. To enhance it:
1. Add OpenAI/Claude API integration in `backend/main.py`
2. Implement more sophisticated NLP processing
3. Add template selection based on content type

### Infographic Templates
The system includes multiple templates. To add more:
1. Create new template components
2. Add template selection logic based on content analysis
3. Implement different visual layouts
4. Update the template hook in `src/hooks/useTemplates.ts`

## 🐛 Troubleshooting

### Backend Issues:

**Qdrant Connection Error:**
```bash
# Check if Qdrant is running
docker-compose ps qdrant

# Restart Qdrant
docker-compose restart qdrant

# Check logs
docker-compose logs qdrant
```

**PostgreSQL Connection Error:**
```bash
# Check database
docker-compose exec postgres psql -U postgres -l

# Reset database
docker-compose down -v
docker-compose up -d
```

**OpenAI API Error:**
```bash
# Verify API key
echo $OPENAI_API_KEY

# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

## Troubleshooting

### Common Issues

1. **Transcript Not Available**
   - Some videos don't have transcripts
   - Private or restricted videos can't be accessed
   - Try with different YouTube videos

2. **CORS Issues**
   - Ensure backend is running on port 8000
   - Check CORS configuration in `backend/main.py`

3. **Processing Timeouts**
   - Very long videos may take more time
   - Check backend logs for detailed error messages

4. **Demo Mode**
   - If you see "Demo Mode" indicator, the app is using simulated data
   - This is normal for the Netlify deployment
   - For real transcript processing, run locally with Python backend

5. **Vector Database Issues**
   - Ensure Qdrant is running: `docker-compose ps qdrant`
   - Check collection exists: `curl http://localhost:6333/collections`
   - Reload icons if needed: `python scripts/load_images_to_qdrant.py`

### Logs
- Frontend: Browser developer console
- Backend: Terminal running the Python server
- Docker: `docker-compose logs [service_name]`

## 📊 Performance Optimization

### Production Settings:
```bash
# Set production environment variables
DEBUG=false
LOG_LEVEL=warning
WORKERS=4

# Use production database
DB_HOST=your-production-db-host

# Enable Redis caching
REDIS_URL=redis://your-redis-host:6379
```

### Scaling:
- **Horizontal**: Multiple API server instances behind load balancer
- **Vertical**: Increase CPU/RAM for vector operations
- **Database**: Use managed PostgreSQL and Redis services
- **Storage**: Use CDN for template files

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI**: For GPT and CLIP models
- **Qdrant**: For vector database technology
- **FastAPI**: For the excellent Python web framework
- **React**: For the frontend framework
- **YouTube**: For transcript API access

## License

MIT License - see LICENSE file for details