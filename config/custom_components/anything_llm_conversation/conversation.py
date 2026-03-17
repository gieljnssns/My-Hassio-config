"""AnythingLLM Conversation agent entity."""

from __future__ import annotations

import html
import logging
import re
from typing import Literal

from homeassistant.components import conversation
from homeassistant.components.conversation import (
    ChatLog,
    ConversationEntity,
    ConversationEntityFeature,
    ConversationInput,
    ConversationResult,
    async_get_chat_log,
)
from homeassistant.components.homeassistant.exposed_entities import async_should_expose
from homeassistant.config_entries import ConfigSubentry
from homeassistant.const import ATTR_NAME, MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, TemplateError
from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
    intent,
    template,
)
from homeassistant.helpers.chat_session import async_get_chat_session
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import AnythingLLMConfigEntry
from .const import (
    CONF_ATTACH_USERNAME,
    CONF_WORKSPACE_SLUG,
    CONF_FAILOVER_WORKSPACE_SLUG,
    CONF_MAX_TOKENS,
    CONF_PROMPT,
    CONF_TEMPERATURE,
    CONF_THREAD_SLUG,
    CONF_FAILOVER_THREAD_SLUG,
    CONF_ENABLE_AGENT_PREFIX,
    CONF_AGENT_KEYWORDS,
    CONF_ENABLE_HEALTH_CHECK,
    DEFAULT_ATTACH_USERNAME,
    DEFAULT_WORKSPACE_SLUG,
    DEFAULT_MAX_TOKENS,
    DEFAULT_PROMPT,
    DEFAULT_TEMPERATURE,
    DEFAULT_THREAD_SLUG,
    DEFAULT_FAILOVER_THREAD_SLUG,
    DEFAULT_FAILOVER_WORKSPACE_SLUG,
    DEFAULT_ENABLE_AGENT_PREFIX,
    DEFAULT_AGENT_KEYWORDS,
    DEFAULT_ENABLE_HEALTH_CHECK,
    DOMAIN,
    EVENT_CONVERSATION_FINISHED,
)
from .helpers import (
    detect_mode_switch,
    detect_suggested_modes,
    is_mode_query,
    get_mode_name,
    get_mode_prompt,
)
from .response_processor import (
    clean_response_for_tts,
    should_continue_conversation,
    QueryResponse,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: AnythingLLMConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the AnythingLLM Conversation entities."""
    for subentry in config_entry.subentries.values():
        if subentry.subentry_type != "conversation":
            continue

        async_add_entities(
            [AnythingLLMAgentEntity(hass, config_entry, subentry)],
            config_subentry_id=subentry.subentry_id,
        )


class AnythingLLMAgentEntity(
    ConversationEntity, conversation.AbstractConversationAgent
):
    """AnythingLLM conversation agent."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = ConversationEntityFeature.CONTROL

    def __init__(
        self,
        hass: HomeAssistant,
        entry: AnythingLLMConfigEntry,
        subentry: ConfigSubentry,
    ) -> None:
        """Initialize the agent."""
        self.hass = hass
        self.entry = entry
        self.subentry = subentry
        self.history: dict[str, list[dict]] = {}
        
        # Mode management - track mode per conversation
        self.conversation_modes: dict[str, str] = {}  # conversation_id -> mode_key
        
        # Workspace management - track workspace per conversation
        self.conversation_workspaces: dict[str, str] = {}  # conversation_id -> workspace_slug
        self.conversation_threads: dict[str, str | None] = {}  # conversation_id -> thread_slug (None = use default)

        self.options = subentry.data
        self._attr_unique_id = subentry.subentry_id
        
        # Caching for performance optimization
        self._exposed_entities_cache: list[dict[str, any]] | None = None
        self._last_states_count: int = 0
        self._system_prompt_cache: dict[str, str] = {}  # Cache by device_id
        self._last_prompt_template: str = self.options.get(CONF_PROMPT, DEFAULT_PROMPT)

        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, subentry.subentry_id)},
            name=subentry.title,
            manufacturer="AnythingLLM",
            model=self.options.get(CONF_WORKSPACE_SLUG, DEFAULT_WORKSPACE_SLUG),
            entry_type=dr.DeviceEntryType.SERVICE,
        )
        self.client = entry.runtime_data

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return a list of supported languages."""
        return MATCH_ALL

    async def async_process(self, user_input: ConversationInput) -> ConversationResult:
        """Process a sentence."""
        with (
            async_get_chat_session(self.hass, user_input.conversation_id) as session,
            async_get_chat_log(self.hass, session, user_input) as chat_log,
        ):
            return await self._async_handle_message(user_input, chat_log)

    async def _async_handle_message(
        self,
        user_input: ConversationInput,
        chat_log: ChatLog,
    ) -> ConversationResult:
        """Call the API."""
        conversation_id = chat_log.conversation_id
        
        # Get current mode for this conversation (default to "default")
        current_mode = self.conversation_modes.get(conversation_id, "default")
        
        # Check for workspace switch command
        workspace_switch_result = self._check_workspace_switch(user_input.text, conversation_id, user_input.language)
        if workspace_switch_result:
            return workspace_switch_result
        
        # Check for mode query first
        if is_mode_query(user_input.text):
            mode_name = get_mode_name(current_mode)
            _LOGGER.debug("Mode query detected, current mode: %s", mode_name)
            
            intent_response = intent.IntentResponse(language=user_input.language)
            intent_response.async_set_speech(f"I'm currently in {mode_name}.")
            
            return conversation.ConversationResult(
                response=intent_response, conversation_id=conversation_id
            )
        
        # Check for mode switch
        new_mode = detect_mode_switch(user_input.text)
        if new_mode:
            old_mode = current_mode
            self.conversation_modes[conversation_id] = new_mode
            mode_name = get_mode_name(new_mode)
            
            # Clear history and cache when switching modes
            if conversation_id in self.history:
                del self.history[conversation_id]
            self._system_prompt_cache.clear()
            
            _LOGGER.info("Mode switched from %s to %s for conversation %s", old_mode, new_mode, conversation_id)
            
            intent_response = intent.IntentResponse(language=user_input.language)
            intent_response.async_set_speech(f"Switching to {mode_name}.")
            
            return conversation.ConversationResult(
                response=intent_response, conversation_id=conversation_id
            )
        
        exposed_entities = self.get_exposed_entities()

        if conversation_id in self.history:
            messages = self.history[conversation_id]
        else:
            user_input.conversation_id = conversation_id
            try:
                system_message = self._generate_system_message(
                    exposed_entities, user_input, current_mode
                )
            except TemplateError as err:
                _LOGGER.error("Error rendering prompt: %s", err)
                intent_response = intent.IntentResponse(language=user_input.language)
                intent_response.async_set_error(
                    intent.IntentResponseErrorCode.UNKNOWN,
                    f"Sorry, I had a problem with my template: {err}",
                )
                return conversation.ConversationResult(
                    response=intent_response, conversation_id=conversation_id
                )
            messages = [system_message]
        
        # Add @agent prefix if enabled and keywords detected
        user_content = user_input.text
        if self._should_use_agent_prefix(user_content):
            user_content = f"@agent {user_content}"
            _LOGGER.debug("Added @agent prefix to message: %s", user_content)
        
        user_message = {"role": "user", "content": user_content}
        if self.options.get(CONF_ATTACH_USERNAME, DEFAULT_ATTACH_USERNAME):
            user = user_input.context.user_id
            if user is not None:
                user_message[ATTR_NAME] = user

        messages.append(user_message)

        try:
            # Determine which workspace and thread slug to use
            active_workspace = self.conversation_workspaces.get(conversation_id)
            opt_workspace_slug = self.options.get(CONF_WORKSPACE_SLUG, DEFAULT_WORKSPACE_SLUG)
            data_workspace_slug = self.entry.data.get(CONF_WORKSPACE_SLUG, DEFAULT_WORKSPACE_SLUG)
            default_workspace = opt_workspace_slug if opt_workspace_slug != DEFAULT_WORKSPACE_SLUG else data_workspace_slug

            # If using a custom workspace (not the default), use built-in thread (None)
            if active_workspace and active_workspace != default_workspace:
                active_thread = None
                _LOGGER.info(
                    "Using custom workspace '%s' for conversation %s (built-in thread)",
                    active_workspace,
                    conversation_id,
                )
            else:
                # Using the default workspace, use the configured thread slug (primary or failover)
                active_workspace = default_workspace
                active_thread = self.options.get(CONF_THREAD_SLUG, DEFAULT_THREAD_SLUG)
                _LOGGER.info(
                    "Using default workspace '%s' for conversation %s (thread: %s)",
                    active_workspace,
                    conversation_id,
                    active_thread or "None",
                )

            query_response = await self.query(user_input, messages, active_workspace, active_thread)
        except Exception as err:
            _LOGGER.error(err)
            intent_response = intent.IntentResponse(language=user_input.language)
            intent_response.async_set_error(
                intent.IntentResponseErrorCode.UNKNOWN,
                f"Sorry, I had a problem talking to the API: {err}",
            )
            return conversation.ConversationResult(
                response=intent_response, conversation_id=conversation_id
            )

        # Store assistant response in history
        assistant_message = {"role": "assistant", "content": query_response.text}
        messages.append(assistant_message)
        self.history[conversation_id] = messages

        self.hass.bus.async_fire(
            EVENT_CONVERSATION_FINISHED,
            {
                "response": query_response.response,
                "user_input": user_input,
                "messages": messages,
                "agent_id": self.subentry.subentry_id,
            },
        )

        intent_response = intent.IntentResponse(language=user_input.language)
        intent_response.async_set_speech(query_response.text)

        # Detect if LLM is asking a follow-up question to enable continued conversation
        should_continue = should_continue_conversation(query_response.text)

        return conversation.ConversationResult(
            response=intent_response,
            conversation_id=conversation_id,
            continue_conversation=should_continue,
        )

    def _check_workspace_switch(
        self, user_text: str, conversation_id: str, language: str
    ) -> conversation.ConversationResult | None:
        """Check if user is requesting a workspace switch.
        
        Supports commands like:
        - !workspace finance            → Switch to finance workspace
        - switch to finance workspace   → Switch to finance workspace
        - use technical workspace       → Switch to technical-support workspace
        - !workspace default            → Return to primary configured workspace
        - switch to default workspace   → Return to primary configured workspace
        - !workspace                    → Show current workspace
        - what workspace                → Show current workspace
        """
        text_lower = user_text.lower().strip()
        
        # Check for workspace query - support various natural language patterns
        workspace_query_patterns = [
            "!workspace",
            "what workspace",
            "current workspace", 
            "which workspace",
            "what workspace are you in",
            "what workspace am i in",
            "which workspace are you in",
            "which workspace am i in",
            "what workspace are you using",
            "what workspace am i using",
        ]
        
        # Also check if the text contains key phrases
        is_workspace_query = (
            text_lower in workspace_query_patterns or
            text_lower.startswith("what workspace") or
            text_lower.startswith("which workspace") or
            (text_lower.startswith("current") and "workspace" in text_lower)
        )
        
        if is_workspace_query and not any(
            text_lower.startswith(p) for p in ["switch to", "use ", "change workspace to", "switch workspace to"]
        ):
            current_workspace = self.conversation_workspaces.get(conversation_id)
            if current_workspace:
                response_text = f"Currently using workspace: {current_workspace}"
            else:
                # Get default workspace
                opt_workspace_slug = self.options.get(CONF_WORKSPACE_SLUG, DEFAULT_WORKSPACE_SLUG)
                data_workspace_slug = self.entry.data.get(CONF_WORKSPACE_SLUG, DEFAULT_WORKSPACE_SLUG)
                workspace_slug = opt_workspace_slug if opt_workspace_slug != DEFAULT_WORKSPACE_SLUG else data_workspace_slug
                response_text = f"Using default workspace: {workspace_slug}"
            
            intent_response = intent.IntentResponse(language=language)
            intent_response.async_set_speech(response_text)
            return conversation.ConversationResult(
                response=intent_response, conversation_id=conversation_id
            )
        
        # Extract workspace name from various command patterns
        new_workspace = None
        
        # Pattern 1: "!workspace <name>"
        if text_lower.startswith("!workspace "):
            new_workspace = user_text.split(" ", 1)[1].strip()
        
        # Pattern 2: "switch to <name> workspace"
        elif text_lower.startswith("switch to ") and " workspace" in text_lower:
            # Extract workspace name between "switch to" and "workspace"
            parts = text_lower.replace("switch to ", "").replace(" workspace", "").strip()
            new_workspace = parts
        
        # Pattern 3: "use <name> workspace"
        elif text_lower.startswith("use ") and " workspace" in text_lower:
            # Extract workspace name between "use" and "workspace"
            parts = text_lower.replace("use ", "").replace(" workspace", "").strip()
            new_workspace = parts
        
        # Pattern 4: "change workspace to <name>"
        elif text_lower.startswith("change workspace to "):
            new_workspace = text_lower.replace("change workspace to ", "").strip()
        
        # Pattern 5: "switch workspace to <name>"
        elif text_lower.startswith("switch workspace to "):
            new_workspace = text_lower.replace("switch workspace to ", "").strip()
        
        # If we found a workspace switch request
        if new_workspace:
            # Sanitize workspace name: strip surrounding whitespace/punctuation,
            # normalize spaces to hyphens, and lowercase. This prevents trailing
            # punctuation from voice input (e.g. "finance.") from becoming part
            # of the workspace slug used for API calls.
            new_workspace = new_workspace.strip()
            # Remove leading/trailing characters that aren't letters, digits, underscore or hyphen
            new_workspace = re.sub(r'^[^A-Za-z0-9_-]+|[^A-Za-z0-9_-]+$', '', new_workspace)
            # Replace inner spaces with hyphens and normalize to lowercase
            new_workspace = new_workspace.replace(' ', '-').lower()
            new_workspace_lower = new_workspace
            
            # Handle "default" keyword to return to primary workspace
            if new_workspace_lower == "default":
                # Clear the workspace override to return to configured default
                if conversation_id in self.conversation_workspaces:
                    del self.conversation_workspaces[conversation_id]
                
                # Clear the thread override to restore configured thread
                if conversation_id in self.conversation_threads:
                    del self.conversation_threads[conversation_id]
                
                # Clear history when switching workspaces (different context)
                if conversation_id in self.history:
                    del self.history[conversation_id]
                
                # Get the actual default workspace name
                opt_workspace_slug = self.options.get(CONF_WORKSPACE_SLUG, DEFAULT_WORKSPACE_SLUG)
                data_workspace_slug = self.entry.data.get(CONF_WORKSPACE_SLUG, DEFAULT_WORKSPACE_SLUG)
                default_workspace = opt_workspace_slug if opt_workspace_slug != DEFAULT_WORKSPACE_SLUG else data_workspace_slug
                
                _LOGGER.info(
                    "Workspace reset to default (%s) for conversation %s",
                    default_workspace,
                    conversation_id,
                )
                
                intent_response = intent.IntentResponse(language=language)
                intent_response.async_set_speech(
                    f"Switched to workspace {default_workspace}. How can I help you?"
                )
                return conversation.ConversationResult(
                    response=intent_response, conversation_id=conversation_id
                )
            
            # Validate workspace slug format (basic validation)
            if not new_workspace or len(new_workspace) < 1:
                intent_response = intent.IntentResponse(language=language)
                intent_response.async_set_speech("Please provide a valid workspace slug.")
                return conversation.ConversationResult(
                    response=intent_response, conversation_id=conversation_id
                )
            
            # Store the new workspace for this conversation
            old_workspace = self.conversation_workspaces.get(conversation_id, "default")
            self.conversation_workspaces[conversation_id] = new_workspace
            
            # Clear thread override - use the new workspace's default thread
            # (configured thread slug is only valid for the default workspace)
            self.conversation_threads[conversation_id] = None
            
            # Clear history when switching workspaces (different context)
            if conversation_id in self.history:
                del self.history[conversation_id]
            
            _LOGGER.info(
                "Workspace switched from %s to %s for conversation %s (stored in conversation_workspaces dict)",
                old_workspace,
                new_workspace,
                conversation_id,
            )
            _LOGGER.debug("conversation_workspaces state: %s", self.conversation_workspaces)
            
            intent_response = intent.IntentResponse(language=language)
            intent_response.async_set_speech(
                f"Switched to workspace {new_workspace}. How can I help you?"
            )
            return conversation.ConversationResult(
                response=intent_response, conversation_id=conversation_id
            )
        
        return None

    def _should_use_agent_prefix(self, user_text: str) -> bool:
        """Determine if @agent prefix should be added based on keywords."""
        if not self.options.get(CONF_ENABLE_AGENT_PREFIX, DEFAULT_ENABLE_AGENT_PREFIX):
            return False
        
        keywords_str = self.options.get(CONF_AGENT_KEYWORDS, DEFAULT_AGENT_KEYWORDS)
        keywords = [kw.strip().lower() for kw in keywords_str.split(",")]
        user_text_lower = user_text.lower()
        
        return any(keyword in user_text_lower for keyword in keywords if keyword)

    def _generate_system_message(
        self, exposed_entities, user_input: conversation.ConversationInput, mode_key: str = "default"
    ):
        # Get user's custom prompt (if any)
        user_prompt = self.options.get(CONF_PROMPT, DEFAULT_PROMPT)
        
        # If user has customized the prompt, use it as the base persona
        # Otherwise use the default BASE_PERSONA from const.py
        if user_prompt != DEFAULT_PROMPT:
            # User customized - use their prompt as base, but still apply mode behaviors
            raw_prompt = get_mode_prompt(mode_key, custom_base_persona=user_prompt)
        else:
            # Use default mode system
            raw_prompt = get_mode_prompt(mode_key)
        
        # Detect if query patterns suggest a different mode might be helpful
        suggested_modes = detect_suggested_modes(user_input.text, mode_key)
        if suggested_modes:
            # Add a hint to the prompt (AI still decides whether to suggest)
            mode_names = ", ".join([get_mode_name(m) for m in suggested_modes[:2]])  # Top 2 matches
            mode_hint = f"\n\n[SYSTEM HINT: User query patterns suggest {mode_names} might be relevant for this question. Consider offering to switch if appropriate.]"
            raw_prompt = raw_prompt + mode_hint
            _LOGGER.debug("Pattern match detected - suggesting modes: %s", mode_names)
        
        prompt = self._async_generate_prompt(raw_prompt, exposed_entities, user_input, mode_key)
        return {"role": "system", "content": prompt}

    def _async_generate_prompt(
        self,
        raw_prompt: str,
        exposed_entities,
        user_input: conversation.ConversationInput,
        mode_key: str = "default",
    ) -> str:
        """Generate a prompt for the user."""
        # Check if prompt template changed - invalidate cache if so
        if raw_prompt != self._last_prompt_template:
            self._system_prompt_cache.clear()
            self._last_prompt_template = raw_prompt
            _LOGGER.debug("System prompt cache cleared due to template change")
        
        # Use device_id and mode as cache key
        cache_key = f"{user_input.device_id or 'default'}_{len(exposed_entities)}_{mode_key}"
        
        # Return cached prompt if available
        if cache_key in self._system_prompt_cache:
            return self._system_prompt_cache[cache_key]
        
        # Generate and cache the prompt
        prompt = template.Template(raw_prompt, self.hass).async_render(
            {
                "ha_name": self.hass.config.location_name,
                "exposed_entities": exposed_entities,
                "current_device_id": user_input.device_id,
            },
            parse_result=False,
        )
        
        self._system_prompt_cache[cache_key] = prompt
        _LOGGER.debug("Cached system prompt for key: %s", cache_key)
        return prompt

    def get_exposed_entities(self) -> list[dict[str, any]]:
        # Check if we can use cached entities
        current_states_count = len(self.hass.states.async_all())
        
        # Invalidate cache if number of states changed (entities added/removed)
        if current_states_count != self._last_states_count:
            self._exposed_entities_cache = None
            self._system_prompt_cache.clear()  # Clear prompt cache when entities change
            self._last_states_count = current_states_count
            _LOGGER.debug("Entity cache invalidated due to state count change")
        
        # Return cached entities if available
        if self._exposed_entities_cache is not None:
            return self._exposed_entities_cache
        
        # Build fresh entity list - get registry once
        entity_registry = er.async_get(self.hass)
        states = [
            state
            for state in self.hass.states.async_all()
            if async_should_expose(self.hass, conversation.DOMAIN, state.entity_id)
        ]
        exposed_entities = []
        for state in states:
            entity_id = state.entity_id
            entity = entity_registry.async_get(entity_id)

            exposed_entities.append(
                {
                    "entity_id": entity_id,
                    "name": state.name,
                    "state": state.state,
                    "aliases": entity.aliases if entity and entity.aliases else [],
                }
            )
        
        # Cache the result
        self._exposed_entities_cache = exposed_entities
        _LOGGER.debug("Cached %d exposed entities", len(exposed_entities))
        return exposed_entities

    async def query(
        self,
        user_input: conversation.ConversationInput,
        messages: list[dict],
        workspace_override: str | None = None,
        thread_override: str | None | bool = False,
    ) -> QueryResponse:
        """Process a sentence."""
        # Use workspace override if provided (from conversation-specific workspace)
        if workspace_override:
            workspace_slug = workspace_override
            _LOGGER.info("Using workspace override: %s", workspace_override)
        else:
            # Prefer subentry options values; if default placeholders are present, fall back to main entry data
            opt_workspace_slug = self.options.get(CONF_WORKSPACE_SLUG, DEFAULT_WORKSPACE_SLUG)
            data_workspace_slug = self.entry.data.get(CONF_WORKSPACE_SLUG, DEFAULT_WORKSPACE_SLUG)
            workspace_slug = opt_workspace_slug if opt_workspace_slug != DEFAULT_WORKSPACE_SLUG else data_workspace_slug
            _LOGGER.debug("Using default workspace (no override): %s", workspace_slug)
        
        max_tokens = self.options.get(CONF_MAX_TOKENS, DEFAULT_MAX_TOKENS)
        temperature = self.options.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE)
        
        # Handle thread override: False = use configured, None = use workspace default, string = use that thread
        if thread_override is False:
            # No override specified - use configured thread
            thread_slug = self.options.get(CONF_THREAD_SLUG, DEFAULT_THREAD_SLUG)
        elif thread_override is None:
            # Explicit None - don't use any thread (workspace default)
            thread_slug = None
        else:
            # String value - use that specific thread
            thread_slug = thread_override
        
        failover_thread_slug = self.options.get(CONF_FAILOVER_THREAD_SLUG, DEFAULT_FAILOVER_THREAD_SLUG)
        opt_failover_workspace_slug = self.options.get(CONF_FAILOVER_WORKSPACE_SLUG, DEFAULT_FAILOVER_WORKSPACE_SLUG)
        data_failover_workspace_slug = self.entry.data.get(CONF_FAILOVER_WORKSPACE_SLUG, DEFAULT_FAILOVER_WORKSPACE_SLUG)
        failover_workspace_slug = opt_failover_workspace_slug or data_failover_workspace_slug

        _LOGGER.info("Sending request to AnythingLLM workspace '%s' with %d messages", workspace_slug, len(messages))

        # Call AnythingLLM API
        try:
            response = await self.client.chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                workspace_slug=workspace_slug if workspace_slug else None,
                thread_slug=thread_slug if thread_slug else None,
                failover_thread_slug=failover_thread_slug if failover_thread_slug else None,
                failover_workspace_slug=failover_workspace_slug if failover_workspace_slug else None,
            )
        except Exception as err:
            _LOGGER.error("Error from AnythingLLM: %s", err)
            raise

        _LOGGER.debug("Received response from AnythingLLM (type: %s)", response.get("type", "unknown"))

        # Extract the text response from AnythingLLM
        # AnythingLLM returns: {"textResponse": "...", "type": "chat", ...}
        text_response = response.get("textResponse", "")
        
        if not text_response:
            raise HomeAssistantError("Empty response from AnythingLLM")

        # Remove <think> tags before sending to TTS
        text_response = clean_response_for_tts(text_response)

        return QueryResponse(response=response, text=text_response)
