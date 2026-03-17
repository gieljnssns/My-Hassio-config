"""Constants for the AnythingLLM Conversation integration."""

DOMAIN = "anything_llm_conversation"
DEFAULT_NAME = "AnythingLLM Conversation"
DEFAULT_CONVERSATION_NAME = "AnythingLLM Conversation"

CONF_BASE_URL = "base_url"
DEFAULT_CONF_BASE_URL = "http://localhost:3001/api"

# Failover configuration
CONF_FAILOVER_BASE_URL = "failover_base_url"
CONF_FAILOVER_API_KEY = "failover_api_key"
CONF_FAILOVER_WORKSPACE_SLUG = "failover_workspace_slug"


# Timeout configuration (in seconds)
CONF_HEALTH_CHECK_TIMEOUT = "health_check_timeout"
DEFAULT_HEALTH_CHECK_TIMEOUT = 3.0  # Quick health check for endpoint availability
CONF_CHAT_TIMEOUT = "chat_timeout"
DEFAULT_CHAT_TIMEOUT = 60.0  # Timeout for chat completion requests

EVENT_CONVERSATION_FINISHED = "anything_llm_conversation.conversation.finished"

CONF_PROMPT = "prompt"
DEFAULT_PROMPT = """I want you to act as smart home manager of Home Assistant.
I will provide information of smart home along with a question, you will truthfully make correction or answer using information provided in one sentence in everyday language.

Current Time: {{now()}}

Available Devices:
```csv
entity_id,name,state,aliases
{% for entity in exposed_entities -%}
{{ entity.entity_id }},{{ entity.name }},{{ entity.state }},{{entity.aliases | join('/')}}
{% endfor -%}
```

The current state of devices is provided in available devices.
"""
CONF_WORKSPACE_SLUG = "workspace_slug"
DEFAULT_WORKSPACE_SLUG = "default-workspace"
CONF_MAX_TOKENS = "max_tokens"
DEFAULT_MAX_TOKENS = 150
CONF_TEMPERATURE = "temperature"
DEFAULT_TEMPERATURE = 0.5
CONF_ATTACH_USERNAME = "attach_username"
DEFAULT_ATTACH_USERNAME = False
CONF_THREAD_SLUG = "thread_slug"
DEFAULT_THREAD_SLUG = ""
CONF_FAILOVER_THREAD_SLUG = "failover_thread_slug"
DEFAULT_FAILOVER_THREAD_SLUG = ""
DEFAULT_FAILOVER_WORKSPACE_SLUG = ""  # Default for per-agent override
CONF_ENABLE_AGENT_PREFIX = "enable_agent_prefix"
DEFAULT_ENABLE_AGENT_PREFIX = True
CONF_AGENT_KEYWORDS = "agent_keywords"
DEFAULT_AGENT_KEYWORDS = "search, lookup, find online, web search, google, browse, check online, look up, scrape"
CONF_ENABLE_HEALTH_CHECK = "enable_health_check"
DEFAULT_ENABLE_HEALTH_CHECK = True
