# TypeScript Guidelines

## Overview

Open Stream leverages TypeScript 5.8.3 for type safety, enhanced developer experience, and maintainable code. This guide covers TypeScript best practices, patterns, and conventions specific to the React + Electron + Python architecture.

## Configuration and Setup

### TypeScript Configuration

The project uses multiple TypeScript configurations for different environments:

```json
// tsconfig.json (root)
{
  "files": [],
  "references": [
    { "path": "./tsconfig.node.json" },
    { "path": "./tsconfig.web.json" }
  ],
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/renderer/src/*"]
    }
  }
}

// tsconfig.web.json (renderer process)
{
  "extends": "@electron-toolkit/tsconfig/tsconfig.web.json",
  "include": ["src/renderer/src/**/*"],
  "compilerOptions": {
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "exactOptionalPropertyTypes": true
  }
}

// tsconfig.node.json (main/preload processes)
{
  "extends": "@electron-toolkit/tsconfig/tsconfig.node.json",
  "include": ["src/main/**/*", "src/preload/**/*"],
  "compilerOptions": {
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true
  }
}
```

### Path Mapping

```typescript
// Configured in tsconfig.json
{
  "baseUrl": ".",
  "paths": {
    "@/*": ["src/renderer/src/*"],
    "@/components/*": ["src/renderer/src/components/*"],
    "@/hooks/*": ["src/renderer/src/hooks/*"],
    "@/utils/*": ["src/renderer/src/utils/*"],
    "@/lib/*": ["src/renderer/src/lib/*"],
    "@/types/*": ["src/renderer/src/types/*"]
  }
}

// Usage in imports
import { Button } from '@/components/ui/button'
import { useServer } from '@/hooks/useServer'
import { cn } from '@/lib/utils'
import type { AnalysisResult } from '@/types/analysis'
```

## Type Definition Standards

### 1. Interface Design Patterns

#### Component Props Interfaces

```typescript
// Good: Descriptive interface with clear hierarchy
interface AnalysisResultProps {
  // Required props first
  result: AnalysisResult
  
  // Optional props with defaults indicated
  showMetadata?: boolean
  variant?: 'compact' | 'detailed'
  
  // Event handlers
  onRetry?: () => void
  onExport?: (result: AnalysisResult) => void
  
  // Standard React props
  className?: string
  children?: React.ReactNode
}

// Better: Use discriminated unions for complex variants
interface AnalysisResultBaseProps {
  result: AnalysisResult
  className?: string
}

interface CompactAnalysisProps extends AnalysisResultBaseProps {
  variant: 'compact'
  showMetadata?: false
}

interface DetailedAnalysisProps extends AnalysisResultBaseProps {
  variant: 'detailed'
  showMetadata: boolean
  onExport: (result: AnalysisResult) => void
}

type AnalysisResultProps = CompactAnalysisProps | DetailedAnalysisProps
```

#### Domain Model Interfaces

```typescript
// Analysis domain types
interface AnalysisResult {
  readonly id: string
  readonly text: string
  readonly timestamp: number
  readonly processing_time_ms: number
  
  // Core analysis results
  readonly toxic: boolean
  readonly toxicity_score: number
  readonly sentiment: SentimentType
  readonly sentiment_score: number
  
  // Optional analyses
  readonly emotions?: EmotionScores
  readonly hate_speech?: boolean
  readonly hate_speech_score?: number
  readonly language_detected?: string
  
  // Model metadata
  readonly ai_enabled: boolean
  readonly model_versions: ModelVersions
  
  // Legacy compatibility (marked as deprecated)
  /** @deprecated Use toxicity_score instead */
  readonly confidence?: number
  /** @deprecated Use emotions object instead */
  readonly emotion?: string
}

// Supporting types with strict definitions
type SentimentType = 'positive' | 'negative' | 'neutral'

interface EmotionScores {
  readonly joy: number
  readonly sadness: number
  readonly anger: number
  readonly fear: number
  readonly surprise: number
  readonly disgust: number
}

interface ModelVersions {
  readonly toxicity: string
  readonly sentiment: string
  readonly emotion?: string
}

// Server communication types
interface AnalyzeRequest {
  readonly text: string
  readonly priority?: number
}

interface AnalyzeResponse {
  readonly success: boolean
  readonly data?: AnalysisResult
  readonly error?: string
}
```

