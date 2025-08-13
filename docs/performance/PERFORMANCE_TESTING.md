# Open Stream - Performance Testing Guide

This guide provides comprehensive testing procedures to validate and monitor all performance improvements implemented in Open Stream.

## Quick Start

```bash
# Start the application
npm run dev

# Wait for startup, then run basic performance tests
curl http://127.0.0.1:55555/performance | jq '.'
curl http://127.0.0.1:55555/health | jq '.'
```

## Testing Categories

### 1. Startup Performance Testing

#### Test Cold Startup (First Run)
```bash
#!/bin/bash
# test-cold-startup.sh

echo "Testing cold startup performance..."

# Clean all caches
rm -rf ~/.cache/open-stream-models
rm -rf ~/.cache/huggingface
rm -f ~/.python-path-cache.json

# Remove any existing venv
if [ -d "server/venv" ]; then
  rm -rf server/venv
fi

# Time the full startup process
echo "Starting application..."
start_time=$(date +%s.%N)

# Start application in background
npm run dev &
APP_PID=$!

# Wait for health endpoint to be available
echo "Waiting for server to be ready..."
while ! curl -s http://127.0.0.1:55555/health > /dev/null 2>&1; do
  sleep 0.5
done

end_time=$(date +%s.%N)
startup_time=$(echo "$end_time - $start_time" | bc)

echo "✅ Cold startup completed in ${startup_time}s"

# Get detailed metrics
curl -s http://127.0.0.1:55555/performance | jq '.server'

# Cleanup
kill $APP_PID
```

#### Test Warm Startup (Cached)
```bash
#!/bin/bash
# test-warm-startup.sh

echo "Testing warm startup performance..."

# Ensure previous setup exists (run cold startup first if needed)
if [ ! -d "server/venv" ]; then
  echo "No existing setup found. Run cold startup test first."
  exit 1
fi

# Time the warm startup
start_time=$(date +%s.%N)

npm run dev &
APP_PID=$!

# Wait for health endpoint
while ! curl -s http://127.0.0.1:55555/health > /dev/null 2>&1; do
  sleep 0.1
done

end_time=$(date +%s.%N)
startup_time=$(echo "$end_time - $start_time" | bc)

echo "✅ Warm startup completed in ${startup_time}s"

# Get startup metrics
curl -s http://127.0.0.1:55555/performance | jq '{
  startup_time: .server.uptime_seconds,
  python_discovery: .server.python_discovery_time,
  models_status: .ai_manager.models_status
}'

kill $APP_PID
```

#### Python Path Caching Test
```bash
#!/bin/bash
# test-python-cache.sh

echo "Testing Python path caching..."

# Remove cache
rm -f ~/.python-path-cache.json

echo "First run (cache miss):"
time_output=$(time (npm run dev > /dev/null 2>&1 &
APP_PID=$!
sleep 3
kill $APP_PID
) 2>&1)

echo "Cache miss time: $time_output"

echo "Second run (cache hit):"
time_output=$(time (npm run dev > /dev/null 2>&1 &
APP_PID=$!
sleep 3
kill $APP_PID
) 2>&1)

echo "Cache hit time: $time_output"

# Check cache file
if [ -f ~/.python-path-cache.json ]; then
  echo "✅ Python path cache created:"
  cat ~/.python-path-cache.json | jq '.'
else
  echo "❌ Python path cache not found"
fi
```

### 2. Memory Usage Testing

#### Memory Monitoring Test
```bash
#!/bin/bash
# test-memory-usage.sh

echo "Testing memory usage patterns..."

# Start application
npm run dev &
APP_PID=$!

# Wait for startup
sleep 5

echo "Memory usage monitoring (60 seconds):"
echo "Time,Memory_MB,Models_Loaded,Cache_Size"

for i in {1..60}; do
  memory_data=$(curl -s http://127.0.0.1:55555/performance | jq -r '
    [
      now,
      .ai_manager.memory_usage_mb,
      .ai_manager.models_loaded,
      .ai_manager.cache_size
    ] | @csv
  ')
  echo "$memory_data"
  sleep 1
done

echo "Final memory statistics:"
curl -s http://127.0.0.1:55555/performance | jq '.ai_manager'

kill $APP_PID
```

