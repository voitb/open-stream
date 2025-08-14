# Styling Guidelines

## Overview

Open Stream uses Tailwind CSS 4.x with a custom design system for consistent, maintainable, and performant styling. This guide covers styling patterns, design system usage, and best practices for the application.

## Design System Foundation

### CSS Custom Properties (CSS Variables)

The application uses a comprehensive design system built on CSS custom properties for theming and consistency:

```css
/* From src/renderer/src/assets/main.css */
:root {
  /* Border radius system */
  --radius: 0.625rem;              /* Base radius (10px) */
  --radius-sm: calc(var(--radius) - 4px);  /* 6px */
  --radius-md: calc(var(--radius) - 2px);  /* 8px */
  --radius-lg: var(--radius);              /* 10px */
  --radius-xl: calc(var(--radius) + 4px);  /* 14px */
  
  /* Color system using OKLCH */
  --background: oklch(1 0 0);          /* Pure white */
  --foreground: oklch(0.145 0 0);      /* Dark text */
  --primary: oklch(0.205 0 0);         /* Primary brand */
  --secondary: oklch(0.97 0 0);        /* Secondary gray */
  --muted: oklch(0.97 0 0);            /* Muted backgrounds */
  --accent: oklch(0.97 0 0);           /* Accent highlights */
  --destructive: oklch(0.577 0.245 27.325); /* Error/danger */
  --border: oklch(0.922 0 0);          /* Border gray */
  --input: oklch(0.922 0 0);           /* Input backgrounds */
  --ring: oklch(0.708 0 0);            /* Focus rings */
}

/* Dark theme variations */
.dark {
  --background: oklch(0.145 0 0);      /* Dark background */
  --foreground: oklch(0.985 0 0);      /* Light text */
  --primary: oklch(0.922 0 0);         /* Light primary */
  /* ... other dark theme values */
}
```

### Tailwind CSS Configuration

The project uses Tailwind CSS 4.x with an inline theme configuration:

```css
@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-primary: var(--primary);
  --color-secondary: var(--secondary);
  /* ... mapping CSS variables to Tailwind tokens */
}
```

## Component Styling Patterns

### 1. Utility-First Approach

```typescript
// Good: Utility classes for styling
const Button = ({ variant = 'primary', size = 'md', className, ...props }) => {
  return (
    <button
      className={cn(
        // Base styles
        'inline-flex items-center justify-center rounded-lg font-medium transition-colors',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
        'disabled:pointer-events-none disabled:opacity-50',
        
        // Variant styles
        {
          'bg-primary text-primary-foreground hover:bg-primary/90': variant === 'primary',
          'bg-secondary text-secondary-foreground hover:bg-secondary/80': variant === 'secondary',
          'bg-destructive text-destructive-foreground hover:bg-destructive/90': variant === 'destructive',
          'border border-input bg-background hover:bg-accent hover:text-accent-foreground': variant === 'outline',
        },
        
        // Size styles
        {
          'h-8 px-3 text-sm': size === 'sm',
          'h-10 px-4 py-2': size === 'md',
          'h-11 px-8 text-lg': size === 'lg',
        },
        
        className
      )}
      {...props}
    />
  )
}

// Avoid: Inline styles
const BadButton = ({ style, ...props }) => (
  <button
    style={{
      backgroundColor: '#007bff',
      color: 'white',
      padding: '8px 16px',
      borderRadius: '6px',
      ...style
    }}
    {...props}
  />
)
```

### 2. Class Composition with clsx and tailwind-merge

```typescript
import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Usage examples
const dynamicClasses = cn(
  'base-class',
  {
    'conditional-class': condition,
    'another-class': anotherCondition,
  },
  'additional-class',
  className // From props
)

// Complex conditional styling
const AnalysisResult = ({ result, isOptimistic }) => {
  return (
    <div
      className={cn(
        'rounded-lg border p-4 transition-all duration-200',
        {
          'bg-green-50 border-green-200': !result.toxic,
          'bg-red-50 border-red-200': result.toxic,
          'opacity-60 animate-pulse': isOptimistic,
        }
      )}
    >
      {/* Content */}
    </div>
  )
}
```

### 3. Component Variants System