### 2. Generic Type Patterns

#### Utility Types

```typescript
// API response wrapper
interface ApiResponse<T> {
  readonly success: boolean
  readonly data?: T
  readonly error?: string
  readonly timestamp: number
}

// Hook state pattern
interface AsyncState<T, E = string> {
  readonly data: T | null
  readonly loading: boolean
  readonly error: E | null
}

// Event handler patterns
type EventHandler<T = void> = (data: T) => void
type AsyncEventHandler<T = void> = (data: T) => Promise<void>

// Component factory pattern
interface ComponentFactory<T extends Record<string, any>> {
  create: <K extends keyof T>(type: K, props: T[K]) => React.ReactElement
}

// Usage examples
type AnalysisApiResponse = ApiResponse<AnalysisResult>
type ServerState = AsyncState<ServerInfo>
type OnAnalysisComplete = EventHandler<AnalysisResult>
```

#### Hook Type Patterns

```typescript
// Custom hook return type pattern
interface UseAnalysisReturn {
  // State
  readonly currentAnalysis: AnalysisResult | null
  readonly history: AnalysisResult[]
  readonly loading: boolean
  readonly error: string | null
  
  // Actions
  readonly analyzeText: (text: string) => Promise<AnalysisResult>
  readonly clearHistory: () => void
  readonly retryLastAnalysis: () => Promise<void>
  
  // Computed values
  readonly canAnalyze: boolean
  readonly hasResults: boolean
}

// Generic hook pattern
interface UseAsyncOperationOptions<T> {
  readonly onSuccess?: (data: T) => void
  readonly onError?: (error: Error) => void
  readonly retry?: boolean
  readonly retryCount?: number
}

interface UseAsyncOperationReturn<T> {
  readonly execute: (...args: any[]) => Promise<T>
  readonly reset: () => void
  readonly state: AsyncState<T>
}

function useAsyncOperation<T>(
  operation: (...args: any[]) => Promise<T>,
  options?: UseAsyncOperationOptions<T>
): UseAsyncOperationReturn<T>
```

### 3. Discriminated Unions

#### State Machine Patterns

```typescript
// Server connection states
type ServerConnectionState = 
  | { status: 'disconnected'; lastError?: string }
  | { status: 'connecting'; attemptNumber: number }
  | { status: 'connected'; port: number; apiUrl: string }
  | { status: 'error'; error: string; canRetry: boolean }

// Analysis states
type AnalysisState =
  | { phase: 'idle' }
  | { phase: 'validating'; text: string }
  | { phase: 'processing'; text: string; progress: number }
  | { phase: 'completed'; result: AnalysisResult }
  | { phase: 'failed'; error: string; text: string }

// UI state patterns
type FormState<T> =
  | { status: 'editing'; data: Partial<T>; errors: Record<keyof T, string[]> }
  | { status: 'submitting'; data: T }
  | { status: 'success'; data: T; result: any }
  | { status: 'error'; data: T; error: string }

// Usage in components
const AnalysisComponent = () => {
  const [analysisState, setAnalysisState] = useState<AnalysisState>({ phase: 'idle' })
  
  const handleStateChange = (newState: AnalysisState) => {
    switch (newState.phase) {
      case 'idle':
        // Handle idle state
        break
      case 'validating':
        // TypeScript knows newState.text is available
        console.log('Validating:', newState.text)
        break
      case 'processing':
        // TypeScript knows both text and progress are available
        console.log('Processing:', newState.text, newState.progress)
        break
      case 'completed':
        // TypeScript knows result is available
        console.log('Completed:', newState.result)
        break
      case 'failed':
        // TypeScript knows error and text are available
        console.log('Failed:', newState.error, newState.text)
        break
      default:
        // TypeScript ensures exhaustive checking
        const _exhaustive: never = newState
        throw new Error(`Unhandled state: ${_exhaustive}`)
    }
  }
}
```

