# Open Stream - System Architecture

## Overview

Open Stream is a sophisticated desktop application built with a three-process architecture: Electron main process, React renderer, and embedded Python FastAPI backend. The application provides AI-powered content analysis and moderation capabilities using state-of-the-art Hugging Face transformer models.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Desktop Application                                │
├─────────────────┬───────────────────┬─────────────────────────────────────────┤
│   Renderer      │   Main Process    │        Python Backend                  │
│   (React UI)    │   (Electron)      │       (FastAPI + AI)                   │
│                 │                   │                                         │
│ ┌─────────────┐ │ ┌───────────────┐ │ ┌─────────────────────────────────────┐ │
│ │    App.tsx  │ │ │  index.ts     │ │ │           main.py                   │ │
│ │             │ │ │               │ │ │                                     │ │
│ │ ┌─────────┐ │ │ │ ┌───────────┐ │ │ │ ┌─────────────────────────────────┐ │ │
│ │ │useServer│ │ │ │ │server.ts  │ │ │ │ │          AI Manager             │ │ │
│ │ │  Hook   │ │ │ │ │           │ │ │ │ │                                 │ │ │
│ │ └─────────┘ │ │ │ └───────────┘ │ │ │ │ • Toxicity Detection (BERT)     │ │ │
│ │             │ │ │               │ │ │ │ • Sentiment Analysis (5-star)   │ │ │
│ │ Component   │ │ │ IPC Handlers  │ │ │ │ • Emotion Detection (optional)  │ │ │
│ │ Library     │ │ │               │ │ │ │ • Hate Speech Detection         │ │ │
│ └─────────────┘ │ └───────────────┘ │ └─────────────────────────────────────┘ │
│                 │                   │                                         │
│      IPC        │     HTTP          │           Services                      │
│   Bridge API    │   Client          │                                         │
└─────────────────┴───────────────────┴─────────────────────────────────────────┘
```

## Technology Stack

### Frontend Layer
- **Electron 37.2.3**: Cross-platform desktop application framework
- **React 19.1.0**: Modern UI library with concurrent features
- **TypeScript 5.8.3**: Type-safe development experience
- **Vite 7.0.5**: Fast build tooling and development server
- **Custom CSS**: Minimal styling for AI analysis interface

### Backend Layer
- **Python 3.8+**: Runtime environment (3.11-3.12 recommended)
- **FastAPI 0.115.0+**: High-performance web framework
- **Uvicorn**: ASGI server with standard extensions
- **Pydantic**: Data validation and serialization

### AI/ML Stack
- **Hugging Face Transformers 4.36.0+**: Model management and inference
- **PyTorch 2.1.0+**: Deep learning framework
- **Pre-trained Models**:
  - `unitary/toxic-bert`: Toxicity detection
  - `distilbert-base-uncased-finetuned-sst-2-english`: Sentiment analysis
  - `nlptown/bert-base-multilingual-uncased-sentiment`: 5-star rating
  - `j-hartmann/emotion-english-distilroberta-base`: Emotion detection

## Process Architecture

### Three-Process Design Pattern

**1. Renderer Process (React Frontend)**
- Runs in isolated context with limited Node.js access
- Communicates with main process via IPC
- Handles UI state management and user interactions
- Located: `/src/renderer/`

**2. Main Process (Electron)**
- Manages application lifecycle and window creation
- Spawns and manages Python backend server
- Acts as IPC-to-HTTP bridge
- Handles security boundaries and process coordination
- Located: `/src/main/`

**3. Python Backend (FastAPI Server)**
- Runs as child process with dynamic port allocation
- Provides AI inference capabilities
- Manages ML model lifecycle and caching
- Located: `/server/`

### Inter-Process Communication

```typescript
// IPC Bridge Pattern
┌─────────────┐    IPC     ┌──────────────┐    HTTP    ┌─────────────┐
│  Renderer   │◄──────────►│ Main Process │◄──────────►│   Python    │
│             │   secure   │              │  localhost │             │
│ window.     │            │ ipcMain      │            │ FastAPI     │
│ serverAPI   │            │ handlers     │            │ endpoints   │
└─────────────┘            └──────────────┘            └─────────────┘
```

**IPC Channel Contracts**:
- `server:getPort` → Dynamic port discovery
- `server:isReady` → Health check status
- `server:getApiUrl` → API base URL
- `server:analyze` → Text analysis request
- `server:processChat` → Chat moderation request

## Data Flow Architecture

### Request Processing Pipeline

```
1. User Input (React Component)
   ↓
2. State Update + Loading Indicator
   ↓
3. IPC Call via serverAPI hook
   ↓
4. Main Process IPC Handler
   ↓
5. HTTP Request to Python Backend
   ↓
6. AI Model Inference (CPU/GPU)
   ↓
7. Response Processing & Validation
   ↓
8. HTTP Response
   ↓
9. IPC Response to Renderer
   ↓