```typescript
// Variant definitions using CVA (Class Variance Authority)
import { cva, type VariantProps } from "class-variance-authority"

const buttonVariants = cva(
  // Base classes
  "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        primary: "bg-primary text-primary-foreground hover:bg-primary/90",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        sm: "h-8 px-3 text-xs",
        md: "h-10 px-4 py-2",
        lg: "h-11 px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "md",
    },
  }
)

interface ButtonProps extends 
  React.ButtonHTMLAttributes<HTMLButtonElement>,
  VariantProps<typeof buttonVariants> {}

const Button = ({ className, variant, size, ...props }: ButtonProps) => {
  return (
    <button
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
}
```

## Design System Components

### 1. Color Usage Patterns

```typescript
// Semantic color usage
const StatusIndicator = ({ status }: { status: 'ready' | 'loading' | 'error' }) => {
  return (
    <div
      className={cn(
        'flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium',
        {
          'bg-green-50 text-green-700 border border-green-200': status === 'ready',
          'bg-blue-50 text-blue-700 border border-blue-200': status === 'loading',
          'bg-red-50 text-red-700 border border-red-200': status === 'error',
        }
      )}
    >
      <StatusIcon status={status} />
      <span>{status}</span>
    </div>
  )
}

// Analysis result theming
const ToxicityResult = ({ result }: { result: AnalysisResult }) => {
  return (
    <div
      className={cn(
        'rounded-lg border p-4 transition-all',
        {
          // Safe content
          'bg-green-50 border-green-200 text-green-900': !result.toxic,
          // Toxic content
          'bg-red-50 border-red-200 text-red-900': result.toxic,
        }
      )}
    >
      <div className="flex items-center justify-between">
        <span className="font-medium">
          {result.toxic ? '⚠️ Toxic Content' : '✅ Safe Content'}
        </span>
        <span className="text-sm opacity-75">
          {(result.toxicity_score * 100).toFixed(1)}%
        </span>
      </div>
    </div>
  )
}
```

### 2. Typography System

```typescript
// Typography utilities
const TypographyComponents = () => {
  return (
    <div className="space-y-4">
      {/* Headings */}
      <h1 className="text-4xl font-bold tracking-tight text-foreground">
        Heading 1
      </h1>
      <h2 className="text-3xl font-semibold tracking-tight text-foreground">
        Heading 2
      </h2>
      <h3 className="text-2xl font-semibold text-foreground">
        Heading 3
      </h3>
      <h4 className="text-xl font-medium text-foreground">
        Heading 4
      </h4>
      
      {/* Body text */}
      <p className="text-base text-foreground leading-7">
        Regular body text with proper line height
      </p>
      <p className="text-sm text-muted-foreground">
        Secondary text with muted color
      </p>
      <p className="text-xs text-muted-foreground">
        Caption text for additional information
      </p>
      
      {/* Code and monospace */}
      <code className="relative rounded bg-muted px-[0.3rem] py-[0.2rem] font-mono text-sm font-semibold">
        Inline code
      </code>
    </div>
  )
}
```

### 3. Spacing and Layout

```typescript
// Consistent spacing patterns
const LayoutComponents = () => {
  return (
    <>
      {/* Container with consistent padding */}
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Section spacing */}
        <section className="py-8 lg:py-12">
          
          {/* Card with consistent spacing */}
          <div className="rounded-lg border bg-card p-6 shadow-sm">
            
            {/* Content with proper spacing */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Card Title</h3>
              <p className="text-muted-foreground">Card description</p>
              
              {/* Button group with gap */}
              <div className="flex gap-3">
                <Button>Primary</Button>
                <Button variant="outline">Secondary</Button>
              </div>
            </div>
          </div>
        </section>
      </div>
      
      {/* Grid layouts */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* Grid items */}
      </div>
      
      {/* Flex layouts */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        {/* Flex items */}
      </div>
    </>
  )
}
```

## Feature-Specific Styling

### 1. Analysis Results Styling

