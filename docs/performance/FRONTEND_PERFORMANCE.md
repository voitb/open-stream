# Frontend Performance Guidelines

## Overview

Open Stream is an AI-powered desktop application that requires optimal performance for real-time text analysis and smooth user interactions. This guide covers React 19 optimization patterns, memoization strategies, bundle optimization, and performance monitoring techniques.

## React 19 Performance Features

### 1. React Compiler Optimizations

React 19 includes automatic optimizations that reduce the need for manual memoization:

```typescript
// React 19 automatically optimizes these patterns
const AnalysisComponent = ({ data }: { data: AnalysisResult[] }) => {
  // Automatic memoization of calculations
  const processedData = data
    .filter(result => result.toxic)
    .map(result => ({
      ...result,
      severity: result.toxicity_score > 0.8 ? 'high' : 'moderate'
    }))
  
  // Automatic event handler optimization
  const handleResultClick = (result: AnalysisResult) => {
    console.log('Clicked:', result.id)
  }
  
  return (
    <div>
      {processedData.map(result => (
        <ResultCard 
          key={result.id}
          result={result}
          onClick={() => handleResultClick(result)}
        />
      ))}
    </div>
  )
}

// Manual optimization still available when needed
const OptimizedComponent = memo(({ items }: { items: Item[] }) => {
  const expensiveCalculation = useMemo(() => {
    return items.reduce((acc, item) => {
      // Very expensive operation
      return acc + complexCalculation(item)
    }, 0)
  }, [items])
  
  return <div>{expensiveCalculation}</div>
})
```

### 2. Concurrent Features

```typescript
import { startTransition, useDeferredValue, useTransition } from 'react'

// Priority-based updates for better UX
const AnalysisInterface = () => {
  const [inputText, setInputText] = useState('')
  const [results, setResults] = useState<AnalysisResult[]>([])
  const [isPending, startTransition] = useTransition()
  
  // Immediate updates for input responsiveness
  const handleInputChange = (value: string) => {
    setInputText(value) // Urgent update
    
    // Defer non-urgent updates
    startTransition(() => {
      // This won't block the input
      updateSearchResults(value)
    })
  }
  
  // Deferred value for expensive operations
  const deferredQuery = useDeferredValue(inputText)
  
  useEffect(() => {
    if (deferredQuery) {
      // This will be deferred when user is typing
      performExpensiveSearch(deferredQuery)
    }
  }, [deferredQuery])
  
  return (
    <div>
      <input 
        value={inputText}
        onChange={(e) => handleInputChange(e.target.value)}
        placeholder="Type to search..."
      />
      {isPending && <div>Searching...</div>}
      <ResultsList results={results} />
    </div>
  )
}
```

### 3. Server Components (Future Enhancement)

```typescript
// When upgrading to server components
async function AnalysisHistoryPage() {
  // This runs on the server, reducing client bundle
  const analysisHistory = await fetchAnalysisHistory()
  
  return (
    <div>
      <h1>Analysis History</h1>
      <AnalysisHistoryClient initialData={analysisHistory} />
    </div>
  )
}

// Client component for interactivity
'use client'
const AnalysisHistoryClient = ({ initialData }: { initialData: AnalysisResult[] }) => {
  const [filter, setFilter] = useState('')
  
  const filteredHistory = useMemo(() => {
    return initialData.filter(result => 
      result.text.toLowerCase().includes(filter.toLowerCase())
    )
  }, [initialData, filter])
  
  return (
    <div>
      <input 
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        placeholder="Filter history..."
      />
      <HistoryList results={filteredHistory} />
    </div>
  )
}
```

## Memoization Strategies

### 1. Strategic Component Memoization

