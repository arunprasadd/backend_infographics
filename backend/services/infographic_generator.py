"""
Infographic Generation Service
Combines templates, icons, and content to generate final infographics
"""
import json
import logging
from typing import Dict, List, Optional
from .vector_db import VectorIconService
from .template_service import TemplateService
import base64
from PIL import Image, ImageDraw, ImageFont
import io

logger = logging.getLogger(__name__)

class InfographicGenerator:
    def __init__(self):
        self.vector_service = VectorIconService()
        self.template_service = TemplateService()
    
    def generate_infographic_data(self, content_analysis: Dict, template_id: str) -> Dict:
        """Generate complete infographic data with positioned icons"""
        try:
            # Get template coordinates
            template_data = self.template_service.get_template_coordinates(template_id)
            
            if not template_data:
                logger.error(f"Template {template_id} not found")
                return {}
            
            # Find relevant icons based on content
            content_text = f"{content_analysis.get('mainTitle', '')} {' '.join(content_analysis.get('keyPoints', []))}"
            category = content_analysis.get('category', 'business')
            
            relevant_icons = self.vector_service.find_relevant_icons(
                content=content_text,
                category=category,
                limit=10
            )
            
            # Map icons to template positions
            positioned_elements = self._map_icons_to_positions(
                content_analysis,
                template_data,
                relevant_icons
            )
            
            # Generate final infographic structure
            infographic_data = {
                "template": template_data['template'],
                "content": content_analysis,
                "positioned_elements": positioned_elements,
                "color_schemes": template_data['color_schemes'],
                "dimensions": {
                    "width": template_data['template']['width'],
                    "height": template_data['template']['height']
                }
            }
            
            return infographic_data
            
        except Exception as e:
            logger.error(f"Error generating infographic data: {str(e)}")
            return {}
    
    def _map_icons_to_positions(self, content: Dict, template_data: Dict, icons: List[Dict]) -> Dict:
        """Map content elements to template positions with appropriate icons"""
        positioned_elements = {
            "key_points": [],
            "statistics": [],
            "quotes": [],
            "title": []
        }
        
        coordinates = template_data.get('coordinates', {})
        
        # Map key points
        key_points = content.get('keyPoints', [])
        key_point_coords = coordinates.get('key_point', [])
        
        for i, point in enumerate(key_points):
            if i < len(key_point_coords):
                coord = key_point_coords[i]
                
                # Find best matching icon for this key point
                best_icon = self._find_best_icon_for_text(point, icons)
                
                positioned_elements["key_points"].append({
                    "index": i,
                    "text": point,
                    "position": {
                        "x": coord['x'],
                        "y": coord['y'],
                        "width": coord['width'],
                        "height": coord['height']
                    },
                    "icon": best_icon,
                    "icon_size": coord.get('icon_size', 'medium')
                })
        
        # Map statistics
        statistics = content.get('statistics', [])
        stat_coords = coordinates.get('statistic', [])
        
        for i, stat in enumerate(statistics):
            if i < len(stat_coords):
                coord = stat_coords[i]
                
                # Find icon for statistic
                stat_text = f"{stat.get('label', '')} {stat.get('value', '')}"
                best_icon = self._find_best_icon_for_text(stat_text, icons)
                
                positioned_elements["statistics"].append({
                    "index": i,
                    "data": stat,
                    "position": {
                        "x": coord['x'],
                        "y": coord['y'],
                        "width": coord['width'],
                        "height": coord['height']
                    },
                    "icon": best_icon,
                    "icon_size": coord.get('icon_size', 'medium')
                })
        
        # Map quotes
        quotes = content.get('quotes', [])
        quote_coords = coordinates.get('quote', [])
        
        for i, quote in enumerate(quotes):
            if i < len(quote_coords):
                coord = quote_coords[i]
                
                positioned_elements["quotes"].append({
                    "index": i,
                    "text": quote,
                    "position": {
                        "x": coord['x'],
                        "y": coord['y'],
                        "width": coord['width'],
                        "height": coord['height']
                    },
                    "icon": self._find_best_icon_for_text("quote", icons),
                    "icon_size": coord.get('icon_size', 'medium')
                })
        
        return positioned_elements
    
    def _find_best_icon_for_text(self, text: str, available_icons: List[Dict]) -> Optional[Dict]:
        """Find the best matching icon for given text"""
        if not available_icons:
            return None
        
        text_lower = text.lower()
        best_icon = None
        best_score = 0
        
        for icon in available_icons:
            score = 0
            
            # Check keyword matches
            for keyword in icon.get('keywords', []):
                if keyword.lower() in text_lower:
                    score += 2
            
            # Check category relevance
            if icon.get('category', '').lower() in text_lower:
                score += 1
            
            # Use similarity score from vector search
            if 'similarity_score' in icon:
                score += icon['similarity_score']
            
            if score > best_score:
                best_score = score
                best_icon = icon
        
        return best_icon or available_icons[0]  # Return first icon as fallback
    
    def render_infographic_preview(self, infographic_data: Dict) -> str:
        """Generate a preview image of the infographic (base64 encoded)"""
        try:
            template = infographic_data.get('template', {})
            width = template.get('width', 1200)
            height = template.get('height', 1800)
            
            # Create image
            img = Image.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(img)
            
            # Try to load a font (fallback to default if not available)
            try:
                font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
                font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
                font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
            except:
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Draw title
            content = infographic_data.get('content', {})
            title = content.get('mainTitle', 'Infographic Title')
            
            # Calculate title position (centered)
            title_bbox = draw.textbbox((0, 0), title, font=font_large)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (width - title_width) // 2
            
            draw.text((title_x, 50), title, fill='black', font=font_large)
            
            # Draw positioned elements
            positioned_elements = infographic_data.get('positioned_elements', {})
            
            # Draw key points
            for element in positioned_elements.get('key_points', []):
                pos = element['position']
                text = element['text']
                
                # Draw icon placeholder (circle)
                draw.ellipse([
                    pos['x'], pos['y'],
                    pos['x'] + pos['width'], pos['y'] + pos['height']
                ], fill='lightblue', outline='blue')
                
                # Draw text next to icon
                text_x = pos['x'] + pos['width'] + 20
                draw.text((text_x, pos['y']), text[:80], fill='black', font=font_medium)
            
            # Draw statistics
            for element in positioned_elements.get('statistics', []):
                pos = element['position']
                stat = element['data']
                
                # Draw icon placeholder
                draw.rectangle([
                    pos['x'], pos['y'],
                    pos['x'] + pos['width'], pos['y'] + pos['height']
                ], fill='lightgreen', outline='green')
                
                # Draw statistic
                stat_text = f"{stat.get('value', '')}: {stat.get('label', '')}"
                text_x = pos['x'] + pos['width'] + 20
                draw.text((text_x, pos['y']), stat_text[:60], fill='black', font=font_medium)
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            logger.error(f"Error rendering infographic preview: {str(e)}")
            return ""