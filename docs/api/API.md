# Open Stream - API Reference

## API Architecture Overview

Open Stream implements a three-layer API architecture:

1. **IPC API**: Secure communication between React renderer and Electron main process
2. **HTTP API**: RESTful endpoints provided by the embedded Python FastAPI backend
3. **Internal APIs**: Service layer interfaces for AI model management

## IPC API Layer

### Overview

The IPC API provides a secure bridge between the React frontend and Electron main process. All communication is type-safe and validated at both ends.

### Server Management APIs

#### `window.serverAPI.getPort()`

Get the dynamically allocated port number for the Python backend.

**Returns**: `Promise<number>`

```typescript
const port = await window.serverAPI.getPort()
console.log(`Backend running on port ${port}`)
```

#### `window.serverAPI.isReady()`

Check if the Python backend server is ready to accept requests.

**Returns**: `Promise<boolean>`

```typescript
const ready = await window.serverAPI.isReady()
if (ready) {
  // Server is ready for AI analysis
}
```

#### `window.serverAPI.getApiUrl()`

Get the complete base URL for the Python backend API.

**Returns**: `Promise<string>`

```typescript
const apiUrl = await window.serverAPI.getApiUrl()
// Returns: "http://127.0.0.1:55555" (example port)
```

### Analysis APIs

#### `window.serverAPI.analyze(text: string)`

Perform comprehensive AI analysis on text content including toxicity detection and sentiment analysis.

**Parameters**:
- `text` (string): Text content to analyze (1-1000 characters)

**Returns**: `Promise<AnalyzeResponse>`

```typescript
interface AnalyzeResponse {
  text: string
  toxic: boolean
  toxicity_score: number      // 0.0 - 1.0
  sentiment: 'positive' | 'negative' | 'neutral'
  confidence: number          // 0.0 - 1.0
  ai_enabled: boolean
}

// Example usage
try {
  const result = await window.serverAPI.analyze("This is great content!")
  console.log({
    toxic: result.toxic,           // false
    sentiment: result.sentiment,   // "positive"
    confidence: result.confidence  // 0.95
  })
} catch (error) {
  console.error('Analysis failed:', error.message)
}
```

#### `window.serverAPI.processChat(message: ChatMessage)`

Process and moderate chat messages with comprehensive AI analysis and moderation recommendations.

**Parameters**:
```typescript
interface ChatMessage {
  username: string    // 1-50 characters
  message: string     // 1-500 characters
  channel: string     // 1-50 characters
  timestamp?: number  // Unix timestamp (optional)
}
```

**Returns**: `Promise<ChatResponse>`

```typescript
interface ChatResponse {
  message_id: string
  action: 'allow' | 'warning' | 'timeout' | 'ban'
  reason: string | null
}

// Example usage
const chatMessage = {
  username: "user123",
  message: "Hello everyone!",
  channel: "general",
  timestamp: Date.now()
}

const moderation = await window.serverAPI.processChat(chatMessage)
console.log({
  action: moderation.action,     // "allow"
  reason: moderation.reason      // null
})
```

### Type Definitions

```typescript
// Global type definitions for renderer process
declare global {
  interface Window {
    serverAPI: {
      getPort: () => Promise<number>
      isReady: () => Promise<boolean>
      getApiUrl: () => Promise<string>
      analyze: (text: string) => Promise<AnalyzeResponse>
      processChat: (message: ChatMessage) => Promise<ChatResponse>
    }
  }
}
```

## HTTP API Layer

### Base Configuration

**Server**: `http://127.0.0.1:{dynamic_port}`
**Content-Type**: `application/json`
**CORS Origins**: `["http://localhost:*", "file://*"]`

### Authentication

No authentication required for local desktop application. The server is bound to localhost only and accessible solely from the parent Electron application.

### Health Check Endpoint

#### `GET /health`

Check server status and AI model availability.

**Response**: `200 OK`

```json
{
  "status": "ok",
  "port": 55555,
  "ai_enabled": true,
  "version": "2.0.0"
}
```

**Response Schema**:
```typescript
interface HealthResponse {
  status: 'ok' | 'error'
  port: number              // 1024-65535
  ai_enabled: boolean       // Whether AI models are loaded
  version: string           // API version (semver)
}
```

### Content Analysis Endpoints

#### `POST /analyze`

Perform comprehensive AI analysis of text content.

**Request Body**:
```json
{
  "text": "Content to analyze",
  "options": {}  // Optional parameters (reserved for future use)
}
```

**Request Schema**:
```typescript
interface AnalyzeRequest {
  text: string              // 1-1000 characters
  options?: Record<string, any>  // Optional analysis parameters
}
```

