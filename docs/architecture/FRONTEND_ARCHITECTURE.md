# Frontend Architecture Guidelines

## Overview

Open Stream's frontend architecture follows a modern, scalable pattern designed to support complex AI-powered desktop applications. This document outlines the architectural principles, patterns, and structure that enable maintainable and performant development.

## Architectural Principles

### 1. Separation of Concerns

```
Presentation Layer → Business Logic Layer → Data Layer → IPC Layer
     (Components)      (Hooks & Context)    (Utils)    (Electron IPC)
```

### 2. Unidirectional Data Flow

```
User Interaction → Hook State Update → Context/Provider → Component Re-render
                                    ↓
               Server Communication ← IPC Bridge ← Electron Main Process
```

### 3. Component Hierarchy

```
App (Root)
├── Providers (Global State)
├── Layout Components
├── Feature Components
│   ├── Smart Components (Logic)
│   └── Dumb Components (UI)
└── Utility Components
```

## File Structure Organization

### Current Structure (Post-Refactoring)

```
src/renderer/src/
├── App.tsx                 # Root component with providers
├── main.tsx               # React DOM entry point
├── env.d.ts               # Environment type definitions
│
├── providers/             # Global state management
│   ├── analysis-provider.tsx
│   ├── server-provider.tsx
│   ├── theme-provider.tsx
│   └── index.ts
│
├── hooks/                 # Custom React hooks
│   ├── useServer.ts       # Server communication hook
│   ├── useAnalysis.ts     # Analysis logic hook
│   ├── useLocalStorage.ts # Local storage management
│   └── index.ts
│
├── utils/                 # Pure utility functions
│   ├── analysis.ts        # Analysis data processing
│   ├── validation.ts      # Input validation
│   ├── formatting.ts      # Text formatting utilities
│   └── index.ts
│
├── components/            # Reusable UI components
│   ├── ui/               # Basic building blocks
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── loading-spinner.tsx
│   │   ├── error-alert.tsx
│   │   └── index.ts
│   │
│   ├── features/         # Feature-specific components
│   │   ├── analysis/
│   │   │   ├── analysis-container.tsx
│   │   │   ├── toxicity-result.tsx
│   │   │   ├── sentiment-result.tsx
│   │   │   ├── emotion-result.tsx
│   │   │   └── index.ts
│   │   │
│   │   ├── input/
│   │   │   ├── text-input.tsx
│   │   │   ├── input-controls.tsx
│   │   │   ├── input-metadata.tsx
│   │   │   └── index.ts
│   │   │
│   │   └── server/
│   │       ├── server-status.tsx
│   │       ├── connection-indicator.tsx
│   │       ├── debug-panel.tsx
│   │       └── index.ts
│   │
│   ├── layout/           # Layout and structural components
│   │   ├── app-layout.tsx
│   │   ├── main-container.tsx
│   │   ├── header.tsx
│   │   └── index.ts
│   │
│   └── index.ts          # Main component exports
│
├── lib/                  # External library configurations
│   ├── utils.ts          # Tailwind CSS utility (cn function)
│   └── constants.ts      # Application constants
│
└── assets/               # Static assets
    ├── main.css          # Tailwind CSS configuration
    ├── electron.svg
    └── wavy-lines.svg
```

### Feature-Based Organization

#### Analysis Feature Module

```
components/features/analysis/
├── analysis-container.tsx     # Main analysis coordinator
├── analysis-input.tsx         # Text input with validation
├── analysis-results.tsx       # Results display wrapper
├── toxicity-result.tsx        # Toxicity analysis display
├── sentiment-result.tsx       # Sentiment analysis display
├── emotion-result.tsx         # Emotion analysis display
├── loading-skeleton.tsx       # Loading state placeholder
├── error-fallback.tsx         # Error state display
├── types.ts                   # Feature-specific types
└── index.ts                   # Feature exports
```

#### Server Communication Module

```
components/features/server/
├── server-status.tsx          # Server connection status
├── connection-indicator.tsx   # Visual connection state
├── initialization-screen.tsx  # Server startup screen
├── debug-panel.tsx           # Development debugging tools
├── retry-controls.tsx        # Connection retry interface
└── index.ts
```

## Provider Pattern Implementation

### 1. Context Architecture

