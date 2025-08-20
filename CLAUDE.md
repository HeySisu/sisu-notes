# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a **documentation and knowledge repository** for Hebbia, containing internal documentation, onboarding materials, and architectural specifications. This is NOT a code repository - it contains markdown files with documentation, links to external resources, and knowledge base content.

## Repository Structure

```text
/
├── Knowledge_Base/          # Core technical and product documentation
│   ├── Product_Vision_Doc.md        # Company product vision and strategy
│   ├── mono_architecture.md         # Complete microservices architecture overview
│   ├── data_models_documentation.md # Database models and relationships
│   └── Why_Work_at_Hebbia_Engineers.md
└── Onboarding/             # Employee onboarding materials
    ├── Employee_Onboarding.md       # New hire process and training sessions
    ├── Eng_Links.md                 # Engineering documentation links
    ├── Printer.md                   # Office setup documentation
    └── Questions.md                 # Common questions and answers
```

## Key Documentation Files

### Architecture Documentation

- **`Knowledge_Base/mono_architecture.md`**: Comprehensive microservices architecture overview including:
  - Core services: brain (orchestrator), agents (AI), doc_manager, search, sheets
  - Data pipeline: fastbuild → doc_manager_indexer → Elasticsearch
  - Infrastructure: PostgreSQL, Kafka, Temporal workflows, AWS services
  - Multi-tenant SaaS architecture with RBAC permissions

### Data Models

- **`Knowledge_Base/data_models_documentation.md`**: Complete database schema documentation
  - Multi-tenant hierarchy: Tenant → Organization → Users/Repositories
  - Core models: User, Document, Repository, Sheet, DocumentChatConversation
  - All models centralized in `brain/models/` (100+ models)
  - UUID primary keys, JSONB metadata, soft deletes, versioning patterns

### Product Strategy

- **`Knowledge_Base/Product_Vision_Doc.md`**: Company vision focused on Information Retrieval (IR)
  - Mission: "Most capable AI platform"
  - Core differentiator: Matrix Agent for metadata-driven search
  - Priority framework: P0 (IR + revenue) → P1 (IR only) → P2 (revenue only) → P3 (neither)

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

This repository serves as a central knowledge hub for company information, technical architecture, and onboarding processes rather than containing executable code.
