# Component Development Guidelines

## Overview

This document provides comprehensive guidelines for developing React components in the Open Stream project, focusing on the transition from a monolithic 550-line App.tsx to a modular, maintainable component architecture.

## Architecture Pattern: Providers → Hooks → Utils → Components

### Component Hierarchy

```
src/renderer/src/
├── providers/          # Context providers for global state
├── hooks/             # Custom React hooks for logic
├── utils/             # Pure utility functions
├── components/        # Reusable UI components
├── features/          # Feature-specific modules
└── lib/              # External library configurations
```

## Component Creation Standards

### 1. Component Structure

#### Basic Component Template

```typescript
import { memo, forwardRef } from 'react'
import { cn } from '@/lib/utils'

interface ComponentProps {
  children?: React.ReactNode
  className?: string
  variant?: 'default' | 'secondary' | 'destructive'
  size?: 'sm' | 'md' | 'lg'
}

const Component = memo(forwardRef<HTMLDivElement, ComponentProps>(
  ({ children, className, variant = 'default', size = 'md', ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          'component-base-styles',
          {
            'variant-default': variant === 'default',
            'variant-secondary': variant === 'secondary',
            'variant-destructive': variant === 'destructive',
            'size-sm': size === 'sm',
            'size-md': size === 'md',
            'size-lg': size === 'lg',
          },
          className
        )}
        {...props}
      >
        {children}
      </div>
    )
  }
))

Component.displayName = 'Component'

export { Component, type ComponentProps }
```

#### Feature Component Template

```typescript
import { memo, useCallback, useMemo } from 'react'
import { useAnalysis } from '@/hooks/useAnalysis'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { ErrorAlert } from '@/components/ui/error-alert'

interface AnalysisFeatureProps {
  text: string
  onResult?: (result: AnalysisResult) => void
  onError?: (error: string) => void
}

const AnalysisFeature = memo<AnalysisFeatureProps>(({ 
  text, 
  onResult, 
  onError 
}) => {
  const { 
    result, 
    loading, 
    error, 
    analyze 
  } = useAnalysis()

  const handleAnalyze = useCallback(async () => {
    try {
      const analysisResult = await analyze(text)
      onResult?.(analysisResult)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Analysis failed'
      onError?.(errorMessage)
    }
  }, [text, analyze, onResult, onError])

  const canAnalyze = useMemo(() => {
    return text.trim().length > 0 && !loading
  }, [text, loading])

  if (loading) {
    return <LoadingSpinner />
  }

  if (error) {
    return <ErrorAlert error={error} onRetry={handleAnalyze} />
  }

  return (
    <div className="analysis-feature">
      {/* Component implementation */}
    </div>
  )
})

AnalysisFeature.displayName = 'AnalysisFeature'

export { AnalysisFeature, type AnalysisFeatureProps }
```

### 2. Props Interface Design

#### Required vs Optional Props

```typescript
// Good: Clear separation of required and optional props
interface ButtonProps {
  // Required props first
  children: React.ReactNode
  onClick: () => void
  
  // Optional props with defaults
  variant?: 'primary' | 'secondary' | 'destructive'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  loading?: boolean
  className?: string
  
  // Event handlers (optional)
  onFocus?: () => void
  onBlur?: () => void
}

// Avoid: Mixed required/optional without clear organization
interface BadButtonProps {
  variant?: string
  children: React.ReactNode
  size?: string
  onClick: () => void
  disabled?: boolean
}
```

#### Union Types for Variants

```typescript
// Good: Strict union types
type ButtonVariant = 'primary' | 'secondary' | 'destructive'
type ButtonSize = 'sm' | 'md' | 'lg'

interface ButtonProps {
  variant?: ButtonVariant
  size?: ButtonSize
}

// Better: Use const assertions for type safety
const BUTTON_VARIANTS = ['primary', 'secondary', 'destructive'] as const
const BUTTON_SIZES = ['sm', 'md', 'lg'] as const

type ButtonVariant = typeof BUTTON_VARIANTS[number]
type ButtonSize = typeof BUTTON_SIZES[number]
```

