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
- **[ENVIRONMENT_SETUP.md](./ENVIRONMENT_SETUP.md)** - Comprehensive environment setup guide
  - Platform-specific instructions (Linux/Mac/Windows)
  - Multiple setup methods (venv, Docker, Conda, Poetry)
  - Troubleshooting common issues

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

#### Language-Specific Guides
- **[PYTHON_IMPLEMENTATION_GUIDE.md](./PYTHON_IMPLEMENTATION_GUIDE.md)** - Python implementation patterns and best practices
- **[JAVASCRIPT_IMPLEMENTATION_GUIDE.md](./JAVASCRIPT_IMPLEMENTATION_GUIDE.md)** - JavaScript/TypeScript implementation guide
- **[GO_IMPLEMENTATION_GUIDE.md](./GO_IMPLEMENTATION_GUIDE.md)** - Go implementation patterns

### Troubleshooting & Support

- **[DEPENDENCY_TROUBLESHOOTING.md](./DEPENDENCY_TROUBLESHOOTING.md)** - Common dependency issues and solutions
  - Platform-specific issues
  - Virtual environment problems
  - Package compatibility

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
3. Follow [ENVIRONMENT_SETUP.md](./ENVIRONMENT_SETUP.md)
4. Use [API_REFERENCE.md](./API_REFERENCE.md) for integration

#### For Framework Integrators
1. Read [AE_FRAMEWORK_INTEGRATION.md](./AE_FRAMEWORK_INTEGRATION.md)
2. Reference [API_REFERENCE.md](./API_REFERENCE.md)
3. Check [REPOSITORY_STRUCTURE.md](./REPOSITORY_STRUCTURE.md)

#### For Problem Implementers
1. Choose problems from [PROBLEM_CATALOG.md](./PROBLEM_CATALOG.md)
2. Follow language-specific implementation guides
3. Use [ENVIRONMENT_SETUP.md](./ENVIRONMENT_SETUP.md) for local testing

#### For Contributors
1. Review [REPOSITORY_STRUCTURE.md](./REPOSITORY_STRUCTURE.md)
2. Follow [DRAFT_PR_GUIDELINES.md](./DRAFT_PR_GUIDELINES.md)
3. Check language-specific implementation guides

## 📋 Document Consolidation Recommendations

Based on content analysis, the following consolidation is recommended:

### 1. Merge Implementation Guides
**Current**: Three separate language-specific guides (Python, JavaScript, Go)
**Recommendation**: Create a single `IMPLEMENTATION_GUIDE.md` with language-specific sections
**Rationale**: Reduces duplication of general principles, easier to maintain consistency

### 2. Combine Setup Documentation
**Current**: `ENVIRONMENT_SETUP.md` and `DEPENDENCY_TROUBLESHOOTING.md`
**Recommendation**: Merge into comprehensive `SETUP_AND_TROUBLESHOOTING.md`
**Rationale**: Users typically need both during initial setup

### 3. Consolidate API Documentation
**Current**: `API_REFERENCE.md` and `AE_FRAMEWORK_INTEGRATION.md` have overlapping content
**Recommendation**: Keep separate but ensure clear cross-references
**Rationale**: Different audiences - general API users vs. specific framework integration

### 4. Unified Problem Documentation
**Current**: `PROBLEM_CATALOG.md` contains all problem details
**Recommendation**: Keep as-is, well-organized
**Rationale**: Single source of truth for problems

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