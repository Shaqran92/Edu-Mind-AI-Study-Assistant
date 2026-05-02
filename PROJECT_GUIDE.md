# EduMind AI Study Assistant - Project Guide

## Overview

**EduMind** is an advanced AI-powered study assistant built with PyQt6. It helps students learn effectively through:
- Intelligent content summarization
- Interactive flashcards and quizzes
- Concept mapping and visualization
- Study analytics and progress tracking
- Offline-first architecture with optional AI integration

## Latest Updates (v1.1.0)

### 🔒 Security Improvements
- **Removed environment variable exposure**: No more .env file needed
- **Secure keyring integration**: API keys stored in system keyring
- **Hardcoded safe defaults**: App works offline without configuration
- **Removed python-dotenv dependency**: Simpler, more secure setup

### 🚀 Advanced Features Added
- **Response Caching**: Intelligent LRU caching reduces API calls
- **Advanced Analytics**: Track learning patterns and progress
- **Performance Monitoring**: Identify bottlenecks and optimize
- **Session Management**: Persistent state with crash recovery
- **Batch Processing**: Efficient async task handling

### ✨ Code Quality Improvements
- Consolidated configuration system
- Enhanced error handling
- Better documentation and type hints
- Removed security vulnerabilities

## Project Structure

```
EduMind/
├── app.py                 # Entry point
├── config.py             # ✨ NEW: Secure configuration system
├── setup.py              # ✨ UPDATED: Secure setup wizard
│
├── core/                 # Core functionality
│   ├── ai/              # AI providers (OpenAI, Gemini, Offline)
│   ├── services/        # ✨ NEW Advanced services
│   │   ├── response_cache.py      # Response caching
│   │   ├── advanced_analytics.py  # Learning analytics
│   │   ├── performance.py         # Performance optimization
│   │   └── session_manager.py     # Session persistence
│   ├── auth/            # Authentication
│   ├── export/          # Export functionality
│   ├── analytics/       # Analytics engine
│   └── [other modules]
│
├── ui/                  # UI components (PyQt6)
│   ├── main.py         # Main window
│   ├── widgets/        # UI widgets
│   ├── dialogs/        # Dialog windows
│   └── themes/         # Theme management
│
├── data/               # Data directory
│   ├── edumind.db     # SQLite database
│   ├/.cache/          # Response cache
│   ├/analytics/       # Analytics data
│   └/sessions/        # Session states
│
├── utils/             # Utilities
└── tests/             # Test suite
```

## Installation

### 1. Clone and Setup

```bash
cd EduMind
python setup.py
pip install -r requirements.txt
```

### 2. Configure AI Provider (Optional)

Launch the app and go to **Settings → API Configuration**:
- **Offline**: Works without any API keys (default)
- **OpenAI**: Add your OpenAI API key (stored securely)
- **Gemini**: Add your Gemini API key (stored securely)

API keys are stored in your system's secure keyring, never in plain text.

## Usage

### Starting the Application

```bash
python -m ui.main
```

### Key Features

#### 📚 Study Tools
- **Upload & Extract**: Import PDFs, documents, and web content
- **Summarize**: Generate intelligent summaries with customizable modes
- **Flashcards**: Auto-generate spaced repetition flashcards
- **Quiz**: Create interactive quizzes with instant feedback
- **Concept Maps**: Visualize relationships between concepts

#### 📊 Analytics
- Track study sessions and performance
- Monitor quiz scores and improvements
- Analyze learning patterns
- Get personalized recommendations

#### ⚙️ Settings
- **API Configuration**: Manage AI provider keys securely
- **Theme**: Choose light, dark, or system theme
- **Language**: Select output language
- **Performance**: Adjust cache and processing settings

## Advanced Features

### 1. Response Caching
Intelligent caching system that:
- Reduces API costs by caching similar queries
- Uses LRU (Least Recently Used) eviction
- Supports TTL (Time-To-Live) for fresh responses
- Limits cache size to 100MB by default

```python
from core.services.response_cache import get_cache

cache = get_cache()
# Automatic caching for AI responses
```

### 2. Advanced Analytics
Comprehensive learning analytics:
- Session tracking with detailed metrics
- Learning pattern analysis
- Performance insights
- Personalized recommendations

```python
from core.services.advanced_analytics import get_analytics

analytics = get_analytics()
analytics.start_session("Physics")
# ... study activities ...
analytics.record_quiz_taken(score=92.5)
session_summary = analytics.end_session()
```