## React-Specific TypeScript Patterns

### 1. Component Type Definitions

#### Functional Components

```typescript
// Basic component with typed props
interface ButtonProps {
  children: React.ReactNode
  variant?: 'primary' | 'secondary' | 'destructive'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  onClick?: () => void
  className?: string
}

const Button: React.FC<ButtonProps> = ({ 
  children, 
  variant = 'primary', 
  size = 'md',
  disabled = false,
  onClick,
  className 
}) => {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={cn(getButtonClasses(variant, size), className)}
    >
      {children}
    </button>
  )
}

// Alternative: More explicit typing without React.FC
const ButtonExplicit = ({ 
  children, 
  variant = 'primary', 
  size = 'md',
  disabled = false,
  onClick,
  className 
}: ButtonProps): JSX.Element => {
  // Implementation
}
```

#### Forwarded Ref Components

```typescript
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  helperText?: string
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helperText, className, ...props }, ref) => {
    return (
      <div className="input-wrapper">
        {label && (
          <label className="input-label" htmlFor={props.id}>
            {label}
          </label>
        )}
        <input
          ref={ref}
          className={cn(
            'input-base',
            { 'input-error': error },
            className
          )}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={error ? `${props.id}-error` : undefined}
          {...props}
        />
        {error && (
          <span id={`${props.id}-error`} className="input-error-text">
            {error}
          </span>
        )}
        {helperText && !error && (
          <span className="input-helper-text">{helperText}</span>
        )}
      </div>
    )
  }
)

Input.displayName = 'Input'
```

#### Higher-Order Components

```typescript
// HOC with proper typing
interface WithLoadingProps {
  loading: boolean
}

function withLoading<P extends object>(
  Component: React.ComponentType<P>
): React.ComponentType<P & WithLoadingProps> {
  return ({ loading, ...props }: P & WithLoadingProps) => {
    if (loading) {
      return <LoadingSpinner />
    }
    
    return <Component {...(props as P)} />
  }
}

// Usage
const AnalysisResults = ({ results }: { results: AnalysisResult[] }) => (
  <div>{/* Results display */}</div>
)

const AnalysisResultsWithLoading = withLoading(AnalysisResults)

// Usage in component
<AnalysisResultsWithLoading 
  results={results} 
  loading={isLoading} 
/>
```

### 2. Hook Typing Patterns

#### Custom Hook Implementation

```typescript
// useServer hook with comprehensive typing
interface ServerState {
  readonly isReady: boolean
  readonly port: number | null
  readonly apiUrl: string | null
  readonly error: string | null
  readonly isChecking: boolean
  readonly serverAPIAvailable: boolean
  readonly isInitializing: boolean
}

interface ServerActions {
  readonly analyzeText: (text: string, priority?: number) => Promise<AnalysisResult>
  readonly processChat: (message: ChatMessage) => Promise<ChatResponse>
  readonly clearCache: () => void
  readonly forceServerCheck: () => void
  readonly retryInitialization: () => Promise<void>
  readonly getCacheStats: () => CacheStats
}

type UseServerReturn = ServerState & ServerActions

function useServer(): UseServerReturn {
  const [state, setState] = useState<ServerState>({
    isReady: false,
    port: null,
    apiUrl: null,
    error: null,
    isChecking: true,
    serverAPIAvailable: false,
    isInitializing: true
  })
  
  // Implementation...
  
  return {
    ...state,
    analyzeText: useCallback(async (text: string, priority = 1) => {
      // Implementation with proper error handling
    }, []),
    processChat: useCallback(async (message: ChatMessage) => {
      // Implementation
    }, []),
    // ... other actions
  }
}
```

#### Generic Hooks

