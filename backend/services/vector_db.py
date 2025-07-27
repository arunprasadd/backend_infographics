"""
Vector Database Service for Icon Management using ChromaDB
Handles icon embeddings, similarity search, and retrieval - NO OpenAI API key needed
"""
import chromadb
from chromadb.config import Settings
import numpy as np
from PIL import Image
import os
import logging
from typing import List, Dict, Optional
from tqdm import tqdm
import uuid
import hashlib

logger = logging.getLogger(__name__)

class VectorIconService:
    def __init__(self):
        # Initialize ChromaDB client (local persistent storage)
        self.db_path = os.getenv('VECTOR_DB_PATH', '/app/data/vector_db')
        
        # Try to create directory, handle permission errors gracefully
        try:
            os.makedirs(self.db_path, exist_ok=True)
        except PermissionError:
            logger.warning(f"Permission denied creating {self.db_path}, using /tmp")
            self.db_path = '/tmp/vector_db'
            os.makedirs(self.db_path, exist_ok=True)
        
        try:
            # Initialize ChromaDB with proper settings
            self.client = chromadb.PersistentClient(
                path=self.db_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Collection name for icons
            self.collection_name = "icon_collection"
            
            # Get or create collection with default embedding function
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            logger.info("ChromaDB initialized successfully")
            
            # Initialize default icons if collection is empty
            self._initialize_default_icons()
            
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {str(e)}")
            # Fallback to mock service
            self.collection = None
    
    def _initialize_default_icons(self):
        """Initialize with icons from the images folder"""
        try:
            # Check if collection already has icons
            if self.collection and self.collection.count() > 0:
                logger.info(f"Collection already has {self.collection.count()} icons")
                return
            
            # Look for images folder
            images_folder = "/app/images"
            if not os.path.exists(images_folder):
                # Try alternative paths
                alternative_paths = [
                    "./images",
                    "../images", 
                    "/images",
                    os.path.join(os.path.dirname(__file__), "../../images")
                ]
                
                for path in alternative_paths:
                    if os.path.exists(path):
                        images_folder = path
                        break
                else:
                    logger.warning("Images folder not found, creating sample icons")
                    self._create_sample_icons()
                    return
            
            logger.info(f"Loading icons from: {images_folder}")
            self.add_images_from_folder(images_folder)
            
        except Exception as e:
            logger.error(f"Error initializing default icons: {str(e)}")
    
    def add_images_from_folder(self, folder_path: str):
        """Add all images from a folder to the collection"""
        if not self.collection:
            logger.error("Collection not initialized")
            return
        
        try:
            # Get all image files
            image_extensions = ('.png', '.jpg', '.jpeg', '.svg', '.gif', '.bmp')
            image_files = [
                os.path.join(folder_path, filename) 
                for filename in os.listdir(folder_path)
                if os.path.isfile(os.path.join(folder_path, filename)) 
                and filename.lower().endswith(image_extensions)
            ]
            
            logger.info(f"Found {len(image_files)} images to process")
            
            if not image_files:
                logger.warning("No image files found in folder")
                return
            
            # Process images in batches
            batch_size = 10
            for i in tqdm(range(0, len(image_files), batch_size), desc="Adding images to ChromaDB"):
                batch_files = image_files[i:i + batch_size]
                self._add_image_batch(batch_files)
            
            logger.info(f"Successfully added {len(image_files)} images to collection")
            
        except Exception as e:
            logger.error(f"Error adding images from folder: {str(e)}")
    
    def _add_image_batch(self, image_files: List[str]):
        """Add a batch of images to the collection"""
        try:
            ids = []
            documents = []
            metadatas = []
            
            for image_path in image_files:
                try:
                    # Extract metadata from filename
                    filename = os.path.basename(image_path)
                    name_without_ext = os.path.splitext(filename)[0]
                    
                    # Generate keywords from filename
                    keywords = []
                    if '_' in name_without_ext:
                        keywords.extend(name_without_ext.split('_'))
                    if '-' in name_without_ext:
                        keywords.extend(name_without_ext.split('-'))
                    
                    # Clean keywords
                    keywords = [kw.lower().strip() for kw in keywords if len(kw) > 2]
                    
                    # Determine category from filename or folder
                    category = self._determine_category(name_without_ext, keywords)
                    
                    # Create document text for embedding (ChromaDB will embed this)
                    document_text = f"{name_without_ext} {' '.join(keywords)} {category}"
                    
                    # Generate unique ID
                    file_hash = hashlib.md5(filename.encode()).hexdigest()[:8]
                    unique_id = f"{name_without_ext}_{file_hash}"
                    
                    ids.append(unique_id)
                    documents.append(document_text)
                    metadatas.append({
                        "filename": filename,
                        "name": name_without_ext,
                        "category": category,
                        "keywords": " ".join(keywords),  # Convert list to string
                        "path": image_path
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing {image_path}: {str(e)}")
                    continue
            
            # Add batch to collection
            if ids and documents:
                self.collection.add(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )
                
        except Exception as e:
            logger.error(f"Error adding image batch: {str(e)}")
    
    def _determine_category(self, filename: str, keywords: List[str]) -> str:
        """Determine category based on filename and keywords"""
        filename_lower = filename.lower()
        all_text = filename_lower + " " + " ".join(keywords)
        
        # Category mapping
        category_keywords = {
            'business': ['business', 'office', 'work', 'corporate', 'meeting', 'deal', 'plan', 'analytics'],
            'technology': ['tech', 'computer', 'digital', 'ai', 'robot', 'code', 'data', 'cyber'],
            'education': ['education', 'school', 'learn', 'study', 'book', 'teacher', 'student', 'graduation'],
            'health': ['health', 'medical', 'doctor', 'hospital', 'medicine', 'fitness', 'wellness'],
            'communication': ['chat', 'message', 'call', 'phone', 'email', 'social', 'network'],
            'finance': ['money', 'dollar', 'payment', 'bank', 'finance', 'credit', 'investment'],
            'transport': ['car', 'vehicle', 'transport', 'travel', 'journey', 'road', 'traffic'],
            'lifestyle': ['lifestyle', 'home', 'family', 'love', 'happy', 'celebration', 'party']
        }
        
        # Find best matching category
        for category, category_words in category_keywords.items():
            if any(word in all_text for word in category_words):
                return category
        
        return 'general'
    
    def _create_sample_icons(self):
        """Create sample icon data when no images folder is found"""
        try:
            sample_icons = [
                {
                    "name": "Business Growth",
                    "category": "business",
                    "keywords": ["growth", "increase", "profit", "success"],
                    "description": "Business growth and success icon"
                },
                {
                    "name": "Artificial Intelligence",
                    "category": "technology", 
                    "keywords": ["ai", "artificial", "intelligence", "robot", "automation"],
                    "description": "AI and technology icon"
                },
                {
                    "name": "Learning",
                    "category": "education",
                    "keywords": ["learn", "education", "study", "knowledge", "book"],
                    "description": "Learning and education icon"
                }
            ]
            
            # Add sample icons
            ids = [f"sample_{i}" for i in range(len(sample_icons))]
            documents = [f"{icon['name']} {' '.join(icon['keywords'])} {icon['category']}" for icon in sample_icons]
            metadatas = sample_icons
            
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            
            logger.info("Created sample icons")
            
        except Exception as e:
            logger.error(f"Error creating sample icons: {str(e)}")
    
    def find_relevant_icons(self, content: str, category: str = None, limit: int = 6) -> List[Dict]:
        """Find relevant icons based on content similarity"""
        if not self.collection:
            logger.warning("Collection not available, returning empty results")
            return []
        
        try:
            # Build query with category filter if specified
            where_filter = {"category": category} if category else None
            
            # Search using text query
            results = self.collection.query(
                query_texts=[content],
                n_results=limit,
                where=where_filter
            )
            
            # Format results
            icons = []
            if results['ids'] and len(results['ids']) > 0:
                for i in range(len(results['ids'][0])):
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    distance = results['distances'][0][i] if results['distances'] else 0
                    
                    icon = {
                        "id": results['ids'][0][i],
                        "name": metadata.get('name', results['ids'][0][i]),
                        "category": metadata.get('category', 'general'),
                        "keywords": metadata.get('keywords', []),
                        "description": f"Icon for {metadata.get('name', 'content')}",
                        "similarity_score": 1.0 - distance,  # Convert distance to similarity
                        "svg_path": self._generate_svg_placeholder(metadata.get('name', 'icon'))
                    }
                    icons.append(icon)
            
            return icons
            
        except Exception as e:
            logger.error(f"Error finding relevant icons: {str(e)}")
            return self._get_fallback_icons(limit)
    
    def _generate_svg_placeholder(self, name: str) -> str:
        """Generate a simple SVG placeholder"""
        # Simple circle SVG as placeholder
        return f'<circle cx="12" cy="12" r="10" fill="currentColor"/>'
    
    def _get_fallback_icons(self, limit: int) -> List[Dict]:
        """Return fallback icons when search fails"""
        fallback_icons = [
            {
                "id": f"fallback_{i}",
                "name": f"Icon {i+1}",
                "category": "general",
                "keywords": ["general", "icon"],
                "description": f"Fallback icon {i+1}",
                "similarity_score": 0.5,
                "svg_path": '<circle cx="12" cy="12" r="10" fill="currentColor"/>'
            }
            for i in range(min(limit, 6))
        ]
        return fallback_icons
    
    def get_collection_info(self) -> Dict:
        """Get information about the collection"""
        try:
            if not self.collection:
                return {"status": "not_available", "count": 0}
            
            count = self.collection.count()
            return {
                "status": "available",
                "count": count,
                "collection_name": self.collection_name
            }
            
        except Exception as e:
            logger.error(f"Error getting collection info: {str(e)}")
            return {"status": "error", "count": 0, "error": str(e)}