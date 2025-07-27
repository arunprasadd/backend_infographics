#!/usr/bin/env python3
"""
Image Loading Script for ChromaDB Vector Database
Loads images from the images folder and stores them with OpenCLIP embeddings
NO OpenAI API key required!
"""

import sys
import os
sys.path.append('/app')

from services.vector_db import VectorIconService
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main function to load images into ChromaDB"""
    
    print("🚀 Loading images into ChromaDB with OpenCLIP...")
    print("📝 Note: No OpenAI API key required!")
    
    # Initialize the vector service
    vector_service = VectorIconService()
    
    # Check if images folder exists
    images_folder = "/app/images"
    if not os.path.exists(images_folder):
        print(f"❌ Images folder not found at: {images_folder}")
        print("📁 Please ensure your images are mounted to /app/images in the container")
        
        # Try to find images in alternative locations
        alternative_paths = [
            "./images",
            "../images",
            "/images"
        ]
        
        for path in alternative_paths:
            if os.path.exists(path):
                print(f"✅ Found images at: {path}")
                images_folder = path
                break
        else:
            print("⚠️  No images found, will create sample icons")
            vector_service._create_sample_icons()
            return
    
    # Load images from folder
    print(f"📂 Loading images from: {images_folder}")
    vector_service.add_images_from_folder(images_folder)
    
    # Get collection info
    info = vector_service.get_collection_info()
    print(f"✅ Collection info: {info}")
    
    # Test search functionality
    print("\n🔍 Testing icon search...")
    test_queries = [
        "business growth",
        "technology innovation", 
        "education learning",
        "communication chat"
    ]
    
    for query in test_queries:
        results = vector_service.find_relevant_icons(query, limit=3)
        print(f"Query: '{query}' -> Found {len(results)} icons")
        for result in results[:2]:  # Show first 2 results
            print(f"  - {result['name']} (category: {result['category']}, score: {result['similarity_score']:.3f})")
    
    print("\n🎉 Image loading completed successfully!")
    print("💡 Your icons are now ready for semantic search!")

if __name__ == "__main__":
    main()