# EduMind Migration Guide: v1.0 → v1.1

This guide explains how to update existing code to use the new advanced services in EduMind v1.1.

## Overview of Changes

### What Changed?
- **Configuration**: No more .env files, using secure keyring
- **Architecture**: New modular services for caching, analytics, and performance
- **Security**: API keys stored securely in system keyring
- **Performance**: Response caching and async processing

### What Stayed the Same?
- PyQt6 UI architecture
- Core AI providers (OpenAI, Gemini, Offline)
- Database schema
- Study tools (summaries, flashcards, quizzes)

## Migration Steps

### Step 1: Update Configuration

#### Old Way (v1.0)
```python
# config.py - relied on .env file
import os
from dotenv import load_dotenv

load_dotenv()
provider = os.getenv('EDUMIND_PROVIDER', 'offline')
api_key = os.getenv('OPENAI_API_KEY', '')
```

#### New Way (v1.1)
```python
# config.py - no .env needed, uses keyring
from config import settings

provider = settings.provider
api_key = settings.openai_api_key  # Loaded from keyring

# Directories are auto-created
settings.ensure_directories_exist()
```

### Step 2: Application Initialization

#### Old Way (v1.0)
```python
# app.py - minimal initialization
from ui.main import run_app
run_app()
```

#### New Way (v1.1)
```python
# app.py - with proper service initialization
from app_init import initialize_app, cleanup_app
import atexit

if not initialize_app():
    print("Failed to initialize app")
    exit(1)

# Register cleanup on exit
atexit.register(cleanup_app)

from ui.main import run_app
run_app()
```

### Step 3: Use Analytics

#### Old Way (v1.0)
```python
# Manual tracking in multiple places
session_start = datetime.now()
# ... study activities ...
session_end = datetime.now()
duration = (session_end - session_start).total_seconds()
```

#### New Way (v1.1)
```python
from core.service_utils import SessionHelper

# Start session
session_id = SessionHelper.start_new_session("Physics", "openai")

# ... study activities (automatically tracked) ...

# End session - get summary automatically
summary = SessionHelper.end_current_session()
print(f"Session score: {summary['average_score']}")
```

### Step 4: Add Response Caching

#### Old Way (v1.0)
```python
# No caching - every query hits the API
response = ai_provider.summarize(text)
```

#### New Way (v1.1)
```python
from core.service_utils import cache_result

@cache_result
def get_summary(text):
    return ai_provider.summarize(text)

# First call - hits API
summary1 = get_summary(text)

# Second call with same text - returns from cache
summary2 = get_summary(text)  # Instant!
```

### Step 5: Track Performance

#### Old Way (v1.0)
```python
# No performance monitoring
response = expensive_operation()
```

#### New Way (v1.1)
```python
from core.service_utils import track_performance

@track_performance("summarization")
def summarize_content(text):
    return ai_provider.summarize(text)

response = summarize_content(text)

# View performance stats
from core.service_utils import PerformanceHelper
stats = PerformanceHelper.get_operation_stats("summarization")
print(f"Average time: {stats['avg']:.2f}ms")
```

### Step 6: Async Processing

#### Old Way (v1.0)
```python
# Blocking UI during AI operations
summary = ai_provider.summarize(large_text)  # Freezes UI
```

#### New Way (v1.1)
```python
from core.service_utils import PerformanceHelper

# Submit async task
future = PerformanceHelper.submit_async_task(
    ai_provider.summarize,
    large_text
)

# UI remains responsive
# Get result when ready
summary = future.result()
```

### Step 7: Analytics Integration

#### Old Way (v1.0)
```python
# No learning analytics
quiz_score = 85
# No tracking
```

#### New Way (v1.1)
```python
from core.service_utils import AnalyticsHelper

# Track quiz
analytics = get_analytics()
analytics.record_quiz_taken(85)

# Get recommendations
recommendations = AnalyticsHelper.get_recommendations()
for rec in recommendations:
    print(rec)  # e.g., "Great performance! Try harder topics"
```

### Step 8: Session Persistence

#### Old Way (v1.0)
```python
# No session restoration
app starts fresh every time
```