```typescript
// providers/analysis-provider.tsx
interface AnalysisContextType {
  // State
  currentAnalysis: AnalysisResult | null
  analysisHistory: AnalysisResult[]
  isAnalyzing: boolean
  
  // Actions
  analyzeText: (text: string) => Promise<void>
  clearHistory: () => void
  clearCurrentAnalysis: () => void
  
  // Configuration
  settings: AnalysisSettings
  updateSettings: (settings: Partial<AnalysisSettings>) => void
}

const AnalysisContext = createContext<AnalysisContextType | null>(null)

export const AnalysisProvider: React.FC<{ children: React.ReactNode }> = ({ 
  children 
}) => {
  const [currentAnalysis, setCurrentAnalysis] = useState<AnalysisResult | null>(null)
  const [analysisHistory, setAnalysisHistory] = useState<AnalysisResult[]>([])
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [settings, setSettings] = useState<AnalysisSettings>(defaultSettings)
  
  const { analyzeText: serverAnalyzeText } = useServer()
  
  const analyzeText = useCallback(async (text: string) => {
    setIsAnalyzing(true)
    try {
      const result = await serverAnalyzeText(text)
      setCurrentAnalysis(result)
      setAnalysisHistory(prev => [result, ...prev.slice(0, 49)]) // Keep last 50
    } catch (error) {
      console.error('Analysis failed:', error)
      throw error
    } finally {
      setIsAnalyzing(false)
    }
  }, [serverAnalyzeText])
  
  const contextValue = useMemo(() => ({
    currentAnalysis,
    analysisHistory,
    isAnalyzing,
    analyzeText,
    clearHistory: () => setAnalysisHistory([]),
    clearCurrentAnalysis: () => setCurrentAnalysis(null),
    settings,
    updateSettings: (newSettings: Partial<AnalysisSettings>) => 
      setSettings(prev => ({ ...prev, ...newSettings }))
  }), [currentAnalysis, analysisHistory, isAnalyzing, analyzeText, settings])
  
  return (
    <AnalysisContext.Provider value={contextValue}>
      {children}
    </AnalysisContext.Provider>
  )
}

export const useAnalysis = () => {
  const context = useContext(AnalysisContext)
  if (!context) {
    throw new Error('useAnalysis must be used within AnalysisProvider')
  }
  return context
}
```

### 2. Provider Composition

```typescript
// providers/index.tsx
import { ServerProvider } from './server-provider'
import { AnalysisProvider } from './analysis-provider'
import { ThemeProvider } from './theme-provider'

export const AppProviders: React.FC<{ children: React.ReactNode }> = ({ 
  children 
}) => {
  return (
    <ServerProvider>
      <AnalysisProvider>
        <ThemeProvider>
          {children}
        </ThemeProvider>
      </AnalysisProvider>
    </ServerProvider>
  )
}

// App.tsx integration
export default function App() {
  return (
    <AppProviders>
      <AppLayout>
        <MainContainer />
      </AppLayout>
    </AppProviders>
  )
}
```

## State Management Principles

### 1. State Categorization

```typescript
// Local Component State (useState)
const ComponentWithLocalState = () => {
  const [inputValue, setInputValue] = useState('')
  const [isExpanded, setIsExpanded] = useState(false)
  // UI state that doesn't need to be shared
}

// Feature State (Context)
const FeatureWithSharedState = () => {
  const { currentAnalysis, analyzeText } = useAnalysis()
  // Business logic state shared across feature
}

// Global State (Top-level Context)
const GlobalStateComponent = () => {
  const { isConnected, serverStatus } = useServer()
  // Application-wide state
}

// Derived State (useMemo)
const DerivedStateComponent = ({ data }: { data: RawData[] }) => {
  const processedData = useMemo(() => {
    return data.filter(item => item.isValid).map(transformData)
  }, [data])
  // Computed values based on props or state
}
```

### 2. State Updates Pattern

```typescript
// Optimistic Updates
const optimisticAnalysis = useCallback(async (text: string) => {
  // 1. Set optimistic state immediately
  const optimisticResult = createOptimisticResult(text)
  setCurrentAnalysis(optimisticResult)
  
  try {
    // 2. Perform async operation
    const realResult = await analyzeText(text)
    
    // 3. Replace with real data
    setCurrentAnalysis(realResult)
  } catch (error) {
    // 4. Revert on error
    setCurrentAnalysis(null)
    throw error
  }
}, [analyzeText])

// Batched Updates with Transitions
const batchedUpdate = useCallback(() => {
  startTransition(() => {
    // Multiple state updates batched together
    setResults(newResults)
    setMetadata(newMetadata)
    setStatus('complete')
  })
}, [])
```

## Component Architecture Rules

### 1. Container/Presentational Pattern