#### Memory Stress Test
```bash
#!/bin/bash
# test-memory-stress.sh

echo "Testing memory management under load..."

npm run dev &
APP_PID=$!
sleep 5

# Generate analysis requests to trigger model loading
echo "Loading all models through API calls..."

# Toxicity model
curl -X POST http://127.0.0.1:55555/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "This is a test for toxicity", "include_toxicity": true}' > /dev/null

# Sentiment model  
curl -X POST http://127.0.0.1:55555/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "This is a test for sentiment", "include_sentiment": true}' > /dev/null

# Check memory after model loading
echo "Memory after model loading:"
curl -s http://127.0.0.1:55555/performance | jq '{
  memory_mb: .ai_manager.memory_usage_mb,
  memory_limit_mb: .ai_manager.memory_limit_mb,
  models_loaded: .ai_manager.models_loaded,
  models_status: .ai_manager.models_status
}'

# Generate high memory usage
echo "Generating memory pressure..."
for i in {1..1000}; do
  curl -X POST http://127.0.0.1:55555/analyze \
    -H "Content-Type: application/json" \
    -d "{\"text\": \"Memory test message number $i with some additional content to vary the input\", \"include_toxicity\": true, \"include_sentiment\": true}" > /dev/null 2>&1 &
  
  if [ $((i % 100)) -eq 0 ]; then
    wait  # Wait for batch to complete
    echo "Batch $((i/100)) completed, checking memory..."
    curl -s http://127.0.0.1:55555/performance | jq '.ai_manager.memory_usage_mb'
  fi
done

wait  # Wait for all requests to complete

echo "Final memory state after stress test:"
curl -s http://127.0.0.1:55555/performance | jq '.ai_manager'

kill $APP_PID
```

### 3. AI Model Performance Testing

#### Model Loading Speed Test
```bash
#!/bin/bash
# test-model-loading.sh

echo "Testing AI model loading performance..."

npm run dev &
APP_PID=$!
sleep 3

echo "Testing model loading times..."

# Test toxicity model loading
echo "Loading toxicity model:"
start_time=$(date +%s.%N)
response=$(curl -X POST http://127.0.0.1:55555/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Test toxicity loading", "include_toxicity": true}')
end_time=$(date +%s.%N)
loading_time=$(echo "$end_time - $start_time" | bc)
processing_time=$(echo "$response" | jq -r '.processing_time_ms')

echo "  Loading time: ${loading_time}s"
echo "  Processing time: ${processing_time}ms"

# Test sentiment model loading
echo "Loading sentiment model:"
start_time=$(date +%s.%N)
response=$(curl -X POST http://127.0.0.1:55555/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Test sentiment loading", "include_sentiment": true}')
end_time=$(date +%s.%N)
loading_time=$(echo "$end_time - $start_time" | bc)
processing_time=$(echo "$response" | jq -r '.processing_time_ms')

echo "  Loading time: ${loading_time}s"
echo "  Processing time: ${processing_time}ms"

kill $APP_PID
```

#### Cache Performance Test
```bash
#!/bin/bash
# test-cache-performance.sh

echo "Testing analysis cache performance..."

npm run dev &
APP_PID=$!
sleep 5

# Pre-load models
curl -X POST http://127.0.0.1:55555/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Preload models", "include_toxicity": true, "include_sentiment": true}' > /dev/null

echo "Testing cache hit performance..."

test_text="This is a test message for cache performance testing"

# First request (cache miss)
echo "Cache miss test:"
start_time=$(date +%s.%N)
response=$(curl -X POST http://127.0.0.1:55555/analyze \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"$test_text\", \"include_toxicity\": true, \"include_sentiment\": true}")
end_time=$(date +%s.%N)
miss_time=$(echo "$end_time - $start_time" | bc)
processing_time=$(echo "$response" | jq -r '.processing_time_ms')

echo "  Request time: ${miss_time}s"
echo "  Processing time: ${processing_time}ms"

# Cache hit requests
echo "Cache hit test (10 requests):"
total_time=0
for i in {1..10}; do
  start_time=$(date +%s.%N)
  curl -X POST http://127.0.0.1:55555/analyze \
    -H "Content-Type: application/json" \
    -d "{\"text\": \"$test_text\", \"include_toxicity\": true, \"include_sentiment\": true}" > /dev/null 2>&1
  end_time=$(date +%s.%N)
  request_time=$(echo "$end_time - $start_time" | bc)
  total_time=$(echo "$total_time + $request_time" | bc)
done

average_hit_time=$(echo "scale=3; $total_time / 10" | bc)
echo "  Average cache hit time: ${average_hit_time}s"

# Performance improvement
improvement=$(echo "scale=1; $miss_time / $average_hit_time" | bc)
echo "  Performance improvement: ${improvement}x faster"

# Check cache statistics
echo "Cache statistics:"
curl -s http://127.0.0.1:55555/performance | jq '{
  cache_size: .ai_manager.cache_size,
  cache_hit_rate: .ai_manager.cache_hit_rate
}'

kill $APP_PID
```

