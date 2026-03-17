"""Helper functions for AnythingLLM Conversation component."""

import asyncio
import logging

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.httpx_client import get_async_client

from .const import (
    CONF_HEALTH_CHECK_TIMEOUT,
    CONF_CHAT_TIMEOUT,
    DEFAULT_HEALTH_CHECK_TIMEOUT,
    DEFAULT_CHAT_TIMEOUT,
)
from .mode_patterns import (
    MODE_KEYWORDS,
    MODE_QUERY_KEYWORDS,
    MODE_SUGGESTION_PATTERNS,
    MODE_SUGGESTION_THRESHOLD,
)
from .modes import (
    PROMPT_MODES,
    BASE_PERSONA,
    MODE_BEHAVIORS,
)

_LOGGER = logging.getLogger(__name__)


def detect_mode_switch(user_input: str) -> str | None:
    """Detect if user input contains mode switch keywords.
    
    Returns the mode key (e.g., 'analysis', 'research') if detected, None otherwise.
    """
    # Sanitize input: trim whitespace and trailing periods
    input_lower = user_input.lower().strip().rstrip(".")
    
    # Check each mode's keywords
    for mode_key, keywords in MODE_KEYWORDS.items():
        if any(keyword in input_lower for keyword in keywords):
            return mode_key
    
    return None


def is_mode_query(user_input: str) -> bool:
    """Check if user is asking about the current mode."""
    input_lower = user_input.lower().strip()
    return any(keyword in input_lower for keyword in MODE_QUERY_KEYWORDS)


def detect_suggested_modes(user_input: str, current_mode: str) -> list[str]:
    """Detect which modes might be relevant based on query patterns.
    
    Returns a list of mode keys that match the user's query patterns,
    excluding the current mode.
    
    Args:
        user_input: The user's query text
        current_mode: The currently active mode key
    
    Returns:
        List of mode keys that match patterns, ordered by match count
    """
    input_lower = user_input.lower().strip()
    mode_scores = {}
    
    # Count pattern matches for each mode
    for mode_key, patterns in MODE_SUGGESTION_PATTERNS.items():
        # Skip current mode - don't suggest switching to same mode
        if mode_key == current_mode:
            continue
            
        match_count = sum(1 for pattern in patterns if pattern in input_lower)
        
        if match_count >= MODE_SUGGESTION_THRESHOLD:
            mode_scores[mode_key] = match_count
    
    # Return modes sorted by match count (highest first)
    return sorted(mode_scores.keys(), key=lambda k: mode_scores[k], reverse=True)


def get_mode_name(mode_key: str) -> str:
    """Get the display name for a mode key."""
    return PROMPT_MODES.get(mode_key, {}).get("name", "Unknown Mode")


def get_mode_prompt(mode_key: str, custom_base_persona: str | None = None) -> str:
    """Get the system prompt for a mode key.
    
    Args:
        mode_key: The mode to get the prompt for
        custom_base_persona: Optional custom base persona to use instead of default
    
    Returns:
        Complete system prompt with base persona + mode behavior
    """
    # If custom base provided, rebuild the prompt with it
    if custom_base_persona:
        mode_data = MODE_BEHAVIORS.get(mode_key)
        if not mode_data:
            return custom_base_persona
        
        # Build mode names for switching instructions
        other_modes = [f'"{m["name"].lower()}"' for k, m in MODE_BEHAVIORS.items() if k != mode_key]
        if len(other_modes) > 1:
            mode_names_text = ", ".join(other_modes[:-1]) + f", or {other_modes[-1]}"
        else:
            mode_names_text = other_modes[0] if other_modes else ""
        
        # Use simple string replacement instead of .format() to avoid conflicts with Jinja2 syntax
        result = custom_base_persona.replace("{mode_specific_behavior}", mode_data["behavior"])
        result = result.replace("{mode_names}", mode_names_text)
        result = result.replace("{mode_display_name}", mode_data["name"])
        return result
    
    # Use pre-built prompt from PROMPT_MODES
    return PROMPT_MODES.get(mode_key, PROMPT_MODES["default"]).get("system_prompt", "")


