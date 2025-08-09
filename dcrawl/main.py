"""Main CLI interface for dcrawl."""

import argparse
import asyncio
import sys
import logging
from typing import Optional

from .crawler import WebCrawler
from .generator import ReactGenerator
from .utils import (
    setup_logging, save_file, load_config, save_default_config,
    validate_url, get_output_filename
)
from .exceptions import DCrawlError, ConfigError

logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        prog='dcrawl',
        description='Convert websites to React components with Tailwind CSS',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python dcrawl.py https://example.com
  python dcrawl.py https://example.com --name MyComponent
  python dcrawl.py https://example.com --output ./components/
  python dcrawl.py init  # Generate config file
        """
    )
    
    # Special case for init command
    parser.add_argument('url_or_init', nargs='?', help='Website URL to crawl, or "init" to generate config')
    parser.add_argument('--name', '-n', help='Component name (default: GeneratedComponent)')
    parser.add_argument('--output', '-o', help='Output directory (default: ./generated)')
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--headless', action='store_true', default=True, help='Run browser in headless mode')
    parser.add_argument('--no-headless', dest='headless', action='store_false', help='Show browser window')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    return parser


async def crawl_website(url: str, config: dict, component_name: str, output_dir: str, verbose: bool = False) -> str:
    """Crawl website and generate component."""
    setup_logging(verbose)
    
    logger.info(f"🔍 Starting crawl of {url}")
    
    # Crawl website
    async with WebCrawler(headless=config['headless'], timeout=config['timeout']) as crawler:
        crawl_result = await crawler.crawl(url)
        
    if not crawl_result.elements:
        raise DCrawlError("No elements extracted from the website")
        
    logger.info(f"✅ Extracted {len(crawl_result.elements)} elements")
    
    # Group by category for summary
    categories = {}
    for element in crawl_result.elements:
        categories[element.category] = categories.get(element.category, 0) + 1
    
    logger.info("📊 Element breakdown:")
    for category, count in categories.items():
        logger.info(f"   - {category}: {count}")
    
    # Generate React component
    logger.info(f"🚀 Generating React component: {component_name}")
    generator = ReactGenerator(component_name)
    component_code = generator.generate(crawl_result)
    
    # Save file
    output_file = get_output_filename(component_name, output_dir)
    saved_path = save_file(component_code, output_file)
    
    logger.info(f"✨ Component generated successfully!")
    logger.info(f"💾 Saved to: {saved_path}")
    
    return saved_path


def handle_init_command(output_path: str) -> None:
    """Handle init command."""
    config_path = save_default_config(output_path)
    print(f"✅ Configuration file generated: {config_path}")
    print(f"📝 Edit the file and use with: python dcrawl.py <url> --config {config_path}")


def handle_crawl_command(args, config: dict) -> None:
    """Handle crawl command."""
    url = args.url
    
    if not validate_url(url):
        print(f"❌ Error: Invalid URL: {url}")
        print("📝 URL must start with http:// or https://")
        sys.exit(1)
    
    # Override config with CLI args
    component_name = args.name or config.get('component_name', 'GeneratedComponent')
    output_dir = args.output or config.get('output_dir', './generated')
    
    try:
        # Run async crawl
        saved_path = asyncio.run(crawl_website(
            url=url,
            config=config,
            component_name=component_name,
            output_dir=output_dir,
            verbose=args.verbose
        ))
        
        # Print success message
        print(f"\n{'='*50}")
        print(f"✅ Successfully generated {component_name}")
        print(f"📄 File: {saved_path}")
        print(f"🔗 Source: {url}")
        print(f"{'='*50}\n")
        
    except DCrawlError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def main(argv: Optional[list] = None):
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)
    
    # Handle init command
    if args.url_or_init == 'init':
        output_path = args.output or 'dcrawl.config.json'
        handle_init_command(output_path)
        return
    
    # Handle URL
    url = args.url_or_init
    if not url:
        parser.print_help()
        sys.exit(1)
    
    # Load configuration
    try:
        config = load_config(args.config)
    except ConfigError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    
    # Set headless based on args
    config['headless'] = args.headless
    
    # Create a fake args object for handle_crawl_command
    args.url = url
    handle_crawl_command(args, config)


if __name__ == '__main__':
    main()