### 4. API Performance Testing

#### Throughput Test
```bash
#!/bin/bash
# test-api-throughput.sh

echo "Testing API throughput..."

npm run dev &
APP_PID=$!
sleep 5

# Pre-load models
curl -X POST http://127.0.0.1:55555/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Preload", "include_toxicity": true, "include_sentiment": true}' > /dev/null

echo "Running throughput test (100 requests)..."
start_time=$(date +%s.%N)

# Run requests in parallel
for i in {1..100}; do
  curl -X POST http://127.0.0.1:55555/analyze \
    -H "Content-Type: application/json" \
    -d "{\"text\": \"Throughput test message $i\", \"include_toxicity\": true}" > /dev/null 2>&1 &
done

wait  # Wait for all requests to complete

end_time=$(date +%s.%N)
total_time=$(echo "$end_time - $start_time" | bc)
throughput=$(echo "scale=2; 100 / $total_time" | bc)

echo "✅ Completed 100 requests in ${total_time}s"
echo "✅ Throughput: ${throughput} requests/second"

kill $APP_PID
```

#### Bulk Analysis Test
```bash
#!/bin/bash
# test-bulk-analysis.sh

echo "Testing bulk analysis performance..."

npm run dev &
APP_PID=$!
sleep 5

# Create test data
test_data='[
  "This is a positive message",
  "This is a negative message",
  "This is a neutral message", 
  "This is a toxic message with hate",
  "This is a normal message"
]'

echo "Testing bulk analysis (5 texts):"
start_time=$(date +%s.%N)

response=$(curl -X POST http://127.0.0.1:55555/analyze-bulk \
  -H "Content-Type: application/json" \
  -d "{\"texts\": $test_data, \"include_toxicity\": true, \"include_sentiment\": true}")

end_time=$(date +%s.%N)
request_time=$(echo "$end_time - $start_time" | bc)
processing_time=$(echo "$response" | jq -r '.processing_time_ms')

echo "  Request time: ${request_time}s"
echo "  Total processing time: ${processing_time}ms"
echo "  Average per text: $(echo "scale=2; $processing_time / 5" | bc)ms"

kill $APP_PID
```

### 5. Background Loading Test

#### Background Loading Verification
```bash
#!/bin/bash
# test-background-loading.sh

echo "Testing background model loading..."

# Start with clean state
rm -rf server/venv
rm -f ~/.python-path-cache.json

npm run dev &
APP_PID=$!

echo "Monitoring background loading progress..."

for i in {1..30}; do
  status=$(curl -s http://127.0.0.1:55555/health 2>/dev/null | jq -r '.status' 2>/dev/null)
  if [ "$status" = "healthy" ]; then
    echo "Server ready at ${i}s"
    break
  fi
  echo "Waiting... (${i}s)"
  sleep 1
done

echo "Model loading status over time:"
for i in {1..60}; do
  models_status=$(curl -s http://127.0.0.1:55555/performance 2>/dev/null | jq -r '.ai_manager.models_status' 2>/dev/null)
  background_loading=$(curl -s http://127.0.0.1:55555/performance 2>/dev/null | jq -r '.ai_manager.background_loading' 2>/dev/null)
  
  echo "Time ${i}s: Background loading: $background_loading, Models: $models_status"
  
  if [ "$background_loading" = "false" ]; then
    echo "✅ Background loading completed at ${i}s"
    break
  fi
  
  sleep 1
done

# Test immediate UI responsiveness
echo "Testing UI responsiveness during background loading:"
curl -s http://127.0.0.1:55555/health | jq '.'

kill $APP_PID
```

