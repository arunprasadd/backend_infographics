#!/bin/sh

echo "🎬 YouTube Transcript Extraction Test"
echo "🌐 API: https://api.videotoinfographics.com"
echo "=" * 50

API_BASE="https://api.videotoinfographics.com"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "\n${BLUE}1. Starting YouTube Transcript Extraction${NC}"
echo "================================================================"
echo "Testing with: Rick Astley - Never Gonna Give You Up"
echo "URL: https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Start transcript processing
GENERATE_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}' \
  "$API_BASE/api/generate")

# Extract HTTP status and response body
HTTP_STATUS=$(echo "$GENERATE_RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
RESPONSE_BODY=$(echo "$GENERATE_RESPONSE" | sed '/HTTP_STATUS:/d')

echo "HTTP Status: $HTTP_STATUS"
echo "Response:"
echo "$RESPONSE_BODY"

if [ "$HTTP_STATUS" = "200" ]; then
    JOB_ID=$(echo "$RESPONSE_BODY" | grep -o '"jobId":"[^"]*"' | cut -d'"' -f4)
    
    if [ -n "$JOB_ID" ]; then
        echo -e "\n${GREEN}✅ Transcript extraction job started!${NC}"
        echo "Job ID: $JOB_ID"
        
        echo -e "\n${BLUE}2. Monitoring Transcript Processing${NC}"
        echo "================================================================"
        
        # Monitor progress for up to 60 seconds
        for i in $(seq 1 20); do
            echo -e "\n--- Check $i/20 (${i}0s) ---"
            
            STATUS_RESPONSE=$(curl -s "$API_BASE/api/status/$JOB_ID")
            echo "$STATUS_RESPONSE"
            
            # Check if completed
            if echo "$STATUS_RESPONSE" | grep -q '"status":"completed"'; then
                echo -e "\n${GREEN}🎉 Transcript processing completed!${NC}"
                
                echo -e "\n${BLUE}3. Getting Extracted Transcript & Analysis${NC}"
                echo "================================================================"
                
                RESULT_RESPONSE=$(curl -s "$API_BASE/api/infographic/$JOB_ID")
                
                # Pretty print the result (show transcript and analysis)
                echo "$RESULT_RESPONSE" | head -100
                
                echo -e "\n${GREEN}✅ SUCCESS: Transcript extracted and analyzed!${NC}"
                echo -e "\n${YELLOW}📋 What was extracted:${NC}"
                echo "• Video metadata (title, channel, thumbnail)"
                echo "• Full transcript text"
                echo "• AI-analyzed key points"
                echo "• Statistics and quotes"
                echo "• Content category classification"
                echo "• Relevant icons matched to content"
                
                break
            elif echo "$STATUS_RESPONSE" | grep -q '"status":"error"'; then
                echo -e "\n${RED}❌ Transcript extraction failed${NC}"
                break
            fi
            
            sleep 3
        done
    else
        echo -e "\n${RED}❌ No job ID found in response${NC}"
    fi
else
    echo -e "\n${RED}❌ Failed to start transcript extraction${NC}"
fi

echo -e "\n${BLUE}Quick Commands for Manual Testing:${NC}"
echo "================================================================"
echo "1. Start extraction:"
echo "curl -X POST -H 'Content-Type: application/json' \\"
echo "  -d '{\"url\": \"https://www.youtube.com/watch?v=dQw4w9WgXcQ\"}' \\"
echo "  $API_BASE/api/generate"

echo -e "\n2. Check status (replace JOB_ID):"
echo "curl $API_BASE/api/status/YOUR_JOB_ID"

echo -e "\n3. Get transcript result (replace JOB_ID):"
echo "curl $API_BASE/api/infographic/YOUR_JOB_ID"

echo -e "\n${YELLOW}💡 Other YouTube URLs you can test:${NC}"
echo "• https://www.youtube.com/watch?v=9bZkp7q19f0 (Gangnam Style)"
echo "• https://youtu.be/kJQP7kiw5Fk (Despacito)"
echo "• Any YouTube video with available transcripts"