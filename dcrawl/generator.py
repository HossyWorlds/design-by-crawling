"""Simple React component generator with Tailwind CSS."""

import re
from datetime import datetime
from typing import List, Dict
from .crawler import Element, CrawlResult
from .exceptions import GenerationError
import logging

logger = logging.getLogger(__name__)


class ReactGenerator:
    """Simple React component generator with Tailwind CSS."""
    
    def __init__(self, component_name: str = "GeneratedComponent"):
        self.component_name = component_name
        
    def generate(self, crawl_result: CrawlResult) -> str:
        """Generate React component from crawl result."""
        logger.info(f"Generating React component: {self.component_name}")
        
        try:
            # Group elements by category
            grouped = self._group_elements(crawl_result.elements)
            
            # Generate JSX
            jsx_content = self._generate_jsx(grouped)
            
            # Generate full component
            component = self._generate_component(jsx_content, crawl_result.url)
            
            logger.info("Component generation completed")
            return component
            
        except Exception as e:
            logger.error(f"Error generating component: {e}")
            raise GenerationError(f"Failed to generate component: {e}")
            
    def _group_elements(self, elements: List[Element]) -> Dict[str, List[Element]]:
        """Group elements by category."""
        grouped = {}
        for element in elements:
            if element.category not in grouped:
                grouped[element.category] = []
            grouped[element.category].append(element)
        return grouped
        
    def _generate_jsx(self, grouped_elements: Dict[str, List[Element]]) -> str:
        """Generate JSX content from grouped elements."""
        jsx_parts = []
        
        # Navigation first
        if 'navigation' in grouped_elements:
            jsx_parts.append('      {/* Navigation */}')
            jsx_parts.append('      <nav className="flex items-center justify-between px-6 py-4 border-b">')
            for element in grouped_elements['navigation'][:3]:
                jsx_parts.append(f'        {self._element_to_jsx(element, 8)}')
            jsx_parts.append('      </nav>')
            jsx_parts.append('')
        
        # Headers
        if 'header' in grouped_elements:
            jsx_parts.append('      {/* Headers */}')
            jsx_parts.append('      <header className="container mx-auto px-6 py-8">')
            for element in grouped_elements['header'][:5]:
                jsx_parts.append(f'        {self._element_to_jsx(element, 8)}')
            jsx_parts.append('      </header>')
            jsx_parts.append('')
        
        # Main content
        jsx_parts.append('      {/* Main Content */}')
        jsx_parts.append('      <main className="container mx-auto px-6 py-8">')
        
        # Other categories
        for category, elements in grouped_elements.items():
            if category in ['navigation', 'header']:
                continue
                
            if elements:
                jsx_parts.append(f'        {{/* {category.title()} */}}')
                jsx_parts.append('        <section className="mb-6">')
                
                for element in elements[:5]:  # Limit elements per section
                    jsx_parts.append(f'          {self._element_to_jsx(element, 10)}')
                    
                jsx_parts.append('        </section>')
                jsx_parts.append('')
        
        jsx_parts.append('      </main>')
        
        return '\n'.join(jsx_parts)
        
    def _element_to_jsx(self, element: Element, indent: int = 6) -> str:
        """Convert element to JSX."""
        indent_str = ' ' * indent
        
        # Get Tailwind classes
        classes = self._generate_tailwind_classes(element)
        
        # Clean text
        text = self._clean_text(element.text)
        
        # Self-closing tags
        if element.tag in ['img', 'input', 'br', 'hr']:
            attrs = self._get_jsx_attributes(element, classes)
            return f'<{element.tag}{attrs} />'
        
        # Regular tags
        attrs = self._get_jsx_attributes(element, classes)
        if len(text) > 50:
            text = text[:50] + "..."
            
        return f'<{element.tag}{attrs}>{text}</{element.tag}>'
        
    def _generate_tailwind_classes(self, element: Element) -> str:
        """Generate Tailwind classes from element styles."""
        classes = []
        styles = element.styles
        
        # Layout
        if 'flex' in styles.get('display', ''):
            classes.append('flex')
        elif 'block' in styles.get('display', ''):
            classes.append('block')
            
        # Typography
        font_size = styles.get('fontSize', '')
        if '24px' in font_size or '2rem' in font_size:
            classes.append('text-2xl')
        elif '20px' in font_size:
            classes.append('text-xl')
        elif '18px' in font_size:
            classes.append('text-lg')
        elif '14px' in font_size:
            classes.append('text-sm')
            
        font_weight = styles.get('fontWeight', '')
        if font_weight in ['700', 'bold']:
            classes.append('font-bold')
        elif font_weight in ['600', '500']:
            classes.append('font-medium')
            
        # Colors
        color = styles.get('color', '')
        if 'rgb(0, 0, 0)' in color or '#000' in color:
            classes.append('text-black')
        elif 'rgb(255, 255, 255)' in color or '#fff' in color:
            classes.append('text-white')
        elif 'gray' in color or 'grey' in color:
            classes.append('text-gray-600')
            
        bg_color = styles.get('backgroundColor', '')
        if 'rgb(255, 255, 255)' in bg_color or '#fff' in bg_color:
            classes.append('bg-white')
        elif 'rgb(0, 0, 0)' in bg_color or '#000' in bg_color:
            classes.append('bg-black')
            
        # Spacing - simplified
        padding = styles.get('padding', '')
        if padding and padding != '0px':
            if '16px' in padding or '1rem' in padding:
                classes.append('p-4')
            elif '8px' in padding:
                classes.append('p-2')
            else:
                classes.append('p-2')
                
        # Border radius
        border_radius = styles.get('borderRadius', '')
        if border_radius and border_radius != '0px':
            classes.append('rounded')
            
        # Box shadow
        box_shadow = styles.get('boxShadow', '')
        if box_shadow and box_shadow != 'none':
            classes.append('shadow')
            
        # Use existing classes if they look like Tailwind
        existing_classes = element.classes.split() if element.classes else []
        for cls in existing_classes:
            if self._is_tailwind_class(cls):
                classes.append(cls)
                
        # Remove duplicates and limit
        classes = list(dict.fromkeys(classes))[:8]  # Keep unique, limit to 8
        
        return ' '.join(classes) if classes else 'p-2'
        
    def _is_tailwind_class(self, cls: str) -> bool:
        """Check if a class looks like Tailwind CSS."""
        tailwind_patterns = [
            r'^(p|m|px|py|mx|my|pt|pb|pl|pr|mt|mb|ml|mr)-\d+$',
            r'^text-(xs|sm|base|lg|xl|2xl|3xl|4xl|5xl|6xl)$',
            r'^text-(black|white|gray|red|blue|green|yellow)-\d+$',
            r'^bg-(black|white|gray|red|blue|green|yellow)-\d+$',
            r'^font-(thin|light|normal|medium|semibold|bold|extrabold|black)$',
            r'^(flex|block|inline|hidden|relative|absolute|fixed)$',
            r'^rounded(-sm|-md|-lg|-xl|-full)?$',
            r'^shadow(-sm|-md|-lg|-xl|-2xl)?$'
        ]
        return any(re.match(pattern, cls) for pattern in tailwind_patterns)
        
    def _get_jsx_attributes(self, element: Element, classes: str) -> str:
        """Get JSX attributes for element."""
        attrs = []
        
        if classes:
            attrs.append(f'className="{classes}"')
            
        # Special attributes
        if element.tag == 'a' and element.attributes.get('href'):
            href = element.attributes['href']
            if href.startswith('http'):
                attrs.append(f'href="{href}"')
            else:
                attrs.append('href="#"')
                
        if element.tag == 'img' and element.attributes.get('src'):
            attrs.append(f'src="{element.attributes["src"]}"')
            attrs.append(f'alt="{element.attributes.get("alt", "")}"')
            
        if element.tag == 'input':
            attrs.append(f'type="{element.attributes.get("type", "text")}"')
            if element.attributes.get('placeholder'):
                attrs.append(f'placeholder="{element.attributes["placeholder"]}"')
                
        return ' ' + ' '.join(attrs) if attrs else ''
        
    def _clean_text(self, text: str) -> str:
        """Clean text for JSX."""
        if not text:
            return ""
            
        # Clean and escape
        text = text.strip()
        text = text.replace('"', '\\"')
        text = text.replace('\n', ' ')
        text = re.sub(r'\s+', ' ', text)  # Collapse whitespace
        
        return text
        
    def _generate_component(self, jsx_content: str, source_url: str) -> str:
        """Generate complete React component."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return f'''// Generated by design-by-crawling
// Generated on: {timestamp}
// Source: {source_url}

import React from 'react';

function {self.component_name}() {{
  return (
    <div className="min-h-screen bg-white">
{jsx_content}
    </div>
  );
}}

export default {self.component_name};'''