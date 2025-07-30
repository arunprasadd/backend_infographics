# Frontend Integration Guide
## YouTube to Infographic API

This guide helps you integrate the YouTube to Infographic API with your frontend application.

## 🌐 API Base URL
```
https://api.videotoinfographics.com
```

## 📚 API Documentation
Visit: https://api.videotoinfographics.com/docs

## 🔑 Key Endpoints

### 1. Health Check
```http
GET /api/health
```
**Response:**
```json
{
  "status": "healthy",
  "message": "YouTube to Infographic API is running",
  "services": {
    "vector_db": "connected",
    "template_service": "connected",
    "openai": "connected"
  }
}
```

### 2. Start Infographic Generation
```http
POST /api/generate
Content-Type: application/json

{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

**Response:**
```json
{
  "jobId": "uuid-string",
  "message": "Processing started"
}
```

### 3. Check Processing Status
```http
GET /api/status/{jobId}
```

**Response:**
```json
{
  "status": "processing|completed|error",
  "stage": "Current processing stage",
  "progress": 75,
  "message": "Status message"
}
```

**Status Values:**
- `processing`: Job is being processed
- `completed`: Job finished successfully
- `error`: Job failed

### 4. Get Completed Infographic
```http
GET /api/infographic/{jobId}
```

**Response:**
```json
{
  "id": "job-id",
  "videoMetadata": {
    "id": "video-id",
    "title": "Video Title",
    "thumbnailUrl": "https://...",
    "channelName": "Channel Name"
  },
  "analysis": {
    "mainTitle": "Infographic Title",
    "keyPoints": ["Point 1", "Point 2", ...],
    "statistics": [
      {
        "label": "Metric Name",
        "value": "75%",
        "percentage": 75
      }
    ],
    "quotes": ["Notable quote"],
    "category": "business|education|technology|health",
    "summary": "Content summary"
  },
  "templateData": {
    "template": {...},
    "positioned_elements": {...}
  },
  "templateType": "modern-business"
}
```

### 5. Get Available Templates
```http
GET /api/templates
```

**Response:**
```json
{
  "templates": [
    {
      "id": "modern-business",
      "name": "Modern Business",
      "category": "business",
      "description": "Clean corporate design"
    }
  ]
}
```

### 6. Search Icons
```http
POST /api/icons/search
Content-Type: application/json

{
  "content": "business growth",
  "category": "business",
  "limit": 5
}
```

## 🔄 Frontend Implementation Flow

### 1. Basic Workflow
```javascript
// 1. Start generation
const response = await fetch('https://api.videotoinfographics.com/api/generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ url: youtubeUrl })
});

const { jobId } = await response.json();

// 2. Poll for status
const pollStatus = async () => {
  const statusResponse = await fetch(`https://api.videotoinfographics.com/api/status/${jobId}`);
  const status = await statusResponse.json();
  
  if (status.status === 'completed') {
    // Get final result
    const resultResponse = await fetch(`https://api.videotoinfographics.com/api/infographic/${jobId}`);
    const infographic = await resultResponse.json();
    return infographic;
  } else if (status.status === 'error') {
    throw new Error(status.message);
  } else {
    // Continue polling
    setTimeout(pollStatus, 2000);
  }
};

pollStatus();
```

### 2. React Hook Example
```javascript
import { useState, useEffect } from 'react';

