# Open Stream API Guidelines

## Overview

This document outlines the API architecture and guidelines for the Open Stream AI application - an Electron-based desktop application with an embedded Python FastAPI backend for AI-powered content moderation.

## Architecture Pattern: IPC-to-HTTP Bridge

### Three-Process Architecture

```
┌─────────────────┐    IPC     ┌──────────────────┐    HTTP    ┌─────────────────┐
│   Renderer      │◄──────────►│   Main Process   │◄──────────►│  Python FastAPI │
│   (React UI)    │            │  (Electron)      │            │   (AI Backend)  │
└─────────────────┘            └──────────────────┘            └─────────────────┘
```

### Process Responsibilities

**Renderer Process (React/TypeScript)**
- User interface and interactions
- State management for UI components
- IPC communication with main process

**Main Process (Electron)**
- Python server lifecycle management
- IPC-to-HTTP bridge functionality
- Port allocation and service discovery
- Security boundary enforcement

**Python Backend (FastAPI)**
- AI model management and inference
- Content analysis and moderation
- RESTful API endpoints

## IPC API Layer

### Channel Contracts

All IPC channels follow the `namespace:action` naming convention:

#### Server Management Channels

```typescript
// Server status and configuration
'server:getPort' → Promise<number>
'server:isReady' → Promise<boolean>
'server:getApiUrl' → Promise<string>

// AI analysis operations
'server:analyze' → Promise<AnalyzeResponse>
'server:processChat' → Promise<ChatResponse>
```

#### TypeScript Interface Definitions

```typescript
interface ServerAPI {
  getPort: () => Promise<number>
  isReady: () => Promise<boolean>
  getApiUrl: () => Promise<string>
  analyze: (text: string) => Promise<AnalyzeResponse>
  processChat: (message: ChatMessage) => Promise<ChatResponse>
}

interface AnalyzeResponse {
  text: string
  toxic: boolean
  confidence: number
  sentiment: string
  categories: string[]
}

interface ChatMessage {
  username: string
  message: string
  channel: string
  timestamp?: number
}

interface ChatResponse {
  message_id: string
  action: 'allow' | 'warning' | 'timeout' | 'ban'
  reason: string | null
}
```

### Security Boundaries

**IPC Security**
- Context isolation enabled
- Preload script exposes limited API surface
- No direct Node.js access from renderer
- Input validation at IPC boundary

**HTTP Security**
- Localhost-only binding (127.0.0.1)
- Random port allocation (50000-60000 range)
- CORS configured for Electron origins
- No external network access

## HTTP API Layer

### Base Configuration

**Server Binding**: `127.0.0.1:{dynamic_port}`
**Content-Type**: `application/json`
**CORS Origins**: `["http://localhost:*", "file://*"]`

### Endpoint Standards

#### Request/Response Format

All endpoints follow RESTful conventions:

```http
POST /analyze
Content-Type: application/json

{
  "text": "content to analyze",
  "options": {} // optional parameters
}
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "text": "content to analyze",
  "toxic": false,
  "toxicity_score": 0.1,
  "sentiment": "neutral",
  "confidence": 0.75,
  "ai_enabled": true
}
```

#### Error Response Format

Following RFC 7807 Problem Details standard:

```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json

{
  "detail": [
    {
      "loc": ["body", "text"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Rate Limiting

No explicit rate limiting implemented - protected by:
- Local-only access
- Single-user desktop application context
- Process lifecycle tied to Electron app

## Data Flow Patterns

### Async Operation Flow

```
1. User Input (React)
   ↓
2. State Update + Loading State
   ↓
3. IPC Call to Main Process
   ↓
4. HTTP Request to Python Backend
   ↓
5. AI Model Inference
   ↓
6. HTTP Response
   ↓
7. IPC Response
   ↓
8. UI State Update + Results Display
```

### Error Propagation

```
Python Exception
   ↓
FastAPI Error Handler
   ↓
HTTP Error Response
   ↓
Electron HTTP Client
   ↓
IPC Error Response
   ↓
