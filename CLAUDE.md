# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a **documentation and knowledge repository** for Hebbia, containing internal documentation, onboarding materials, and architectural specifications. This is NOT a code repository - it contains markdown files with documentation, links to external resources, and knowledge base content.

## Repository Overview

This repository contains comprehensive documentation and knowledge resources for Hebbia, organized into several key areas:

- **Knowledge Base**: Core technical documentation, product vision, architecture, and data models
- **Mono Documentation**: Detailed technical analysis, codebase assessment, API specifications, and performance optimization
- **Interview Materials**: Engineering guidelines, levels, system design prep, and hiring processes
- **Tools & Utilities**: Database exploration tools and organizational documentation
- **Onboarding**: New hire processes, engineering links, and setup documentation
- **Auto-Sync Integration**: The `mono` directory links to `~/Hebbia/mono_analysis` with automatic synchronization

## Key Documentation Files

### Architecture Documentation

- **`Knowledge_Base/mono_architecture.md`**: Comprehensive microservices architecture overview including:
  - Core services: brain (orchestrator), agents (AI), doc_manager, search, sheets
  - Data pipeline: fastbuild → doc_manager_indexer → Elasticsearch
  - Infrastructure: PostgreSQL, Kafka, Temporal workflows, AWS services
  - Multi-tenant SaaS architecture with RBAC permissions

### Mono Architecture Technical Documentation

- **`mono_doc/COMPREHENSIVE_CODEBASE_ANALYSIS.md`**: Detailed analysis of the mono codebase structure and patterns
- **`mono_doc/CODEBASE_ASSESSMENT.md`**: Assessment of codebase quality, architecture, and recommendations
- **`mono_doc/api-guidelines.md`**: API development standards and best practices
- **`mono_doc/openapi.yaml`**: Complete OpenAPI specification for the mono system
- **`mono_doc/SHEETS_PERFORMANCE_OPTIMIZATION.md`**: Comprehensive performance optimization strategies for the Sheets feature
- **`mono_doc/SHEETS_PERFORMANCE_LOGGING_STRATEGY.md`**: Performance monitoring and logging approach for Sheets

### Data Models

- **`Knowledge_Base/data_models_documentation.md`**: Complete database schema documentation
  - Multi-tenant hierarchy: Tenant → Organization → Users/Repositories
  - Core models: User, Document, Repository, Sheet, DocumentChatConversation
  - All models centralized in `brain/models/` (100+ models)
  - UUID primary keys, JSONB metadata, soft deletes, versioning patterns

### Product Strategy & Planning

- **`Knowledge_Base/Product_Vision_Doc.md`**: Company vision focused on Information Retrieval (IR)
  - Mission: "Most capable AI platform"
  - Core differentiator: Matrix Agent for metadata-driven search
  - Priority framework: P0 (IR + revenue) → P1 (IR only) → P2 (revenue only) → P3 (neither)
- **`Knowledge_Base/Product_strategy.md`**: Product strategy and planning documentation
- **`Knowledge_Base/2025_q1_product_roadmap.md`**: Q1 2025 product roadmap and priorities

### Interview & Hiring Materials

- **`interview/Hebbia_Eng_Guidelines.md`**: Comprehensive engineering interview guidelines and process
- **`interview/Hebbia_Levels.md`**: Engineering levels, expectations, and career progression
- **`interview/System_Design_Interview_Guidelines.md`**: System design interview preparation and guidelines
- **`interview/Stripe_Interview_Process_for_Different_Roles.md`**: Detailed interview process for various engineering roles

### Tools & Utilities

- **`tools/db_explorer.py`**: Database exploration utility for working with Hebbia's data models
- **`tools/org_structure.md`**: Organizational structure documentation and team information

## Important Context

### Company Background

Hebbia is an AI-powered document processing and search platform serving enterprise customers, particularly in financial services and legal verticals. The platform transforms unstructured documents into AI-queryable knowledge through:

1. **Document Processing Pipeline**: Ingestion → OCR/Parsing → Indexing → AI-powered search
2. **Matrix Interface**: Spreadsheet-like collaborative data analysis tool
3. **Multi-Document Chat**: AI conversations across document collections
4. **Enterprise Features**: Multi-tenancy, RBAC, integrations (Box, SharePoint, S3)

### Technical Stack (Referenced in docs)

- **Languages**: Python (FastAPI), TypeScript/JavaScript (frontend)
- **Databases**: PostgreSQL, Elasticsearch, Weaviate (vector search)
- **Infrastructure**: AWS (ECS, Lambda, RDS, S3), Docker, Terraform
- **AI/ML**: Multiple LLM providers, document processing, semantic search
- **Workflow**: Temporal for orchestration, Kafka for event streaming

## Usage Notes

Since this is a documentation repository:

- **Do NOT** look for package.json, requirements.txt, or build scripts
- **Do NOT** expect to find source code or tests
- **Focus on** understanding architectural patterns and business context from documentation
- **Reference** external links for complete technical specifications
- **Understand** this represents the knowledge base for a complex microservices platform

## Working with This Repository

When asked about Hebbia's architecture or systems:

1. Reference the comprehensive architecture documentation in `mono_architecture.md`
2. Use data model documentation for database schema questions
3. Refer to product vision for strategic context and priorities
4. Note that detailed technical implementations are in external systems, not this repo

**Additional Resources Available:**
- **Mono Architecture Deep Dive**: Use `mono_doc/` files for detailed technical analysis, codebase assessment, and API specifications
- **Performance Optimization**: Reference `mono_doc/SHEETS_PERFORMANCE_*` files for Sheets performance insights
- **Interview Preparation**: Use `interview/` materials for hiring guidelines and system design prep
- **Product Planning**: Check `Knowledge_Base/` for strategy documents and roadmap information
- **Database Tools**: Use `tools/db_explorer.py` for exploring data models and relationships

### Auto-Sync Mono Analysis Repository

This workspace includes an **automated synchronization rule** that ensures the latest mono analysis data is always available:

- **Location**: `.cursor/rules/auto_sync_mono.md`
- **Function**: Automatically runs `git pull` in `~/Hebbia/mono_analysis` before any terminal command
- **Purpose**: Maintains consistency between the linked `mono` directory and the actual repository
- **Benefit**: All commands have access to the most current analysis and insights without manual syncing

**Note**: The `mono` directory in this workspace is a symlink to `~/Hebbia/mono_analysis`, providing seamless access to the latest mono architecture analysis.

This repository serves as a central knowledge hub for company information, technical architecture, and onboarding processes rather than containing executable code.
