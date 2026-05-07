# Documentation Index

Welcome! This guide will help you navigate the codebase.

## Getting Started

1. **New to the project?** Start with [README.md](README.md)
2. **Want to understand the structure?** Read [ARCHITECTURE.md](ARCHITECTURE.md)
3. **Curious about what changed?** See [BEFORE_AFTER.md](BEFORE_AFTER.md)

---

## Documentation Files

### [README.md](README.md)
**Purpose**: Project overview and quick start guide

**Contains**:
- Project description
- Feature list
- Installation instructions
- Running the bot locally
- Setup guide
- Testing procedure

**Read this when**: You're getting started or explaining the project to someone

---

### [ARCHITECTURE.md](ARCHITECTURE.md)
**Purpose**: Deep dive into code organization and patterns

**Contains**:
- Directory structure with explanation
- Core module components (exceptions, constants, validators, clients)
- Service layer breakdown
- Error handling strategy
- Logging approach
- Guidelines for adding features

**Read this when**: 
- Adding a new feature
- Understanding how a module works
- Debugging issues
- Writing code that follows patterns

---

### [BEFORE_AFTER.md](BEFORE_AFTER.md)
**Purpose**: Visual comparison of refactored code

**Contains**:
- Projects changes and updates

**Read this when**:
- Appreciating changes

---

## Project Structure

```
yt-bot/
├── README.md                  # Start here
├── ARCHITECTURE.md            # Deep dive into structure
├── BEFORE_AFTER.md            # Visual comparison
├── INDEX.md                   # This file
│
├── app/
│   ├── __init__.py            # Package marker
│   ├── config.py              # Environment configuration
│   ├── main.py                # FastAPI application
│   │
│   ├── core/                  # Core abstractions
│   │   ├── __init__.py
│   │   ├── exceptions.py      # Custom exception hierarchy
│   │   ├── constants.py       # All magic strings and numbers
│   │   ├── validators.py      # Input validation logic
│   │   └── clients.py         # External API client setup
│   │
│   ├── services/              # Business logic
│   │   ├── __init__.py
│   │   ├── orchestrator.py    # Pipeline coordinator
│   │   ├── transcript.py      # YouTube transcript extraction
│   │   ├── classify.py        # Content type classification
│   │   ├── summarize.py       # LLM summarization
│   │   ├── translate.py       # Khaya translation
│   │   ├── tts.py             # Audio generation
│   │   └── telegram.py        # Telegram API client
│   │
│   └── utils/                 # Utilities
│       ├── __init__.py
│       ├── logger.py          # Logging setup
│       ├── youtube.py         # YouTube URL parsing
│       ├── prompt.py          # Prompt template loading
│       └── storage.py         # GCS utilities (future)
│
├── prompts/                   # Prompt templates
│   ├── classification.txt
│   ├── summarization.txt
│   └── summarization_rewrite.txt
│
├── logs/                      # Application logs
│
├── pyproject.toml             # Project configuration
├── requirements.txt           # Dependencies
└── .env                       # Environment variables (create this)
```

---

## Development Workflow

### When you start a new task:

1. **Read** the relevant ARCHITECTURE.md section
2. **Find** where code should go (use quick reference above)
3. **Follow** the established patterns (error handling, logging, etc.)
4. **Add constants** to `app/core/constants.py` (no magic strings!)
5. **Add exceptions** if new error types (to `app/core/exceptions.py`)
6. **Update docstrings** for your functions
7. **Log appropriately** at each step
8. **Test** by running the bot with a sample video

---

## Troubleshooting

### Services failing?
1. Check `logs/bot.log` for detailed error messages
2. Look at the specific exception type (raised by service)
3. Trace it back in ARCHITECTURE.md
4. Check if configuration is missing (.env file)

### Import errors?
1. Ensure you're importing from `app.core` for constants/exceptions
2. Check that module __init__.py files exist
3. Verify the import path matches the file location

### Unclear patterns?
1. Look at similar code in the same service
2. Check BEFORE_AFTER.md for examples
3. Read ARCHITECTURE.md for the pattern
4. Look at how other services handle similar cases

---

## Quick Links

- [README.md](README.md) - Project overview
- [ARCHITECTURE.md](ARCHITECTURE.md) - Code structure
- [BEFORE_AFTER.md](BEFORE_AFTER.md) - Improvements shown
- [CLEANUP_SUMMARY.md](CLEANUP_SUMMARY.md) - Complete changelog
