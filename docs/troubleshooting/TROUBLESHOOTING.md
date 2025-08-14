# Open Stream - Troubleshooting Guide

## Common Issues and Solutions

This guide covers the most frequent issues encountered with Open Stream and provides step-by-step solutions for resolving them.

## Application Startup Issues

### Issue: Application Won't Start

**Symptoms**:
- Electron window doesn't appear
- Application crashes immediately
- Error messages in console

**Diagnostic Steps**:
```bash
# Check if Node.js and PNPM are properly installed
node --version  # Should be 18+
pnpm --version  # Should be 8+

# Verify project installation
cd open-stream
pnpm install

# Check for TypeScript errors
pnpm typecheck

# Try starting with verbose logging
DEBUG=* pnpm dev
```

**Solutions**:

1. **Missing Dependencies**:
```bash
# Reinstall all dependencies using PNPM
rm -rf node_modules pnpm-lock.yaml
pnpm install

# Rebuild native modules
pnpm rebuild
```

2. **TypeScript Compilation Errors**:
```bash
# Clean compiled output
rm -rf out/

# Check individual TypeScript configs
pnpm typecheck:node
pnpm typecheck:web

# Fix any reported type errors before proceeding
```

3. **Electron Version Conflicts**:
```bash
# Check Electron installation
pnpm exec electron --version

# Reinstall Electron if needed
pnpm add -D electron@latest
```

4. **PNPM-Specific Issues**:
```bash
# Clear PNPM cache and store
pnpm store prune

# Check PNPM configuration
pnpm config list

# Verify PNPM installation
which pnpm
pnpm --version
```

### Issue: Python Server Won't Start

**Symptoms**:
- "Failed to start Python server" error
- Backend server timeout
- Health check failures

**Diagnostic Steps**:
```bash
# Check Python installation
python3 --version  # Should be 3.8+
which python3

# Test manual server startup
cd server
python3 main.py 55555

# Check for port conflicts
lsof -i :55555  # macOS/Linux
netstat -an | grep :55555  # Windows
```

**Solutions**:

1. **Python Not Found**:
```bash
# Install Python 3.8+ from python.org
# Or use package manager:

# macOS with Homebrew
brew install python@3.11

# Ubuntu/Debian
sudo apt-get install python3.11 python3.11-venv python3.11-pip

# Windows - Download from python.org
```

2. **Virtual Environment Issues**:
```bash
# Manual venv creation and testing
cd server
python3 -m venv test-venv
source test-venv/bin/activate  # Unix/macOS
# test-venv\Scripts\activate     # Windows

# Test dependency installation
pip install -r requirements.txt
python main.py 55555
```

3. **Port Already in Use**:
```bash
# Find and kill process using the port
# macOS/Linux
lsof -ti:55555 | xargs kill -9

# Windows
netstat -ano | findstr :55555
taskkill /PID <process_id> /F

# Or restart the application to get a new random port
```

## AI Model Loading Issues

### Issue: Models Won't Download

**Symptoms**:
- "Failed to load models" error
- Timeout during model download
- Network connection errors

**Diagnostic Steps**:
```bash
# Test internet connectivity to Hugging Face
curl -I https://huggingface.co

# Check available disk space
df -h  # Unix/macOS
dir C:\  # Windows

# Test manual model download
cd server
python3 -c "
from transformers import pipeline
model = pipeline('sentiment-analysis', model='distilbert-base-uncased-finetuned-sst-2-english')
print('Model loaded successfully')
"
```

**Solutions**:

1. **Network/Firewall Issues**:
```bash
# Configure proxy if needed
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080

# Or disable SSL verification (not recommended for production)
export CURL_CA_BUNDLE=""
```

2. **Insufficient Disk Space**:
```bash
# Check model cache directory
ls -la ~/.cache/huggingface/  # Default location

# Clean old models if needed
rm -rf ~/.cache/huggingface/transformers/

# Or specify custom cache directory with more space
export TRANSFORMERS_CACHE=/path/to/large/disk/models
```

3. **Model Cache Corruption**:
```bash
# Clear model cache completely
cd server
rm -rf models/

# Clear Hugging Face cache
rm -rf ~/.cache/huggingface/

# Restart application to re-download models
```

### Issue: Models Load But Inference Fails

**Symptoms**:
- Models appear to load successfully
- Analysis requests return errors
- GPU/CUDA related errors

**Diagnostic Steps**:
```bash
# Test models individually
cd server
python3 -c "
from transformers import pipeline
import torch

print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')

# Test toxicity model
tox_model = pipeline('text-classification', model='unitary/toxic-bert', device=-1)
result = tox_model('This is a test')
print(f'Toxicity result: {result}')

# Test sentiment model
sent_model = pipeline('sentiment-analysis', model='distilbert-base-uncased-finetuned-sst-2-english', device=-1)
result = sent_model('This is great')
print(f'Sentiment result: {result}')
"
```

