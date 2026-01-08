"""
Provider registry system for managing integrations
Each provider is a self-contained module that can be tested independently
"""

from typing import Callable, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ProviderResult:
    """Standard provider response format"""
    success: bool
    output: Any
    message: str
    metadata: Dict[str, Any] = None
    error: Optional[str] = None
    
    def to_tuple(self) -> Tuple[bool, Any, str]:
        """Convert to legacy tuple format for backwards compatibility"""
        return (self.success, self.output, self.message)


class ProviderRegistry:
    """Central registry for all providers"""
    
    def __init__(self):
        self._providers: Dict[str, Callable] = {}
    
    def register(self, name: str, provider_fn: Callable) -> Callable:
        """
        Register a provider function
        
        Usage:
            @registry.register("openai")
            def openai_provider(params, user_id, credentials):
                ...
        """
        if name in self._providers:
            logger.warning(f"Overwriting provider: {name}")
        self._providers[name] = provider_fn
        logger.info(f"Registered provider: {name}")
        return provider_fn
    
    def get(self, name: str) -> Optional[Callable]:
        """Get a provider by name"""
        return self._providers.get(name)
    
    def list_providers(self) -> Dict[str, Callable]:
        """List all registered providers"""
        return dict(self._providers)
    
    def execute(self, name: str, params: Dict[str, Any], user_id: str, 
                credentials: Dict[str, str], step_results: list) -> ProviderResult:
        """
        Execute a provider
        
        Args:
            name: Provider name
            params: Step parameters (may contain placeholders from previous steps)
            user_id: User executing the step
            credentials: User's credentials for this provider
            step_results: Results from previous steps (for references)
        
        Returns:
            ProviderResult with standard format
        """
        provider = self.get(name)
        if not provider:
            return ProviderResult(
                success=False,
                output=None,
                message=f"Provider '{name}' not registered",
                error=f"Unknown provider: {name}"
            )
        
        try:
            result = provider(
                params=params,
                user_id=user_id,
                credentials=credentials,
                step_results=step_results
            )
            
            # Ensure we always get a ProviderResult
            if not isinstance(result, ProviderResult):
                result = ProviderResult(
                    success=True,
                    output=result,
                    message="Provider executed successfully"
                )
            
            return result
        
        except Exception as e:
            logger.error(f"Provider {name} failed: {str(e)}", exc_info=True)
            return ProviderResult(
                success=False,
                output=None,
                message=f"Provider {name} failed",
                error=str(e)
            )


# Global registry instance
registry = ProviderRegistry()


def register_provider(name: str):
    """Decorator to register a provider"""
    def decorator(fn: Callable) -> Callable:
        return registry.register(name, fn)
    return decorator
