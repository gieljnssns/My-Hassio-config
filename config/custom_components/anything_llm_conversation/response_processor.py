"""Response processing utilities for cleaning and formatting LLM responses."""

import html
import re

# Compiled regex patterns for text cleaning (performance optimization)
_RE_THINK_TAGS = re.compile(r'<think>.*?</think>', flags=re.DOTALL | re.IGNORECASE)
_RE_MARKDOWN_LINKS = re.compile(r'\[([^\]]+)\]\([^\)]+\)')
_RE_WHITESPACE = re.compile(r'\s+')
_RE_BR_TAGS = re.compile(r'<br\s*/?>', flags=re.IGNORECASE)
_RE_HTML_TAGS = re.compile(r'<[^>]+>')
_RE_CELSIUS = re.compile(r'(\d+)C\b')
_RE_FAHRENHEIT = re.compile(r'(\d+)F\b')

# Follow-up detection phrases
FOLLOW_UP_PHRASES = frozenset([
    "which one",
    "would you like",
    "do you want",
    "would you prefer",
    "which do you",
    "what would you",
    "shall i",
    "should i",
    "choose from",
    "select from",
    "pick from",
])
# Compiled once — single regex scan is faster than N individual `in` checks.
# Phrases sorted longest-first so multi-word phrases win in alternation.
_RE_FOLLOW_UP = re.compile(
    r"(?:" + "|".join(re.escape(p) for p in sorted(FOLLOW_UP_PHRASES, key=len, reverse=True)) + r")",
    re.IGNORECASE,
)


def clean_response_for_tts(text: str) -> str:
    """Clean up LLM response for text-to-speech.
    
    Args:
        text: Raw response text from LLM
        
    Returns:
        Cleaned text optimized for TTS playback
    """
    # Decode HTML entities FIRST so that tag-based patterns below match both
    # literal tags and HTML-encoded variants (e.g. &lt;think&gt; → <think>).
    text = html.unescape(text)
    text = _RE_BR_TAGS.sub(' ', text)   # Convert <br> to space before tag stripping

    # Option 1: Remove <think> tags and their content
    text = _RE_THINK_TAGS.sub('', text)
    
    # Option 2: Remove only the <think> tags but keep the content inside
    # Uncomment below and comment out Option 1 above to use this instead
    # text = re.sub(r'</?think>', '', text, flags=re.IGNORECASE)

    # Strip remaining HTML tags (after think-tag removal so inner text is preserved)
    text = _RE_HTML_TAGS.sub('', text)
    
    # Option 3: Remove asterisks (markdown bold/italic)
    text = text.replace('*', '')
    
    # Option 4: Remove other common markdown formatting
    # Uncomment the ones you want to remove:
    # text = text.replace('_', '')  # Remove underscores (italic)
    # text = text.replace('~', '')  # Remove tildes (strikethrough)
    # text = text.replace('`', '')  # Remove backticks (code)
    # text = text.replace('#', '')  # Remove hash symbols (headers)
    text = _RE_MARKDOWN_LINKS.sub(r'\1', text)  # Convert [text](url) to just text
    # text = re.sub(r'```[^`]*```', '', text, flags=re.DOTALL)  # Remove code blocks
    # text = re.sub(r'https?://\S+', '', text)  # Remove URLs
    text = _RE_WHITESPACE.sub(' ', text)  # Normalize whitespace to single spaces
    
    # Option 5: HTML entity handling
    # html.unescape and <br> conversion are applied unconditionally at the top of
    # this function. To apply a second pass after markdown processing, uncomment:
    # text = html.unescape(text)
    # text = _RE_BR_TAGS.sub(' ', text)
    # text = _RE_HTML_TAGS.sub('', text)
    
    # Option 6: Emoji handling
    # Uncomment to handle emojis (requires emoji package: pip install emoji):
    # import emoji
    # text = emoji.replace_emoji(text, replace='')  # Remove all emojis
    # OR convert emojis to text descriptions:
    # text = emoji.demojize(text, delimiters=(" ", " "))  # 😀 becomes "grinning face"
    
    # Option 7: Special character cleanup
    # Uncomment to clean up characters that don't work well with TTS:
    text = text.replace('°', ' degrees ')  # Temperature symbols
    text = text.replace('%', ' percent ')  # Percent signs
    text = text.replace('$', ' dollars ')  # Currency
    text = text.replace('€', ' euros ')
    text = text.replace('£', ' pounds ')
    text = _RE_CELSIUS.sub(r'\1 degrees Celsius', text)  # 25C -> 25 degrees Celsius
    text = _RE_FAHRENHEIT.sub(r'\1 degrees Fahrenheit', text)  # 77F -> 77 degrees Fahrenheit
    
    # Clean up stray leading punctuation that may remain after tag removal
    text = text.strip()
    text = text.lstrip('.,;:!?-')  # Remove leading punctuation

    # Remove a single leading period/dot if present (after other leading punctuation is stripped)
    if text.startswith('.'):
        text = text[1:]
        text = text.lstrip()  # Remove any space after the dot

    return text.strip()


def should_continue_conversation(response_text: str) -> bool:
    """Detect if LLM response indicates a follow-up question.
    
    Args:
        response_text: The response text to analyze
        
    Returns:
        True if response appears to ask a follow-up question
    """
    if not response_text:
        return False
    
    response_lower = response_text.lower()
    
    # Check if ends with question mark
    if response_text.rstrip().endswith("?"):
        return True
    
    # Check for follow-up phrases using a single compiled regex scan
    return bool(_RE_FOLLOW_UP.search(response_lower))


class QueryResponse:
    """LLM query response value object."""

    def __init__(self, response: dict, text: str) -> None:
        """Initialize query response value object.
        
        Args:
            response: Raw response dict from API
            text: Cleaned text for TTS
        """
        self.response = response
        self.text = text