```typescript
// Expensive components that benefit from memoization
const AnalysisResultCard = memo<{
  result: AnalysisResult
  onEdit: (id: string) => void
  onDelete: (id: string) => void
}>(({ result, onEdit, onDelete }) => {
  // Expensive calculations
  const analysisMetrics = useMemo(() => {
    return {
      confidenceLevel: calculateConfidence(result),
      riskAssessment: assessRisk(result),
      recommendations: generateRecommendations(result)
    }
  }, [result])
  
  // Memoized event handlers
  const handleEdit = useCallback(() => {
    onEdit(result.id)
  }, [onEdit, result.id])
  
  const handleDelete = useCallback(() => {
    onDelete(result.id)
  }, [onDelete, result.id])
  
  return (
    <div className="analysis-card">
      <div className="metrics">
        <MetricsDisplay metrics={analysisMetrics} />
      </div>
      <div className="actions">
        <button onClick={handleEdit}>Edit</button>
        <button onClick={handleDelete}>Delete</button>
      </div>
    </div>
  )
}, (prevProps, nextProps) => {
  // Custom comparison for complex objects
  return (
    prevProps.result.id === nextProps.result.id &&
    prevProps.result.timestamp === nextProps.result.timestamp &&
    prevProps.onEdit === nextProps.onEdit &&
    prevProps.onDelete === nextProps.onDelete
  )
})

// Light components that don't need memoization
const SimpleButton = ({ children, onClick }: { 
  children: React.ReactNode
  onClick: () => void 
}) => {
  return (
    <button onClick={onClick} className="simple-button">
      {children}
    </button>
  )
}
```

### 2. Hook Optimization

```typescript
// Optimized custom hooks
const useAnalysisProcessor = (rawResults: AnalysisResult[]) => {
  // Memoize expensive transformations
  const processedResults = useMemo(() => {
    return rawResults.map(result => ({
      ...result,
      // Expensive calculations
      sentiment_confidence: calculateSentimentConfidence(result),
      toxicity_level: categorizeToxicity(result.toxicity_score),
      threat_score: calculateThreatScore(result),
      summary: generateSummary(result)
    }))
  }, [rawResults])
  
  // Memoize filtered data
  const toxicResults = useMemo(() => {
    return processedResults.filter(result => result.toxic)
  }, [processedResults])
  
  const safeResults = useMemo(() => {
    return processedResults.filter(result => !result.toxic)
  }, [processedResults])
  
  // Memoize statistics
  const statistics = useMemo(() => {
    return {
      total: processedResults.length,
      toxic: toxicResults.length,
      safe: safeResults.length,
      avgToxicity: processedResults.reduce((sum, r) => sum + r.toxicity_score, 0) / processedResults.length,
      avgSentiment: processedResults.reduce((sum, r) => sum + r.sentiment_score, 0) / processedResults.length
    }
  }, [processedResults, toxicResults, safeResults])
  
  return {
    processedResults,
    toxicResults,
    safeResults,
    statistics
  }
}

// Optimized server communication hook
const useOptimizedServer = () => {
  const [state, setState] = useState<ServerState>(initialState)
  
  // Memoize stable references
  const analyzeText = useCallback(async (text: string) => {
    // Check cache first to avoid unnecessary requests
    const cached = getCachedResult(text)
    if (cached && isCacheValid(cached)) {
      return cached.result
    }
    
    const result = await window.serverAPI.analyze(text)
    setCachedResult(text, result)
    return result
  }, [])
  
  // Memoize rarely changing values
  const serverInfo = useMemo(() => ({
    isReady: state.isReady,
    port: state.port,
    apiUrl: state.apiUrl,
    capabilities: getServerCapabilities(state)
  }), [state.isReady, state.port, state.apiUrl])
  
  return {
    ...state,
    analyzeText,
    serverInfo
  }
}
```

### 3. Context Optimization

