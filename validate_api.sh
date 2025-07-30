#!/bin/bash

echo "🚀 YouTube to Infographic API Validation"
echo "🌐 Testing API at: https://api.videotoinfographics.com"
echo "=" * 60

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to test endpoint
test_endpoint() {
    local name="$1"
    local url="$2"
    local method="${3:-GET}"
    local data="$4"
    
    echo -e "\n${YELLOW}Testing: $name${NC}"
    echo "URL: $url"
    
    if [ "$method" = "POST" ] && [ -n "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$url" 2>/dev/null)
    else
        response=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null)
    fi
    
    # Split response and status code
    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$status_code" = "200" ]; then
        echo -e "${GREEN}✅ PASS${NC} - HTTP $status_code"
        # Pretty print JSON if it's valid JSON
        if echo "$body" | jq . >/dev/null 2>&1; then
            echo "$body" | jq . | head -10
        else
            echo "$body" | head -5
        fi
    else
        echo -e "${RED}❌ FAIL${NC} - HTTP $status_code"
        echo "$body" | head -3
    fi
    
    return $([ "$status_code" = "200" ] && echo 0 || echo 1)
}

# Test 1: Health Check
test_endpoint "Health Check" "https://api.videotoinfographics.com/api/health"
health_status=$?

# Test 2: Templates
test_endpoint "Templates" "https://api.videotoinfographics.com/api/templates"
templates_status=$?

# Test 3: Template Coordinates
test_endpoint "Template Coordinates" "https://api.videotoinfographics.com/api/templates/modern-business/coordinates"
coordinates_status=$?

# Test 4: Icon Search
icon_search_data='{"content": "business growth", "category": "business", "limit": 5}'
test_endpoint "Icon Search" "https://api.videotoinfographics.com/api/icons/search" "POST" "$icon_search_data"
icons_status=$?

# Test 5: Generate Infographic (start job)
generate_data='{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
echo -e "\n${YELLOW}Testing: Generate Infographic${NC}"
echo "URL: https://api.videotoinfographics.com/api/generate"
echo "Data: $generate_data"

generate_response=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -d "$generate_data" \
    "https://api.videotoinfographics.com/api/generate" 2>/dev/null)

generate_status_code=$(echo "$generate_response" | tail -n1)
generate_body=$(echo "$generate_response" | head -n -1)

if [ "$generate_status_code" = "200" ]; then
    echo -e "${GREEN}✅ PASS${NC} - HTTP $generate_status_code"
    echo "$generate_body" | jq .
    
    # Extract job ID for status check
    job_id=$(echo "$generate_body" | jq -r '.jobId' 2>/dev/null)
    
    if [ "$job_id" != "null" ] && [ -n "$job_id" ]; then
        echo -e "\n${YELLOW}Testing: Job Status${NC}"
        echo "Job ID: $job_id"
        
        # Test status endpoint
        status_response=$(curl -s -w "\n%{http_code}" \
            "https://api.videotoinfographics.com/api/status/$job_id" 2>/dev/null)
        
        status_status_code=$(echo "$status_response" | tail -n1)
        status_body=$(echo "$status_response" | head -n -1)
        
        if [ "$status_status_code" = "200" ]; then
            echo -e "${GREEN}✅ PASS${NC} - Status Check HTTP $status_status_code"
            echo "$status_body" | jq .
            generate_status=0
        else
            echo -e "${RED}❌ FAIL${NC} - Status Check HTTP $status_status_code"
            generate_status=1
        fi
    else
        echo -e "${RED}❌ FAIL${NC} - No job ID returned"
        generate_status=1
    fi
else
    echo -e "${RED}❌ FAIL${NC} - HTTP $generate_status_code"
    echo "$generate_body"
    generate_status=1
fi

# Test 6: CORS Headers
echo -e "\n${YELLOW}Testing: CORS Headers${NC}"
cors_response=$(curl -s -I -X OPTIONS \
    -H "Origin: https://videotoinfographics.com" \
    -H "Access-Control-Request-Method: POST" \
    -H "Access-Control-Request-Headers: Content-Type" \
    "https://api.videotoinfographics.com/api/health" 2>/dev/null)

if echo "$cors_response" | grep -i "access-control-allow-origin" >/dev/null; then
    echo -e "${GREEN}✅ PASS${NC} - CORS Headers Present"
    echo "$cors_response" | grep -i "access-control"
    cors_status=0
else
    echo -e "${RED}❌ FAIL${NC} - CORS Headers Missing"
    cors_status=1
fi

# Summary
echo -e "\n" "=" * 60
echo -e "${YELLOW}📋 VALIDATION SUMMARY${NC}"
echo "=" * 60

tests_passed=0
total_tests=6

[ $health_status -eq 0 ] && ((tests_passed++)) && echo -e "${GREEN}✅${NC} Health Check"
[ $health_status -ne 0 ] && echo -e "${RED}❌${NC} Health Check"

[ $templates_status -eq 0 ] && ((tests_passed++)) && echo -e "${GREEN}✅${NC} Templates"
[ $templates_status -ne 0 ] && echo -e "${RED}❌${NC} Templates"

[ $coordinates_status -eq 0 ] && ((tests_passed++)) && echo -e "${GREEN}✅${NC} Template Coordinates"
[ $coordinates_status -ne 0 ] && echo -e "${RED}❌${NC} Template Coordinates"

[ $icons_status -eq 0 ] && ((tests_passed++)) && echo -e "${GREEN}✅${NC} Icon Search"
[ $icons_status -ne 0 ] && echo -e "${RED}❌${NC} Icon Search"

[ $generate_status -eq 0 ] && ((tests_passed++)) && echo -e "${GREEN}✅${NC} Video Generation"
[ $generate_status -ne 0 ] && echo -e "${RED}❌${NC} Video Generation"

[ $cors_status -eq 0 ] && ((tests_passed++)) && echo -e "${GREEN}✅${NC} CORS Configuration"
[ $cors_status -ne 0 ] && echo -e "${RED}❌${NC} CORS Configuration"

echo ""
echo "Tests Passed: $tests_passed/$total_tests ($(( tests_passed * 100 / total_tests ))%)"

if [ $tests_passed -ge 4 ]; then
    echo -e "${GREEN}🎉 API IS READY FOR FRONTEND INTEGRATION!${NC}"
    echo ""
    echo "🔗 Frontend Integration URLs:"
    echo "   API Base: https://api.videotoinfographics.com"
    echo "   Health: https://api.videotoinfographics.com/api/health"
    echo "   Docs: https://api.videotoinfographics.com/docs"
    echo ""
    echo "📝 Key Endpoints:"
    echo "   POST /api/generate - Start video processing"
    echo "   GET /api/status/{jobId} - Check processing status"
    echo "   GET /api/infographic/{jobId} - Get completed infographic"
    echo "   GET /api/templates - Get available templates"
    echo "   POST /api/icons/search - Search for icons"
else
    echo -e "${RED}⚠️ API HAS ISSUES THAT NEED TO BE ADDRESSED${NC}"
    echo "Please check the failed tests above."
fi

exit $([ $tests_passed -ge 4 ] && echo 0 || echo 1)