```typescript
// Generic async data fetching hook
interface UseAsyncDataOptions<T> {
  readonly initialData?: T
  readonly onSuccess?: (data: T) => void
  readonly onError?: (error: Error) => void
  readonly dependencies?: React.DependencyList
}

interface UseAsyncDataReturn<T> {
  readonly data: T | null
  readonly loading: boolean
  readonly error: Error | null
  readonly refresh: () => Promise<void>
  readonly mutate: (newData: T | null) => void
}

function useAsyncData<T>(
  fetcher: () => Promise<T>,
  options: UseAsyncDataOptions<T> = {}
): UseAsyncDataReturn<T> {
  const { initialData = null, onSuccess, onError, dependencies = [] } = options
  
  const [data, setData] = useState<T | null>(initialData)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  
  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    
    try {
      const result = await fetcher()
      setData(result)
      onSuccess?.(result)
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error')
      setError(error)
      onError?.(error)
    } finally {
      setLoading(false)
    }
  }, dependencies)
  
  useEffect(() => {
    fetchData()
  }, [fetchData])
  
  const mutate = useCallback((newData: T | null) => {
    setData(newData)
    setError(null)
  }, [])
  
  return {
    data,
    loading,
    error,
    refresh: fetchData,
    mutate
  }
}

// Usage
const { data: analysisHistory, loading, error, refresh } = useAsyncData(
  () => fetch('/api/analysis/history').then(res => res.json() as Promise<AnalysisResult[]>),
  {
    onSuccess: (history) => console.log('Loaded history:', history.length),
    onError: (error) => console.error('Failed to load history:', error)
  }
)
```

### 3. Event Handler Typing

```typescript
// Comprehensive event handler patterns
interface AnalysisInputProps {
  value: string
  onChange: (value: string) => void
  onSubmit: (text: string) => Promise<void>
  onFocus?: () => void
  onBlur?: () => void
  onKeyDown?: (event: React.KeyboardEvent<HTMLTextAreaElement>) => void
}

const AnalysisInput: React.FC<AnalysisInputProps> = ({
  value,
  onChange,
  onSubmit,
  onFocus,
  onBlur,
  onKeyDown
}) => {
  // Internal handlers with proper typing
  const handleChange = useCallback((event: React.ChangeEvent<HTMLTextAreaElement>) => {
    onChange(event.target.value)
  }, [onChange])
  
  const handleKeyDown = useCallback((event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Call external handler first
    onKeyDown?.(event)
    
    // Handle internal logic
    if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
      event.preventDefault()
      onSubmit(value)
    }
  }, [onKeyDown, onSubmit, value])
  
  const handleSubmit = useCallback(async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    await onSubmit(value)
  }, [onSubmit, value])
  
  return (
    <form onSubmit={handleSubmit}>
      <textarea
        value={value}
        onChange={handleChange}
        onFocus={onFocus}
        onBlur={onBlur}
        onKeyDown={handleKeyDown}
        placeholder="Enter text to analyze..."
      />
    </form>
  )
}
```

## Electron-Specific TypeScript

### 1. IPC Type Safety

```typescript
// Preload API definition
interface ServerAPI {
  analyze: (text: string) => Promise<AnalysisResult>
  isReady: () => Promise<boolean>
  getPort: () => Promise<number>
  getApiUrl: () => Promise<string>
  processChat: (message: ChatMessage) => Promise<ChatResponse>
}

interface ElectronAPI {
  openExternal: (url: string) => Promise<void>
  showMessageBox: (options: MessageBoxOptions) => Promise<MessageBoxReturnValue>
  getVersion: () => Promise<string>
}

// Global type definitions
declare global {
  interface Window {
    serverAPI: ServerAPI
    electronAPI: ElectronAPI
  }
}

// Preload script implementation
import { contextBridge, ipcRenderer } from 'electron'

const serverAPI: ServerAPI = {
  analyze: (text: string) => ipcRenderer.invoke('server:analyze', text),
  isReady: () => ipcRenderer.invoke('server:isReady'),
  getPort: () => ipcRenderer.invoke('server:getPort'),
  getApiUrl: () => ipcRenderer.invoke('server:getApiUrl'),
  processChat: (message: ChatMessage) => ipcRenderer.invoke('server:processChat', message)
}

const electronAPI: ElectronAPI = {
  openExternal: (url: string) => ipcRenderer.invoke('electron:openExternal', url),
  showMessageBox: (options) => ipcRenderer.invoke('electron:showMessageBox', options),
  getVersion: () => ipcRenderer.invoke('electron:getVersion')
}

contextBridge.exposeInMainWorld('serverAPI', serverAPI)
contextBridge.exposeInMainWorld('electronAPI', electronAPI)
```