**Response**: `200 OK`

```json
{
  "text": "Content to analyze",
  "toxic": false,
  "toxicity_score": 0.1,
  "sentiment": "neutral",
  "confidence": 0.75,
  "ai_enabled": true
}
```

**Response Schema**:
```typescript
interface AnalyzeResponse {
  text: string
  toxic: boolean            // Whether content is classified as toxic
  toxicity_score: number    // Toxicity confidence score (0-1)
  sentiment: 'positive' | 'negative' | 'neutral'
  confidence: number        // Sentiment analysis confidence (0-1)
  ai_enabled: boolean       // Whether AI models were used
}
```

**Error Responses**:

`422 Unprocessable Entity` - Validation Error:
```json
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

`500 Internal Server Error` - Server Error:
```json
{
  "detail": "AI model inference failed",
  "error_code": "MODEL_ERROR",
  "timestamp": "2025-08-12T10:30:00Z"
}
```

#### Examples

**Positive Content Analysis**:
```bash
curl -X POST http://127.0.0.1:55555/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "This is amazing content!"}'

# Response:
{
  "text": "This is amazing content!",
  "toxic": false,
  "toxicity_score": 0.05,
  "sentiment": "positive",
  "confidence": 0.95,
  "ai_enabled": true
}
```

**Toxic Content Analysis**:
```bash
curl -X POST http://127.0.0.1:55555/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "You are stupid and worthless"}'

# Response:
{
  "text": "You are stupid and worthless",
  "toxic": true,
  "toxicity_score": 0.85,
  "sentiment": "negative",
  "confidence": 0.92,
  "ai_enabled": true
}
```

### Chat Moderation Endpoints

#### `POST /chat/process`

Process and moderate chat messages with AI-powered analysis.

**Request Body**:
```json
{
  "username": "user123",
  "message": "Hello everyone!",
  "channel": "general",
  "timestamp": 1692345600
}
```

**Request Schema**:
```typescript
interface ChatRequest {
  username: string    // 1-50 characters
  message: string     // 1-500 characters
  channel: string     // 1-50 characters
  timestamp?: number  // Unix timestamp (optional)
}
```

**Response**: `200 OK`

```json
{
  "message_id": "msg_abc123",
  "action": "allow",
  "reason": null
}
```

**Response Schema**:
```typescript
interface ChatResponse {
  message_id: string                    // Unique message identifier
  action: 'allow' | 'warning' | 'timeout' | 'ban'
  reason: string | null                 // Explanation for moderation action
}
```

**Moderation Actions**:
- `allow`: Message is safe, no action needed
- `warning`: Minor issues detected, warn user
- `timeout`: Moderate toxicity, temporary restriction
- `ban`: High toxicity, permanent restriction

### System Control Endpoints

#### `POST /shutdown`

Gracefully shutdown the Python backend server.

**Response**: `200 OK`

```json
{
  "status": "shutting down"
}
```

## AI Model Integration APIs

### Model Management

The AI system uses a singleton pattern for model management with lazy loading:

```python
# Internal API - not directly accessible
from server.services.ai_manager import ai_manager

# Get toxicity detection model
toxicity_model = ai_manager.get_toxicity_model()

# Get sentiment analysis model  
sentiment_model = ai_manager.get_sentiment_model()

# Get emotion detection model (optional)
emotion_model = ai_manager.get_emotion_model()
```

### Service Layer APIs

#### Toxicity Service

```python
from server.services.toxicity_service import toxicity_service

result = await toxicity_service.analyze("text to check")
# Returns:
{
  "toxic": boolean,
  "score": float,           # 0.0 - 1.0
  "severity": str,          # "none", "low", "medium", "high", "extreme"
  "label": str,             # Model-specific label
  "action": str             # "allow", "warning", "timeout", "ban"
}
```

#### Sentiment Service

```python
from server.services.sentiment_service import sentiment_service

