# Hebbia Monorepo Architecture Overview

## 🏗️ High-Level Architecture

This is a **microservices architecture** for an AI-powered document processing and search platform with the following key characteristics:

- **Language**: Primarily Python with FastAPI services
- **Database**: PostgreSQL with Alembic migrations  
- **Search**: Elasticsearch integration
- **Infrastructure**: Docker containers, AWS services
- **Event Streaming**: Kafka for service communication
- **Workflow Engine**: Temporal for orchestrating long-running processes

## 🧠 Core Services

### `brain/` - Central Orchestrator
- **Role**: Main API gateway and central orchestrator
- **Responsibilities**: 
  - Authentication and authorization (Auth0 integration)
  - User and organization management
  - Document operations coordination
  - Central database model definitions
- **Key Models**: Users, Organizations, Documents, Sheets, Permissions
- **Database Models**: Contains all database models for the entire system (100+ models)
- **Key Files**:
  - `app.py` - FastAPI application
  - `models/` - All database models (centralized)
  - `routes/` - API endpoints
  - `data_layer/` - Database operations

### `agents/` - AI Processing Engine  
- **Role**: AI agents for document processing and chat
- **Capabilities**: 
  - Multi-document chat conversations
  - Deep research with multiple data sources
  - Automated document analysis tasks
  - Follow-up question generation
- **Key Features**: 
  - Message handling and compression
  - Title generation
  - Single and multi-document chat
  - WebSocket support for real-time communication
- **Key Files**:
  - `agents/` - Core agent implementations
  - `routes/multi_doc_chat.py` - Multi-document chat API
  - `utils/` - Agent utilities and helpers

### `doc_manager/` - Document Management
- **Role**: Document operations, metadata, and permissions
- **Features**: 
  - Document lists and collections
  - Document tagging and metadata
  - Search filters and saved filters
  - Folder management and hierarchy
  - Integration with external sources (Box, SharePoint, S3)
- **RBAC**: Fine-grained permission system for document access
- **Key Components**:
  - `doc_permission_checker/` - Permission validation
  - `search/` - Document search functionality
  - `rerank/` - Search result ranking
  - `rbac/` - Role-based access control

### `search/` - Search Infrastructure
- **Role**: Elasticsearch-based search with AI capabilities
- **Integration**: Works with agents for AI-powered search
- **Features**: Advanced search queries, filtering, ranking

### `sheets/` & `sheets_engine/` - Spreadsheet Platform
- **Role**: Collaborative spreadsheet-like interface for data analysis
- **Features**: 
  - Matrix operations and data organization
  - Cell computations and formulas
  - Collaborative editing
  - Data visualization
  - Integration with document search results

### `artifacts/` - Content Generation
- **Role**: Manages generated content and templates
- **Features**: 
  - Document decomposition and analysis
  - Template management and generation
  - Article and content creation
  - Editor integration (TipTap)

### `company_searcher/` - Company Intelligence
- **Role**: Company search and information retrieval
- **Features**: Company data lookup and search capabilities

## 📊 Data Processing Pipeline

### `fastbuild/` - Document Processing Pipeline
The core document processing pipeline that transforms raw documents into searchable, AI-queryable content:

**Pipeline Steps**:
1. **Ingestion**: Documents from various sources (S3, Box, SharePoint, etc.)
2. **Fetch**: Download and prepare documents for processing
3. **OCR/Parsing**: Text extraction using multiple parsing strategies
4. **PDF Processing**: Specialized PDF handling with PyPDF and PDF.js
5. **Conversion**: Convert documents to standardized formats
6. **Status Updates**: Track processing status throughout pipeline
7. **Indexing**: Send processed documents to `doc_manager_indexer`

### `doc_manager_indexer/` - Search Indexing
- **Role**: Indexes processed documents into Elasticsearch
- **Features**: 
  - Fan-out processing for scalability
  - Metadata generation and classification
  - Document association management
  - Crawl synchronization

### `maximizer/` - Queue Management & Rate Limiting
- **Role**: Manages queues and enforces rate limits across services
- **Features**: 
  - Priority queue management
  - Rate limiting per user/organization
  - License handling and enforcement
  - Message mapping and routing
  - Queue garbage collection

## 🗃️ Data Layer

### `migrations/` - Database Schema Management
- **Tool**: Alembic for database migrations
- **History**: 200+ migration files tracking schema evolution since 2022
- **Models**: All models defined centrally in `brain/models/`
- **Key Tables**: Users, Organizations, Documents, Sheets, Permissions, Audit Logs

### `python_lib/` - Shared Libraries
- **Common Code**: Shared utilities, configuration, database connections
- **LLM Integration**: 
  - `llm/prompts.py` - Centralized prompt management
  - AI model interfaces and message handling
- **Core Utilities**: Configuration management, database connections, constants

## 🔧 Supporting Infrastructure

