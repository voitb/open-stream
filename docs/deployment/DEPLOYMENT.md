# Open Stream - Deployment Guide

## Build and Distribution Overview

Open Stream uses Electron Builder for cross-platform desktop application packaging. The build process compiles TypeScript, bundles the React application, packages Python backend assets, and creates platform-specific distributables.

## Build Prerequisites

### System Requirements

**Development Machine**:
- **Node.js 18+** with **PNPM package manager** (8.0+)
- **Python 3.8-3.12** (for validation and testing)
- **Git** for version control
- **Platform-specific tools** (see Platform Requirements)

**Target Platform Requirements**:
- **Windows**: 4GB RAM, Windows 10+
- **macOS**: 4GB RAM, macOS 10.15+
- **Linux**: 4GB RAM, Modern distribution with glibc 2.17+

### PNPM Installation and Configuration

**Installing PNPM**:
```bash
# Install globally via npm (if not already installed)
npm install -g pnpm@latest

# Or via other methods:
curl -fsSL https://get.pnpm.io/install.sh | sh  # Unix/macOS
iwr https://get.pnpm.io/install.ps1 -useb | iex  # Windows PowerShell

# Verify installation
pnpm --version  # Should be 8.0+
```

**PNPM Configuration for Build**:
```bash
# Configure PNPM for optimal build performance
pnpm config set store-dir ~/.pnpm-store
pnpm config set network-timeout 300000
pnpm config set fetch-retries 3
```

### Platform-Specific Build Tools

**Windows Development**:
```bash
# Install Visual Studio Build Tools or Visual Studio Community
# Required for native module compilation
pnpm add -g windows-build-tools

# Install NSIS for installer creation (optional - bundled)
choco install nsis
```

**macOS Development**:
```bash
# Install Xcode Command Line Tools
xcode-select --install

# For code signing (optional)
# Apple Developer account required
```

**Linux Development**:
```bash
# Ubuntu/Debian
sudo apt-get install build-essential

# CentOS/RHEL
sudo yum groupinstall "Development Tools"
```

## Build Configuration

### Electron Builder Configuration

The build process is configured in `electron-builder.yml`:

```yaml
# Application Identity
appId: com.yourcompany.openstream
productName: Open Stream

# File Inclusion Rules
files:
  - '!**/.vscode/*'
  - '!src/*'                    # Source files excluded (compiled in out/)
  - '!{.env,.env.*,.npmrc,pnpm-lock.yaml}'
  - '!{tsconfig.json,tsconfig.node.json,tsconfig.web.json}'

# Python Backend Assets
extraResources:
  - from: server
    to: server
    filter:
      - "**/*.py"
      - "requirements.txt"
      - "!venv/**/*"           # Exclude development venv
      - "!__pycache__"

# Unpack for Python execution
asarUnpack:
  - resources/**
```

### TypeScript Compilation Configuration

**Multi-Target Compilation**:
- `tsconfig.json`: Main configuration
- `tsconfig.node.json`: Main and preload processes (Node.js)
- `tsconfig.web.json`: Renderer process (Browser)

```json
// tsconfig.web.json example
{
  "extends": "@electron-toolkit/tsconfig/tsconfig.web.json",
  "include": [
    "src/renderer/src/env.d.ts",
    "src/renderer/src/**/*",
    "src/preload/*.d.ts"
  ],
  "compilerOptions": {
    "composite": true,
    "baseUrl": ".",
    "paths": {
      "@renderer/*": ["src/renderer/src/*"]
    }
  }
}
```

## Build Process

### Local Development Builds

```bash
# Type checking with PNPM
pnpm typecheck

# Development build (unpackaged)
pnpm build:unpack

# Quick development test
pnpm build && pnpm start
```

### Production Builds

**All Platforms** (from appropriate host):
```bash
# Clean previous builds
rm -rf out/ dist/

# Install dependencies using PNPM
pnpm install --frozen-lockfile

# Type checking and compilation
pnpm typecheck
pnpm build

# Platform-specific builds
pnpm build:win     # Windows (from Windows or cross-compile)
pnpm build:mac     # macOS (from macOS only)
pnpm build:linux   # Linux (from Linux or cross-compile)
```

### Cross-Platform Building