#### New Way (v1.1)
```python
from core.service_utils import SessionHelper

# Get available sessions
sessions = SessionHelper.get_available_sessions()
if sessions:
    # Load most recent
    manager = get_session_manager()
    manager.load_session(sessions[0]['session_id'])
    
    # State automatically restored
    state = manager.current_session
    print(f"Resuming: {state.current_subject}")
```

## Compatibility

### Backwards Compatibility
- Old UI code continues to work
- Database schema unchanged
- Core functions have same signatures

### Breaking Changes
- `.env` file no longer used (configure in Settings instead)
- `python-dotenv` dependency removed
- `config.py` imports must be updated

## Common Migration Patterns

### Pattern 1: Adding Analytics to Existing Function

```python
# Before
def process_document(file_path):
    text = extract_text(file_path)
    summary = ai_provider.summarize(text)
    return summary

# After
from core.service_utils import track_analytics

@track_analytics("content_processing")
def process_document(file_path):
    text = extract_text(file_path)
    analytics.record_content_processed(len(text))
    
    summary = ai_provider.summarize(text)
    analytics.record_summary_created()
    
    return summary
```

### Pattern 2: Adding Caching to AI Calls

```python
# Before
def get_quiz_questions(text):
    return ai_provider.quiz(text)

# After
from core.service_utils import cache_result

@cache_result
def get_quiz_questions(text):
    return ai_provider.quiz(text)

# Same calls now cached automatically
```

### Pattern 3: Using Async for Long Operations

```python
# Before - blocking
quiz_results = generate_large_quiz(content)

# After - non-blocking
from core.service_utils import PerformanceHelper

future = PerformanceHelper.submit_async_task(
    generate_large_quiz,
    content
)

# Do other work while processing
# Then get results
quiz_results = future.result()
```

## Configuration Migration

### API Keys

#### Old Way (.env file)
```
# .env (no longer supported)
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=ai-...
```

#### New Way (Secure Keyring)
1. Launch EduMind
2. Go to Settings → API Configuration
3. Select provider (OpenAI or Gemini)
4. Enter API key (stored securely)
5. Key automatically saved to system keyring

### Settings

All settings previously in `.env` are now:
1. **Hardcoded safe defaults** in `config.py`
2. **User overrides** via Settings dialog
3. **Persisted** in database (not .env file)

### Environment Variables

If you still need to use environment variables for CI/CD:

```python
# Optional: Load from environment if provided
import os
from config import settings

if os.getenv('OPENAI_API_KEY'):
    # Will be read from keyring instead
    # This is just for reference
    pass
```

## Testing Migration

### Verify Configuration
```bash
python -c "from config import settings; print(f'Provider: {settings.provider}')"
```

### Verify Services
```bash
python app_init.py
# Should show all services initialized successfully
```

### Verify Analytics
```bash
from core.services.advanced_analytics import get_analytics
analytics = get_analytics()
print(f"Tracked sessions: {len(analytics.sessions)}")
```

## Troubleshooting Migration

### Issue: "ModuleNotFoundError: No module named 'dotenv'"
**Solution**: This is expected. The dependency was removed. Remove any `from dotenv import` lines.

### Issue: "API key not found"
**Solution**: 
1. Keys are now in system keyring, not .env
2. Configure in Settings → API Configuration
3. Or reinstall and set during setup

### Issue: "Old sessions lost"
**Solution**: 
1. Sessions are now in `data/sessions/` (different format)
2. Old `sessions.json` won't be auto-migrated
3. Restart app to create new sessions

### Issue: Cache not working
**Solution**:
```python
from core.service_utils import CacheHelper

# Check status
status = CacheHelper.get_cache_status()
print(status)

# Optimize if large
result = CacheHelper.optimize_cache()
print(f"Removed {result['entries_removed']} old entries")
```

## Performance Checklist

- [ ] Call `initialize_app()` before starting UI
- [ ] Use `@cache_result` on expensive functions
- [ ] Use `submit_async_task()` for long operations
- [ ] Track performance with `@track_performance()`
- [ ] Track analytics with `@track_analytics()`
- [ ] Monitor cache stats regularly
- [ ] Call `cleanup_app()` on exit

## Support

For questions about migration:
1. Check [PROJECT_GUIDE.md](PROJECT_GUIDE.md)
2. Review [CONTRIBUTING.md](CONTRIBUTING.md)
3. Check application logs in `data/logs/`

---

**Happy migrating! 🚀**