### 6. Performance Benchmarking

#### Complete Performance Benchmark
```bash
#!/bin/bash
# benchmark-performance.sh

echo "Running complete performance benchmark..."

# Create results directory
mkdir -p performance_results
timestamp=$(date +%Y%m%d_%H%M%S)

# Cold startup benchmark
echo "1. Cold startup benchmark..."
./test-cold-startup.sh > "performance_results/cold_startup_${timestamp}.log"

# Warm startup benchmark
echo "2. Warm startup benchmark..."
./test-warm-startup.sh > "performance_results/warm_startup_${timestamp}.log"

# Memory usage benchmark
echo "3. Memory usage benchmark..."
./test-memory-usage.sh > "performance_results/memory_usage_${timestamp}.csv"

# Cache performance benchmark
echo "4. Cache performance benchmark..."
./test-cache-performance.sh > "performance_results/cache_performance_${timestamp}.log"

# API throughput benchmark
echo "5. API throughput benchmark..."
./test-api-throughput.sh > "performance_results/throughput_${timestamp}.log"

echo "✅ Benchmark complete. Results in performance_results/"
echo "Results summary:"
echo "- Cold startup: $(tail -1 performance_results/cold_startup_${timestamp}.log)"
echo "- Warm startup: $(tail -1 performance_results/warm_startup_${timestamp}.log)"
echo "- Throughput: $(tail -1 performance_results/throughput_${timestamp}.log)"
```

### 7. Continuous Performance Monitoring

#### Performance Monitor Script
```bash
#!/bin/bash
# monitor-performance.sh

echo "Starting continuous performance monitoring..."

# Create monitoring log
log_file="performance_monitor_$(date +%Y%m%d_%H%M%S).log"

# Start application
npm run dev &
APP_PID=$!
sleep 5

echo "Monitoring performance metrics every 10 seconds..."
echo "Time,Memory_MB,Models_Loaded,Cache_Size,Cache_Hit_Rate,Active_Requests" > "$log_file"

# Monitor for specified duration (default 1 hour)
duration=${1:-3600}  # Duration in seconds
end_time=$(($(date +%s) + duration))

while [ $(date +%s) -lt $end_time ]; do
  performance_data=$(curl -s http://127.0.0.1:55555/performance 2>/dev/null | jq -r '
    [
      now,
      .ai_manager.memory_usage_mb,
      .ai_manager.models_loaded,
      .ai_manager.cache_size,
      .ai_manager.cache_hit_rate,
      .server.active_requests
    ] | @csv
  ' 2>/dev/null)
  
  if [ -n "$performance_data" ]; then
    echo "$performance_data" >> "$log_file"
    echo "$(date): $performance_data"
  fi
  
  sleep 10
done

echo "✅ Monitoring complete. Data saved to $log_file"
kill $APP_PID
```

#### Performance Alert System
```bash
#!/bin/bash
# performance-alerts.sh

echo "Starting performance alert monitoring..."

npm run dev &
APP_PID=$!
sleep 5

# Alert thresholds
MEMORY_THRESHOLD_MB=800
RESPONSE_TIME_THRESHOLD_MS=1000
CACHE_HIT_RATE_THRESHOLD=0.5

while true; do
  # Get performance metrics
  perf_data=$(curl -s http://127.0.0.1:55555/performance)
  
  memory_mb=$(echo "$perf_data" | jq -r '.ai_manager.memory_usage_mb')
  cache_hit_rate=$(echo "$perf_data" | jq -r '.ai_manager.cache_hit_rate')
  
  # Test response time
  start_time=$(date +%s.%N)
  curl -s http://127.0.0.1:55555/health > /dev/null
  end_time=$(date +%s.%N)
  response_time=$(echo "($end_time - $start_time) * 1000" | bc)
  
  # Check thresholds
  if (( $(echo "$memory_mb > $MEMORY_THRESHOLD_MB" | bc -l) )); then
    echo "⚠️  ALERT: High memory usage: ${memory_mb}MB (threshold: ${MEMORY_THRESHOLD_MB}MB)"
  fi
  
  if (( $(echo "$response_time > $RESPONSE_TIME_THRESHOLD_MS" | bc -l) )); then
    echo "⚠️  ALERT: Slow response time: ${response_time}ms (threshold: ${RESPONSE_TIME_THRESHOLD_MS}ms)"
  fi
  
  if (( $(echo "$cache_hit_rate < $CACHE_HIT_RATE_THRESHOLD" | bc -l) )); then
    echo "⚠️  ALERT: Low cache hit rate: ${cache_hit_rate} (threshold: ${CACHE_HIT_RATE_THRESHOLD})"
  fi
  
  sleep 30
done
```