**Solutions**:

1. **CUDA/GPU Issues**:
```bash
# Force CPU-only inference
# Edit server/services/ai_manager.py
# Change: self.device = 0 if torch.cuda.is_available() else -1
# To: self.device = -1  # Force CPU

# Restart application
```

2. **Memory Issues**:
```bash
# Check available memory
free -h  # Linux
vm_stat  # macOS
wmic OS get TotalVisibleMemorySize,FreePhysicalMemory  # Windows

# Reduce model memory usage by loading one at a time
# Edit server/services/ai_manager.py to implement lazy loading
```

3. **PyTorch/Transformers Version Conflicts**:
```bash
# Check versions
pip list | grep -E "(torch|transformers)"

# Reinstall with compatible versions
pip uninstall torch transformers
pip install torch>=2.0.0 transformers>=4.30.0
```

## IPC Communication Issues

### Issue: Frontend Can't Communicate with Backend

**Symptoms**:
- "Backend server not ready" errors
- IPC timeouts
- No response from serverAPI calls

**Diagnostic Steps**:
```bash
# Check if backend is running
curl http://127.0.0.1:55555/health

# Test IPC channels in renderer dev tools
window.serverAPI.getPort().then(console.log).catch(console.error)
window.serverAPI.isReady().then(console.log).catch(console.error)

# Check main process logs in terminal
```

**Solutions**:

1. **Backend Server Not Started**:
```bash
# Check server startup logs
# Look for "✅ Backend server is ready!" message

# If not found, check Python server logs
# Restart application with clean state
```

2. **IPC Handler Issues**:
```typescript
// Check if IPC handlers are properly registered in src/main/index.ts
// Verify the handlers match the preload API definitions

// Test individual IPC channels:
// In main process console:
console.log('IPC handlers registered:', Object.keys(ipcMain._events))
```

3. **Context Isolation Problems**:
```typescript
// Verify preload script is loading properly
// Check src/preload/index.ts

// In renderer dev tools:
console.log('serverAPI available:', !!window.serverAPI)
console.log('serverAPI methods:', Object.keys(window.serverAPI))
```

## Performance Issues

### Issue: Slow AI Analysis

**Symptoms**:
- Analysis takes >10 seconds
- UI becomes unresponsive
- High CPU usage

**Diagnostic Steps**:
```bash
# Monitor CPU and memory usage
top  # Unix/macOS
taskmgr  # Windows

# Check Python process specifically
ps aux | grep python
ps aux | grep electron

# Test analysis performance directly
time curl -X POST http://127.0.0.1:55555/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "test message"}'
```

**Solutions**:

1. **First-Time Model Loading**:
```bash
# Models load on first request, this is normal
# Wait 30-60 seconds for initial load
# Subsequent requests should be much faster

# To pre-load models, modify server/main.py:
# Call load_models() in startup_event instead of on first request
```

2. **CPU Optimization**:
```python
# Edit server/services/ai_manager.py
import torch
import os

# Add CPU optimization
torch.set_num_threads(4)  # Adjust based on CPU cores
os.environ['OMP_NUM_THREADS'] = '4'
os.environ['MKL_NUM_THREADS'] = '4'
```

3. **Memory Swapping**:
```bash
# Check if system is swapping memory
# Add more RAM or reduce model count
# Monitor with htop or Activity Monitor

# Temporary solution: Restart application to clear memory
```

### Issue: High Memory Usage

**Symptoms**:
- Application uses >4GB RAM
- System becomes slow
- Out of memory errors

**Solutions**:

1. **Model Memory Optimization**:
```python
# Edit server/services/ai_manager.py
# Add memory-efficient loading

def get_toxicity_model(self):
    if 'toxicity' not in self.models:
        self.models['toxicity'] = pipeline(
            "text-classification",
            model="unitary/toxic-bert",
            device=-1,
            model_kwargs={
                "low_cpu_mem_usage": True,
                "torch_dtype": torch.float16  # Use half precision
            }
        )
    return self.models['toxicity']
```

2. **Implement Model Cleanup**:
```python
# Add to ai_manager.py
def cleanup_unused_models(self):
    """Remove models from memory when not in use"""
    import gc
    self.models.clear()
    gc.collect()
    torch.cuda.empty_cache() if torch.cuda.is_available() else None
```

## Build and Distribution Issues

### Issue: Build Fails

**Symptoms**:
- TypeScript compilation errors
- Electron packaging failures
- Missing dependencies in build

**Diagnostic Steps**:
```bash
# Check build step by step using PNPM
pnpm typecheck
pnpm build
pnpm build:unpack

# Check for platform-specific issues
DEBUG=electron-builder pnpm build:win
```

**Solutions**:

1. **TypeScript Errors**:
```bash
# Fix TypeScript configuration
# Check tsconfig.json, tsconfig.node.json, tsconfig.web.json

# Common fixes:
# - Update type definitions
# - Fix import paths
# - Resolve module resolution issues
```

2. **Missing Python Files in Build**:
```yaml
# Check electron-builder.yml
extraResources:
  - from: server
    to: server
    filter:
      - "**/*.py"
      - "requirements.txt"
      - "!venv/**/*"  # Make sure venv is excluded
```

3. **Code Signing Issues**:
```bash
# For macOS builds
export CSC_IDENTITY_AUTO_DISCOVERY=false  # Disable auto-signing

# For Windows builds
# Ensure certificate is properly configured
```

4. **PNPM Build Dependencies**:
```bash
# Clear PNPM cache and rebuild
pnpm store prune
rm -rf node_modules pnpm-lock.yaml
pnpm install

# Check for native dependencies
pnpm rebuild
```

### Issue: Distributed App Won't Start

**Symptoms**:
- Packaged app crashes on launch
- Python server fails in production
- Missing dependencies

**Solutions**:

1. **Python Path Issues**:
```typescript
// Check src/main/server.ts
// Verify getServerScriptPath() returns correct path for production

private getServerScriptPath(): string {
  if (is.dev) {
    return path.join(__dirname, '../../server/main.py')
  } else {
    // Verify this path is correct for your packaging setup
    return path.join(process.resourcesPath, 'server', 'main.py')
  }
}
```

2. **Missing Python Runtime**:
```bash
# User doesn't have Python installed
# Add installation check and user guidance

# Or bundle Python with the application (advanced)
```

## Development Environment Issues

### Issue: Hot Reload Not Working

**Symptoms**:
- Changes to code don't reflect in UI
- Need to restart application for changes
- Vite dev server issues

**Solutions**:

1. **Check Vite Configuration**:
```typescript
// Verify electron.vite.config.ts is correct
// Check that HMR is enabled
// Ensure file paths are correct
```

2. **Port Conflicts**:
```bash
# Check if Vite dev server port is available
lsof -i :5173  # Default Vite port

# Kill conflicting processes or change port
```

3. **File System Watching**:
```bash
# Increase file watcher limits (Linux)
echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# macOS - no action needed usually
# Windows - restart VS Code/editor
```

### Issue: TypeScript Errors in IDE

**Symptoms**:
- Red squiggly lines in VS Code
- IntelliSense not working
- Type checking inconsistencies

**Solutions**:

1. **Reload TypeScript Service**:
```
Ctrl+Shift+P → "TypeScript: Reload Projects"
```

2. **Check TypeScript Configuration**:
```bash
# Verify tsconfig files are valid using PNPM
pnpm exec tsc --noEmit -p tsconfig.json
pnpm exec tsc --noEmit -p tsconfig.web.json
pnpm exec tsc --noEmit -p tsconfig.node.json
```

3. **Update Type Definitions**:
```bash
pnpm add -D @types/node@latest
pnpm add -D @types/react@latest
pnpm add -D @types/react-dom@latest
```

### Issue: PNPM-Specific Problems

**Symptoms**:
- Package installation failures
- Module resolution errors
- Peer dependency warnings

**Solutions**:

1. **PNPM Cache Issues**:
```bash
# Clear PNPM store and cache
pnpm store prune

# Remove node_modules and reinstall
rm -rf node_modules pnpm-lock.yaml
pnpm install
```

2. **Peer Dependency Issues**:
```bash
# Check peer dependency requirements
pnpm install --dev

# Configure peer dependency rules in package.json:
{
  "pnpm": {
    "peerDependencyRules": {
      "ignoreMissing": ["react-native"],
      "allowedVersions": {
        "react": "19"
      }
    }
  }
}
```

3. **Module Hoisting Issues**:
```bash
# Create/edit .npmrc file for problematic packages
echo 'shamefully-hoist=true' >> .npmrc

# Or use public-hoist-pattern for specific packages
echo 'public-hoist-pattern[]=*eslint*' >> .npmrc
```

4. **PNPM Store Corruption**:
```bash
# Verify PNPM store integrity
pnpm store status

# Rebuild store if needed
pnpm store prune --force
pnpm install
```

## Diagnostic Tools and Commands

### System Information Collection

