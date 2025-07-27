"""
Template Management Service
Handles local template storage, retrieval, and coordinate management
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import logging
from typing import Dict, List, Optional, Tuple
import os
from datetime import datetime
import shutil

logger = logging.getLogger(__name__)

class TemplateService:
    def __init__(self):
        # Initialize local template storage
        self.templates_dir = os.getenv('TEMPLATES_DIR', '/app/templates')
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Initialize PostgreSQL connection for coordinates
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', 5432),
            'database': os.getenv('DB_NAME', 'infographic_db'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres')
        }
        
        # Initialize database tables
        self._init_database()
        
        # Initialize default templates if none exist
        self._init_default_templates()
    
    def _init_database(self):
        """Initialize database tables for template coordinates"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Create templates table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS templates (
                    id VARCHAR(50) PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    description TEXT,
                    s3_path VARCHAR(255),
                    width INTEGER DEFAULT 1200,
                    height INTEGER DEFAULT 1800,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create icon coordinates table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS template_icon_coordinates (
                    id SERIAL PRIMARY KEY,
                    template_id VARCHAR(50) REFERENCES templates(id),
                    element_type VARCHAR(50) NOT NULL, -- 'key_point', 'statistic', 'quote', 'title'
                    element_index INTEGER NOT NULL, -- 0, 1, 2, etc for multiple elements
                    x_coordinate INTEGER NOT NULL,
                    y_coordinate INTEGER NOT NULL,
                    width INTEGER DEFAULT 24,
                    height INTEGER DEFAULT 24,
                    icon_size VARCHAR(20) DEFAULT 'medium', -- 'small', 'medium', 'large'
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(template_id, element_type, element_index)
                )
            """)
            
            # Create color schemes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS template_color_schemes (
                    id SERIAL PRIMARY KEY,
                    template_id VARCHAR(50) REFERENCES templates(id),
                    scheme_name VARCHAR(50) NOT NULL,
                    primary_color VARCHAR(7) NOT NULL,
                    secondary_color VARCHAR(7) NOT NULL,
                    accent_color VARCHAR(7) NOT NULL,
                    background_color VARCHAR(7) NOT NULL,
                    text_color VARCHAR(7) NOT NULL,
                    is_default BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info("Database tables initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
    
    def _init_default_templates(self):
        """Initialize default templates with coordinates"""
        default_templates = [
            {
                "id": "modern-business",
                "name": "Modern Business",
                "category": "business",
                "description": "Clean corporate design with professional layout",
                "width": 1200,
                "height": 1800,
                "icon_coordinates": [
                    {"element_type": "key_point", "element_index": 0, "x": 100, "y": 400, "width": 32, "height": 32},
                    {"element_type": "key_point", "element_index": 1, "x": 100, "y": 520, "width": 32, "height": 32},
                    {"element_type": "key_point", "element_index": 2, "x": 100, "y": 640, "width": 32, "height": 32},
                    {"element_type": "key_point", "element_index": 3, "x": 100, "y": 760, "width": 32, "height": 32},
                    {"element_type": "key_point", "element_index": 4, "x": 100, "y": 880, "width": 32, "height": 32},
                    {"element_type": "statistic", "element_index": 0, "x": 200, "y": 1100, "width": 40, "height": 40},
                    {"element_type": "statistic", "element_index": 1, "x": 600, "y": 1100, "width": 40, "height": 40},
                ],
                "color_schemes": [
                    {
                        "scheme_name": "Corporate Blue",
                        "primary_color": "#2563EB",
                        "secondary_color": "#1E40AF",
                        "accent_color": "#3B82F6",
                        "background_color": "#FFFFFF",
                        "text_color": "#1F2937",
                        "is_default": True
                    }
                ]
            },
            {
                "id": "educational-flow",
                "name": "Educational Flow",
                "category": "education",
                "description": "Perfect for learning content with step-by-step layout",
                "width": 1200,
                "height": 1800,
                "icon_coordinates": [
                    {"element_type": "key_point", "element_index": 0, "x": 80, "y": 350, "width": 28, "height": 28},
                    {"element_type": "key_point", "element_index": 1, "x": 80, "y": 450, "width": 28, "height": 28},
                    {"element_type": "key_point", "element_index": 2, "x": 80, "y": 550, "width": 28, "height": 28},
                    {"element_type": "key_point", "element_index": 3, "x": 80, "y": 650, "width": 28, "height": 28},
                    {"element_type": "key_point", "element_index": 4, "x": 80, "y": 750, "width": 28, "height": 28},
                    {"element_type": "key_point", "element_index": 5, "x": 80, "y": 850, "width": 28, "height": 28},
                ],
                "color_schemes": [
                    {
                        "scheme_name": "Academic Blue",
                        "primary_color": "#1D4ED8",
                        "secondary_color": "#1E40AF",
                        "accent_color": "#3B82F6",
                        "background_color": "#F8FAFC",
                        "text_color": "#0F172A",
                        "is_default": True
                    }
                ]
            }
        ]
        
        for template in default_templates:
            self.save_template(template)
    
    def save_template(self, template_data: Dict) -> bool:
        """Save template to database and S3"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Check if template exists
            cursor.execute("SELECT id FROM templates WHERE id = %s", (template_data['id'],))
            exists = cursor.fetchone()
            
            if not exists:
                # Insert template
                cursor.execute("""
                    INSERT INTO templates (id, name, category, description, width, height)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    template_data['id'],
                    template_data['name'],
                    template_data['category'],
                    template_data['description'],
                    template_data.get('width', 1200),
                    template_data.get('height', 1800)
                ))
                
                # Insert icon coordinates
                for coord in template_data.get('icon_coordinates', []):
                    cursor.execute("""
                        INSERT INTO template_icon_coordinates 
                        (template_id, element_type, element_index, x_coordinate, y_coordinate, width, height)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (template_id, element_type, element_index) 
                        DO UPDATE SET 
                            x_coordinate = EXCLUDED.x_coordinate,
                            y_coordinate = EXCLUDED.y_coordinate,
                            width = EXCLUDED.width,
                            height = EXCLUDED.height
                    """, (
                        template_data['id'],
                        coord['element_type'],
                        coord['element_index'],
                        coord['x'],
                        coord['y'],
                        coord.get('width', 24),
                        coord.get('height', 24)
                    ))
                
                # Insert color schemes
                for scheme in template_data.get('color_schemes', []):
                    cursor.execute("""
                        INSERT INTO template_color_schemes 
                        (template_id, scheme_name, primary_color, secondary_color, accent_color, background_color, text_color, is_default)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        template_data['id'],
                        scheme['scheme_name'],
                        scheme['primary_color'],
                        scheme['secondary_color'],
                        scheme['accent_color'],
                        scheme['background_color'],
                        scheme['text_color'],
                        scheme.get('is_default', False)
                    ))
                
                conn.commit()
                logger.info(f"Template {template_data['id']} saved successfully")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error saving template: {str(e)}")
            return False
    
    def get_template_coordinates(self, template_id: str) -> Dict:
        """Get icon coordinates for a template"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get template info
            cursor.execute("SELECT * FROM templates WHERE id = %s", (template_id,))
            template = cursor.fetchone()
            
            if not template:
                return {}
            
            # Get coordinates
            cursor.execute("""
                SELECT element_type, element_index, x_coordinate, y_coordinate, width, height, icon_size
                FROM template_icon_coordinates 
                WHERE template_id = %s 
                ORDER BY element_type, element_index
            """, (template_id,))
            
            coordinates = cursor.fetchall()
            
            # Get color schemes
            cursor.execute("""
                SELECT scheme_name, primary_color, secondary_color, accent_color, background_color, text_color, is_default
                FROM template_color_schemes 
                WHERE template_id = %s
            """, (template_id,))
            
            color_schemes = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            # Format response
            result = {
                "template": dict(template),
                "coordinates": {},
                "color_schemes": [dict(scheme) for scheme in color_schemes]
            }
            
            # Group coordinates by element type
            for coord in coordinates:
                element_type = coord['element_type']
                if element_type not in result['coordinates']:
                    result['coordinates'][element_type] = []
                
                result['coordinates'][element_type].append({
                    "index": coord['element_index'],
                    "x": coord['x_coordinate'],
                    "y": coord['y_coordinate'],
                    "width": coord['width'],
                    "height": coord['height'],
                    "icon_size": coord['icon_size']
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting template coordinates: {str(e)}")
            return {}
    
    def get_all_templates(self) -> List[Dict]:
        """Get all available templates"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT t.*, 
                       COUNT(DISTINCT tic.id) as icon_positions,
                       COUNT(DISTINCT tcs.id) as color_schemes
                FROM templates t
                LEFT JOIN template_icon_coordinates tic ON t.id = tic.template_id
                LEFT JOIN template_color_schemes tcs ON t.id = tcs.template_id
                GROUP BY t.id, t.name, t.category, t.description, t.s3_path, t.width, t.height, t.created_at, t.updated_at
                ORDER BY t.created_at DESC
            """)
            
            templates = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return [dict(template) for template in templates]
            
        except Exception as e:
            logger.error(f"Error getting templates: {str(e)}")
            return []
    
    def upload_template_to_s3(self, template_id: str, file_content: bytes, file_type: str = "svg") -> str:
        """Upload template file to S3"""
        if not self.s3_client:
            logger.warning("S3 client not configured")
            return ""
        
        try:
            file_key = f"templates/{template_id}.{file_type}"
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_key,
                Body=file_content,
                ContentType=f"image/{file_type}"
            )
            
            # Update template record with S3 path
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute(
                "UPDATE templates SET s3_path = %s WHERE id = %s",
                (file_key, template_id)
            )
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return file_key
            
        except Exception as e:
            logger.error(f"Error uploading template to S3: {str(e)}")
            return ""