"""Helper functions for AnythingLLM Conversation component."""

import asyncio
import logging
from typing import Callable

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
    _MODE_PATTERN_REGEXES,
    MODE_SUGGESTION_THRESHOLD,
)
from .modes import (
    PROMPT_MODES,
    BASE_PERSONA,
    MODE_BEHAVIORS,
    get_workspace_prompt_config,
    get_workspace_display_name,
)

_LOGGER = logging.getLogger(__name__)


# Legacy mode keys now map to workspace slugs.
MODE_TO_WORKSPACE = {
    "analysis": "analysis",
    "research": "research",
    "security": "security",
    "code_review": "investigation",
    "troubleshooting": "investigation",
    "guest": "default",
    "default": "default",
}


def detect_mode_switch(user_input: str) -> str | None:
    """Detect if user input contains mode switch keywords.
    
    Returns a workspace slug (e.g., 'analysis', 'research') if detected, None otherwise.
    """
    # Sanitize input: trim whitespace and trailing periods
    input_lower = user_input.lower().strip().rstrip(".")
    
    # Check each mode's keywords
    for mode_key, keywords in MODE_KEYWORDS.items():
        if any(keyword in input_lower for keyword in keywords):
            return MODE_TO_WORKSPACE.get(mode_key, mode_key)
    
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
    # Issue 18: use pre-compiled regex per mode — single scan instead of N `in` checks.
    for mode_key, pattern_re in _MODE_PATTERN_REGEXES.items():
        suggested_workspace = MODE_TO_WORKSPACE.get(mode_key, mode_key)

        # Skip current workspace - don't suggest switching to same target
        if suggested_workspace == current_mode:
            continue

        match_count = len(pattern_re.findall(input_lower))

        if match_count >= MODE_SUGGESTION_THRESHOLD:
            mode_scores[suggested_workspace] = mode_scores.get(suggested_workspace, 0) + match_count
    
    # Return modes sorted by match count (highest first)
    return sorted(mode_scores.keys(), key=lambda k: mode_scores[k], reverse=True)


def get_mode_name(mode_key: str) -> str:
    """Get the display name for a mode/workspace key."""
    if mode_key in ("default", "", None):
        return "Default Workspace"
    return get_workspace_display_name(mode_key)


def get_workspace_prompt(workspace_slug: str | None) -> str | None:
    """Get a workspace-specific system prompt by slug."""
    workspace_config = get_workspace_prompt_config(workspace_slug)
    if workspace_config:
        return workspace_config["system_prompt"]
    return None