```typescript
// Toxicity analysis component
const ToxicityAnalysis = ({ result }: { result: AnalysisResult }) => {
  const severityLevel = useMemo(() => {
    if (result.toxicity_score >= 0.8) return 'high'
    if (result.toxicity_score >= 0.5) return 'moderate'
    if (result.toxicity_score >= 0.2) return 'low'
    return 'minimal'
  }, [result.toxicity_score])

  return (
    <div
      className={cn(
        'rounded-lg border p-4 transition-all duration-200',
        {
          'bg-red-50 border-red-200': severityLevel === 'high',
          'bg-orange-50 border-orange-200': severityLevel === 'moderate',
          'bg-yellow-50 border-yellow-200': severityLevel === 'low',
          'bg-green-50 border-green-200': severityLevel === 'minimal',
        }
      )}
    >
      <div className="flex items-center justify-between mb-2">
        <span
          className={cn(
            'text-sm font-medium',
            {
              'text-red-700': severityLevel === 'high',
              'text-orange-700': severityLevel === 'moderate',
              'text-yellow-700': severityLevel === 'low',
              'text-green-700': severityLevel === 'minimal',
            }
          )}
        >
          {result.toxic ? '⚠️ Toxic Content' : '✅ Safe Content'}
        </span>
        <span className="text-xs opacity-60">
          {(result.toxicity_score * 100).toFixed(1)}%
        </span>
      </div>
      
      {/* Progress bar */}
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={cn(
            'h-2 rounded-full transition-all duration-300',
            {
              'bg-red-500': severityLevel === 'high',
              'bg-orange-500': severityLevel === 'moderate',
              'bg-yellow-500': severityLevel === 'low',
              'bg-green-500': severityLevel === 'minimal',
            }
          )}
          style={{ width: `${result.toxicity_score * 100}%` }}
        />
      </div>
    </div>
  )
}
```

### 2. Input Components Styling

```typescript
// Text input with validation states
const TextInput = forwardRef<HTMLTextAreaElement, {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  error?: string
  disabled?: boolean
  maxLength?: number
}>(({ value, onChange, placeholder, error, disabled, maxLength, ...props }, ref) => {
  const characterCount = value.length
  const isNearLimit = maxLength && characterCount > maxLength * 0.8
  const isAtLimit = maxLength && characterCount >= maxLength

  return (
    <div className="space-y-2">
      <textarea
        ref={ref}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        maxLength={maxLength}
        className={cn(
          // Base styles
          'flex min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2',
          'text-sm ring-offset-background placeholder:text-muted-foreground',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
          'disabled:cursor-not-allowed disabled:opacity-50',
          'resize-none transition-colors',
          
          // Error state
          {
            'border-red-500 focus-visible:ring-red-500': error,
          }
        )}
        {...props}
      />
      
      {/* Character count and error */}
      <div className="flex justify-between items-center text-xs">
        {maxLength && (
          <span
            className={cn(
              'text-muted-foreground',
              {
                'text-orange-600': isNearLimit,
                'text-red-600': isAtLimit,
              }
            )}
          >
            {characterCount}/{maxLength}
          </span>
        )}
        {error && (
          <span className="text-red-600">{error}</span>
        )}
      </div>
    </div>
  )
})
```

### 3. Server Status Indicators

```typescript
// Server connection status component
const ServerStatus = ({ 
  isReady, 
  isChecking, 
  error, 
  serverAPIAvailable 
}: ServerStatusProps) => {
  const status = useMemo(() => {
    if (error) return 'error'
    if (isChecking) return 'checking'
    if (!serverAPIAvailable) return 'unavailable'
    return isReady ? 'ready' : 'loading'
  }, [error, isChecking, serverAPIAvailable, isReady])

  return (
    <div
      className={cn(
        'flex items-center gap-2 rounded-lg border px-3 py-2 text-sm transition-all',
        {
          'bg-green-50 border-green-200 text-green-700': status === 'ready',
          'bg-blue-50 border-blue-200 text-blue-700': status === 'checking' || status === 'loading',
          'bg-red-50 border-red-200 text-red-700': status === 'error' || status === 'unavailable',
        }
      )}
    >
      {/* Status indicator */}
      <div
        className={cn(
          'w-2 h-2 rounded-full transition-all',
          {
            'bg-green-500': status === 'ready',
            'bg-blue-500 animate-pulse': status === 'checking' || status === 'loading',
            'bg-red-500': status === 'error' || status === 'unavailable',
          }
        )}
      />
      
      {/* Status text */}
      <span className="font-medium">
        {status === 'ready' && '✅ Server Ready'}
        {status === 'checking' && '🔄 Checking Connection...'}
        {status === 'loading' && '⏳ Loading Models...'}
        {status === 'error' && `❌ Error: ${error}`}
        {status === 'unavailable' && '⚠️ Server Unavailable'}
      </span>
    </div>
  )
}
```

## Animation and Transitions

### 1. Micro-interactions

```typescript
// Button with hover and active states
const InteractiveButton = ({ children, loading, ...props }) => {
  return (
    <button
      className={cn(
        'relative inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2',
        'bg-primary text-primary-foreground font-medium',
        'transition-all duration-200 ease-in-out',
        'hover:bg-primary/90 hover:scale-105',
        'active:scale-95',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
        'disabled:pointer-events-none disabled:opacity-50 disabled:scale-100',
        {
          'cursor-wait': loading,
        }
      )}
      {...props}
    >
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
        </div>
      )}
      <span className={cn({ 'opacity-0': loading })}>
        {children}
      </span>
    </button>
  )
}
```