```typescript
// Split contexts to prevent unnecessary re-renders
interface AnalysisDataContext {
  currentAnalysis: AnalysisResult | null
  history: AnalysisResult[]
  statistics: AnalysisStatistics
}

interface AnalysisActionsContext {
  analyzeText: (text: string) => Promise<void>
  clearHistory: () => void
  deleteResult: (id: string) => void
  exportResults: () => void
}

// Data context - changes frequently
const AnalysisDataProvider = ({ children }: { children: React.ReactNode }) => {
  const [data, setData] = useState<AnalysisDataContext>({
    currentAnalysis: null,
    history: [],
    statistics: initialStats
  })
  
  const contextValue = useMemo(() => data, [data])
  
  return (
    <AnalysisDataContext.Provider value={contextValue}>
      {children}
    </AnalysisDataContext.Provider>
  )
}

// Actions context - stable references
const AnalysisActionsProvider = ({ children }: { children: React.ReactNode }) => {
  const { analyzeText: serverAnalyze } = useServer()
  
  const actions = useMemo<AnalysisActionsContext>(() => ({
    analyzeText: async (text: string) => {
      const result = await serverAnalyze(text)
      // Update data context
    },
    clearHistory: () => {
      // Clear history logic
    },
    deleteResult: (id: string) => {
      // Delete result logic
    },
    exportResults: () => {
      // Export logic
    }
  }), [serverAnalyze])
  
  return (
    <AnalysisActionsContext.Provider value={actions}>
      {children}
    </AnalysisActionsContext.Provider>
  )
}

// Usage in components
const AnalysisComponent = () => {
  // Only subscribes to data changes
  const { currentAnalysis, statistics } = useContext(AnalysisDataContext)
  // Only subscribes to action changes (rare)
  const { analyzeText } = useContext(AnalysisActionsContext)
  
  return <div>{/* Component content */}</div>
}
```

## Bundle Size Optimization

### 1. Code Splitting Strategies

```typescript
// Route-based code splitting (future enhancement)
const AnalysisPage = lazy(() => import('./pages/AnalysisPage'))
const HistoryPage = lazy(() => import('./pages/HistoryPage'))
const SettingsPage = lazy(() => import('./pages/SettingsPage'))

// Component-based splitting for heavy components
const AdvancedAnalysisPanel = lazy(() => 
  import('./components/AdvancedAnalysisPanel').then(module => ({
    default: module.AdvancedAnalysisPanel
  }))
)

// Feature-based splitting
const ExportFeature = lazy(() => 
  import('./features/export').then(module => ({
    default: module.ExportContainer
  }))
)

// Conditional loading based on features
const ConditionalFeatureLoader = ({ featureEnabled }: { featureEnabled: boolean }) => {
  if (!featureEnabled) {
    return <FeatureDisabledMessage />
  }
  
  return (
    <Suspense fallback={<FeatureLoadingSkeleton />}>
      <AdvancedAnalysisPanel />
    </Suspense>
  )
}
```

### 2. Tree Shaking Optimization

```typescript
// Good: Import only what you need
import { memo, useCallback, useMemo } from 'react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'

// Avoid: Importing entire libraries
// import * as React from 'react'
// import * as utils from '@/lib/utils'

// Tree-shakeable utility exports
// utils/index.ts
export { cn } from './cn'
export { formatDate } from './date'
export { validateInput } from './validation'
export { debounce } from './debounce'

// Instead of barrel exports that import everything
// export * from './all-utils' // Don't do this

// Optimize third-party imports
// Good: Specific imports
import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

// Avoid: Default imports that might include more
// import clsx from 'clsx' // Might include more than needed
```

### 3. Asset Optimization