### 2. Main Process Typing

```typescript
// Main process server management
import { ipcMain } from 'electron'
import type { AnalysisResult, ChatMessage, ChatResponse } from '../types'

class ServerManager {
  private port: number | null = null
  private isReady = false
  
  async initialize(): Promise<void> {
    // Server initialization logic
  }
  
  async analyzeText(text: string): Promise<AnalysisResult> {
    if (!this.isReady) {
      throw new Error('Server not ready')
    }
    
    // Analysis implementation
    const response = await fetch(`http://127.0.0.1:${this.port}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    })
    
    if (!response.ok) {
      throw new Error(`Analysis failed: ${response.statusText}`)
    }
    
    return response.json() as Promise<AnalysisResult>
  }
  
  async processChat(message: ChatMessage): Promise<ChatResponse> {
    // Chat processing implementation
  }
}

// IPC handler registration with type safety
const serverManager = new ServerManager()

ipcMain.handle('server:analyze', async (_, text: string): Promise<AnalysisResult> => {
  return serverManager.analyzeText(text)
})

ipcMain.handle('server:isReady', async (): Promise<boolean> => {
  return serverManager.isReady
})

ipcMain.handle('server:getPort', async (): Promise<number> => {
  return serverManager.port ?? 0
})
```

## Error Handling with TypeScript

### 1. Typed Error Classes

```typescript
// Custom error types
abstract class AppError extends Error {
  abstract readonly code: string
  abstract readonly statusCode: number
  
  constructor(message: string, public readonly context?: Record<string, any>) {
    super(message)
    this.name = this.constructor.name
  }
}

class AnalysisError extends AppError {
  readonly code = 'ANALYSIS_ERROR'
  readonly statusCode = 400
}

class ServerConnectionError extends AppError {
  readonly code = 'SERVER_CONNECTION_ERROR'
  readonly statusCode = 503
}

class ValidationError extends AppError {
  readonly code = 'VALIDATION_ERROR'
  readonly statusCode = 422
  
  constructor(
    message: string,
    public readonly field: string,
    context?: Record<string, any>
  ) {
    super(message, context)
  }
}

// Error handling utilities
type ErrorResult<T> = 
  | { success: true; data: T }
  | { success: false; error: AppError }

async function safeAnalyze(text: string): Promise<ErrorResult<AnalysisResult>> {
  try {
    if (!text.trim()) {
      throw new ValidationError('Text cannot be empty', 'text')
    }
    
    const result = await window.serverAPI.analyze(text)
    return { success: true, data: result }
  } catch (error) {
    if (error instanceof AppError) {
      return { success: false, error }
    }
    
    return { 
      success: false, 
      error: new AnalysisError('Unknown analysis error', { originalError: error })
    }
  }
}

// Usage in components
const AnalysisComponent = () => {
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [error, setError] = useState<AppError | null>(null)
  
  const handleAnalyze = async (text: string) => {
    const analysisResult = await safeAnalyze(text)
    
    if (analysisResult.success) {
      setResult(analysisResult.data)
      setError(null)
    } else {
      setError(analysisResult.error)
      setResult(null)
    }
  }
  
  return (
    <div>
      {error && (
        <ErrorDisplay 
          error={error} 
          onRetry={error.code === 'SERVER_CONNECTION_ERROR' ? () => handleAnalyze('') : undefined}
        />
      )}
      {result && <AnalysisResults result={result} />}
    </div>
  )
}
```

### 2. Type Guards and Validation

```typescript
// Type guard functions
function isAnalysisResult(value: unknown): value is AnalysisResult {
  return (
    typeof value === 'object' &&
    value !== null &&
    typeof (value as any).text === 'string' &&
    typeof (value as any).toxic === 'boolean' &&
    typeof (value as any).toxicity_score === 'number' &&
    typeof (value as any).sentiment === 'string' &&
    typeof (value as any).sentiment_score === 'number'
  )
}

