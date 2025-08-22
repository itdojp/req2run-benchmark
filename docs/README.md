# Req2Run Documentation Guide

This directory contains comprehensive documentation for the Req2Run Benchmark system. Below is an organized guide to help you navigate the documentation effectively.

## 📚 Documentation Structure

### Core Documentation

#### System Overview
- **[SYSTEM_OVERVIEW.md](./SYSTEM_OVERVIEW.md)** - High-level overview of the Req2Run benchmark system
  - Executive summary and purpose
  - Technical architecture and requirements
  - Evaluation process and scoring system
  - Getting started guide

#### Problem Specifications
- **[PROBLEM_CATALOG.md](./PROBLEM_CATALOG.md)** - Complete catalog of all 36 benchmark problems
  - Detailed problem descriptions by difficulty level
  - Requirements and evaluation criteria
  - Problem statistics and categories

#### Repository Structure
- **[REPOSITORY_STRUCTURE.md](./REPOSITORY_STRUCTURE.md)** - Complete repository layout and file organization
  - Directory structure explanation
  - File naming conventions
  - Component relationships

### Integration & Setup Guides

#### Environment Setup
- **[SETUP_AND_TROUBLESHOOTING.md](./SETUP_AND_TROUBLESHOOTING.md)** - Complete setup and troubleshooting guide
  - Platform-specific instructions (Linux/Mac/Windows)
  - Multiple setup methods (venv, Docker, Conda, Poetry)
  - Comprehensive troubleshooting for common issues
  - Dependency resolution strategies

#### API Integration
- **[API_REFERENCE.md](./API_REFERENCE.md)** - Complete API documentation
  - RESTful endpoints
  - WebSocket streaming
  - SDK usage examples

- **[AE_FRAMEWORK_INTEGRATION.md](./AE_FRAMEWORK_INTEGRATION.md)** - AE Framework integration guide
  - Integration methods and best practices
  - Complete code examples
  - Testing and validation

### Problem Implementation Guides

- **[implementation-guide.md](./implementation-guide.md)** - Comprehensive implementation guide for all supported languages
  - Python patterns and best practices
  - JavaScript/TypeScript implementation
  - Go implementation patterns
  - Java and Rust guidelines


### Development Workflow

- **[DRAFT_PR_GUIDELINES.md](./DRAFT_PR_GUIDELINES.md)** - GitHub Actions cost optimization guidelines
  - Draft PR workflow
  - CI/CD best practices
  - Cost reduction strategies

## 🗂️ Documentation Organization

### By Audience

#### For AI System Developers
1. Start with [SYSTEM_OVERVIEW.md](./SYSTEM_OVERVIEW.md)
2. Review [PROBLEM_CATALOG.md](./PROBLEM_CATALOG.md)
3. Follow [SETUP_AND_TROUBLESHOOTING.md](./SETUP_AND_TROUBLESHOOTING.md)
4. Use [API_REFERENCE.md](./API_REFERENCE.md) for integration

#### For Framework Integrators
1. Read [AE_FRAMEWORK_INTEGRATION.md](./AE_FRAMEWORK_INTEGRATION.md)
2. Reference [API_REFERENCE.md](./API_REFERENCE.md)
3. Check [REPOSITORY_STRUCTURE.md](./REPOSITORY_STRUCTURE.md)

#### For Problem Implementers
1. Choose problems from [PROBLEM_CATALOG.md](./PROBLEM_CATALOG.md)
2. Follow language-specific implementation guides
3. Use [SETUP_AND_TROUBLESHOOTING.md](./SETUP_AND_TROUBLESHOOTING.md) for local testing

#### For Contributors
1. Review [REPOSITORY_STRUCTURE.md](./REPOSITORY_STRUCTURE.md)
2. Follow [DRAFT_PR_GUIDELINES.md](./DRAFT_PR_GUIDELINES.md)
3. Check language-specific implementation guides

## 📋 Document Consolidation Status

### ✅ Completed Consolidations

1. **Implementation Guides**: Unified into `implementation-guide.md`
   - All language-specific patterns in one document
   - Reduces duplication and maintains consistency

2. **Setup Documentation**: Combined into `SETUP_AND_TROUBLESHOOTING.md`
   - Merged environment setup with troubleshooting
   - Single reference for all setup needs

### 📚 Maintained Separation

3. **API Documentation**: Kept separate with cross-references
   - `API_REFERENCE.md` for general API users
   - `AE_FRAMEWORK_INTEGRATION.md` for specific framework integration
   - Clear cross-references between documents

4. **Problem Documentation**: `PROBLEM_CATALOG.md` remains standalone
   - Single source of truth for all problems
   - Well-organized and comprehensive

## 🔄 Documentation Maintenance

### Update Frequency
- **Problem Catalog**: Update when new problems are added
- **API Reference**: Update with each API version change
- **Setup Guides**: Update when dependencies or requirements change
- **System Overview**: Quarterly review for accuracy

### Version Control
- All documentation follows semantic versioning
- Major changes require PR review
- Minor updates can be direct commits

## 🌐 Internationalization

Selected documents are available in multiple languages:
- English (primary)
- Japanese (日本語)

See individual document headers for language availability.

## 📞 Support

For documentation issues or suggestions:
- Create an issue in the [GitHub repository](https://github.com/itdojp/req2run-benchmark)
- Contact: contact@itdo.jp

---

**Last Updated**: 2024-01-30
**Documentation Version**: 1.0.0