```typescript
// Lazy loading for images and assets
const OptimizedImageComponent = ({ src, alt }: { src: string; alt: string }) => {
  const [isLoaded, setIsLoaded] = useState(false)
  const [isInView, setIsInView] = useState(false)
  const imgRef = useRef<HTMLImageElement>(null)
  
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true)
          observer.disconnect()
        }
      },
      { threshold: 0.1 }
    )
    
    if (imgRef.current) {
      observer.observe(imgRef.current)
    }
    
    return () => observer.disconnect()
  }, [])
  
  return (
    <div ref={imgRef} className="image-container">
      {isInView && (
        <img
          src={src}
          alt={alt}
          onLoad={() => setIsLoaded(true)}
          className={cn(
            'transition-opacity duration-300',
            isLoaded ? 'opacity-100' : 'opacity-0'
          )}
        />
      )}
      {!isLoaded && <ImageSkeleton />}
    </div>
  )
}

// Dynamic icon loading
const DynamicIcon = ({ name }: { name: string }) => {
  const IconComponent = useMemo(() => {
    return lazy(() => 
      import('lucide-react').then(module => ({
        default: module[name as keyof typeof module] as React.ComponentType
      }))
    )
  }, [name])
  
  return (
    <Suspense fallback={<div className="icon-placeholder" />}>
      <IconComponent />
    </Suspense>
  )
}
```

## Performance Monitoring

### 1. React DevTools Profiler Integration

```typescript
// Development profiler wrapper
const ProfilerWrapper = ({ id, children }: { 
  id: string
  children: React.ReactNode 
}) => {
  if (process.env.NODE_ENV !== 'development') {
    return <>{children}</>
  }
  
  return (
    <Profiler
      id={id}
      onRender={(id, phase, actualDuration, baseDuration, startTime, commitTime) => {
        if (actualDuration > 16) { // More than one frame
          console.warn(`Slow render in ${id}:`, {
            phase,
            actualDuration,
            baseDuration,
            startTime,
            commitTime
          })
        }
      }}
    >
      {children}
    </Profiler>
  )
}

// Usage in components
const AnalysisContainer = () => {
  return (
    <ProfilerWrapper id="AnalysisContainer">
      <AnalysisComponent />
    </ProfilerWrapper>
  )
}
```

### 2. Custom Performance Hooks

```typescript
// Performance measurement hook
const usePerformanceMonitor = (componentName: string) => {
  const renderStartTime = useRef<number>(0)
  const renderCount = useRef<number>(0)
  
  useEffect(() => {
    renderStartTime.current = performance.now()
    renderCount.current += 1
  })
  
  useEffect(() => {
    const renderDuration = performance.now() - renderStartTime.current
    
    if (renderDuration > 16) {
      console.warn(`${componentName} slow render:`, {
        duration: renderDuration,
        renderCount: renderCount.current
      })
    }
    
    // Send to analytics in production
    if (process.env.NODE_ENV === 'production' && renderDuration > 100) {
      // analytics.track('slow_render', {
      //   component: componentName,
      //   duration: renderDuration
      // })
    }
  })
  
  return {
    renderCount: renderCount.current
  }
}

// Memory usage monitoring
const useMemoryMonitor = () => {
  const [memoryUsage, setMemoryUsage] = useState<any>(null)
  
  useEffect(() => {
    const interval = setInterval(() => {
      if ('memory' in performance) {
        setMemoryUsage((performance as any).memory)
      }
    }, 5000)
    
    return () => clearInterval(interval)
  }, [])
  
  return memoryUsage
}

// Usage in components
const MonitoredComponent = () => {
  const { renderCount } = usePerformanceMonitor('MonitoredComponent')
  const memoryUsage = useMemoryMonitor()
  
  if (process.env.NODE_ENV === 'development') {
    console.log(`Render count: ${renderCount}`, memoryUsage)
  }
  
  return <div>{/* Component content */}</div>
}
```

### 3. Bundle Analysis

```bash
# Add to package.json scripts
{
  "scripts": {
    "analyze": "npx vite-bundle-analyzer",
    "build:analyze": "npm run build && npm run analyze"
  }
}

# Performance testing script
npm run build:analyze
```