### 2. Loading States

```typescript
// Skeleton loading component
const LoadingSkeleton = () => {
  return (
    <div className="space-y-4 animate-pulse">
      {/* Header skeleton */}
      <div className="h-6 bg-gray-200 rounded-md w-3/4" />
      
      {/* Content skeletons */}
      <div className="space-y-3">
        <div className="h-20 bg-gray-200 rounded-lg" />
        <div className="h-16 bg-gray-200 rounded-lg" />
        <div className="h-12 bg-gray-200 rounded-lg w-1/2" />
      </div>
    </div>
  )
}

// Result card with loading state
const AnalysisCard = ({ result, loading }: { result?: AnalysisResult; loading: boolean }) => {
  if (loading) {
    return (
      <div className="rounded-lg border border-gray-200 p-4 animate-pulse">
        <div className="space-y-3">
          <div className="h-4 bg-gray-200 rounded w-1/3" />
          <div className="h-3 bg-gray-200 rounded w-full" />
          <div className="h-3 bg-gray-200 rounded w-2/3" />
        </div>
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-gray-200 p-4 animate-in fade-in duration-300">
      {/* Actual content */}
    </div>
  )
}
```

### 3. Page Transitions

```typescript
// Slide-in animations for content
const SlideInContainer = ({ children, delay = 0 }: { 
  children: React.ReactNode; 
  delay?: number 
}) => {
  return (
    <div
      className="animate-in slide-in-from-bottom-4 fade-in duration-500"
      style={{ animationDelay: `${delay}ms` }}
    >
      {children}
    </div>
  )
}

// Staggered animation for list items
const AnimatedList = ({ items }: { items: any[] }) => {
  return (
    <div className="space-y-2">
      {items.map((item, index) => (
        <SlideInContainer key={item.id} delay={index * 100}>
          <ListItem item={item} />
        </SlideInContainer>
      ))}
    </div>
  )
}
```

## Responsive Design Patterns

### 1. Mobile-First Approach

```typescript
// Responsive component layout
const ResponsiveLayout = ({ children }) => {
  return (
    <div className="container mx-auto px-4 sm:px-6 lg:px-8">
      {/* Mobile: single column, Desktop: two columns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8">
        {children}
      </div>
    </div>
  )
}

// Responsive text input
const ResponsiveTextInput = (props) => {
  return (
    <textarea
      className={cn(
        // Mobile: smaller padding and text
        'min-h-[100px] text-sm px-3 py-2',
        // Tablet and up: larger padding and text
        'sm:min-h-[120px] sm:text-base sm:px-4 sm:py-3',
        // Desktop: even larger
        'lg:min-h-[140px] lg:text-lg',
        // Base styles
        'w-full rounded-md border border-input bg-background',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring'
      )}
      {...props}
    />
  )
}
```

### 2. Adaptive Navigation

```typescript
// Responsive navigation component
const Navigation = () => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  return (
    <nav className="border-b border-gray-200 bg-background">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex-shrink-0">
            <h1 className="text-xl font-bold text-foreground">Open Stream</h1>
          </div>
          
          {/* Desktop navigation */}
          <div className="hidden md:flex items-center space-x-8">
            <NavLink href="/analysis">Analysis</NavLink>
            <NavLink href="/history">History</NavLink>
            <NavLink href="/settings">Settings</NavLink>
          </div>
          
          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100"
            >
              {/* Menu icon */}
            </button>
          </div>
        </div>
      </div>
      
      {/* Mobile menu */}
      {isMobileMenuOpen && (
        <div className="md:hidden border-t border-gray-200">
          <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
            <MobileNavLink href="/analysis">Analysis</MobileNavLink>
            <MobileNavLink href="/history">History</MobileNavLink>
            <MobileNavLink href="/settings">Settings</MobileNavLink>
          </div>
        </div>
      )}
    </nav>
  )
}
```

## Dark Mode Support

### 1. Theme Implementation

