# Backend Infographics API

Backend API for YouTube to Infographic Generator - converts YouTube videos into beautiful infographics using AI-powered content analysis and vector-based icon search.

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API Key (optional, for advanced analysis)
- Domain: api.videotoinfographics.com

### Deployment
```bash
# Clone repository
git clone <backend-repo-url>
cd backend_infographics

# Setup environment
cp .env.example .env
# Edit .env with your configuration

# Deploy with SSL
chmod +x deploy_with_ssl.sh
./deploy_with_ssl.sh api.videotoinfographics.com
```

## 🏗️ Architecture
- **FastAPI**: High-performance Python web framework
- **ChromaDB**: Vector database for semantic icon search
- **PostgreSQL**: Template coordinates and metadata
- **Nginx**: Reverse proxy with SSL termination
- **Let's Encrypt**: Free SSL certificates

## 📚 API Documentation
- **API Docs**: https://api.videotoinfographics.com/docs
- **Health Check**: https://api.videotoinfographics.com/api/health

## 🔧 Features
- Real YouTube transcript extraction
- AI-powered content analysis
- Vector-based icon search (698+ icons)
- Template coordinate system
- Professional infographic generation