```typescript
// Webpack bundle analyzer configuration (if using webpack)
const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin

module.exports = {
  plugins: [
    new BundleAnalyzerPlugin({
      analyzerMode: 'server',
      openAnalyzer: true,
      generateStatsFile: true,
      statsFilename: 'bundle-stats.json'
    })
  ]
}
```

## Electron-Specific Performance

### 1. IPC Optimization

```typescript
// Batch IPC operations
const useBatchedIPC = () => {
  const operationQueue = useRef<Array<{ id: string; operation: () => Promise<any> }>>([])
  const isProcessing = useRef(false)
  
  const addOperation = useCallback(async (operation: () => Promise<any>) => {
    const id = Math.random().toString(36)
    
    return new Promise((resolve, reject) => {
      operationQueue.current.push({
        id,
        operation: async () => {
          try {
            const result = await operation()
            resolve(result)
          } catch (error) {
            reject(error)
          }
        }
      })
      
      if (!isProcessing.current) {
        processQueue()
      }
    })
  }, [])
  
  const processQueue = useCallback(async () => {
    if (isProcessing.current || operationQueue.current.length === 0) {
      return
    }
    
    isProcessing.current = true
    
    // Process up to 5 operations at once
    const batch = operationQueue.current.splice(0, 5)
    
    await Promise.allSettled(
      batch.map(({ operation }) => operation())
    )
    
    isProcessing.current = false
    
    // Process remaining queue
    if (operationQueue.current.length > 0) {
      setTimeout(processQueue, 0)
    }
  }, [])
  
  return { addOperation }
}

// Cache IPC results
const useIPCCache = <T>(key: string, fetcher: () => Promise<T>, ttl = 60000) => {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  
  const fetchWithCache = useCallback(async () => {
    // Check cache first
    const cached = getFromCache(key)
    if (cached && Date.now() - cached.timestamp < ttl) {
      setData(cached.data)
      return cached.data
    }
    
    setLoading(true)
    setError(null)
    
    try {
      const result = await fetcher()
      setData(result)
      setToCache(key, result)
      return result
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'))
      throw err
    } finally {
      setLoading(false)
    }
  }, [key, fetcher, ttl])
  
  return { data, loading, error, fetch: fetchWithCache }
}
```

### 2. Main Process Optimization

```typescript
// Debounce server requests in main process
class OptimizedServerManager {
  private debounceMap = new Map<string, NodeJS.Timeout>()
  private requestCache = new Map<string, { result: any; timestamp: number }>()
  
  async analyzeTextDebounced(text: string, delay = 300): Promise<AnalysisResult> {
    const key = `analyze:${text}`
    
    // Check cache first
    const cached = this.requestCache.get(key)
    if (cached && Date.now() - cached.timestamp < 60000) {
      return cached.result
    }
    
    // Debounce the request
    return new Promise((resolve, reject) => {
      const existingTimeout = this.debounceMap.get(key)
      if (existingTimeout) {
        clearTimeout(existingTimeout)
      }
      
      const timeout = setTimeout(async () => {
        try {
          const result = await this.analyzeText(text)
          this.requestCache.set(key, { result, timestamp: Date.now() })
          resolve(result)
        } catch (error) {
          reject(error)
        } finally {
          this.debounceMap.delete(key)
        }
      }, delay)
      
      this.debounceMap.set(key, timeout)
    })
  }
  
  // Cleanup old cache entries
  private cleanupCache() {
    const now = Date.now()
    const maxAge = 5 * 60 * 1000 // 5 minutes
    
    for (const [key, { timestamp }] of this.requestCache.entries()) {
      if (now - timestamp > maxAge) {
        this.requestCache.delete(key)
      }
    }
  }
}
```

## Performance Testing

### 1. Automated Performance Tests