**From macOS** (recommended for multi-platform):
```bash
# Build all platforms
pnpm exec electron-builder --mac --win --linux

# Specific platform targeting
pnpm exec electron-builder --win --x64
pnpm exec electron-builder --linux --x64
```

**From Windows**:
```bash
# Windows native
pnpm exec electron-builder --win

# Linux via Docker
pnpm exec electron-builder --linux --x64
```

**From Linux**:
```bash
# Linux native
pnpm exec electron-builder --linux

# Windows via Wine (complex setup)
pnpm exec electron-builder --win
```

## Python Backend Packaging

### Dependency Management

**Requirements Specification** (`server/requirements.txt`):
```txt
# Core server dependencies
fastapi>=0.115.0
uvicorn[standard]>=0.32.0

# AI/ML stack
transformers>=4.36.0
torch>=2.1.0
accelerate>=0.25.0
sentencepiece>=0.1.99
protobuf>=3.20.0

# Support libraries
numpy>=1.24.0
scipy>=1.11.0
huggingface-hub>=0.20.0
```

### Runtime Python Environment

**Virtual Environment Creation** (Handled automatically):
```typescript
// src/main/server.ts - firstTimeSetup()
const venvPath = is.dev 
  ? path.join(__dirname, '../../server/venv')
  : path.join(app.getPath('userData'), 'server-venv')

await this.execCommand(`"${this.pythonPath}" -m venv "${venvPath}"`)
```

**Dependency Installation Process**:
1. Detect system Python (3.8+ required)
2. Create isolated virtual environment
3. Upgrade pip to latest version
4. Install from `requirements.txt`
5. Fallback to individual package installation if batch fails

### Model Management

**Model Download Strategy**:
- Models downloaded on first use (not during build)
- Cached in user data directory: `~/.open-stream/models/`
- Lazy loading reduces distribution size
- Offline fallback to rule-based analysis

**Model Caching Configuration**:
```python
# server/services/ai_manager.py
os.environ['TRANSFORMERS_CACHE'] = str(self.models_dir)
os.environ['HF_HOME'] = str(self.models_dir)
```

## Platform-Specific Deployment

### Windows Deployment

**Build Output**:
- `OpenStream-{version}-setup.exe`: NSIS installer
- Self-extracting installer with Python dependency management
- Desktop and Start Menu shortcuts

**Installation Process**:
```bash
# User-facing installation
1. Download installer from GitHub Releases
2. Run installer (requires admin for system-wide install)
3. Launch application
4. First-run: Python environment setup (automatic)
5. Model download on first analysis (automatic)
```

**Windows-Specific Configuration**:
```yaml
# electron-builder.yml
win:
  executableName: OpenStream
  target: nsis
  icon: build/icon.ico

nsis:
  oneClick: false
  allowToChangeInstallationDirectory: true
  createDesktopShortcut: always
  createStartMenuShortcut: true
  artifactName: ${name}-${version}-setup.${ext}
```

### macOS Deployment

**Build Output**:
- `Open Stream-{version}.dmg`: Disk image for distribution
- Application bundle with embedded Python support
- Code signing ready (requires Apple Developer account)

**Installation Process**:
```bash
# User installation
1. Download DMG from GitHub Releases
2. Mount DMG and drag to Applications
3. Launch from Applications folder
4. macOS may prompt for security approval
5. First-run: Python environment setup (automatic)
```

**macOS-Specific Configuration**:
```yaml
# electron-builder.yml
mac:
  category: public.app-category.entertainment
  target: dmg
  icon: build/icon.icns
  hardenedRuntime: true        # For notarization
  gatekeeperAssess: false      # For development

dmg:
  artifactName: ${name}-${version}.${ext}
  background: build/background.png  # Optional
```

**Code Signing** (Optional):
```bash
# Set signing identity
export CSC_NAME="Developer ID Application: Your Name"
export CSC_KEY_PASSWORD="your-password"

# Build with signing
pnpm build:mac
```

### Linux Deployment

**Build Output**:
- `Open Stream-{version}.AppImage`: Portable application
- No installation required, single executable file
- Includes Python runtime dependencies