### 3. Performance Optimization
- Real-time performance monitoring
- Operation timing and profiling
- Bottleneck identification
- Async task pool for non-blocking operations

```python
from core.services.performance import get_performance_monitor, get_task_pool

monitor = get_performance_monitor()
pool = get_task_pool()

# Monitor specific operations
pool.submit_task(heavy_computation)
```

### 4. Session Management
Robust session persistence:
- Auto-save state
- Crash recovery
- Multi-session support
- Session export/import

```python
from core.services.session_manager import get_session_manager

manager = get_session_manager()
session = manager.create_session()
# ... user interactions ...
manager.save_session()
```

## Configuration

### Safe Defaults
The application comes with safe defaults and no required configuration:

```python
# config.py - Default Settings
provider: str = "offline"
openai_api_key: str = ""  # From keyring
gemini_api_key: str = ""  # From keyring
model_openai: str = "gpt-4o-mini"
model_gemini: str = "gemini-2.0-flash"
max_chunk_chars: int = 1800
enable_cache: bool = True
cache_max_size_mb: int = 100
```

### Custom Configuration
Settings persist across sessions in the application's database. Changes made in the Settings dialog are automatically saved.

## API Keys Setup (Optional)

### OpenAI
1. Visit [platform.openai.com](https://platform.openai.com)
2. Create an API key
3. In EduMind: Settings → API Configuration → OpenAI
4. Paste your key (stored securely in system keyring)

### Google Gemini
1. Visit [makersuite.google.com](https://makersuite.google.com/app/apikey)
2. Create an API key
3. In EduMind: Settings → API Configuration → Gemini
4. Paste your key (stored securely in system keyring)

## Security

- **No .env files**: Configuration doesn't rely on environment files
- **Keyring storage**: API keys stored in system keyring (Windows Credential Manager, macOS Keychain, Linux Secret Service)
- **Secure defaults**: App works offline without API keys
- **No API exposure**: Keys never appear in logs or config files
- **Auto-validation**: Invalid configurations automatically fall back to offline mode

## Performance Tips

1. **Enable Caching**: Improves response times for similar queries
2. **Batch Processing**: Process multiple items together
3. **Monitor Performance**: Check Settings → Performance Stats
4. **Regular Cleanup**: Clear cache if it grows too large
5. **Study Sessions**: Consistent study patterns improve performance

## Troubleshooting

### App Won't Start
```bash
# Ensure dependencies are installed
pip install -r requirements.txt

# Check database integrity
python -c "from data.db import init_db; init_db()"
```

### API Key Not Working
1. Check Settings → API Configuration
2. Verify key is correct in your provider's dashboard
3. Ensure provider is set to "Online" in settings
4. Try offline mode first to test other features

### Performance Issues
1. Check cache size: Settings → Performance Stats
2. Clear cache if > 90MB
3. Check for slow operations: Settings → Performance Stats
4. Restart application

### Session Not Saving
1. Ensure data directory has write permissions
2. Check disk space (minimum 100MB recommended)
3. Check logs in data/logs/ for errors

## Development

### Running Tests
```bash
pytest tests/
pytest tests/ --cov=core
```

### Building Executable
```bash
# Generate standalone executable
python scripts/build.py
```

### Code Style
```bash
# Format code
black .

# Check types
mypy core/

# Lint
ruff check .
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - See [LICENSE.txt](LICENSE.txt)

## Support

- 📖 Documentation: See [README.md](README.md)
- 🐛 Report Issues: Check existing issues first
- 💡 Suggestions: Open a discussion

## Changelog

### v1.1.0 (Current)
- ✨ Secure configuration system (no .env)
- ✨ Response caching with LRU eviction
- ✨ Advanced analytics and session tracking
- ✨ Performance monitoring tools
- ✨ Robust session management
- 🔒 Security improvements (keyring integration)
- 🐛 Bug fixes and optimizations
- 📚 Enhanced documentation

### v1.0.0
- Initial release
- Core study tools (summaries, flashcards, quizzes)
- AI provider integration
- PyQt6 UI

## Roadmap

- [ ] Mobile companion app
- [ ] Collaborative study groups
- [ ] Advanced ML models
- [ ] Browser extension
- [ ] Cloud synchronization
- [ ] Voice-based interaction

---

**Made with ❤️ by CodeCrafters Team**
