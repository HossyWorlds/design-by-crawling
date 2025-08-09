"""Simple web crawler with element analysis."""

import asyncio
from typing import Dict, List, Optional, Tuple
from playwright.async_api import async_playwright, Browser, Page
import logging
from dataclasses import dataclass

from .exceptions import CrawlingError

logger = logging.getLogger(__name__)


@dataclass
class Element:
    """Simplified element data structure."""
    tag: str
    text: str
    classes: str
    styles: Dict[str, str]
    attributes: Dict[str, str]
    position: Dict[str, float]
    category: str


@dataclass
class CrawlResult:
    """Result of crawling a website."""
    url: str
    title: str
    elements: List[Element]


class WebCrawler:
    """Simple web crawler with built-in analysis."""
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
        self.browser: Optional[Browser] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=self.headless)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.browser:
            await self.browser.close()
            
    async def crawl(self, url: str) -> CrawlResult:
        """Crawl a website and return analyzed elements."""
        if not self.browser:
            raise CrawlingError("Browser not initialized")
            
        logger.info(f"Starting crawl of {url}")
        
        try:
            page = await self.browser.new_page()
            
            # Navigate to page
            response = await page.goto(url, timeout=self.timeout)
            if not response or response.status >= 400:
                raise CrawlingError(f"Failed to load {url}: HTTP {response.status if response else 'No response'}")
                
            # Wait for content
            await page.wait_for_load_state('networkidle', timeout=15000)
            await asyncio.sleep(2)  # Additional wait
            
            # Get page title
            title = await page.title()
            
            # Extract elements
            elements = await self._extract_elements(page)
            
            logger.info(f"Successfully extracted {len(elements)} elements from {url}")
            
            await page.close()
            return CrawlResult(url=url, title=title, elements=elements)
            
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
            raise CrawlingError(f"Failed to crawl {url}: {e}")
            
    async def _extract_elements(self, page: Page) -> List[Element]:
        """Extract and analyze elements from the page."""
        # Define selectors for different element types
        selectors = [
            ('nav, [role="navigation"]', 'navigation'),
            ('h1, h2, h3, h4, h5, h6', 'header'),
            ('button, [role="button"]', 'button'),
            ('a[href]', 'link'),
            ('img[src]', 'image'),
            ('input, textarea, select', 'form'),
            ('p, span, div', 'content'),
        ]
        
        elements = []
        
        for selector, category in selectors:
            try:
                handles = await page.query_selector_all(selector)
                for handle in handles[:10]:  # Limit to 10 per category
                    element = await self._extract_element_data(handle, category)
                    if element:
                        elements.append(element)
            except Exception as e:
                logger.debug(f"Error extracting {category} elements: {e}")
                continue
                
        return elements
        
    async def _extract_element_data(self, element_handle, category: str) -> Optional[Element]:
        """Extract data from a single element."""
        try:
            data = await element_handle.evaluate('''(el) => {
                const rect = el.getBoundingClientRect();
                const computed = window.getComputedStyle(el);
                
                // Extract attributes
                const attrs = {};
                for (const attr of el.attributes || []) {
                    attrs[attr.name] = attr.value;
                }
                
                // Key styles
                const styles = {
                    display: computed.display,
                    position: computed.position,
                    width: computed.width,
                    height: computed.height,
                    padding: computed.padding,
                    margin: computed.margin,
                    fontSize: computed.fontSize,
                    fontWeight: computed.fontWeight,
                    color: computed.color,
                    backgroundColor: computed.backgroundColor,
                    borderRadius: computed.borderRadius,
                    boxShadow: computed.boxShadow
                };
                
                return {
                    tag: el.tagName.toLowerCase(),
                    text: (el.textContent || '').trim().substring(0, 100),
                    classes: el.className || '',
                    styles: styles,
                    attributes: attrs,
                    position: {
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height
                    },
                    visible: rect.width > 0 && rect.height > 0 && computed.display !== 'none'
                };
            }''')
            
            if not data['visible'] or not data['text']:
                return None
                
            return Element(
                tag=data['tag'],
                text=data['text'],
                classes=data['classes'],
                styles=data['styles'],
                attributes=data['attributes'],
                position=data['position'],
                category=category
            )
            
        except Exception as e:
            logger.debug(f"Failed to extract element data: {e}")
            return None