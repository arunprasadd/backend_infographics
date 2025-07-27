#!/usr/bin/env python3
"""
Validation script to test ChromaDB embeddings and icon search functionality
"""

import sys
import os
sys.path.append('/app')

from services.vector_db import VectorIconService
import json

def main():
    print("🔍 Validating ChromaDB Embeddings...")
    
    # Initialize service
    try:
        vector_service = VectorIconService()
        print("✅ Vector service initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize vector service: {e}")
        return
    
    # Check collection info
    print("\n📊 Collection Information:")
    info = vector_service.get_collection_info()
    print(json.dumps(info, indent=2))
    
    if info.get('count', 0) == 0:
        print("⚠️  No icons found in collection!")
        return
    
    # Test search functionality
    print(f"\n🔍 Testing Search with {info['count']} icons...")
    
    test_queries = [
        ("business growth", "business"),
        ("artificial intelligence", "technology"), 
        ("education learning", "education"),
        ("communication chat", "communication"),
        ("money finance", "finance"),
        ("health medical", "health"),
        ("travel journey", "transport"),
        ("social media", "communication")
    ]
    
    all_working = True
    
    for query, expected_category in test_queries:
        try:
            results = vector_service.find_relevant_icons(query, limit=5)
            
            if not results:
                print(f"❌ No results for query: '{query}'")
                all_working = False
                continue
            
            print(f"\n🎯 Query: '{query}' (expecting {expected_category} category)")
            print(f"   Found {len(results)} relevant icons:")
            
            for i, result in enumerate(results[:3]):
                score = result.get('similarity_score', 0)
                category = result.get('category', 'unknown')
                name = result.get('name', 'unnamed')
                
                # Check if we got reasonable results
                status = "✅" if score > 0.3 else "⚠️"
                print(f"   {status} {i+1}. {name}")
                print(f"      Category: {category} | Score: {score:.3f}")
                
                if score < 0.1:
                    all_working = False
                    
        except Exception as e:
            print(f"❌ Error searching for '{query}': {e}")
            all_working = False
    
    # Test category filtering
    print(f"\n🏷️  Testing Category Filtering...")
    categories = ['business', 'technology', 'education', 'communication']
    
    for category in categories:
        try:
            results = vector_service.find_relevant_icons(
                content="general search", 
                category=category, 
                limit=3
            )
            
            if results:
                print(f"✅ Found {len(results)} icons in '{category}' category")
                # Check if results actually match the category
                matching_category = sum(1 for r in results if r.get('category') == category)
                if matching_category > 0:
                    print(f"   {matching_category}/{len(results)} icons match the category filter")
            else:
                print(f"⚠️  No icons found in '{category}' category")
                
        except Exception as e:
            print(f"❌ Error filtering by category '{category}': {e}")
            all_working = False
    
    # Final validation
    print(f"\n{'='*50}")
    if all_working and info.get('count', 0) > 0:
        print("🎉 Embeddings validation PASSED!")
        print("✅ ChromaDB is working correctly")
        print("✅ Icon search is functional")
        print("✅ Similarity scoring is working")
        print(f"✅ {info['count']} icons are properly embedded")
    else:
        print("❌ Embeddings validation FAILED!")
        print("🔧 Check the logs above for specific issues")
    
    print(f"{'='*50}")

if __name__ == "__main__":
    main()