class AnythingLLMClient:
    """AnythingLLM API client."""

    def __init__(
        self,
        hass: HomeAssistant,
        api_key: str,
        base_url: str,
        workspace_slug: str,
        failover_api_key: str | None = None,
        failover_base_url: str | None = None,
        failover_workspace_slug: str | None = None,
        failover_thread_slug: str | None = None,
        enable_health_check: bool = True,
        health_check_timeout: float = DEFAULT_HEALTH_CHECK_TIMEOUT,
        chat_timeout: float = DEFAULT_CHAT_TIMEOUT,
    ):
        """Initialize AnythingLLM client."""
        self.hass = hass
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.workspace_slug = workspace_slug
        self.failover_api_key = failover_api_key
        self.failover_base_url = failover_base_url.rstrip("/") if failover_base_url else None
        self.failover_workspace_slug = failover_workspace_slug
        self.failover_thread_slug = failover_thread_slug
        self.enable_health_check = enable_health_check
        self.health_check_timeout = health_check_timeout
        self.chat_timeout = chat_timeout
        self.http_client = get_async_client(hass)
        self.using_failover = False

    async def check_endpoint_health(self, base_url: str, api_key: str) -> bool:
        """Check if AnythingLLM endpoint is active."""
        try:
            # Try to ping the API - AnythingLLM may not have a dedicated health endpoint
            # So we'll try a simple workspace list or system endpoint
            health_url = f"{base_url}/v1/system"
            response = await self.http_client.get(
                health_url,
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=self.health_check_timeout,
            )
            return response.status_code in (200, 401, 403)  # 401/403 means endpoint is up but auth issue
        except Exception as err:
            _LOGGER.debug("Health check failed for %s: %s", base_url, err)
            return False

    async def get_active_endpoint(self) -> tuple[str, str, str]:
        """Get active endpoint, failing over if necessary."""
        # If health checks are disabled, always use primary endpoint
        if not self.enable_health_check:
            return self.base_url, self.api_key, self.workspace_slug
        
        # Check primary endpoint
        primary_healthy = await self.check_endpoint_health(self.base_url, self.api_key)
        
        if primary_healthy:
            if self.using_failover:
                _LOGGER.info("Primary endpoint is back online, switching from failover")
                self.using_failover = False
            return self.base_url, self.api_key, self.workspace_slug

        # Primary is down, try failover if configured
        if self.failover_base_url and self.failover_api_key:
            _LOGGER.warning("Primary endpoint unavailable, switching to failover")
            if not self.using_failover:
                _LOGGER.info("Switched to failover endpoint")
                self.using_failover = True
            return self.failover_base_url, self.failover_api_key, self.failover_workspace_slug or self.workspace_slug
        else:
            _LOGGER.error("Primary endpoint unavailable and no failover configured")
            raise HomeAssistantError("AnythingLLM endpoint is unavailable")

    async def chat_completion(
        self,
        messages: list[dict],
        temperature: float = 0.5,
        max_tokens: int = 150,
        workspace_slug: str | None = None,
        thread_slug: str | None = None,
        failover_thread_slug: str | None = None,
        failover_workspace_slug: str | None = None,
    ) -> dict:
        """Send chat completion request to AnythingLLM."""
        base_url, api_key, active_workspace_slug = await self.get_active_endpoint()
        
        # Update failover_thread_slug if provided (allows dynamic updates without client reload)
        if failover_thread_slug is not None:
            self.failover_thread_slug = failover_thread_slug
        
        # Update failover_workspace_slug if provided (allows per-agent override)
        if failover_workspace_slug is not None:
            active_failover_workspace = failover_workspace_slug
        else:
            active_failover_workspace = self.failover_workspace_slug
        
        # Determine which workspace and thread slug to use based on active endpoint
        if self.using_failover:
            # If failover_workspace_slug is not set, use a generic default and do not set a thread
            if not active_failover_workspace:
                final_workspace_slug = DEFAULT_FAILOVER_WORKSPACE_SLUG or "default-workspace"
                active_thread_slug = None
                _LOGGER.info("Using failover endpoint - generic default workspace: %s, no thread", final_workspace_slug)
            else:
                final_workspace_slug = active_failover_workspace
                active_thread_slug = self.failover_thread_slug
                _LOGGER.info("Using failover endpoint - workspace: %s, thread: %s", final_workspace_slug, active_thread_slug or "None")
        else:
            # Use the provided workspace override if set, otherwise default to active workspace
            final_workspace_slug = workspace_slug or active_workspace_slug or self.workspace_slug
            active_thread_slug = thread_slug
            _LOGGER.info(
                "Using primary endpoint - workspace: %s (override: %s, active: %s, default: %s), thread: %s",
                final_workspace_slug,
                workspace_slug or "None",
                active_workspace_slug or "None",
                self.workspace_slug,
                active_thread_slug or "None"
            )
        
        # Construct AnythingLLM API endpoint - use thread slug in URL if provided
        if active_thread_slug:
            chat_url = f"{base_url}/v1/workspace/{final_workspace_slug}/thread/{active_thread_slug}/chat"
        else:
            chat_url = f"{base_url}/v1/workspace/{final_workspace_slug}/chat"
        
        _LOGGER.info("API URL: %s", chat_url)
        
        # Extract the system prompt (first message with role 'system')
        system_prompt = None
        for msg in messages:
            if msg.get("role") == "system":
                system_prompt = msg.get("content")
                break
        payload = {
            "message": messages[-1]["content"] if messages else "",
            "mode": "chat",
        }
        if system_prompt:
            payload["prompt"] = system_prompt

        # DEBUG: Uncomment the next line to log the outgoing payload (including prompt)
        _LOGGER.debug("Outgoing AnythingLLM payload: %r", payload)
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        # Try up to 2 times on the selected endpoint
        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = await self.http_client.post(
                    chat_url,
                    json=payload,
                    headers=headers,
                    timeout=self.chat_timeout,
                )
                _LOGGER.debug("AnythingLLM response status: %s, body: %s", response.status_code, response.text[:500])
                response.raise_for_status()
                return response.json()
            except Exception as err:
                _LOGGER.error("Error calling AnythingLLM API at %s (attempt %d/%d): %s", base_url, attempt + 1, max_retries, err)
                
                # If this was the last retry, try switching endpoints
                if attempt == max_retries - 1:
                    # If we were using failover and it failed, try primary one more time
                    if self.using_failover and self.failover_base_url:
                        _LOGGER.warning("Failover endpoint failed after retries, trying primary endpoint")
                        try:
                            # Construct primary URL with thread slug if provided
                            if thread_slug:
                                primary_url = f"{self.base_url}/v1/workspace/{self.workspace_slug}/thread/{thread_slug}/chat"
                            else:
                                primary_url = f"{self.base_url}/v1/workspace/{self.workspace_slug}/chat"
                            primary_headers = {
                                "Authorization": f"Bearer {self.api_key}",
                                "Content-Type": "application/json",
                            }
                            response = await self.http_client.post(
                                primary_url,
                                json=payload,
                                headers=primary_headers,
                                timeout=DEFAULT_CHAT_TIMEOUT,
                            )
                            _LOGGER.debug("Primary retry response status: %s, body: %s", response.status_code, response.text[:500])
                            response.raise_for_status()
                            _LOGGER.info("Primary endpoint succeeded, switching back")
                            self.using_failover = False
                            return response.json()
                        except Exception as primary_err:
                            _LOGGER.error("Primary endpoint also failed: %s", primary_err)
                    
                    raise HomeAssistantError(f"AnythingLLM API error: {err}") from err
                
                # Wait a bit before retrying (exponential backoff)
                await asyncio.sleep(0.5 * (attempt + 1))



