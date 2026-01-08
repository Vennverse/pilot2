"""
Initialize provider registry by loading all provider modules
"""

# Import all provider modules to register them
import providers.ai
import providers.http

__all__ = ["ai", "http"]