## Automated Test Runner

### Main Test Suite
```bash
#!/bin/bash
# run-performance-tests.sh

echo "🚀 Open Stream Performance Test Suite"
echo "======================================"

# Make scripts executable
chmod +x test-*.sh
chmod +x benchmark-performance.sh

# Check dependencies
if ! command -v jq &> /dev/null; then
    echo "❌ jq is required for JSON processing. Install with: brew install jq"
    exit 1
fi

if ! command -v bc &> /dev/null; then
    echo "❌ bc is required for calculations. Install with: brew install bc"
    exit 1
fi

# Run test suite
echo "Running performance test suite..."

tests=(
    "test-cold-startup.sh:Cold Startup"
    "test-warm-startup.sh:Warm Startup"  
    "test-python-cache.sh:Python Caching"
    "test-memory-stress.sh:Memory Management"
    "test-model-loading.sh:Model Loading"
    "test-cache-performance.sh:Cache Performance"
    "test-api-throughput.sh:API Throughput"
    "test-background-loading.sh:Background Loading"
)

passed=0
failed=0

for test in "${tests[@]}"; do
    IFS=':' read -r script name <<< "$test"
    echo ""
    echo "Running $name test..."
    
    if ./"$script"; then
        echo "✅ $name test passed"
        ((passed++))
    else
        echo "❌ $name test failed"
        ((failed++))
    fi
done

echo ""
echo "======================================"
echo "Test Results: $passed passed, $failed failed"

if [ $failed -eq 0 ]; then
    echo "🎉 All performance tests passed!"
    exit 0
else
    echo "⚠️  Some tests failed. Check the output above."
    exit 1
fi
```

## Expected Performance Targets

### Startup Performance Targets
- **Cold startup**: < 5 seconds to UI ready
- **Warm startup**: < 3 seconds to UI ready  
- **Python discovery (cached)**: < 500ms
- **Server ready**: < 3 seconds

### Runtime Performance Targets
- **Memory usage**: < 1GB peak, < 400MB typical
- **First analysis**: < 500ms (including model loading)
- **Cached analysis**: < 50ms
- **Cache hit rate**: > 60%
- **API throughput**: > 10 requests/second

### Memory Management Targets
- **Model unloading**: Automatic when > 1GB usage
- **Cache cleanup**: LRU eviction maintaining 1000 entries
- **Memory leaks**: No memory growth over time
- **GC efficiency**: < 1% CPU time spent in garbage collection

## Troubleshooting Performance Issues

### Common Issues and Solutions

1. **Slow startup times**
   ```bash
   # Check Python cache
   cat ~/.python-path-cache.json
   
   # Check virtual environment
   ls -la server/venv/
   
   # Verify background loading
   curl http://127.0.0.1:55555/performance | jq '.ai_manager.background_loading'
   ```

2. **High memory usage**
   ```bash
   # Check model status
   curl http://127.0.0.1:55555/performance | jq '.ai_manager'
   
   # Force cleanup
   curl -X POST http://127.0.0.1:55555/cleanup-models
   ```

3. **Low cache hit rates**
   ```bash
   # Check cache statistics
   curl http://127.0.0.1:55555/performance | jq '.ai_manager.cache_size, .ai_manager.cache_hit_rate'
   
   # Verify request patterns (cache works best with repeated requests)
   ```

4. **Slow analysis responses**
   ```bash
   # Check if models are loaded
   curl http://127.0.0.1:55555/health | jq '.models_loaded'
   
   # Check system resources
   top -p $(pgrep -f "python.*main.py")
   ```

This comprehensive testing guide ensures all performance optimizations are working correctly and provides tools for ongoing performance monitoring and validation.