```typescript
// Theme provider for dark mode
const ThemeProvider = ({ children }: { children: React.ReactNode }) => {
  const [theme, setTheme] = useState<'light' | 'dark'>('light')

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null
    if (savedTheme) {
      setTheme(savedTheme)
    } else {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      setTheme(prefersDark ? 'dark' : 'light')
    }
  }, [])

  useEffect(() => {
    document.documentElement.className = theme
    localStorage.setItem('theme', theme)
  }, [theme])

  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

// Theme toggle component
const ThemeToggle = () => {
  const { theme, setTheme } = useTheme()

  return (
    <button
      onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
      className={cn(
        'p-2 rounded-md transition-colors',
        'hover:bg-accent hover:text-accent-foreground',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring'
      )}
    >
      {theme === 'light' ? '🌙' : '☀️'}
    </button>
  )
}
```

### 2. Dark Mode Optimized Components

```typescript
// Component that works well in both themes
const Card = ({ children, className, ...props }) => {
  return (
    <div
      className={cn(
        // Base styles that work in both themes
        'rounded-lg border bg-card text-card-foreground shadow-sm',
        'transition-colors duration-200',
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

// Analysis result with dark mode support
const AnalysisResult = ({ result }) => {
  return (
    <Card className="p-4">
      <div className="space-y-3">
        <div
          className={cn(
            'flex items-center justify-between p-3 rounded-md',
            {
              // Light mode colors
              'bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300': !result.toxic,
              'bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300': result.toxic,
            }
          )}
        >
          <span>{result.toxic ? '⚠️ Toxic' : '✅ Safe'}</span>
          <span className="text-sm opacity-75">
            {(result.toxicity_score * 100).toFixed(1)}%
          </span>
        </div>
      </div>
    </Card>
  )
}
```

## Performance Considerations

### 1. CSS-in-JS vs Utility Classes

```typescript
// Prefer: Tailwind utilities (minimal runtime cost)
const OptimizedComponent = () => {
  return (
    <div className="flex items-center justify-between p-4 bg-white rounded-lg shadow">
      {/* Content */}
    </div>
  )
}

// Avoid: Runtime CSS-in-JS (performance overhead)
const NonOptimizedComponent = () => {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '16px',
        backgroundColor: 'white',
        borderRadius: '8px',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
      }}
    >
      {/* Content */}
    </div>
  )
}
```

### 2. Conditional Class Optimization

```typescript
// Optimized: Pre-computed class strings
const statusClasses = {
  ready: 'bg-green-50 text-green-700 border-green-200',
  loading: 'bg-blue-50 text-blue-700 border-blue-200',
  error: 'bg-red-50 text-red-700 border-red-200',
} as const

const StatusBadge = ({ status }: { status: keyof typeof statusClasses }) => {
  return (
    <div className={cn('px-3 py-1 rounded-full text-sm font-medium border', statusClasses[status])}>
      {status}
    </div>
  )
}

// Less optimal: Runtime class computation
const StatusBadgeNonOptimized = ({ status }) => {
  return (
    <div
      className={cn(
        'px-3 py-1 rounded-full text-sm font-medium border',
        status === 'ready' && 'bg-green-50 text-green-700 border-green-200',
        status === 'loading' && 'bg-blue-50 text-blue-700 border-blue-200',
        status === 'error' && 'bg-red-50 text-red-700 border-red-200'
      )}
    >
      {status}
    </div>
  )
}
```

## Best Practices Summary

### ✅ Styling Do's

1. **Use design system tokens**: Leverage CSS custom properties for consistency
2. **Follow utility-first approach**: Use Tailwind classes over custom CSS
3. **Implement proper theming**: Support both light and dark modes
4. **Use semantic color names**: `bg-destructive` instead of `bg-red-500`
5. **Optimize for performance**: Pre-compute class strings when possible
6. **Maintain responsive design**: Mobile-first approach with breakpoints
7. **Use proper spacing**: Consistent spacing scale throughout the app
8. **Implement loading states**: Skeleton screens and loading indicators

### ❌ Styling Don'ts

1. **Don't use inline styles**: Avoid `style` prop for styling
2. **Don't hardcode colors**: Use design system tokens instead
3. **Don't ignore accessibility**: Ensure proper contrast and focus states
4. **Don't create unnecessary custom CSS**: Leverage Tailwind utilities
5. **Don't forget mobile optimization**: Always test on mobile devices
6. **Don't use magic numbers**: Use design system spacing values
7. **Don't mix styling approaches**: Stick to utility-first consistently
8. **Don't ignore dark mode**: Design with both themes in mind

This styling guide ensures consistent, maintainable, and performant styling across the Open Stream application while leveraging the full power of Tailwind CSS and modern design patterns.