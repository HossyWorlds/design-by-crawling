"""Utility functions for dcrawl."""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from .exceptions import ConfigError

# Default configuration values
DEFAULT_CONFIG = {
    "headless": True,
    "timeout": 30000,
    "component_name": "GeneratedComponent",
    "output_dir": "./generated",
    "max_elements_per_category": 10
}


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )


def save_file(content: str, filepath: str) -> str:
    """Save content to file and return the path."""
    path = Path(filepath)
    
    # Create directory if needed
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename if file exists
    if path.exists():
        stem = path.stem
        suffix = path.suffix
        counter = 1
        while path.exists():
            path = path.parent / f"{stem}_{counter}{suffix}"
            counter += 1
    
    # Save file
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    return str(path)


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from file."""
    if not config_path:
        return DEFAULT_CONFIG.copy()
        
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
        
        # Merge with defaults
        config = DEFAULT_CONFIG.copy()
        config.update(user_config)
        return config
        
    except FileNotFoundError:
        raise ConfigError(f"Configuration file not found: {config_path}")
    except json.JSONDecodeError as e:
        raise ConfigError(f"Invalid JSON in configuration file: {e}")
    except Exception as e:
        raise ConfigError(f"Error loading configuration: {e}")


def save_default_config(output_path: str = "dcrawl.config.json") -> str:
    """Save default configuration to file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(DEFAULT_CONFIG, f, indent=2)
        
    return output_path


def validate_url(url: str) -> bool:
    """Validate URL format."""
    if not url:
        return False
    return url.startswith(('http://', 'https://'))


def get_output_filename(component_name: str, output_dir: str) -> str:
    """Get output filename for component."""
    filename = f"{component_name}.jsx"
    return os.path.join(output_dir, filename)