function isServerState(value: unknown): value is ServerState {
  return (
    typeof value === 'object' &&
    value !== null &&
    typeof (value as any).isReady === 'boolean' &&
    typeof (value as any).isChecking === 'boolean' &&
    typeof (value as any).serverAPIAvailable === 'boolean'
  )
}

// Runtime validation with Zod (optional enhancement)
import { z } from 'zod'

const AnalysisResultSchema = z.object({
  id: z.string(),
  text: z.string(),
  timestamp: z.number(),
  toxic: z.boolean(),
  toxicity_score: z.number().min(0).max(1),
  sentiment: z.enum(['positive', 'negative', 'neutral']),
  sentiment_score: z.number().min(0).max(1),
  emotions: z.record(z.number()).optional(),
  ai_enabled: z.boolean(),
  processing_time_ms: z.number(),
  model_versions: z.record(z.string())
})

type AnalysisResult = z.infer<typeof AnalysisResultSchema>

// Validation function
function validateAnalysisResult(data: unknown): AnalysisResult {
  try {
    return AnalysisResultSchema.parse(data)
  } catch (error) {
    throw new ValidationError('Invalid analysis result format', 'result', { 
      data, 
      zodError: error 
    })
  }
}
```

## Performance Optimization with TypeScript

### 1. Memoization with Proper Typing

```typescript
// Memoized selectors with TypeScript
interface AppState {
  analysis: {
    current: AnalysisResult | null
    history: AnalysisResult[]
    loading: boolean
  }
  server: {
    isReady: boolean
    error: string | null
  }
}

// Memoized selector functions
const selectCurrentAnalysis = useMemo(
  () => (state: AppState): AnalysisResult | null => state.analysis.current,
  []
)

const selectAnalysisHistory = useMemo(
  () => (state: AppState): AnalysisResult[] => state.analysis.history,
  []
)

const selectToxicResults = useMemo(
  () => (state: AppState): AnalysisResult[] => 
    state.analysis.history.filter(result => result.toxic),
  []
)

// Memoized component with proper typing
interface AnalysisListProps {
  results: AnalysisResult[]
  onResultSelect: (result: AnalysisResult) => void
  filter?: (result: AnalysisResult) => boolean
}

const AnalysisList = memo<AnalysisListProps>(({ 
  results, 
  onResultSelect, 
  filter 
}) => {
  const filteredResults = useMemo(() => {
    return filter ? results.filter(filter) : results
  }, [results, filter])
  
  const handleResultClick = useCallback((result: AnalysisResult) => {
    return () => onResultSelect(result)
  }, [onResultSelect])
  
  return (
    <div className="analysis-list">
      {filteredResults.map(result => (
        <AnalysisResultCard
          key={result.id}
          result={result}
          onClick={handleResultClick(result)}
        />
      ))}
    </div>
  )
}, (prevProps, nextProps) => {
  // Custom comparison for performance
  return (
    prevProps.results === nextProps.results &&
    prevProps.onResultSelect === nextProps.onResultSelect &&
    prevProps.filter === nextProps.filter
  )
})
```

### 2. Lazy Loading and Code Splitting

```typescript
// Lazy-loaded components with proper typing
const LazyAnalysisHistory = lazy(() => 
  import('./components/AnalysisHistory').then(module => ({
    default: module.AnalysisHistory
  }))
)

const LazySettingsPanel = lazy(() => 
  import('./components/SettingsPanel').then(module => ({
    default: module.SettingsPanel
  }))
)