result = await sentiment_service.analyze_sentiment("text to analyze")
# Returns:
{
  "sentiment": str,         # "positive", "negative", "neutral"
  "stars": int,             # 1-5 star rating
  "confidence": float       # 0.0 - 1.0
}
```

## Error Handling

### Error Response Format

All HTTP endpoints follow RFC 7807 Problem Details standard:

```json
{
  "detail": "Human-readable error description",
  "error_code": "MACHINE_READABLE_CODE",
  "timestamp": "2025-08-12T10:30:00Z"
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 422 | Request validation failed |
| `MODEL_NOT_LOADED` | 503 | AI models not available |
| `TEXT_TOO_LONG` | 422 | Input text exceeds length limit |
| `ANALYSIS_FAILED` | 500 | AI inference error |
| `SERVER_OVERLOADED` | 503 | Too many concurrent requests |

### Error Propagation Chain

```
Python Exception → FastAPI Error Handler → HTTP Response → 
Electron HTTP Client → IPC Response → React Error Boundary
```

## Rate Limiting and Performance

### Current Limitations

- **No explicit rate limiting** (single-user desktop application)
- **Sequential request processing** (no request batching)
- **CPU-bound inference** (no GPU acceleration)

### Performance Characteristics

| Operation | Typical Latency | Notes |
|-----------|----------------|-------|
| Health check | 5-10ms | Simple status response |
| Toxicity analysis | 100-300ms | BERT model inference |
| Sentiment analysis | 50-150ms | DistilBERT model |
| Combined analysis | 200-500ms | Both models in sequence |

### Memory Usage

| Component | Memory Usage | Notes |
|-----------|--------------|-------|
| Loaded models | 2-4GB | BERT-based transformers |
| FastAPI server | 100-200MB | Python runtime |
| Request processing | 50-100MB | Per concurrent request |

## API Versioning

### Current Version: 2.0.0

**Versioning Strategy**:
- Embedded in API responses and OpenAPI specification
- No URL versioning (single embedded server)
- Breaking changes require full application update

**Version Information**:
```json
{
  "api_version": "2.0.0",
  "models": {
    "toxicity": "unitary/toxic-bert",
    "sentiment": "distilbert-base-uncased-finetuned-sst-2-english"
  },
  "features": [
    "toxicity_detection",
    "sentiment_analysis", 
    "chat_moderation"
  ]
}
```

## OpenAPI Specification

The complete API specification is available in `../../openapi.yaml` and at the interactive documentation endpoint:

**Swagger UI**: `http://127.0.0.1:{port}/docs`
**ReDoc**: `http://127.0.0.1:{port}/redoc`
**OpenAPI JSON**: `http://127.0.0.1:{port}/openapi.json`

## Security Considerations

### API Security

**Local-Only Access**:
- Server bound to `127.0.0.1` (localhost)
- No external network exposure
- Process-level isolation

**Input Validation**:
- Pydantic models validate all inputs
- Text length limits prevent abuse
- Type checking at multiple layers

**CORS Configuration**:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:*", "file://*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Best Practices

**Client Implementation**:
- Always handle API errors gracefully
- Implement timeout and retry logic
- Validate responses on client side
- Use TypeScript for type safety

**Example Error Handling**:
```typescript
async function safeAnalyze(text: string): Promise<AnalyzeResponse | null> {
  try {
    const result = await window.serverAPI.analyze(text)
    return result
  } catch (error) {
    console.error('Analysis failed:', error)
    
    // Fallback to client-side analysis
    return {
      text,
      toxic: false,
      toxicity_score: 0,
      sentiment: 'neutral',
      confidence: 0,
      ai_enabled: false
    }
  }
}
```

## Integration Examples

### React Hook Integration

```typescript
// Custom hook for server communication
import { useState, useCallback } from 'react'

export function useAIAnalysis() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const analyze = useCallback(async (text: string) => {
    setLoading(true)
    setError(null)
    
    try {
      const result = await window.serverAPI.analyze(text)
      return result
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed')
      throw err
    } finally {
      setLoading(false)
    }
  }, [])
  
  return { analyze, loading, error }
}
```

### Batch Processing Pattern

```typescript
// Process multiple texts efficiently
async function batchAnalyze(texts: string[]): Promise<AnalyzeResponse[]> {
  const results = await Promise.all(
    texts.map(text => window.serverAPI.analyze(text))
  )
  return results
}
```

### Real-time Chat Integration

```typescript
// Real-time chat moderation
class ChatModerator {
  async processMessage(message: ChatMessage): Promise<boolean> {
    try {
      const result = await window.serverAPI.processChat(message)
      
      switch (result.action) {
        case 'allow':
          return true
        case 'warning':
          this.sendWarning(message.username, result.reason)
          return true
        case 'timeout':
          this.timeoutUser(message.username, result.reason)
          return false
        case 'ban':
          this.banUser(message.username, result.reason)
          return false
      }
    } catch (error) {
      console.error('Moderation failed:', error)
      return true // Allow on error (fail-open)
    }
  }
}
```

This comprehensive API reference provides all the information needed to integrate with and extend the Open Stream AI analysis capabilities while maintaining the security and performance characteristics of the desktop application architecture.