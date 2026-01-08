"""
HTTP/API Providers: Webhooks and custom APIs
"""

import requests
import logging
from provider_registry import register_provider, ProviderResult

logger = logging.getLogger(__name__)


@register_provider("webhook")
def webhook_provider(params, user_id, credentials, step_results):
    """Send a webhook/HTTP POST request"""
    url = params.get("url")
    payload = params.get("payload", {})
    headers = params.get("headers", {})
    timeout = params.get("timeout", 10)
    
    if not url:
        return ProviderResult(
            success=False,
            output=None,
            message="Webhook URL required",
            error="Missing URL"
        )
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=timeout
        )
        response.raise_for_status()
        
        return ProviderResult(
            success=True,
            output=response.json() if response.content else {"status": "ok"},
            message=f"Webhook sent to {url}",
            metadata={
                "status_code": response.status_code,
                "url": url
            }
        )
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Webhook failed: {str(e)}")
        return ProviderResult(
            success=False,
            output=None,
            message=f"Webhook to {url} failed",
            error=str(e)
        )


@register_provider("custom_api")
def custom_api_provider(params, user_id, credentials, step_results):
    """Call a custom API with authentication"""
    api_key = credentials.get("api_key")
    base_url = params.get("base_url")
    endpoint = params.get("endpoint", "")
    method = (params.get("method", "POST")).upper()
    headers = dict(params.get("headers", {}))
    body = params.get("body", {})
    
    if not base_url and not endpoint:
        return ProviderResult(
            success=False,
            output=None,
            message="Base URL or endpoint required",
            error="Missing URL"
        )
    
    full_url = f"{base_url}{endpoint}" if base_url else endpoint
    
    # Add auth header if API key provided
    if api_key:
        auth_header = params.get("auth_header", "Authorization")
        auth_prefix = params.get("auth_prefix", "Bearer")
        headers[auth_header] = f"{auth_prefix} {api_key}"
    
    try:
        if method == "GET":
            response = requests.get(full_url, headers=headers, params=body, timeout=10)
        elif method == "POST":
            response = requests.post(full_url, headers=headers, json=body, timeout=10)
        elif method == "PUT":
            response = requests.put(full_url, headers=headers, json=body, timeout=10)
        elif method == "PATCH":
            response = requests.patch(full_url, headers=headers, json=body, timeout=10)
        elif method == "DELETE":
            response = requests.delete(full_url, headers=headers, timeout=10)
        else:
            return ProviderResult(
                success=False,
                output=None,
                message=f"Unsupported HTTP method: {method}",
                error="Invalid method"
            )
        
        response.raise_for_status()
        
        return ProviderResult(
            success=True,
            output=response.json() if response.content else {"status": "ok"},
            message=f"Custom API call to {full_url} successful",
            metadata={
                "status_code": response.status_code,
                "method": method,
                "url": full_url
            }
        )
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Custom API call failed: {str(e)}")
        return ProviderResult(
            success=False,
            output=None,
            message="Custom API call failed",
            error=str(e)
        )


@register_provider("logic")
def logic_provider(params, user_id, credentials, step_results):
    """Data transformation/logic step"""
    template = params.get("template", "{}")
    
    try:
        # Simple template replacement with previous step outputs
        result = template
        for i, step_result in enumerate(step_results):
            placeholder = f"{{{{step_{i+1}.output}}}}"
            result = result.replace(placeholder, str(step_result))
        
        return ProviderResult(
            success=True,
            output=result,
            message="Logic step executed",
            metadata={"template": template}
        )
    
    except Exception as e:
        logger.error(f"Logic step failed: {str(e)}")
        return ProviderResult(
            success=False,
            output=None,
            message="Logic step failed",
            error=str(e)
        )
