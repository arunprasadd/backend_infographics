#!/bin/sh

echo "🚀 YouTube to Infographic API Validation with cURL"
echo "🌐 Testing API at: https://api.videotoinfographics.com"
echo "================================================================"

API_BASE="https://api.videotoinfographics.com"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "\n${BLUE}1. Health Check${NC}"
echo "================================================================"
curl -s -w "HTTP Status: %{http_code}\nResponse Time: %{time_total}s\n" \
  "$API_BASE/api/health" | head -20

echo -e "\n${BLUE}2. Get Available Templates${NC}"
echo "================================================================"
curl -s -w "HTTP Status: %{http_code}\n" \
  "$API_BASE/api/templates" | head -30

echo -e "\n${BLUE}3. Get Template Coordinates (Modern Business)${NC}"
echo "================================================================"
curl -s -w "HTTP Status: %{http_code}\n" \
  "$API_BASE/api/templates/modern-business/coordinates" | head -40

echo -e "\n${BLUE}4. Search Icons (Business Context)${NC}"
echo "================================================================"
curl -s -w "HTTP Status: %{http_code}\n" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"content": "business growth success profit", "category": "business", "limit": 5}' \
  "$API_BASE/api/icons/search" | head -30

echo -e "\n${BLUE}5. Search Icons (Technology Context)${NC}"
echo "================================================================"
curl -s -w "HTTP Status: %{http_code}\n" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"content": "artificial intelligence machine learning AI", "category": "technology", "limit": 3}' \
  "$API_BASE/api/icons/search" | head -20

echo -e "\n${BLUE}6. Start YouTube Transcript Processing${NC}"
echo "================================================================"
echo "Testing with Rick Astley - Never Gonna Give You Up (has transcripts)"
GENERATE_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}' \
  "$API_BASE/api/generate")

# Extract HTTP status and response body
HTTP_STATUS=$(echo "$GENERATE_RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
RESPONSE_BODY=$(echo "$GENERATE_RESPONSE" | sed '/HTTP_STATUS:/d')

echo "HTTP Status: $HTTP_STATUS"
echo "$RESPONSE_BODY"

# Extract job ID if successful
if [ "$HTTP_STATUS" = "200" ]; then
    JOB_ID=$(echo "$RESPONSE_BODY" | grep -o '"jobId":"[^"]*"' | cut -d'"' -f4)
    
    if [ -n "$JOB_ID" ]; then
        echo -e "\n${GREEN}✅ Job started successfully!${NC}"
        echo "Job ID: $JOB_ID"
        
        echo -e "\n${BLUE}7. Check Processing Status${NC}"
        echo "================================================================"
        curl -s -w "HTTP Status: %{http_code}\n" \
          "$API_BASE/api/status/$JOB_ID"
        
        echo -e "\n${YELLOW}💡 Monitor job progress with:${NC}"
        echo "curl -s \"$API_BASE/api/status/$JOB_ID\""
        
        echo -e "\n${YELLOW}💡 Get completed infographic with:${NC}"
        echo "curl -s \"$API_BASE/api/infographic/$JOB_ID\""
        
        echo -e "\n${BLUE}8. Test Status Endpoint (Live)${NC}"
        echo "================================================================"
        echo "Checking status every 3 seconds for 15 seconds..."
        
        for i in 1 2 3 4 5; do
            echo -e "\n--- Check $i/5 ---"
            STATUS_RESPONSE=$(curl -s "$API_BASE/api/status/$JOB_ID")
            echo "$STATUS_RESPONSE"
            
            # Check if completed
            if echo "$STATUS_RESPONSE" | grep -q '"status":"completed"'; then
                echo -e "\n${GREEN}🎉 Job completed! Getting final result...${NC}"
                
                echo -e "\n${BLUE}9. Get Completed Infographic${NC}"
                echo "================================================================"
                curl -s -w "HTTP Status: %{http_code}\n" \
                  "$API_BASE/api/infographic/$JOB_ID" | head -50
                break
            elif echo "$STATUS_RESPONSE" | grep -q '"status":"error"'; then
                echo -e "\n${RED}❌ Job failed${NC}"
                break
            fi
            
            sleep 3
        done
    else
        echo -e "\n${RED}❌ No job ID found in response${NC}"
    fi
else
    echo -e "\n${RED}❌ Failed to start job${NC}"
fi

echo -e "\n${BLUE}10. Test CORS Headers${NC}"
echo "================================================================"
curl -s -I \
  -X OPTIONS \
  -H "Origin: https://videotoinfographics.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  "$API_BASE/api/health" | grep -i "access-control"

echo -e "\n${BLUE}11. Test Invalid YouTube URL (Error Handling)${NC}"
echo "================================================================"
curl -s -w "HTTP Status: %{http_code}\n" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"url": "https://invalid-url.com/not-youtube"}' \
  "$API_BASE/api/generate"

echo -e "\n${BLUE}12. Test Missing URL Parameter${NC}"
echo "================================================================"
curl -s -w "HTTP Status: %{http_code}\n" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{}' \
  "$API_BASE/api/generate"

echo -e "\n================================================================"
echo -e "${YELLOW}📋 VALIDATION COMPLETE${NC}"
echo "================================================================"
echo -e "${GREEN}✅ Core Endpoints:${NC}"
echo "   • Health Check: $API_BASE/api/health"
echo "   • Templates: $API_BASE/api/templates"
echo "   • Icon Search: $API_BASE/api/icons/search"
echo ""
echo -e "${GREEN}✅ Processing Workflow:${NC}"
echo "   • Start: POST $API_BASE/api/generate"
echo "   • Monitor: GET $API_BASE/api/status/{jobId}"
echo "   • Result: GET $API_BASE/api/infographic/{jobId}"
echo ""
echo -e "${BLUE}📚 API Documentation:${NC} $API_BASE/docs"
echo -e "${BLUE}🔗 Frontend Integration Guide:${NC} See frontend_integration_guide.md"