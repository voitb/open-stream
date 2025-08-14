# Open Stream - Development Guide

## Quick Start

### Prerequisites

- **Node.js 18+** with **PNPM package manager**
- **Python 3.8-3.12** (3.11 or 3.12 recommended for best compatibility)
- **Git** for version control
- **4-8GB RAM** for AI model operations

### Package Manager Requirement

**Important**: This project uses **PNPM** as the package manager. Do not use npm or yarn.

**Installing PNPM**:
```bash
# Install PNPM globally
npm install -g pnpm@latest

# Or via other methods:
curl -fsSL https://get.pnpm.io/install.sh | sh  # Unix/macOS
iwr https://get.pnpm.io/install.ps1 -useb | iex  # Windows PowerShell

# Verify installation
pnpm --version  # Should be 8.0+
```

**Why PNPM?**
- **Faster installations** - Up to 2x faster than npm
- **Disk space efficiency** - Content-addressable storage saves space
- **Better dependency resolution** - Strict, non-flat node_modules
- **Monorepo support** - Built-in workspace features
- **Enhanced security** - Better dependency isolation

### Initial Setup

```bash
# Clone repository
git clone <repository-url>
cd open-stream

# Install Node.js dependencies with PNPM
pnpm install

# First-time setup (installs Python dependencies automatically)
pnpm dev

# Alternative: Manual Python setup
pnpm run server:install    # Unix/macOS
pnpm run server:install:win # Windows
```

### Development Commands

```bash
# Start development environment (all processes)
pnpm dev

# Individual process development
pnpm dev:renderer           # React frontend only
pnpm run server:dev         # Python backend only (Unix/macOS)
pnpm run server:dev:win     # Python backend only (Windows)

# Type checking
pnpm typecheck              # All TypeScript
pnpm typecheck:node         # Main/preload processes
pnpm typecheck:web          # Renderer process

# Linting and formatting
pnpm lint                   # ESLint
pnpm format                 # Prettier
```

## Development Environment

### Project Structure

```
open-stream/
├── src/                    # Electron + React source
│   ├── main/              # Electron main process
│   │   ├── index.ts       # Application entry point
│   │   └── server.ts      # Python server management class
│   ├── preload/           # IPC security bridge
│   │   ├── index.ts       # Context bridge and API exposure
│   │   └── index.d.ts     # Type definitions
│   └── renderer/          # React application
│       ├── index.html     # Entry HTML
│       └── src/
│           ├── App.tsx    # Main React component
│           ├── hooks/     # Custom React hooks
│           └── components/ # UI components
├── server/                # Python FastAPI backend
│   ├── main.py           # FastAPI application and AI integration
│   ├── requirements.txt  # Python dependencies
│   ├── services/         # AI service modules
│   │   ├── ai_manager.py        # Model management singleton
│   │   ├── sentiment_service.py # Sentiment analysis
│   │   └── toxicity_service.py  # Toxicity detection
│   ├── models/           # Hugging Face model cache (auto-created)
│   └── venv/             # Python virtual environment (auto-created)
├── build/                # Build resources and icons
├── out/                  # Compiled Electron code
├── resources/            # Application resources
├── pnpm-lock.yaml        # PNPM lock file (DO NOT edit manually)
└── docs/                 # Documentation files
```

### Technology Stack

**Frontend Development**:
- **Electron 37.2.3**: Desktop application framework
- **React 19.1.0**: UI library with latest features
- **TypeScript 5.8.3**: Type safety and developer experience
- **Vite 7.0.5**: Build tool and development server
- **PNPM 8+**: Fast, efficient package manager
- **ESLint + Prettier**: Code quality and formatting

**Backend Development**:
- **Python 3.8+**: Runtime (3.11-3.12 recommended)
- **FastAPI 0.115.0+**: Web framework with automatic OpenAPI
- **Uvicorn**: ASGI server implementation
- **Pydantic**: Data validation and type hints
- **Hugging Face Transformers**: AI model management

## Development Workflow

### Setting Up Your Development Environment

