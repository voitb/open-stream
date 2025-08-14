# Open Stream Documentation

Welcome to the comprehensive documentation for Open Stream - an AI-powered desktop application for content analysis and moderation. This documentation covers all aspects from development to deployment.

## Quick Navigation

### 🚀 Getting Started
- **[Development Guide](development/DEVELOPMENT.md)** - Set up your development environment and start contributing with PNPM
- **[API Reference](api/API.md)** - Complete API documentation for all endpoints and integrations

### 🏗️ Architecture & Design
- **[System Architecture](architecture/ARCHITECTURE.md)** - Deep dive into the three-process architecture design
- **[API Guidelines](api/api-guidelines.md)** - API design patterns and best practices

### 🚀 Deployment & Operations  
- **[Deployment Guide](deployment/DEPLOYMENT.md)** - Build and distribution processes using PNPM for all platforms
- **[Performance Optimization](performance/PERFORMANCE.md)** - Comprehensive performance tuning strategies

### 🔧 Maintenance & Support
- **[Troubleshooting Guide](troubleshooting/TROUBLESHOOTING.md)** - Solutions for common issues and PNPM-specific problems

## Documentation Structure

```
docs/
├── README.md                     # This navigation document
├── api/                         # API Documentation
│   ├── API.md                   # Complete API reference
│   └── api-guidelines.md        # API design patterns and best practices
├── architecture/                # System Design
│   └── ARCHITECTURE.md          # Three-process architecture overview
├── development/                 # Developer Resources
│   └── DEVELOPMENT.md           # Development setup and workflow with PNPM
├── deployment/                  # Build & Distribution
│   └── DEPLOYMENT.md            # Cross-platform build processes using PNPM
├── performance/                 # Optimization
│   └── PERFORMANCE.md           # Performance tuning strategies
└── troubleshooting/            # Support & Issues
    └── TROUBLESHOOTING.md       # Common problems and PNPM-specific solutions
```

## Technology Stack Overview

**Frontend**: Electron + React 19.1.0 + TypeScript 5.8.3  
**Backend**: Python FastAPI + Hugging Face Transformers  
**AI Models**: BERT-based toxicity detection and sentiment analysis  
**Build System**: Vite + Electron Builder + **PNPM**

## Key Features

- **AI-Powered Analysis**: Advanced toxicity detection and sentiment analysis using state-of-the-art transformer models
- **Desktop Application**: Cross-platform Electron app for Windows, macOS, and Linux
- **Three-Process Architecture**: Secure IPC communication between React frontend, Electron main process, and Python backend
- **Real-time Processing**: Fast inference with model caching and optimization
- **Developer-Friendly**: Comprehensive TypeScript types and PNPM-optimized development tooling

## Document Relationships

```mermaid
graph TD
    A[README.md] --> B[DEVELOPMENT.md]
    A --> C[API.md]
    A --> D[ARCHITECTURE.md]
    
    B --> C
    B --> E[TROUBLESHOOTING.md]
    
    C --> F[api-guidelines.md]
    
    D --> G[DEPLOYMENT.md]
    D --> H[PERFORMANCE.md]
    
    E --> B
    E --> C
    
    G --> H
    H --> D
```

## Getting Started Paths

### For New Developers
1. Start with **[Development Guide](development/DEVELOPMENT.md)** for PNPM environment setup
2. Review **[System Architecture](architecture/ARCHITECTURE.md)** to understand the design
3. Explore **[API Reference](api/API.md)** for implementation details
4. Use **[Troubleshooting Guide](troubleshooting/TROUBLESHOOTING.md)** for PNPM-specific issues when they arise

### For System Administrators
1. Begin with **[Deployment Guide](deployment/DEPLOYMENT.md)** for PNPM-based build processes
2. Review **[Performance Optimization](performance/PERFORMANCE.md)** for tuning
3. Keep **[Troubleshooting Guide](troubleshooting/TROUBLESHOOTING.md)** handy for user support

### For API Consumers
1. Start with **[API Reference](api/API.md)** for endpoint documentation
2. Review **[API Guidelines](api/api-guidelines.md)** for best practices
3. Check **[System Architecture](architecture/ARCHITECTURE.md)** for integration patterns

## PNPM Integration

This project uses **PNPM** as the exclusive package manager for several advantages:

- **Performance**: Up to 2x faster installations than npm
- **Disk Efficiency**: Content-addressable storage saves significant disk space
- **Security**: Better dependency isolation and resolution
- **Developer Experience**: Improved tooling and monorepo support
- **Build Optimization**: Parallel dependency resolution and caching

All documentation has been updated to reflect PNPM usage throughout:
- Installation and setup procedures
- Build and deployment scripts
- Troubleshooting guides
- Development workflows

## Contributing to Documentation

When updating documentation:

1. **Maintain Cross-References**: Update related documents when making changes
2. **Keep Examples Current**: Ensure code examples work with the latest version and PNPM
3. **Follow Structure**: Match the established format and organization
4. **Update Navigation**: Modify this README if adding new documents
5. **Use PNPM**: All package manager references should use PNPM consistently

## Document Maintenance

| Document | Last Updated | Next Review | Owner |
|----------|--------------|-------------|-------|
| [DEVELOPMENT.md](development/DEVELOPMENT.md) | 2025-08-14 | 2025-09-14 | Dev Team |
| [API.md](api/API.md) | 2025-08-13 | 2025-09-13 | Backend Team |
| [ARCHITECTURE.md](architecture/ARCHITECTURE.md) | 2025-08-13 | 2025-10-13 | Tech Lead |
| [DEPLOYMENT.md](deployment/DEPLOYMENT.md) | 2025-08-14 | 2025-09-14 | DevOps |
| [PERFORMANCE.md](performance/PERFORMANCE.md) | 2025-08-13 | 2025-09-13 | Performance Team |
| [TROUBLESHOOTING.md](troubleshooting/TROUBLESHOOTING.md) | 2025-08-14 | 2025-09-14 | Support Team |

## External Resources

- **[Electron Documentation](https://electronjs.org/docs)** - Desktop application framework
- **[FastAPI Documentation](https://fastapi.tiangolo.com)** - Python web framework
- **[Hugging Face Transformers](https://huggingface.co/docs/transformers)** - AI model library
- **[React Documentation](https://react.dev)** - UI library
- **[TypeScript Handbook](https://typescriptlang.org/docs)** - Type system guide
- **[PNPM Documentation](https://pnpm.io/)** - Package manager guide

## Support Channels

- **GitHub Issues**: Technical problems and bug reports
- **GitHub Discussions**: Feature requests and community Q&A
- **Documentation Issues**: Report documentation problems or suggestions
- **PNPM Support**: Package manager specific questions and issues

---

**Last Updated**: August 14, 2025  
**Documentation Version**: 2.1.0  
**Application Version**: Corresponds to latest release