### 3. Performance Optimization

#### Memoization Best Practices

```typescript
// 1. Memo for pure components
const ExpensiveComponent = memo<ExpensiveComponentProps>(({ data, onSelect }) => {
  // Component implementation
})

// 2. useMemo for expensive calculations
const ProcessedData = memo<{ rawData: any[] }>(({ rawData }) => {
  const processedData = useMemo(() => {
    return rawData
      .filter(item => item.isValid)
      .map(item => ({
        ...item,
        computed: expensiveCalculation(item)
      }))
      .sort((a, b) => a.priority - b.priority)
  }, [rawData])

  return <DataDisplay data={processedData} />
})

// 3. useCallback for event handlers
const InteractiveComponent = memo<{ onUpdate: (data: any) => void }>(({ onUpdate }) => {
  const [state, setState] = useState(defaultState)

  const handleUpdate = useCallback((newData: any) => {
    setState(prev => ({ ...prev, ...newData }))
    onUpdate(newData)
  }, [onUpdate])

  return <div onClick={() => handleUpdate(someData)} />
})
```

#### Avoiding Unnecessary Re-renders

```typescript
// Good: Stable references
const ParentComponent = () => {
  const [items, setItems] = useState([])
  
  // Stable callback reference
  const handleItemSelect = useCallback((item: Item) => {
    setItems(prev => prev.map(i => 
      i.id === item.id ? { ...i, selected: true } : i
    ))
  }, [])
  
  // Stable props object
  const listProps = useMemo(() => ({
    items,
    onItemSelect: handleItemSelect
  }), [items, handleItemSelect])
  
  return <ItemList {...listProps} />
}

// Avoid: Inline objects and functions
const BadParentComponent = () => {
  const [items, setItems] = useState([])
  
  return (
    <ItemList 
      items={items}
      onItemSelect={(item) => {/* handler */}}
      config={{ sortBy: 'name', direction: 'asc' }}
    />
  )
}
```

### 4. Error Handling Standards

#### Component-Level Error Boundaries

```typescript
// Error boundary wrapper for components
import { ErrorBoundary } from '@/components/ErrorBoundary'

const FeatureComponent = () => {
  return (
    <ErrorBoundary
      fallback={<FeatureErrorFallback />}
      onError={(error, errorInfo) => {
        console.error('Feature component error:', error, errorInfo)
        // Send to error tracking service
      }}
    >
      <ActualFeatureComponent />
    </ErrorBoundary>
  )
}

// Custom error fallback
const FeatureErrorFallback = ({ error, onRetry }: {
  error?: Error
  onRetry?: () => void
}) => (
  <div className="feature-error">
    <h3>Something went wrong</h3>
    <p>{error?.message || 'An unexpected error occurred'}</p>
    {onRetry && (
      <button onClick={onRetry} className="retry-button">
        Try Again
      </button>
    )}
  </div>
)
```

#### Async Operation Error Handling

```typescript
const AsyncComponent = () => {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState(null)

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    
    try {
      const result = await dataService.fetch()
      setData(result)
    } catch (err) {
      const errorMessage = err instanceof Error 
        ? err.message 
        : 'Failed to fetch data'
      setError(errorMessage)
      
      // Log error with context
      console.error('Data fetch failed:', {
        error: err,
        timestamp: new Date().toISOString(),
        component: 'AsyncComponent'
      })
    } finally {
      setLoading(false)
    }
  }, [])

  if (loading) return <LoadingSkeleton />
  if (error) return <ErrorState error={error} onRetry={fetchData} />
  if (!data) return <EmptyState onLoad={fetchData} />
  
  return <DataDisplay data={data} />
}
```

## Component Categories

### 1. UI Components (`/components/ui/`)

Basic building blocks with minimal logic:

```typescript
// Button component
export const Button = memo(forwardRef<HTMLButtonElement, ButtonProps>(
  ({ children, variant = 'primary', size = 'md', className, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          'btn-base',
          `btn-${variant}`,
          `btn-${size}`,
          className
        )}
        {...props}
      >
        {children}
      </button>
    )
  }
))

// Input component
export const Input = memo(forwardRef<HTMLInputElement, InputProps>(
  ({ type = 'text', className, error, ...props }, ref) => {
    return (
      <div className="input-wrapper">
        <input
          ref={ref}
          type={type}
          className={cn(
            'input-base',
            { 'input-error': error },
            className
          )}
          {...props}
        />
        {error && <span className="input-error-text">{error}</span>}
      </div>
    )
  }
))
```

### 2. Feature Components (`/components/features/`)

Components with business logic:

```typescript
// Analysis components
export const ToxicityAnalysis = memo<{ result: AnalysisResult }>(({ result }) => {
  const severity = useMemo(() => {
    if (result.toxicity_score >= 0.8) return 'high'
    if (result.toxicity_score >= 0.5) return 'moderate'
    if (result.toxicity_score >= 0.2) return 'low'
    return 'minimal'
  }, [result.toxicity_score])

  return (
    <div className={cn('toxicity-analysis', `severity-${severity}`)}>
      <div className="toxicity-header">
        <span className="toxicity-status">
          {result.toxic ? '⚠️ Toxic' : '✅ Safe'}
        </span>
        <span className="toxicity-score">
          {(result.toxicity_score * 100).toFixed(1)}%
        </span>
      </div>
      <div className="toxicity-details">
        <p>Severity: {severity}</p>
        {result.hate_speech && (
          <p>⚠️ Hate Speech Detected ({((result.hate_speech_score || 0) * 100).toFixed(1)}%)</p>
        )}
      </div>
    </div>
  )
})
```

### 3. Layout Components (`/components/layout/`)

Structural components for page organization:

```typescript
// Main layout wrapper
export const AppLayout = memo<{ children: React.ReactNode }>(({ children }) => {
  return (
    <div className="app-layout">
      <header className="app-header">
        <h1>🤗 Open Stream AI Analysis</h1>
      </header>
      <main className="app-main">
        {children}
      </main>
      <footer className="app-footer">
        {/* Footer content */}
      </footer>
    </div>
  )
})

// Feature section wrapper
export const FeatureSection = memo<{
  title: string
  children: React.ReactNode
  loading?: boolean
  error?: string | null
}>(({ title, children, loading, error }) => {
  return (
    <section className="feature-section">
      <h2 className="feature-title">{title}</h2>
      <div className="feature-content">
        {loading && <LoadingSkeleton />}
        {error && <ErrorAlert error={error} />}
        {!loading && !error && children}
      </div>
    </section>
  )
})
```

## File Organization

### Directory Structure

```
src/renderer/src/components/
├── ui/                     # Basic UI components
│   ├── button.tsx
│   ├── input.tsx
│   ├── loading-spinner.tsx
│   ├── error-alert.tsx
│   └── index.ts           # Barrel exports
├── features/              # Feature-specific components
│   ├── analysis/
│   │   ├── toxicity-result.tsx
│   │   ├── sentiment-result.tsx
│   │   ├── emotion-result.tsx
│   │   └── index.ts
│   ├── input/
│   │   ├── text-input.tsx
│   │   ├── input-controls.tsx
│   │   └── index.ts
│   └── server/
│       ├── server-status.tsx
│       ├── connection-indicator.tsx
│       └── index.ts
├── layout/               # Layout components
│   ├── app-layout.tsx
│   ├── feature-section.tsx
│   └── index.ts
└── index.ts             # Main barrel export
```

### Barrel Exports

```typescript
// components/ui/index.ts
export { Button, type ButtonProps } from './button'
export { Input, type InputProps } from './input'
export { LoadingSpinner } from './loading-spinner'
export { ErrorAlert, type ErrorAlertProps } from './error-alert'

// components/features/analysis/index.ts
export { ToxicityResult } from './toxicity-result'
export { SentimentResult } from './sentiment-result'
export { EmotionResult } from './emotion-result'

// components/index.ts
export * from './ui'
export * from './features'
export * from './layout'
```