1. **PNPM Installation and Verification**:
```bash
# Check PNPM version (should be 8.0+)
pnpm --version

# If not installed, install globally
npm install -g pnpm@latest

# Verify PNPM store location
pnpm store path

# Configure PNPM (optional optimizations)
pnpm config set store-dir ~/.pnpm-store  # Custom store location
pnpm config set auto-install-peers true   # Auto-install peer dependencies
```

2. **Python Environment Verification**:
```bash
# Check Python version (should be 3.8+)
python3 --version

# Verify pip is available
python3 -m pip --version

# Test virtual environment creation
python3 -m venv test-env && rm -rf test-env
```

3. **IDE Setup** (Recommended: VS Code):
```bash
# Install recommended extensions
code --install-extension ms-python.python
code --install-extension ms-vscode.vscode-typescript-next
code --install-extension esbenp.prettier-vscode
code --install-extension dbaeumer.vscode-eslint
```

4. **Environment Configuration**:
```bash
# Optional: Set custom model cache directory
export TRANSFORMERS_CACHE=/path/to/your/models
export HF_HOME=/path/to/your/models

# For development with specific Python version
export PYTHON_PATH=/usr/local/bin/python3.11
```

### Development Process

#### Starting Development

```bash
# Terminal 1: Start main development server
pnpm dev

# Terminal 2: Monitor Python backend logs (optional)
cd server && source venv/bin/activate && python main.py 55555

# Terminal 3: Run tests (when available)
pnpm test
```

#### Making Changes

**Frontend Changes** (`/src/renderer/`):
- Hot reload enabled via Vite
- Changes appear immediately in Electron window
- TypeScript errors shown in terminal and IDE

**Electron Main Process Changes** (`/src/main/`):
- Requires application restart
- Use `Ctrl+R` in Electron window or restart `pnpm dev`

**Python Backend Changes** (`/server/`):
- Auto-restart enabled via uvicorn
- Changes reflected without Electron restart
- Monitor server logs for errors

### AI Model Development

#### Model Integration Workflow

1. **Adding New Models**:
```python
# In server/services/ai_manager.py
def get_custom_model(self):
    """Add new model integration"""
    if 'custom' not in self.models:
        self.models['custom'] = pipeline(
            "text-classification",
            model="your-model/model-name",
            device=self.device,
            model_kwargs={"cache_dir": self.models_dir}
        )
    return self.models['custom']
```

2. **Service Layer Implementation**:
```python
# Create new service in server/services/
class CustomService:
    def __init__(self):
        self.model = None
    
    async def analyze(self, text: str) -> Dict[str, Any]:
        if not self.model:
            self.model = ai_manager.get_custom_model()
        
        try:
            results = self.model(text)
            return {"result": results[0]}
        except Exception as e:
            logger.error(f"Custom analysis failed: {e}")
            return {"error": str(e)}
```

3. **API Endpoint Addition**:
```python
# In server/main.py
@app.post("/custom-analyze")
async def custom_analyze(request: AnalyzeRequest):
    result = await custom_service.analyze(request.text)
    return result
```

4. **Frontend Integration**:
```typescript
// Add to preload/index.ts
const serverAPI = {
  // ... existing methods
  customAnalyze: (text: string) => ipcRenderer.invoke('server:customAnalyze', text)
}

// Add IPC handler in main/index.ts
ipcMain.handle('server:customAnalyze', async (_, text: string) => {
  const response = await axios.post(`http://127.0.0.1:${port}/custom-analyze`, { text })
  return response.data
})
```

### Testing Strategy

#### Unit Testing (Not yet implemented)

```bash
# Frontend tests
pnpm test:renderer

# Backend tests  
cd server && python -m pytest tests/

# Integration tests
pnpm test:integration
```

#### Manual Testing Workflow

1. **AI Model Testing**:
```bash
# Test individual models
curl -X POST http://127.0.0.1:55555/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "This is a test message"}'