React Error Boundary / State
```

### State Synchronization

**Server State Management**:
- Health check polling (1-second interval)
- Connection state tracking
- Automatic retry on connection failure

**AI Model State**:
- Lazy loading on first request
- Fallback to rule-based analysis
- Model availability status in health endpoint

## Performance Considerations

### Model Loading Strategy

**Lazy Loading**: Models load on first API request to minimize startup time
**Memory Management**: Single model instance per type (toxicity, sentiment)
**Fallback Strategy**: Rule-based analysis when AI models unavailable

### Caching Strategy

**Model Caching**: Hugging Face models cached locally in `./models` directory
**No Request Caching**: Real-time analysis required for moderation

### Optimization Bottlenecks

1. **Model Loading Time**: 30-60 seconds on first request
2. **Inference Latency**: 100-500ms per request
3. **Memory Usage**: 2-4GB for loaded BERT models
4. **CPU Intensive**: AI inference on CPU (no GPU acceleration)

## API Versioning Strategy

### Current Approach
- Embedded versioning in API title and responses
- No URL versioning (single embedded server)
- Breaking changes require full application update

### Recommended Evolution
```
/v1/analyze    # Explicit version in URL
/v2/analyze    # Future version with enhanced features
```

### Backwards Compatibility
- Maintain v1 endpoints during transition
- Feature flags for experimental endpoints
- Clear deprecation notices

## Security Analysis

### Threat Model

**Local Attack Surface**:
- Process injection into Electron main process
- IPC message interception
- Python server process compromise

**Mitigations**:
- Context isolation in renderer
- Input validation at all boundaries  
- Process sandboxing via Electron security features

### Authentication

**Current**: No authentication (local desktop app)
**Recommendation**: 
- JWT tokens for multi-user scenarios
- API key authentication for external integrations

### Input Validation

**IPC Layer**: TypeScript type checking + runtime validation
**HTTP Layer**: Pydantic models with field validation
**AI Layer**: Text length limits and content sanitization

## Integration Points

### Port Discovery Mechanism

```typescript
// Dynamic port allocation
constructor() {
  this.port = this.getRandomPort() // 50000-60000 range
}

// Service discovery via IPC
const port = await window.serverAPI.getPort()
const apiUrl = `http://127.0.0.1:${port}`
```

### Health Check Protocol

```typescript
// Exponential backoff health checking
async waitForServer(maxAttempts = 30): Promise<void> {
  for (let i = 0; i < maxAttempts; i++) {
    try {
      const response = await axios.get(`http://127.0.0.1:${this.port}/health`)
      if (response.data.status === 'ok') return
    } catch { /* retry */ }
    await new Promise(resolve => setTimeout(resolve, 1000))
  }
  throw new Error('Backend server failed to start')
}
```

### Graceful Shutdown Flow

```
1. Electron 'before-quit' event
   ↓
2. POST /shutdown to Python server
   ↓  
3. Python process.kill() if HTTP fails
   ↓
4. Cleanup temp files and ports
   ↓
5. Electron app.quit()
```

## Development Guidelines

### Error Handling Patterns

**IPC Layer**:
```typescript
try {
  const result = await window.serverAPI.analyze(text)
  return result
} catch (error) {
  throw new Error(error.response?.data?.detail || error.message)
}
```

**HTTP Layer**:
```python
@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )
```

### Testing Strategy

**Unit Tests**: AI service classes and utility functions
**Integration Tests**: IPC communication and HTTP endpoints  
**E2E Tests**: Full user workflow from UI to AI analysis

### Monitoring and Logging

**Structured Logging**: JSON format with correlation IDs
**Performance Metrics**: Request duration and model inference time
**Error Tracking**: Exception details with stack traces

## Next Steps for Implementation Teams

1. **Generate Server Stubs**: Use OpenAPI spec to generate FastAPI code
2. **Implement Authentication**: Add JWT middleware for multi-user support
3. **Add Monitoring**: Integrate APM solution for production deployments
4. **Optimize Performance**: Implement model warm-up and request batching
5. **Enhance Security**: Add input sanitization and rate limiting
6. **Scale Architecture**: Consider WebSocket for real-time features

---

**Last Updated**: 2025-08-12  
**API Version**: 2.0.0  
**Specification**: OpenAPI 3.1.0