## Testing Guidelines

### Component Testing Template

```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import { AnalysisFeature } from './analysis-feature'

describe('AnalysisFeature', () => {
  const mockProps = {
    text: 'Test text',
    onResult: vi.fn(),
    onError: vi.fn()
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders loading state correctly', () => {
    render(<AnalysisFeature {...mockProps} />)
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
  })

  it('calls onResult when analysis succeeds', async () => {
    const mockResult = { toxic: false, sentiment: 'positive' }
    vi.mocked(useAnalysis).mockReturnValue({
      analyze: vi.fn().mockResolvedValue(mockResult),
      loading: false,
      error: null
    })

    render(<AnalysisFeature {...mockProps} />)
    fireEvent.click(screen.getByRole('button', { name: /analyze/i }))

    await waitFor(() => {
      expect(mockProps.onResult).toHaveBeenCalledWith(mockResult)
    })
  })

  it('handles errors gracefully', async () => {
    const errorMessage = 'Analysis failed'
    vi.mocked(useAnalysis).mockReturnValue({
      analyze: vi.fn().mockRejectedValue(new Error(errorMessage)),
      loading: false,
      error: null
    })

    render(<AnalysisFeature {...mockProps} />)
    fireEvent.click(screen.getByRole('button', { name: /analyze/i }))

    await waitFor(() => {
      expect(mockProps.onError).toHaveBeenCalledWith(errorMessage)
    })
  })
})
```

## Do's and Don'ts

### ✅ Do's

1. **Use TypeScript strictly**
   ```typescript
   // Good: Explicit types
   interface Props {
     count: number
     onIncrement: () => void
   }
   
   // Avoid: Any types
   interface BadProps {
     data: any
     callback: any
   }
   ```

2. **Memoize appropriately**
   ```typescript
   // Good: Memo for expensive components
   const ExpensiveList = memo(({ items }: { items: Item[] }) => {
     return (
       <div>
         {items.map(item => <ExpensiveItem key={item.id} item={item} />)}
       </div>
     )
   })
   ```

3. **Use semantic HTML**
   ```typescript
   // Good: Semantic structure
   <article className="analysis-result">
     <header>
       <h3>Analysis Results</h3>
     </header>
     <section>
       <p>Content here</p>
     </section>
   </article>
   ```

4. **Handle loading and error states**
   ```typescript
   if (loading) return <LoadingSkeleton />
   if (error) return <ErrorState error={error} />
   return <SuccessState data={data} />
   ```

### ❌ Don'ts

1. **Don't use inline styles**
   ```typescript
   // Avoid
   <div style={{ color: 'red', fontSize: '16px' }}>
   
   // Use Tailwind classes instead
   <div className="text-red-500 text-base">
   ```

2. **Don't create overly complex components**
   ```typescript
   // Avoid: Component doing too many things
   const MegaComponent = () => {
     // 200+ lines of logic
     // Multiple concerns mixed together
   }
   
   // Prefer: Split into focused components
   const AnalysisContainer = () => {
     return (
       <>
         <AnalysisInput />
         <AnalysisResults />
         <AnalysisControls />
       </>
     )
   }
   ```

3. **Don't ignore accessibility**
   ```typescript
   // Avoid: Missing accessibility
   <div onClick={handleClick}>Click me</div>
   
   // Use proper interactive elements
   <button onClick={handleClick} aria-label="Analyze text">
     Analyze
   </button>
   ```

4. **Don't prop drill extensively**
   ```typescript
   // Avoid: Deep prop drilling
   <Level1 data={data} />
     <Level2 data={data} />
       <Level3 data={data} />
         <Level4 data={data} />
   
   // Use context for shared state
   const DataProvider = ({ children }) => {
     return (
       <DataContext.Provider value={data}>
         {children}
       </DataContext.Provider>
     )
   }
   ```

This component development guide provides a solid foundation for building maintainable, performant, and accessible React components in the Open Stream project. Following these guidelines will ensure consistency and quality as the codebase grows and evolves.