# Test health endpoint
curl http://127.0.0.1:55555/health
```

2. **Frontend Testing**:
- Test text input and analysis flow
- Verify loading states and error handling
- Check responsiveness and UI feedback

3. **Integration Testing**:
- Test full workflow from UI to AI results
- Verify IPC communication reliability
- Test error propagation and recovery

### Debugging Guide

#### Common Development Issues

**1. Python Server Won't Start**:
```bash
# Check Python path
which python3

# Verify virtual environment
cd server && source venv/bin/activate && python --version

# Check dependencies
pip list | grep -E "(fastapi|uvicorn|transformers)"

# Manual server start for debugging
cd server && python main.py 55555
```

**2. Model Loading Failures**:
```bash
# Check available disk space (models are large)
df -h

# Verify internet connection
curl -I https://huggingface.co

# Check model cache
ls -la server/models/

# Clear model cache if corrupted
rm -rf server/models/*
```

**3. IPC Communication Issues**:
```typescript
// Debug IPC in renderer dev tools
window.serverAPI.getPort().then(console.log).catch(console.error)

// Check main process logs
console.log('IPC received:', eventName, args)
```

**4. Build Issues**:
```bash
# Clean build artifacts
rm -rf out/ dist/

# Verify TypeScript compilation
pnpm typecheck

# Check electron-builder configuration
pnpm build:unpack
```

**5. PNPM-Specific Issues**:
```bash
# Clear PNPM cache
pnpm store prune

# Reinstall dependencies
rm -rf node_modules pnpm-lock.yaml
pnpm install

# Check PNPM configuration
pnpm config list

# Verify shamefully-hoist if needed for problematic packages
echo 'shamefully-hoist=true' >> .npmrc
```

#### Debugging Tools

**Frontend Debugging**:
- Chrome DevTools in Electron renderer
- React Developer Tools extension
- Network tab for HTTP request monitoring

**Backend Debugging**:
- Python debugger (`import pdb; pdb.set_trace()`)
- FastAPI automatic documentation at `http://127.0.0.1:55555/docs`
- Uvicorn detailed logging

**Process Debugging**:
- Electron main process debugging via Node.js inspector
- Process monitoring with Activity Monitor/Task Manager
- Memory usage tracking during model loading

### Code Style and Standards

#### TypeScript/JavaScript

```typescript
// Use strict type definitions
interface ServerAPI {
  analyze: (text: string) => Promise<AnalyzeResponse>
  isReady: () => Promise<boolean>
}

// Prefer async/await over Promises
const result = await window.serverAPI.analyze(text)

// Use proper error handling
try {
  const analysis = await analyzeText(text)
  setResult(analysis)
} catch (error) {
  console.error('Analysis failed:', error)
  setError(error.message)
}
```

#### Python

```python
# Use type hints consistently
async def analyze_text(text: str) -> Dict[str, Any]:
    """Analyze text with proper typing"""
    return {"result": "analyzed"}

# Follow FastAPI patterns
@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_endpoint(request: AnalyzeRequest):
    return await service.analyze(request.text)

# Use proper logging
import logging
logger = logging.getLogger(__name__)
logger.info("Processing request")
```

### Performance Optimization

#### Development Performance

**Faster Development Cycles**:
- Use `pnpm dev:fast` to skip server setup
- Implement code splitting for renderer
- Enable TypeScript incremental compilation
- Utilize PNPM's fast installation and linking

**Model Development**:
- Use smaller models during development
- Implement model mocking for faster iteration
- Cache API responses during UI development

#### Build Performance

```bash
# Parallel TypeScript compilation
pnpm typecheck:node & pnpm typecheck:web & wait

# Optimize Electron packaging
# Use electron-builder.yml configuration

# PNPM performance benefits
# Content-addressable storage
# Symlinked node_modules
# Parallel dependency resolution
```

### Contributing Guidelines

#### Pull Request Process

1. **Feature Development**:
```bash
# Create feature branch
git checkout -b feature/new-ai-model

# Make changes and test
pnpm dev
# Test changes manually

# Commit with conventional commits
git commit -m "feat: add emotion detection model"
```

2. **Code Review Checklist**:
- [ ] TypeScript types are properly defined
- [ ] Python code follows type hint conventions
- [ ] Error handling is implemented
- [ ] Performance impact is considered
- [ ] Documentation is updated
- [ ] PNPM commands are used consistently

3. **Pre-commit Checks**:
```bash
# Run before committing
pnpm typecheck
pnpm lint
pnpm format

# Test basic functionality
pnpm dev # Verify application starts
```

### PNPM Workspace Configuration

#### Workspace Management

```yaml
# pnpm-workspace.yaml (if using workspaces)
packages:
  - 'packages/*'
  - 'apps/*'
```

```json
# package.json PNPM configuration
{
  "pnpm": {
    "onlyBuiltDependencies": [
      "electron",
      "esbuild"
    ],
    "peerDependencyRules": {
      "ignoreMissing": ["@babel/core"],
      "allowedVersions": {
        "react": "19"
      }
    }
  }
}
```

#### PNPM Commands Reference

```bash
# Dependency Management
pnpm add <package>              # Add production dependency
pnpm add -D <package>          # Add development dependency
pnpm add -g <package>          # Add global package
pnpm remove <package>          # Remove dependency
pnpm update                    # Update dependencies

# Project Management
pnpm install                   # Install all dependencies
pnpm install --frozen-lockfile # Install from lockfile only
pnpm install --offline        # Install from cache only
pnpm store prune              # Clean unused packages

# Script Execution
pnpm run <script>             # Run package script
pnpm dev                      # Run development script
pnpm <script>                 # Run script (shorthand)

# Information
pnpm list                     # List installed packages
pnpm list --depth=0          # List top-level packages only
pnpm why <package>           # Show why package is installed
pnpm outdated                # Show outdated packages
```

### Environment Variables

#### Development Configuration

```bash
# .env (optional)
NODE_ENV=development
ELECTRON_IS_DEV=1

# Python model configuration
TRANSFORMERS_CACHE=./server/models
HF_HOME=./server/models
PYTHONUNBUFFERED=1

# Debug flags
DEBUG_IPC=1
DEBUG_PYTHON=1

# PNPM configuration
PNPM_HOME=~/.pnpm
```

#### Production Configuration

```bash
# Production environment
NODE_ENV=production
ELECTRON_IS_PACKAGED=1

# Disable debug features
DEBUG_IPC=0
DEBUG_PYTHON=0
```

### Next Steps for New Developers

1. **First Week**: 
   - Set up development environment with PNPM
   - Understand three-process architecture
   - Make simple UI changes

2. **Second Week**:
   - Explore AI model integration
   - Add new analysis features
   - Understand IPC communication

3. **Ongoing Development**:
   - Optimize model performance
   - Add new AI capabilities
   - Improve user experience

### Resources and Documentation

- **API Documentation**: `http://127.0.0.1:55555/docs` (when server running)
- **OpenAPI Specification**: `../../openapi.yaml`
- **Architecture Guide**: `../architecture/ARCHITECTURE.md`
- **Deployment Guide**: `../deployment/DEPLOYMENT.md`
- **PNPM Documentation**: [https://pnpm.io/](https://pnpm.io/)
- **Hugging Face Models**: [https://huggingface.co/models](https://huggingface.co/models)
- **Electron Documentation**: [https://electronjs.org/docs](https://electronjs.org/docs)
- **FastAPI Documentation**: [https://fastapi.tiangolo.com](https://fastapi.tiangolo.com)

### Getting Help

**Common Issues**:
- Check existing GitHub issues
- Review application logs in console
- Verify Python and Node.js versions
- Ensure PNPM is properly installed and configured

**Community Resources**:
- Electron Discord community
- FastAPI GitHub discussions
- Hugging Face forums for AI/ML questions
- PNPM GitHub discussions

This development guide provides everything needed to contribute effectively to the Open Stream project. The modular architecture and clear separation of concerns make it easy to work on individual components while understanding the full system integration. PNPM's efficient package management ensures fast, reliable dependency management throughout the development process.