# Open Stream

An AI-powered desktop application for content analysis and moderation, built with Electron, React, and Python FastAPI. Open Stream provides real-time toxicity detection and sentiment analysis using state-of-the-art Hugging Face transformer models.

## Features

- **AI-Powered Analysis**: Advanced toxicity detection and sentiment analysis using BERT-based models
- **Desktop Application**: Cross-platform support for Windows, macOS, and Linux
- **Real-time Processing**: Fast inference with intelligent model caching
- **Secure Architecture**: Three-process design with IPC communication
- **Developer-Friendly**: Comprehensive TypeScript types and development tooling

## Quick Start

### Prerequisites

- **Node.js 18+** with **PNPM package manager**
- **Python 3.8-3.12** (3.11 or 3.12 recommended)
- **4-8GB RAM** for AI model operations

### Package Manager Requirement

**Important**: This project uses **PNPM** as the package manager. Do not use npm or yarn.

```bash
# Install PNPM globally if not already installed
npm install -g pnpm@latest

# Or via other methods:
curl -fsSL https://get.pnpm.io/install.sh | sh  # Unix/macOS
iwr https://get.pnpm.io/install.ps1 -useb | iex  # Windows PowerShell

# Verify installation
pnpm --version  # Should be 8.0+
```

### Installation & Development

```bash
# Clone repository
git clone <repository-url>
cd open-stream

# Install dependencies with PNPM
pnpm install

# Start development environment
pnpm dev
```

### Building for Distribution

```bash
# Windows
pnpm build:win

# macOS  
pnpm build:mac

# Linux
pnpm build:linux
```

## Technology Stack

- **Frontend**: Electron + React 19.1.0 + TypeScript 5.8.3 + Vite
- **Backend**: Python FastAPI + Uvicorn + Hugging Face Transformers
- **AI Models**: BERT-based toxicity detection and sentiment analysis
- **Build System**: Electron Builder + **PNPM**

## Documentation

Comprehensive documentation is available in the [`docs/`](docs/) directory:

- **[📚 Documentation Overview](docs/README.md)** - Complete navigation of all documentation
- **[🚀 Development Guide](docs/development/DEVELOPMENT.md)** - Set up your development environment with PNPM
- **[📖 API Reference](docs/api/API.md)** - Complete API documentation
- **[🏗️ System Architecture](docs/architecture/ARCHITECTURE.md)** - Deep dive into the design
- **[🚢 Deployment Guide](docs/deployment/DEPLOYMENT.md)** - Build and distribution processes using PNPM
- **[⚡ Performance Optimization](docs/performance/PERFORMANCE.md)** - Performance tuning strategies
- **[🔧 Troubleshooting](docs/troubleshooting/TROUBLESHOOTING.md)** - Common issues and PNPM-specific solutions

## Project Structure

```
open-stream/
├── src/                    # Electron + React source
│   ├── main/              # Electron main process
│   ├── preload/           # IPC security bridge
│   └── renderer/          # React application
├── server/                # Python FastAPI backend
│   ├── main.py           # FastAPI application
│   ├── services/         # AI service modules
│   └── requirements.txt  # Python dependencies
├── docs/                  # Documentation
├── pnpm-lock.yaml        # PNPM lock file (DO NOT edit manually)
└── build/                 # Build resources
```

## Development Environment

### Recommended IDE Setup

- [VSCode](https://code.visualstudio.com/) + [ESLint](https://marketplace.visualstudio.com/items?itemName=dbaeumer.vscode-eslint) + [Prettier](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode)
- [Python Extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
- [TypeScript Extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode.vscode-typescript-next)

### Available Commands (PNPM)

```bash
# Development
pnpm dev                    # Start development environment
pnpm dev:renderer          # React frontend only
pnpm run server:dev        # Python backend only

# Quality Assurance
pnpm typecheck             # TypeScript type checking
pnpm lint                  # ESLint
pnpm format               # Prettier formatting

# Building
pnpm build                # Compile TypeScript
pnpm build:unpack         # Build without packaging

# Dependency Management
pnpm install              # Install all dependencies
pnpm add <package>        # Add production dependency
pnpm add -D <package>     # Add development dependency
pnpm update               # Update dependencies
pnpm audit                # Security audit
```

## Architecture Overview

Open Stream uses a sophisticated three-process architecture:

1. **Renderer Process (React)**: User interface and interactions
2. **Main Process (Electron)**: Application lifecycle and IPC bridge
3. **Python Backend (FastAPI)**: AI model management and inference

Communication flows securely through IPC channels with full type safety.

## Performance Characteristics

- **Startup Time**: 2-3 seconds (warm start)
- **Model Loading**: 30-60 seconds (first use, cached thereafter)
- **Analysis Latency**: 100-500ms per request
- **Memory Usage**: 2-5GB (including loaded AI models)

## Why PNPM?

This project uses PNPM for several key advantages:

- **Faster installations** - Up to 2x faster than npm
- **Disk space efficiency** - Content-addressable storage saves space
- **Better dependency resolution** - Strict, non-flat node_modules structure
- **Enhanced security** - Better dependency isolation
- **Monorepo support** - Built-in workspace features
- **Improved performance** - Parallel dependency resolution

## Contributing

1. Read the [Development Guide](docs/development/DEVELOPMENT.md) for PNPM setup instructions
2. Review the [System Architecture](docs/architecture/ARCHITECTURE.md) to understand the design
3. Check the [API Documentation](docs/api/API.md) for integration details
4. Use the [Troubleshooting Guide](docs/troubleshooting/TROUBLESHOOTING.md) for PNPM-specific issues

**Contributing Requirements**:
- Use PNPM for all package management operations
- Run `pnpm typecheck` before committing
- Follow the established code style with `pnpm format`
- Test changes with `pnpm dev`

## License

[License information to be added]

## Support

- **GitHub Issues**: Technical problems and bug reports
- **GitHub Discussions**: Feature requests and community Q&A
- **Documentation**: Comprehensive guides in the `docs/` directory
- **PNPM Support**: Check [PNPM documentation](https://pnpm.io/) for package manager issues

---

**Built with** ❤️ **using cutting-edge AI and modern web technologies, powered by PNPM**