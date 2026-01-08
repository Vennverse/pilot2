"""
AI Provider: OpenAI
Handles GPT and related models
"""

from provider_registry import register_provider, ProviderResult
from openai import OpenAI
import os
import logging

logger = logging.getLogger(__name__)


@register_provider("openai")
def openai_provider(params, user_id, credentials, step_results):
    """Execute OpenAI API call"""
    api_key = credentials.get("api_key") or os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY")
    base_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
    
    if not api_key:
        return ProviderResult(
            success=False,
            output=None,
            message="OpenAI API key not configured",
            error="Missing API key"
        )
    
    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        
        prompt = params.get("prompt", "Hello")
        model = params.get("model", "gpt-4")
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens", 1000)
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        output = response.choices[0].message.content
        
        return ProviderResult(
            success=True,
            output=output,
            message=f"OpenAI response: {output[:100]}...",
            metadata={
                "model": model,
                "tokens_used": response.usage.total_tokens,
                "finish_reason": response.choices[0].finish_reason
            }
        )
    
    except Exception as e:
        logger.error(f"OpenAI error: {str(e)}")
        return ProviderResult(
            success=False,
            output=None,
            message="OpenAI API call failed",
            error=str(e)
        )


@register_provider("groq")
def groq_provider(params, user_id, credentials, step_results):
    """Execute Groq API call"""
    api_key = credentials.get("api_key") or os.environ.get("GROQ_API_KEY")
    
    if not api_key:
        return ProviderResult(
            success=False,
            output=None,
            message="Groq API key not configured",
            error="Missing API key"
        )
    
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        
        prompt = params.get("prompt", "Hello")
        model = params.get("model", "llama3-70b-8192")
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        
        output = response.choices[0].message.content
        
        return ProviderResult(
            success=True,
            output=output,
            message=f"Groq response: {output[:100]}...",
            metadata={
                "model": model,
                "tokens_used": response.usage.total_tokens
            }
        )
    
    except Exception as e:
        logger.error(f"Groq error: {str(e)}")
        return ProviderResult(
            success=False,
            output=None,
            message="Groq API call failed",
            error=str(e)
        )