export const useInfographicGeneration = () => {
  const [status, setStatus] = useState(null);
  const [infographic, setInfographic] = useState(null);
  const [error, setError] = useState(null);

  const generateInfographic = async (youtubeUrl) => {
    try {
      setStatus({ status: 'starting', progress: 0 });
      
      const response = await fetch('https://api.videotoinfographics.com/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: youtubeUrl })
      });

      if (!response.ok) throw new Error('Failed to start generation');
      
      const { jobId } = await response.json();
      pollStatus(jobId);
    } catch (err) {
      setError(err.message);
    }
  };

  const pollStatus = async (jobId) => {
    try {
      const response = await fetch(`https://api.videotoinfographics.com/api/status/${jobId}`);
      const statusData = await response.json();
      
      setStatus(statusData);

      if (statusData.status === 'completed') {
        const resultResponse = await fetch(`https://api.videotoinfographics.com/api/infographic/${jobId}`);
        const result = await resultResponse.json();
        setInfographic(result);
      } else if (statusData.status === 'error') {
        setError(statusData.message);
      } else {
        setTimeout(() => pollStatus(jobId), 2000);
      }
    } catch (err) {
      setError(err.message);
    }
  };

  return { generateInfographic, status, infographic, error };
};
```

### 3. Progress Display Component
```javascript
const ProgressDisplay = ({ status }) => {
  if (!status) return null;

  const getProgressColor = () => {
    if (status.status === 'error') return 'bg-red-500';
    if (status.status === 'completed') return 'bg-green-500';
    return 'bg-blue-500';
  };

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="flex justify-between mb-2">
        <span className="text-sm font-medium">{status.stage}</span>
        <span className="text-sm text-gray-500">{status.progress}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div 
          className={`h-2 rounded-full transition-all duration-300 ${getProgressColor()}`}
          style={{ width: `${status.progress}%` }}
        />
      </div>
      <p className="text-xs text-gray-600 mt-1">{status.message}</p>
    </div>
  );
};
```

## 🎨 Template Integration

### Get Templates
```javascript
const fetchTemplates = async () => {
  const response = await fetch('https://api.videotoinfographics.com/api/templates');
  const { templates } = await response.json();
  return templates;
};
```

### Template Selection
```javascript
const TemplateSelector = ({ onSelect }) => {
  const [templates, setTemplates] = useState([]);

  useEffect(() => {
    fetchTemplates().then(setTemplates);
  }, []);

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
      {templates.map(template => (
        <div 
          key={template.id}
          className="border rounded-lg p-4 cursor-pointer hover:border-blue-500"
          onClick={() => onSelect(template)}
        >
          <h3 className="font-semibold">{template.name}</h3>
          <p className="text-sm text-gray-600">{template.description}</p>
          <span className="inline-block bg-gray-100 rounded px-2 py-1 text-xs mt-2">
            {template.category}
          </span>
        </div>
      ))}
    </div>
  );
};
```

## 🔍 Icon Search Integration

```javascript
const searchIcons = async (content, category = null, limit = 6) => {
  const response = await fetch('https://api.videotoinfographics.com/api/icons/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content, category, limit })
  });
  
  const { icons } = await response.json();
  return icons;
};
```

## ⚠️ Error Handling

### Common Error Scenarios
1. **Invalid YouTube URL**: 400 Bad Request
2. **Transcript Not Available**: Job will fail with error status
3. **Network Issues**: Handle connection timeouts
4. **Rate Limiting**: Implement retry logic

### Error Handling Example
```javascript
const handleApiError = (error, response) => {
  if (response?.status === 400) {
    return 'Invalid YouTube URL. Please check the URL and try again.';
  } else if (response?.status === 404) {
    return 'Video not found or transcript not available.';
  } else if (response?.status >= 500) {
    return 'Server error. Please try again later.';
  } else {
    return error.message || 'An unexpected error occurred.';
  }
};
```

## 🚀 Performance Tips

1. **Polling Frequency**: Use 2-3 second intervals for status polling
2. **Caching**: Cache templates and icons locally
3. **Loading States**: Show progress indicators during processing
4. **Error Recovery**: Implement retry logic for failed requests
5. **Timeout Handling**: Set reasonable timeouts (30-60 seconds for generation)

## 🔒 CORS Configuration

The API is configured to accept requests from:
- `https://videotoinfographics.com`
- `https://*.netlify.app`
- `http://localhost:*` (for development)

## 📱 Mobile Considerations

- Use responsive design for progress indicators
- Handle network interruptions gracefully
- Consider offline state management
- Optimize for touch interactions

## 🧪 Testing

Use the validation script to test API connectivity:
```bash
python api_validation.py
```

This will test all endpoints and provide a comprehensive report.