async def get_anythingllm_client(
    hass: HomeAssistant,
    api_key: str,
    base_url: str,
    workspace_slug: str,
    failover_api_key: str | None = None,
    failover_base_url: str | None = None,
    failover_workspace_slug: str | None = None,
    failover_thread_slug: str | None = None,
    enable_health_check: bool = True,
) -> AnythingLLMClient:
    """Create and validate AnythingLLM client."""
    client = AnythingLLMClient(
        hass,
        api_key,
        base_url,
        workspace_slug,
        failover_api_key,
        failover_base_url,
        failover_workspace_slug,
        failover_thread_slug,
        enable_health_check,
        health_check_timeout=float(
            hass.data.get(CONF_HEALTH_CHECK_TIMEOUT, DEFAULT_HEALTH_CHECK_TIMEOUT)
        ) if hasattr(hass, "data") and CONF_HEALTH_CHECK_TIMEOUT in getattr(hass, "data", {}) else DEFAULT_HEALTH_CHECK_TIMEOUT,
        chat_timeout=float(
            hass.data.get(CONF_CHAT_TIMEOUT, DEFAULT_CHAT_TIMEOUT)
        ) if hasattr(hass, "data") and CONF_CHAT_TIMEOUT in getattr(hass, "data", {}) else DEFAULT_CHAT_TIMEOUT,
    )
    
    # Skip health check during setup - it will be done at conversation time
    # This allows installation even if the server is temporarily down
    _LOGGER.info("AnythingLLM client created for %s (health check will occur at conversation time)", base_url)
    
    return client