### `jobs/` - Background Processing (AWS Lambda)
Serverless functions for various background tasks:
- **Email Processing**: `doc_list_email_processor/`, `mailman/`
- **Data Synchronization**: `direct_doclist_sync/`, `browse_syncer/`
- **Migration Jobs**: `filings_migration/`, `earnings_migration/`
- **Health Monitoring**: `flashdocs_health_monitor/`
- **External Integrations**: `pitchbook/`, `thirdbridge/`

### `temporal/` - Workflow Engine
- **Purpose**: Orchestrates long-running, distributed workflows
- **Use Cases**: 
  - Document processing pipelines
  - Data synchronization workflows
  - Multi-step background operations

### `sheet_syncer/` - Spreadsheet Synchronization
- **Role**: Manages synchronization between sheets and external data sources
- **Features**: Document updates, data consistency, scheduling

### `flashdocs/` - Real-time Document Interface
- **Role**: Provides real-time document interaction capabilities
- **Features**: Live document editing and collaboration

## 🏗️ Infrastructure & DevOps

### `infra/` - Infrastructure as Code
- **Tool**: Terraform for AWS infrastructure management
- **Components**: 
  - VPC and networking (`network.tf`)
  - RDS PostgreSQL databases (`postgres.tf`)
  - Elasticsearch clusters (`elastic.tf`)
  - Load balancers (`loadbalancer.tf`)
  - Kafka clusters (`kafka.tf`)
  - S3 buckets and storage (`s3.tf`)
  - IAM roles and policies (`iam.tf`)

### Docker & Containerization
- **Multi-stage builds**: Optimized Docker images
- **Docker Compose**: Local development environment
- **Service-specific Dockerfiles**: Each service has its own container configuration

## 🧪 Development & Testing

### `tests/` - Testing Infrastructure  
- **Types**: Unit tests, integration tests, end-to-end tests
- **Coverage**: Service-specific test suites with shared fixtures
- **Tools**: pytest, fixtures, mocking, test databases

### Development Tools
- **`start-dev.py`**: Local development environment setup script
- **`CLAUDE.md`**: Development guidelines, patterns, and AI assistant instructions
- **`envloader.py`**: Environment configuration management
- **`Makefile`**: Common development tasks and commands

## 🔄 Key Data Flows

### 1. Document Ingestion Flow
```
External Source → fastbuild (fetch/parse/ocr) → doc_manager_indexer → Elasticsearch → Available for search/chat
```

### 2. Search & Chat Flow
```
User Query → agents → search (Elasticsearch) → AI processing → Formatted response
```

### 3. Sheet Operations Flow
```
User Action → sheets → sheets_engine → Database → Real-time updates
```

### 4. Multi-Document Chat Flow
```
User Message → agents → Document retrieval → AI synthesis → Response with citations
```

## 🏛️ Architecture Patterns

### Event-Driven Architecture
- **Kafka**: Inter-service communication and event streaming
- **Event Sourcing**: Audit logs and activity tracking
- **Async Processing**: Background jobs and queue-based operations

### Role-Based Access Control (RBAC)
- **Hierarchical Permissions**: Organization → Document List → Document level
- **Service-Level Enforcement**: Each service validates permissions
- **Centralized Models**: Permission definitions in `brain/models/`

### Multi-Tenant Architecture
- **Organization Isolation**: Data segregated by organization
- **Tenant-Aware Services**: All services respect organizational boundaries
- **Shared Infrastructure**: Common services with tenant isolation

### API-First Design
- **FastAPI**: Standardized REST APIs across all services
- **OpenAPI**: Auto-generated documentation
- **Consistent Patterns**: Shared request/response models

## 🔍 External Integrations

### Document Sources
- **Cloud Storage**: S3, Box, SharePoint, Azure File Share
- **Email**: Direct email integration for document ingestion
- **Web Crawling**: Automated web content extraction

### Data Providers
- **Financial Data**: PitchBook, CapIQ, public filings
- **Third-party APIs**: Various external data sources
- **Real-time Feeds**: Kafka-based data streaming

### AI & ML Services
- **LLM Integration**: Multiple AI model providers
- **Document Processing**: OCR, parsing, classification
- **Search Enhancement**: AI-powered search and ranking

## 🚀 Deployment & Operations

### AWS Services Used
- **Compute**: ECS, Lambda, EC2
- **Storage**: S3, RDS PostgreSQL, Elasticsearch
- **Networking**: VPC, Load Balancers, Route53
- **Security**: IAM, KMS, Secrets Manager
- **Monitoring**: CloudWatch, DataDog integration

### Monitoring & Observability
- **DataDog**: Application and infrastructure monitoring
- **Audit Logging**: Comprehensive activity tracking
- **Health Checks**: Service health monitoring and alerting

This architecture represents a sophisticated enterprise platform that transforms unstructured documents into AI-queryable knowledge with collaborative features. The system emphasizes scalability, security, and AI integration across the entire document lifecycle.