```bash
#!/bin/bash
# scripts/collect-system-info.sh

echo "=== Open Stream System Information ==="
echo "Date: $(date)"
echo

echo "=== System ==="
uname -a
echo

echo "=== Node.js and PNPM ==="
node --version
pnpm --version
pnpm store path
echo

echo "=== Python ==="
python3 --version
pip3 --version
which python3
echo

echo "=== Memory ==="
free -h 2>/dev/null || vm_stat 2>/dev/null || echo "Memory info not available"
echo

echo "=== Disk Space ==="
df -h
echo

echo "=== Process List ==="
ps aux | grep -E "(electron|python|node)" | grep -v grep
echo

echo "=== Network ==="
curl -s -I https://huggingface.co | head -1
curl -s http://127.0.0.1:55555/health 2>/dev/null || echo "Backend not responding"
echo

echo "=== Open Stream Files ==="
ls -la
ls -la server/ 2>/dev/null || echo "Server directory not found"
echo

echo "=== PNPM Configuration ==="
pnpm config list
echo "PNPM Store Size:"
du -sh $(pnpm store path) 2>/dev/null || echo "Store path not accessible"
echo
```

### Log Collection

```bash
#!/bin/bash
# scripts/collect-logs.sh

echo "Collecting Open Stream logs..."

# Create logs directory
mkdir -p logs

# Electron main process logs
echo "Collecting Electron logs..."
cp ~/.config/open-stream/logs/*.log logs/ 2>/dev/null || echo "No Electron logs found"

# Python server logs
echo "Collecting Python logs..."
# Add Python logging to file in server/main.py if not already implemented

# System logs
echo "Collecting system logs..."
dmesg | tail -100 > logs/system.log 2>/dev/null || echo "System logs not accessible"

# Package info
echo "Collecting package information..."
pnpm list > logs/packages.txt 2>/dev/null
pip list > logs/python-packages.txt 2>/dev/null

echo "Logs collected in ./logs/ directory"
```

### Health Check Script

```bash
#!/bin/bash
# scripts/health-check.sh

echo "=== Open Stream Health Check ==="

# Check if application is running
if pgrep -f "open-stream" > /dev/null; then
    echo "✅ Application is running"
else
    echo "❌ Application is not running"
    exit 1
fi

# Check backend server
if curl -s http://127.0.0.1:55555/health > /dev/null; then
    echo "✅ Backend server is responding"
    
    # Check AI status
    AI_STATUS=$(curl -s http://127.0.0.1:55555/health | grep -o '"ai_enabled":[^,]*' | cut -d: -f2)
    if [ "$AI_STATUS" = "true" ]; then
        echo "✅ AI models are loaded"
    else
        echo "⚠️ AI models are not loaded"
    fi
else
    echo "❌ Backend server is not responding"
fi

# Test analysis functionality
echo "Testing analysis functionality..."
RESULT=$(curl -s -X POST http://127.0.0.1:55555/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "test"}' | grep -o '"ai_enabled":[^,]*' | cut -d: -f2)

if [ "$RESULT" = "true" ]; then
    echo "✅ Analysis is working with AI"
elif [ "$RESULT" = "false" ]; then
    echo "⚠️ Analysis is working with fallback rules"
else
    echo "❌ Analysis is not working"
fi

# Check PNPM environment
echo "Checking PNPM environment..."
if command -v pnpm &> /dev/null; then
    echo "✅ PNPM is installed ($(pnpm --version))"
else
    echo "❌ PNPM is not installed"
fi

echo "Health check complete"
```

## Getting Help

### Before Seeking Help

1. **Run Diagnostic Scripts**: Use the provided scripts to collect system information
2. **Check Logs**: Look for error messages in console output
3. **Try Basic Solutions**: Restart application, clear caches, reinstall dependencies with PNPM
4. **Reproduce Issue**: Document exact steps to reproduce the problem

### Information to Include

When reporting issues, include:

- Operating system and version
- Node.js and PNPM versions (`node --version`, `pnpm --version`)
- Python version (`python3 --version`)
- Full error messages and stack traces
- System information from diagnostic scripts
- Steps to reproduce the issue
- Expected vs actual behavior

### Community Resources

- **GitHub Issues**: Check existing issues and create new ones
- **Documentation**: Review all documentation files
- **Stack Overflow**: Search for similar issues
- **Electron Community**: Electron-specific questions
- **Hugging Face Forums**: AI/ML related questions
- **PNPM GitHub**: PNPM-specific questions and issues

### Emergency Recovery

If the application is completely broken:

1. **Complete Reinstall**:
```bash
# Backup any important data
# Remove application completely
rm -rf node_modules server/venv server/models
rm -rf ~/.cache/huggingface
rm -rf out/ dist/

# Clear PNPM cache
pnpm store prune

# Reinstall from scratch
pnpm install
pnpm dev
```

2. **Reset to Known Good State**:
```bash
# Use git to reset to last working commit
git status
git stash  # Save current changes
git checkout main  # Or last known good commit
pnpm install
pnpm dev
```

3. **Contact Support**: If all else fails, create a detailed issue report with diagnostic information

This troubleshooting guide should help resolve the vast majority of issues encountered with Open Stream. The key is to systematically work through the diagnostic steps and apply the appropriate solutions based on the specific symptoms observed. PNPM's efficient package management and caching can help resolve many dependency-related issues quickly.