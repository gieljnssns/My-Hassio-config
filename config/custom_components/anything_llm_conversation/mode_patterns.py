"""Pattern matching data for mode suggestions and detection."""

# Mode detection keywords - explicit mode switching commands
MODE_KEYWORDS = {
    "analysis": ["analysis mode", "analyzer mode", "analyze mode"],
    "research": ["research mode", "researcher mode"],
    "code_review": ["code review mode", "review mode", "code mode"],
    "troubleshooting": ["troubleshooting mode", "debug mode", "fix mode", "troubleshoot mode"],
    "security": ["security mode", "secure mode", "alarm mode", "security system"],
    "guest": ["guest mode", "visitor mode", "simple mode"],
    "default": ["default mode", "normal mode", "standard mode"]
}

# Mode query keywords
MODE_QUERY_KEYWORDS = ["what mode", "which mode", "current mode"]

# Mode suggestion patterns - triggers for automatic mode suggestions
# These are context clues that indicate a query would benefit from a specific mode
MODE_SUGGESTION_PATTERNS = {
    "analysis": [
        # Energy and consumption
        "energy usage", "energy consumption", "power usage", "power consumption",
        "electricity bill", "electric bill", "energy bill", "energy cost",
        "kwh", "kilowatt", "watt hour", "how much energy", "how much power",
        "expensive to run", "spending on", "cost me", "cost to",
        "save energy", "saving energy", "wasting energy", "waste energy",
        # General usage and statistics
        "usage pattern", "behavior pattern", "consumption pattern", "usage trend",
        "show me stats", "statistics", "show statistics", "statistical",
        "how often", "how frequently", "how many times", "frequency of",
        "average", "typically", "usually", "normally", "most often",
        # Historical and time-based analysis
        "historical data", "history of", "over time", "past data", "previous",
        "this month", "last month", "this week", "last week", "past week", "past month",
        "today's", "yesterday's", "daily", "weekly", "monthly",
        "per day", "per week", "per month", "per hour",
        # Trends and comparisons
        "trend", "trending", "pattern", "compared to", "versus", "vs last",
        "more than usual", "less than usual", "compared to last", "difference from",
        "increasing", "decreasing", "changed over", "changes in",
        # Device and sensor analysis
        "device uptime", "device availability", "sensor readings", "sensor data",
        "temperature history", "humidity history", "climate data", "climate pattern",
        "motion detected", "door opened", "triggered", "activations",
        # Monitoring and tracking
        "monitor", "track", "tracking", "total", "sum of", "count",
        "how much did", "how much has", "how many times did", "how many times has",
        # Automation analysis
        "automation ran", "automation triggered", "automation executed",
        "how often does automation", "when does automation", "automation pattern",
        # Performance and efficiency
        "most used", "least used", "most active", "least active",
        "efficient", "efficiency", "performance", "reliability",
        "uptime", "downtime", "availability", "response time",
    ],
    
    "research": [
        # Exploratory questions (clear question patterns)
        "how does", "how do", "what are", "explain", "tell me about",
        "learn about", "understand",
        # Decision-making questions  
        "should i get", "should i buy", "should i use", "should i choose",
        "would it be better", "can i use", "is it possible", "will it work",
        # Comparison and recommendations
        "compare", "comparison", "which is better", "which one", "which should",
        "best way to", "recommend", "recommendation", "suggest", "suggestion",
        "which integration", "which device", "which protocol", "which sensor",
        "which smart", "which lock", "which hub", "which bulb",
        "difference between", "pros and cons", "advantages", "disadvantages",
        "alternative", "alternatives", "option", "options", "versus", "vs",
        # Setup and compatibility
        "how to set up", "how to install", "how to configure", "setup",
        "compatible with", "compatibility", "work with", "works with",
        "integrate with", "integration with", "add support", "connect to",
        # Research context
        "choose between", "pick between", "decide between", "better choice",
    ],
    
    "code_review": [
        # Review requests (specific to code/config review)
        "review my", "review this", "look at my", "look at this",
        "validate my", "validate this", "verify my", "verify this",
        "check my automation", "check my script", "check my config", "check this yaml",
        # Correctness questions
        "is this right", "is this correct", "is this good", "this right",
        "this correct", "look good", "look ok", "looks good", "any issues",
        "any problems with", "anything wrong", "correct way",
        # Code artifacts (combined with review context)
        "my automation", "my script", "my yaml", "my configuration", "my config",
        "this automation", "this script", "this yaml", "this configuration",
        "my template", "this template", "my trigger", "my condition", "my action",
        # Quality and improvement (code-specific)
        "optimize my", "optimize this", "improve my", "improve this",
        "better way to write", "best practice for", "refactor",
        "wrong with my", "mistake in my", "error in my code", "syntax error",
        "clean up", "make this better", "safer way", "secure way", "vulnerability",
    ],
    
    "troubleshooting": [
        # Problem indicators (clear failure states)
        "not working", "isn't working", "doesn't work", "won't work",
        "not responding", "isn't responding", "doesn't respond", "won't respond",
        "stopped working", "stopped responding", "stopped functioning",
        "can't control", "can't get", "unable to", "won't turn",
        # Failure states
        "broken", "dead", "failed", "failing", "failure",
        "offline", "unavailable", "unknown state", "unresponsive", "disconnected",
        "no response", "not reachable", "connection lost", "lost connection",
        # Error conditions
        "error with", "error message", "getting error", "throwing error",
        "timeout", "timed out", "slow to respond", "delayed", "laggy",
        # Diagnostic requests
        "fix", "repair", "debug", "diagnose", "troubleshoot",
        "what's wrong with", "why isn't", "why doesn't", "why won't",
        "help with problem", "having trouble", "having issue", "problem with",
        # Symptoms
        "keeps turning off", "keeps disconnecting", "randomly stops", "intermittent",
        "stuck", "frozen", "hanging", "not updating", "wrong status",
    ],
    "security": [
        "arm system", "disarm system", "security status", "alarm triggered",
        "intruder", "breach", "motion detected", "window open", "door open",
        "security camera", "surveillance", "lock doors", "unlock doors",
        "enable alarm", "disable alarm", "security alert", "panic button",
        "is my home secure", "is the house locked", "security event",
    ],
}

# Minimum confidence threshold for mode suggestions
# How many pattern matches needed before suggesting a mode
MODE_SUGGESTION_THRESHOLD = 1  # Suggest if at least 1 pattern matches