10. UI State Update + Results Display
```

### AI Model Management

**Lazy Loading Strategy**:
- Models load on first API request (not application startup)
- Reduces initial startup time from 60+ seconds to ~3 seconds
- Fallback to rule-based analysis if models fail to load

**Model Caching**:
- Hugging Face models cached in `/server/models/`
- Persistent across application restarts
- Automatic model downloads on first use

**Memory Management**:
- Single model instance per type (singleton pattern)
- Models remain loaded for application lifetime
- CPU-optimized inference (no GPU acceleration)

## Security Architecture

### Process Isolation

**Renderer Security**:
- Context isolation enabled (`contextIsolated: true`)
- No direct Node.js access from web content
- Limited API surface via preload script
- Input validation at IPC boundary

**Main Process Security**:
- IPC input validation and sanitization
- HTTP client restricted to localhost only
- Dynamic port allocation prevents conflicts
- Process lifecycle management

**Python Backend Security**:
- Localhost-only binding (127.0.0.1)
- CORS limited to Electron origins
- No external network access
- Process sandboxing via spawn isolation

### Data Validation Pipeline

```
User Input → TypeScript Types → IPC Validation → Pydantic Models → AI Processing
```

**Validation Layers**:
1. **Frontend**: TypeScript interface validation
2. **IPC Boundary**: Runtime type checking
3. **HTTP Layer**: Pydantic model validation
4. **AI Layer**: Text length limits and sanitization

## Performance Characteristics

### Startup Performance

**Cold Start** (First Run):
- Virtual environment creation: 30-60 seconds
- Python dependencies installation: 2-5 minutes
- Model download: 3-10 minutes (network dependent)

**Warm Start** (Subsequent Runs):
- Application launch: 2-3 seconds
- Python server startup: 1-2 seconds
- Model loading: 30-60 seconds (lazy loading)

### Runtime Performance

**AI Inference Latency**:
- Toxicity detection: 100-300ms
- Sentiment analysis: 50-150ms
- Combined analysis: 200-500ms
- CPU-bound operation (no GPU acceleration)

**Memory Usage**:
- Electron processes: ~200-400MB
- Python backend: ~2-4GB (loaded models)
- Total application: ~2.5-4.5GB

### Optimization Strategies

**Model Optimization**:
- DistilBERT models for faster inference
- CPU-optimized model configurations
- Batch processing capability (not implemented)

**Caching Strategy**:
- Model weights cached locally
- No request result caching (real-time analysis)
- Connection pooling for HTTP requests

## Deployment Architecture

### Build Process

```
Source Code → TypeScript Compilation → Electron Packaging → Platform Binaries
     ↓
Python Assets → Bundle Validation → Code Signing → Distribution
```

**Build Targets**:
- Windows: NSIS installer (.exe)
- macOS: DMG package (.dmg)
- Linux: AppImage (.AppImage)

### Distribution Strategy

**Bundled Assets**:
- Electron application (compiled)
- Python source code and requirements
- Resource files (icons, configurations)
- No pre-downloaded models (lazy loading)

**Runtime Dependencies**:
- Python 3.8+ (user-installed or bundled)
- Internet connection (first run for models)
- 4-8GB available memory
- Multi-core CPU recommended

## Monitoring and Observability

### Logging Architecture

**Structured Logging**:
- Electron main process: Console logging
- Python backend: Python logging module
- Correlation via request IDs
- Different log levels per component

**Health Monitoring**:
- `/health` endpoint with AI status
- Periodic health checks from frontend
- Server availability monitoring
- Model loading status tracking

### Error Handling Strategy

**Error Propagation Chain**:
```
Python Exception → FastAPI Error Handler → HTTP Error Response → 
Electron HTTP Client → IPC Error Response → React Error Boundary
```

**Fallback Mechanisms**:
- Rule-based analysis when AI fails
- Server restart on critical failures
- Graceful degradation patterns
- User-friendly error messages

## Scalability Considerations

### Current Limitations

- Single-user desktop application
- CPU-only AI inference
- No request batching
- Memory-intensive model loading

### Future Scaling Opportunities

**Performance Improvements**:
- GPU acceleration support
- Model quantization for smaller memory footprint
- Request batching for multiple analyses
- Background model pre-loading

**Feature Scaling**:
- Multi-user session support
- WebSocket for real-time features
- Cloud model API integration
- Custom model training pipeline

## Integration Points

### External Dependencies

**Required**:
- Python 3.8+ runtime
- Internet connection (model downloads)
- Operating system integration (Electron)

**Optional**:
- GPU acceleration (CUDA/MPS)
- Custom model configurations
- Extended analysis features

### API Integration Patterns

**Internal APIs**:
- IPC communication (typed, secure)
- HTTP REST endpoints (OpenAPI documented)
- Health check protocol
- Graceful shutdown handling

**Extension Points**:
- Custom model integration
- Additional analysis endpoints
- External service connectors
- Plugin architecture (future)

## Development Architecture

### Code Organization

```
/src/
├── main/           # Electron main process
│   ├── index.ts    # Application entry point
│   └── server.ts   # Python server management
├── preload/        # IPC security bridge
│   └── index.ts    # Context bridge setup
└── renderer/       # React frontend
    ├── src/
    │   ├── App.tsx           # Main UI component
    │   ├── hooks/
    │   │   └── useServer.ts  # Server communication hook
    │   └── components/       # UI components

/server/
├── main.py         # FastAPI application
├── services/       # AI service modules
│   ├── ai_manager.py      # Model management
│   ├── sentiment_service.py
│   └── toxicity_service.py
└── models/         # Cached AI models (runtime)
```

### Build System Architecture

**Multi-Target Compilation**:
- TypeScript configs: `tsconfig.json`, `tsconfig.web.json`, `tsconfig.node.json`
- Electron-vite configuration for optimal bundling
- Platform-specific build scripts
- Asset packaging and optimization

This architecture provides a robust foundation for AI-powered content moderation while maintaining security, performance, and user experience standards appropriate for a desktop application.