def should_apply_tts_cleaning_for_workspace(workspace_slug: str | None) -> bool:
    """Return True if TTS cleaning should be applied for this workspace."""
    workspace_config = get_workspace_prompt_config(workspace_slug)
    if not workspace_config:
        return True
    return workspace_config.get("apply_tts_cleaning", True)


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

        # Cached health state — updated by background task, never blocks a request.
        # None means "not yet checked"; True/False = last known result.
        self._primary_healthy: bool | None = None
        self._health_check_interval: float = 30.0  # seconds between background checks
        self._health_task: asyncio.Task | None = None
        self._health_stop: asyncio.Event = asyncio.Event()
        # Callbacks notified whenever _primary_healthy changes (e.g. binary sensor).
        self._health_listeners: list[Callable[[bool | None], None]] = []

    def add_health_listener(self, callback: Callable[[bool | None], None]) -> None:
        """Register a callback invoked whenever _primary_healthy changes."""
        self._health_listeners.append(callback)

    def remove_health_listener(self, callback: Callable[[bool | None], None]) -> None:
        """Deregister a previously registered health callback."""
        try:
            self._health_listeners.remove(callback)
        except ValueError:
            pass

    def start_health_monitor(self) -> None:
        """Start the background health-check loop. Call once after client creation."""
        if not self.enable_health_check:
            return
        if self._health_task and not self._health_task.done():
            return
        self._health_stop.clear()
        self._health_task = asyncio.ensure_future(self._health_monitor_loop())
        _LOGGER.debug("Health monitor started for %s", self.base_url)

    def stop_health_monitor(self) -> None:
        """Stop the background health-check loop."""
        self._health_stop.set()
        if self._health_task and not self._health_task.done():
            self._health_task.cancel()
        _LOGGER.debug("Health monitor stopped for %s", self.base_url)

    async def _health_monitor_loop(self) -> None:
        """Periodically check endpoint health and cache the result."""
        while not self._health_stop.is_set():
            await self._refresh_health()
            try:
                await asyncio.wait_for(
                    asyncio.shield(asyncio.ensure_future(self._health_stop.wait())),
                    timeout=self._health_check_interval,
                )
            except asyncio.TimeoutError:
                pass  # Normal — interval elapsed, run next check
            except asyncio.CancelledError:
                break

    async def _refresh_health(self) -> None:
        """Run a single health check and update cached state."""
        primary_healthy = await self._check_endpoint_health(self.base_url, self.api_key)
        previous = self._primary_healthy
        if primary_healthy:
            if self.using_failover:
                _LOGGER.info("Primary endpoint is back online, switching from failover")
                self.using_failover = False
            self._primary_healthy = True
        else:
            self._primary_healthy = False
            if self.failover_base_url and self.failover_api_key:
                if not self.using_failover:
                    _LOGGER.warning("Primary endpoint unavailable, switching to failover")
                    self.using_failover = True
            else:
                _LOGGER.warning("Primary endpoint unavailable and no failover configured")

        # Notify listeners when health status changes so UI updates immediately.
        if self._primary_healthy != previous:
            for cb in list(self._health_listeners):
                cb(self._primary_healthy)

    async def _check_endpoint_health(self, base_url: str, api_key: str) -> bool:
        """Probe an AnythingLLM endpoint. Returns True if reachable."""
        try:
            health_url = f"{base_url}/v1/system"
            response = await self.http_client.get(
                health_url,
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=self.health_check_timeout,
            )
            return response.status_code in (200, 401, 403)
        except Exception as err:
            _LOGGER.debug("Health check failed for %s: %s", base_url, err)
            return False

    def get_active_endpoint(self) -> tuple[str, str, str]:
        """Return the active endpoint from cached health state (non-blocking)."""
        if not self.enable_health_check:
            return self.base_url, self.api_key, self.workspace_slug

        # If we haven't completed the first check yet, optimistically use primary.
        if self._primary_healthy is None:
            _LOGGER.debug("Health not yet checked, optimistically using primary endpoint")
            return self.base_url, self.api_key, self.workspace_slug

        if self._primary_healthy or not (self.failover_base_url and self.failover_api_key):
            if not self._primary_healthy:
                _LOGGER.error("Primary endpoint unavailable and no failover configured")
                raise HomeAssistantError("AnythingLLM endpoint is unavailable")
            return self.base_url, self.api_key, self.workspace_slug

        # Primary unhealthy and failover is configured
        return self.failover_base_url, self.failover_api_key, self.failover_workspace_slug or self.workspace_slug

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
        base_url, api_key, active_workspace_slug = self.get_active_endpoint()
        
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

        # Guard: never send an empty or system-only message to the API.
        if not messages or messages[-1].get("role") != "user":
            raise HomeAssistantError("No valid user message to send to AnythingLLM")

        payload = {
            "message": messages[-1]["content"],
            "mode": "chat",
        }
        # The 'prompt' override is only supported on workspace-level endpoints.
        # Thread endpoints manage their own context server-side; sending 'prompt'
        # to a thread endpoint causes AnythingLLM to return a 500 error.
        if system_prompt and not active_thread_slug:
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
                if not response.is_success:
                    _LOGGER.error(
                        "AnythingLLM HTTP %s for %s — response body: %s",
                        response.status_code,
                        chat_url,
                        response.text[:1000],
                    )
                    # Try to surface AnythingLLM's own error message instead of
                    # a generic HTTP status error (e.g. "Ollama unreachable")
                    try:
                        body = response.json()
                        server_error = body.get("error")
                        if server_error:
                            raise HomeAssistantError(f"AnythingLLM error: {server_error}")
                    except HomeAssistantError:
                        raise
                    except Exception:
                        pass
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
    health_check_timeout: float = DEFAULT_HEALTH_CHECK_TIMEOUT,
    chat_timeout: float = DEFAULT_CHAT_TIMEOUT,
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
        health_check_timeout=health_check_timeout,
        chat_timeout=chat_timeout,
    )
    
    # Skip health check during setup - it will be done at conversation time
    # This allows installation even if the server is temporarily down
    _LOGGER.info("AnythingLLM client created for %s (health check will occur at conversation time)", base_url)
    
    return client