```typescript
// Container Component (Logic)
const AnalysisContainer = () => {
  const { currentAnalysis, analyzeText, isAnalyzing } = useAnalysis()
  const [inputText, setInputText] = useState('')
  const [error, setError] = useState<string | null>(null)
  
  const handleAnalyze = useCallback(async () => {
    if (!inputText.trim()) return
    
    setError(null)
    try {
      await analyzeText(inputText)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed')
    }
  }, [inputText, analyzeText])
  
  return (
    <AnalysisPresentation
      inputText={inputText}
      onInputChange={setInputText}
      currentAnalysis={currentAnalysis}
      isAnalyzing={isAnalyzing}
      error={error}
      onAnalyze={handleAnalyze}
    />
  )
}

// Presentational Component (UI)
interface AnalysisPresentationProps {
  inputText: string
  onInputChange: (text: string) => void
  currentAnalysis: AnalysisResult | null
  isAnalyzing: boolean
  error: string | null
  onAnalyze: () => void
}

const AnalysisPresentation = memo<AnalysisPresentationProps>(({
  inputText,
  onInputChange,
  currentAnalysis,
  isAnalyzing,
  error,
  onAnalyze
}) => {
  return (
    <div className="analysis-presentation">
      <TextInput
        value={inputText}
        onChange={onInputChange}
        placeholder="Enter text to analyze..."
        disabled={isAnalyzing}
      />
      
      <AnalysisControls
        onAnalyze={onAnalyze}
        disabled={!inputText.trim() || isAnalyzing}
        loading={isAnalyzing}
      />
      
      {error && <ErrorAlert error={error} />}
      
      {currentAnalysis && (
        <AnalysisResults result={currentAnalysis} />
      )}
    </div>
  )
})
```

### 2. Composition Patterns

```typescript
// Compound Component Pattern
const Analysis = {
  Container: AnalysisContainer,
  Input: AnalysisInput,
  Results: AnalysisResults,
  Controls: AnalysisControls
}

// Usage
const App = () => (
  <Analysis.Container>
    <Analysis.Input />
    <Analysis.Controls />
    <Analysis.Results />
  </Analysis.Container>
)

// Render Props Pattern
const DataFetcher = ({ 
  children 
}: { 
  children: (data: Data, loading: boolean, error: string | null) => React.ReactNode 
}) => {
  const [data, setData] = useState<Data | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // Fetch logic...
  
  return children(data, loading, error)
}

// Usage
<DataFetcher>
  {(data, loading, error) => (
    <>
      {loading && <LoadingSpinner />}
      {error && <ErrorAlert error={error} />}
      {data && <DataDisplay data={data} />}
    </>
  )}
</DataFetcher>
```

## Performance Architecture

### 1. Code Splitting Strategy

```typescript
// Route-based splitting (future enhancement)
const AnalysisPage = lazy(() => import('./pages/analysis'))
const SettingsPage = lazy(() => import('./pages/settings'))
const HistoryPage = lazy(() => import('./pages/history'))

// Component-based splitting
const HeavyComponent = lazy(() => import('./components/heavy-component'))

// Feature-based splitting
const AdvancedAnalysis = lazy(() => 
  import('./features/advanced-analysis').then(module => ({
    default: module.AdvancedAnalysis
  }))
)
```

### 2. Memoization Strategy

```typescript
// Component-level memoization
const ExpensiveComponent = memo(({ data, filters }) => {
  // Expensive rendering logic
}, (prevProps, nextProps) => {
  // Custom comparison function
  return prevProps.data === nextProps.data && 
         prevProps.filters === nextProps.filters
})

// Value memoization
const ProcessedResults = ({ rawResults, filters }) => {
  const processedResults = useMemo(() => {
    return rawResults
      .filter(result => filters.includes(result.type))
      .map(result => enhanceResult(result))
      .sort((a, b) => b.score - a.score)
  }, [rawResults, filters])
  
  return <ResultsList results={processedResults} />
}

// Callback memoization
const InteractiveList = ({ items, onItemUpdate }) => {
  const handleItemClick = useCallback((itemId: string) => {
    return () => {
      const item = items.find(i => i.id === itemId)
      if (item) {
        onItemUpdate(item)
      }
    }
  }, [items, onItemUpdate])
  
  return (
    <div>
      {items.map(item => (
        <ListItem 
          key={item.id} 
          item={item} 
          onClick={handleItemClick(item.id)}
        />
      ))}
    </div>
  )
}
```

## Error Handling Architecture

### 1. Error Boundary Strategy

