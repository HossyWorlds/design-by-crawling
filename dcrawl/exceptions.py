"""Simple exceptions for dcrawl."""


class DCrawlError(Exception):
    """Base exception for dcrawl."""
    pass


class CrawlingError(DCrawlError):
    """Error during crawling process."""
    pass


class GenerationError(DCrawlError):
    """Error during component generation."""
    pass


class ConfigError(DCrawlError):
    """Configuration error."""
    pass