```typescript
// Performance test utilities
const performanceTest = async (testName: string, testFn: () => Promise<void>) => {
  const startTime = performance.now()
  const startMemory = (performance as any).memory?.usedJSHeapSize || 0
  
  await testFn()
  
  const endTime = performance.now()
  const endMemory = (performance as any).memory?.usedJSHeapSize || 0
  
  const results = {
    duration: endTime - startTime,
    memoryDelta: endMemory - startMemory,
    testName
  }
  
  console.log(`Performance Test: ${testName}`, results)
  
  // Assert performance thresholds
  if (results.duration > 1000) {
    console.warn(`Slow test: ${testName} took ${results.duration}ms`)
  }
  
  return results
}

// Component render performance test
const testComponentRender = async () => {
  await performanceTest('AnalysisComponent render', async () => {
    const { rerender } = render(<AnalysisComponent results={largeDataSet} />)
    
    // Test multiple renders
    for (let i = 0; i < 10; i++) {
      rerender(<AnalysisComponent results={[...largeDataSet, newResult]} />)
      await new Promise(resolve => setTimeout(resolve, 16)) // Wait one frame
    }
  })
}

// Analysis operation performance test
const testAnalysisPerformance = async () => {
  await performanceTest('Text analysis operation', async () => {
    const promises = Array.from({ length: 10 }, (_, i) => 
      window.serverAPI.analyze(`Test text ${i}`)
    )
    
    await Promise.all(promises)
  })
}
```

### 2. Load Testing

```typescript
// Stress test component with large datasets
const stressTestComponent = () => {
  const largeDataset = Array.from({ length: 1000 }, (_, i) => ({
    id: `result-${i}`,
    text: `Test text ${i}`,
    toxic: Math.random() > 0.5,
    toxicity_score: Math.random(),
    sentiment: 'neutral' as const,
    sentiment_score: Math.random(),
    ai_enabled: true,
    processing_time_ms: Math.random() * 1000,
    model_versions: { toxicity: 'v1.0', sentiment: 'v1.0' },
    timestamp: Date.now()
  }))
  
  return (
    <ProfilerWrapper id="StressTest">
      <AnalysisResultsList results={largeDataset} />
    </ProfilerWrapper>
  )
}

// Memory leak detection
const memoryLeakTest = () => {
  const [iteration, setIteration] = useState(0)
  
  useEffect(() => {
    const interval = setInterval(() => {
      setIteration(prev => prev + 1)
      
      if (iteration % 100 === 0) {
        const memory = (performance as any).memory
        if (memory) {
          console.log(`Memory usage at iteration ${iteration}:`, {
            used: memory.usedJSHeapSize,
            total: memory.totalJSHeapSize,
            limit: memory.jsHeapSizeLimit
          })
        }
      }
    }, 100)
    
    return () => clearInterval(interval)
  }, [iteration])
  
  return <div>Memory test iteration: {iteration}</div>
}
```

## Best Practices Summary

### ✅ Performance Do's

1. **Use React 19 features**: Leverage automatic optimizations
2. **Implement strategic memoization**: Only memoize expensive operations
3. **Split contexts appropriately**: Separate data and actions
4. **Optimize bundle size**: Use code splitting and tree shaking
5. **Monitor performance**: Use profiling tools and custom hooks
6. **Cache strategically**: Cache expensive computations and API calls
7. **Debounce user inputs**: Prevent excessive API calls
8. **Use Suspense for loading states**: Better user experience

### ❌ Performance Don'ts

1. **Don't over-memoize**: Avoid memoizing simple calculations
2. **Don't ignore bundle analysis**: Regularly check bundle size
3. **Don't block the main thread**: Use concurrent features
4. **Don't ignore memory leaks**: Monitor memory usage
5. **Don't premature optimize**: Measure before optimizing
6. **Don't forget about mobile**: Consider low-powered devices
7. **Don't ignore IPC overhead**: Optimize Electron communication
8. **Don't skip performance testing**: Include perf tests in CI

This performance guide ensures that Open Stream maintains excellent user experience while handling complex AI operations and large datasets efficiently.