```typescript
// Global Error Boundary
class GlobalErrorBoundary extends Component<
  { children: React.ReactNode },
  { hasError: boolean; error: Error | null }
> {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }
  
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error }
  }
  
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log to error reporting service
    console.error('Global error:', error, errorInfo)
    
    // Report to analytics
    this.reportError(error, errorInfo)
  }
  
  reportError(error: Error, errorInfo: ErrorInfo) {
    // Error reporting logic
  }
  
  render() {
    if (this.state.hasError) {
      return <GlobalErrorFallback error={this.state.error} />
    }
    
    return this.props.children
  }
}

// Feature-specific Error Boundaries
const AnalysisErrorBoundary = ({ children }) => (
  <ErrorBoundary
    fallback={<AnalysisErrorFallback />}
    onError={(error, errorInfo) => {
      console.error('Analysis error:', error, errorInfo)
    }}
  >
    {children}
  </ErrorBoundary>
)
```

### 2. Async Error Handling

```typescript
// Hook for async error handling
const useAsyncError = () => {
  const [_, setError] = useState()
  
  return useCallback((error: Error) => {
    setError(() => {
      throw error
    })
  }, [])
}

// Usage in components
const AsyncComponent = () => {
  const throwError = useAsyncError()
  
  const handleAsyncOperation = useCallback(async () => {
    try {
      await riskyAsyncOperation()
    } catch (error) {
      throwError(error) // This will be caught by error boundary
    }
  }, [throwError])
  
  return <button onClick={handleAsyncOperation}>Risky Operation</button>
}
```

## Integration with Electron IPC

### 1. IPC Communication Pattern

```typescript
// Preload script type definitions
interface ServerAPI {
  analyze: (text: string) => Promise<AnalysisResult>
  isReady: () => Promise<boolean>
  getPort: () => Promise<number>
  getApiUrl: () => Promise<string>
  processChat: (message: ChatMessage) => Promise<ChatResponse>
}

declare global {
  interface Window {
    serverAPI: ServerAPI
  }
}

// Hook for server communication
const useServer = () => {
  const [serverState, setServerState] = useState<ServerState>(initialState)
  
  const checkServerStatus = useCallback(async () => {
    try {
      const isReady = await window.serverAPI.isReady()
      const port = await window.serverAPI.getPort()
      
      setServerState(prev => ({
        ...prev,
        isReady,
        port,
        error: null
      }))
    } catch (error) {
      setServerState(prev => ({
        ...prev,
        error: error.message,
        isReady: false
      }))
    }
  }, [])
  
  return {
    ...serverState,
    analyzeText: window.serverAPI.analyze,
    checkStatus: checkServerStatus
  }
}
```

## Migration Strategy (From Monolithic App.tsx)

### Phase 1: Extract Providers

```typescript
// Before: Everything in App.tsx
export default function App() {
  const [serverState, setServerState] = useState(...)
  const [analysisState, setAnalysisState] = useState(...)
  // 500+ lines of mixed concerns
}

// After: Separated providers
export default function App() {
  return (
    <AppProviders>
      <AppLayout>
        <AnalysisContainer />
      </AppLayout>
    </AppProviders>
  )
}
```

### Phase 2: Extract Hooks

```typescript
// Before: Inline logic in components
const Component = () => {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState(null)
  // Repeated logic across components
}

// After: Custom hooks
const Component = () => {
  const { data, loading, error, refetch } = useAnalysis()
  // Reusable logic
}
```

### Phase 3: Extract Components

```typescript
// Before: Monolithic render method
return (
  <div className="container">
    {/* 100+ lines of JSX */}
  </div>
)

// After: Composed components
return (
  <AppLayout>
    <AnalysisInput />
    <AnalysisResults />
    <ServerStatus />
  </AppLayout>
)
```

## Best Practices Summary

### ✅ Architecture Do's

1. **Single Responsibility**: Each component has one clear purpose
2. **Dependency Injection**: Pass dependencies through props or context
3. **Composition over Inheritance**: Use composition patterns
4. **Predictable State Flow**: Clear data flow patterns
5. **Error Boundaries**: Isolate error handling
6. **Performance Optimization**: Strategic memoization and code splitting

### ❌ Architecture Don'ts

1. **Prop Drilling**: Don't pass props through many levels
2. **Tight Coupling**: Components shouldn't depend on specific implementations
3. **Mixed Concerns**: Don't mix UI and business logic
4. **Global State Abuse**: Not everything needs to be in context
5. **Premature Optimization**: Don't optimize without measuring
6. **Complex Hierarchies**: Keep component trees manageable

This frontend architecture provides a solid foundation for scaling the Open Stream application while maintaining code quality, performance, and developer experience.