// Lazy hook loading
const useAnalysisHistory = lazy(() => 
  import('./hooks/useAnalysisHistory').then(module => ({
    default: module.useAnalysisHistory
  }))
)

// Dynamic imports with type safety
async function loadAnalysisModule(): Promise<typeof import('./modules/analysis')> {
  return import('./modules/analysis')
}

const AnalysisContainer = () => {
  const [analysisModule, setAnalysisModule] = useState<typeof import('./modules/analysis') | null>(null)
  
  useEffect(() => {
    loadAnalysisModule().then(setAnalysisModule)
  }, [])
  
  if (!analysisModule) {
    return <LoadingSpinner />
  }
  
  return <analysisModule.AnalysisComponent />
}
```

## Testing with TypeScript

### 1. Component Testing Types

```typescript
// Test utilities with proper typing
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi, type MockedFunction } from 'vitest'
import type { AnalysisResult } from '@/types/analysis'

// Mock implementations with typing
const mockAnalyzeText: MockedFunction<(text: string) => Promise<AnalysisResult>> = vi.fn()

const mockServerAPI: typeof window.serverAPI = {
  analyze: mockAnalyzeText,
  isReady: vi.fn().mockResolvedValue(true),
  getPort: vi.fn().mockResolvedValue(55555),
  getApiUrl: vi.fn().mockResolvedValue('http://127.0.0.1:55555'),
  processChat: vi.fn()
}

// Test fixtures with proper typing
const createMockAnalysisResult = (overrides: Partial<AnalysisResult> = {}): AnalysisResult => ({
  id: 'test-id',
  text: 'Test text',
  timestamp: Date.now(),
  toxic: false,
  toxicity_score: 0.1,
  sentiment: 'positive',
  sentiment_score: 0.8,
  ai_enabled: true,
  processing_time_ms: 150,
  model_versions: {
    toxicity: 'v1.0',
    sentiment: 'v1.0'
  },
  ...overrides
})

// Component test with proper typing
describe('AnalysisComponent', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    Object.defineProperty(window, 'serverAPI', {
      value: mockServerAPI,
      writable: true
    })
  })
  
  it('should handle analysis successfully', async () => {
    const mockResult = createMockAnalysisResult({ 
      text: 'Test input',
      toxic: false 
    })
    
    mockAnalyzeText.mockResolvedValue(mockResult)
    
    render(<AnalysisComponent />)
    
    const textInput = screen.getByPlaceholderText(/enter text/i)
    const analyzeButton = screen.getByRole('button', { name: /analyze/i })
    
    fireEvent.change(textInput, { target: { value: 'Test input' } })
    fireEvent.click(analyzeButton)
    
    await waitFor(() => {
      expect(screen.getByText('✅ Safe Content')).toBeInTheDocument()
    })
    
    expect(mockAnalyzeText).toHaveBeenCalledWith('Test input')
  })
})
```

## Best Practices Summary

### ✅ TypeScript Do's

1. **Use strict TypeScript configuration**: Enable all strict mode options
2. **Prefer interfaces over types**: Use interfaces for object shapes
3. **Use discriminated unions**: For complex state modeling
4. **Implement proper error handling**: Custom error classes with context
5. **Type all async operations**: Proper Promise typing
6. **Use generic types**: For reusable components and hooks
7. **Implement type guards**: For runtime type checking
8. **Document with JSDoc**: Add context to complex types

### ❌ TypeScript Don'ts

1. **Don't use `any` type**: Use `unknown` or proper types instead
2. **Don't ignore TypeScript errors**: Fix all type errors before committing
3. **Don't over-engineer types**: Keep types simple and readable
4. **Don't use function overloads unnecessarily**: Prefer union types
5. **Don't ignore null/undefined**: Use strict null checks
6. **Don't mix naming conventions**: Use consistent naming patterns
7. **Don't skip return type annotations**: Be explicit about return types
8. **Don't use `as any` casting**: Use proper type guards instead

This TypeScript guide ensures type safety, maintainability, and excellent developer experience throughout the Open Stream application development process.