**Installation Process**:
```bash
# User installation
1. Download AppImage from GitHub Releases
2. Make executable: chmod +x Open\ Stream-*.AppImage
3. Run directly: ./Open\ Stream-*.AppImage
4. First-run: Python environment setup (automatic)
```

**Linux-Specific Configuration**:
```yaml
# electron-builder.yml
linux:
  target: AppImage
  maintainer: Your Name
  category: Utility
  
appImage:
  artifactName: ${name}-${version}.${ext}
```

## Continuous Integration

### GitHub Actions Workflow

**Multi-Platform Build Pipeline**:
```yaml
# .github/workflows/build.yml
name: Build and Release

on:
  push:
    tags: ['v*']

jobs:
  build:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    
    runs-on: ${{ matrix.os }}
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
      
      - name: Setup PNPM
        uses: pnpm/action-setup@v2
        with:
          version: latest
          run_install: false
      
      - name: Get PNPM store directory
        id: pnpm-cache
        shell: bash
        run: echo "STORE_PATH=$(pnpm store path)" >> $GITHUB_OUTPUT
      
      - name: Setup PNPM cache
        uses: actions/cache@v3
        with:
          path: ${{ steps.pnpm-cache.outputs.STORE_PATH }}
          key: ${{ runner.os }}-pnpm-store-${{ hashFiles('**/pnpm-lock.yaml') }}
          restore-keys: ${{ runner.os }}-pnpm-store-
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pnpm install --frozen-lockfile
      
      - name: Build application
        run: pnpm build
      
      - name: Package application
        run: |
          if [ "$RUNNER_OS" == "Windows" ]; then
            pnpm build:win
          elif [ "$RUNNER_OS" == "macOS" ]; then
            pnpm build:mac
          else
            pnpm build:linux
          fi
        shell: bash
      
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: dist-${{ matrix.os }}
          path: dist/
```

### Automated Release Process

**Release Strategy**:
1. Tag release: `git tag v1.0.0`
2. Push tag: `git push origin v1.0.0`
3. GitHub Actions builds all platforms using PNPM
4. Artifacts uploaded to GitHub Releases
5. Release notes generated automatically

## Distribution and Updates

### GitHub Releases Distribution

**Release Assets**:
- `OpenStream-{version}-setup.exe` (Windows)
- `Open Stream-{version}.dmg` (macOS)  
- `Open Stream-{version}.AppImage` (Linux)
- `latest.yml`, `latest-mac.yml`, `latest-linux.yml` (Update metadata)

### Auto-Updates (Configured but not implemented)

**Update Configuration**:
```typescript
// src/main/index.ts
import { autoUpdater } from 'electron-updater'

autoUpdater.checkForUpdatesAndNotify()
```

**Update Server Configuration**:
```yaml
# dev-app-update.yml (development)
provider: github
owner: your-username
repo: open-stream
```

## Security Considerations

### Code Signing

**Windows Code Signing**:
```bash
# Set certificate
export CSC_LINK="path/to/certificate.p12"
export CSC_KEY_PASSWORD="certificate-password"

# Build with signing using PNPM
pnpm build:win
```

**macOS Code Signing and Notarization**:
```bash
# Apple Developer credentials
export APPLE_ID="your@apple.id"
export APPLE_ID_PASSWORD="app-specific-password"
export CSC_NAME="Developer ID Application: Your Name"

# Build with signing and notarization using PNPM
pnpm build:mac
```

### Security Best Practices

**Build Security**:
- Use exact dependency versions in `package.json`
- Verify Python package integrity
- Code signing for trusted distribution
- Regular security audits: `pnpm audit`

**Runtime Security**:
- Context isolation enabled in renderer
- No remote code execution
- Local-only HTTP server binding
- Process sandboxing via Electron security features

## Troubleshooting Build Issues

### Common Build Problems

**1. TypeScript Compilation Errors**:
```bash
# Clear TypeScript cache
rm -rf out/
pnpm typecheck:node
pnpm typecheck:web
```

**2. Python Dependency Issues**:
```bash
# Verify Python requirements
cd server
python -m pip install -r requirements.txt

# Test Python server manually
python main.py 55555
```

**3. Electron Builder Failures**:
```bash
# Clean build artifacts
rm -rf dist/ out/

# Debug build process using PNPM
DEBUG=electron-builder pnpm build:unpack

# Check electron-builder logs
cat ~/.electron-builder/debug.log
```

**4. PNPM-Specific Build Issues**:
```bash
# Clear PNPM store and cache
pnpm store prune

# Reinstall dependencies
rm -rf node_modules pnpm-lock.yaml
pnpm install

# Check for native module rebuild requirements
pnpm rebuild
```

**5. Platform-Specific Issues**:

**Windows**:
- Install Visual Studio Build Tools
- Check Windows SDK version compatibility
- Verify NSIS installation

**macOS**:
- Update Xcode Command Line Tools
- Check code signing certificates
- Verify notarization credentials

**Linux**:
- Install build dependencies: `build-essential`
- Check glibc version compatibility
- Verify AppImage creation permissions

### Performance Optimization

**Build Performance with PNPM**:
```bash
# Parallel compilation
pnpm typecheck:node & pnpm typecheck:web & wait

# Use PNPM's concurrent execution
pnpm run --parallel build:node build:web

# Leverage PNPM's content-addressable store
# Shared dependencies across projects save time
```

**Distribution Size Optimization**:
- Python venv excluded from package
- AI models downloaded at runtime
- ASAR packaging for Electron assets
- Tree shaking in Vite build
- PNPM's efficient dependency resolution reduces bundle size

### Monitoring and Analytics

**Build Metrics**:
- Monitor build time across platforms
- Track distribution file sizes
- Monitor download statistics from GitHub Releases
- PNPM install performance metrics

**Runtime Telemetry** (Optional):
- Crash reporting integration
- Performance metrics collection
- Feature usage analytics

## PNPM-Specific Optimizations

### Build Performance Improvements

**PNPM Configuration for CI**:
```bash
# .github/workflows/build.yml additions
- name: Configure PNPM
  run: |
    pnpm config set store-dir ~/.pnpm-store
    pnpm config set network-timeout 300000
    pnpm config set fetch-retries 3
    pnpm config set registry https://registry.npmjs.org/
```

**Local Development Optimizations**:
```bash
# Configure PNPM for faster builds
pnpm config set side-effects-cache true
pnpm config set strict-peer-dependencies false

# Use PNPM workspaces if expanding to monorepo
# pnpm-workspace.yaml
packages:
  - 'apps/*'
  - 'packages/*'
```

**Dependency Management Best Practices**:
```json
// package.json PNPM-specific optimizations
{
  "pnpm": {
    "onlyBuiltDependencies": [
      "electron",
      "esbuild",
      "sharp"
    ],
    "neverBuiltDependencies": [
      "fsevents",
      "swc"
    ],
    "peerDependencyRules": {
      "ignoreMissing": ["@babel/core"],
      "allowedVersions": {
        "react": "19",
        "typescript": "5"
      }
    }
  }
}
```

## Deployment Checklist

### Pre-Release Validation

- [ ] All TypeScript compilation passes with PNPM
- [ ] Python server starts successfully
- [ ] AI models load correctly
- [ ] Cross-platform builds complete using PNPM
- [ ] Application launches on target platforms
- [ ] Python dependency installation works
- [ ] Model download and caching functions
- [ ] IPC communication operates correctly
- [ ] Error handling behaves as expected
- [ ] PNPM audit passes security checks

### Release Process

1. **Version Bump**: Update `package.json` version
2. **Changelog**: Document new features and fixes
3. **Dependency Check**: Run `pnpm audit` and `pnpm outdated`
4. **Tag Release**: `git tag v{version}`
5. **Push Tag**: `git push origin v{version}`
6. **Monitor CI**: Verify all platform builds succeed using PNPM
7. **Test Distributions**: Download and test each platform package
8. **Publish Release**: Make GitHub release public
9. **Announce**: Notify users of new version

### Post-Release Monitoring

- Monitor GitHub Issues for deployment problems
- Check download statistics and adoption
- Track crash reports and error telemetry
- Plan next release cycle improvements
- Review PNPM performance metrics and optimizations

This deployment guide ensures reliable, secure, and user-friendly distribution of the Open Stream application across all supported platforms while maintaining the sophisticated AI capabilities and multi-process architecture. PNPM's efficient package management provides faster builds, better dependency resolution, and improved security throughout the deployment pipeline.