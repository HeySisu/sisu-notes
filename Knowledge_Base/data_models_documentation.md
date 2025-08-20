# Hebbia Data Models Documentation

## Core Data Models Architecture

The data models follow a **multi-tenant SaaS architecture** with hierarchical relationships. All core models are centralized in `brain/models/` and shared across microservices.

### **Hierarchy: Tenant → Organization → Users/Repositories**

**1. Tenant (`tenant.py`)**
- Top-level multi-tenancy isolation
- Contains dedicated AWS resources (RDS, S3, Elasticsearch)
- Schema: `id`, `name`, `kms_key_arn`, `byok_enabled`
- Related: `TenantResource` (infrastructure), `TenantAdmin` (permissions)

**2. Organization (`org.py`)**  
- Business entity within a tenant
- Schema: `id`, `name`, `kms_key_id`, `api_key`, `email_domains`, `integrations`, `config`
- Links to: `tenant_id` (FK), multiple users via `OrgUser`
- Supports: custom branding, MFA requirements, document retention policies

**3. User (`user.py`)**
- Individual user accounts with Auth0 integration
- Schema: `id`, `name`, `auth0_id`, `email`, `platform_role`, `is_locked`, `last_login_at`
- Roles: `USER`, `ADMIN`, `LABELER`
- Auth methods: Auth0, SAML, Google OAuth
- Related: `UserAuthKeys`, `BlocklistedUserTokens`

### **Document Management Core**

**4. Repository (`repository.py`)**
- Document collections/folders
- Schema: `id`, `name`, `organization_id`, `questions`, `tags`, `ticker`, `integrations`
- Features: privacy controls, build tracking, Weaviate class mapping
- Links to: Organization, Documents

**5. Document (`document.py`)**
- Individual files/documents with extensive metadata
- Schema: `id`, `repo_id`, `type`, `title`, `source`, `build_status`, `npassages`, `file_size`
- Document types: BOX, GDRIVE, SEC, SHAREPOINT, LOCAL, etc.
- Build pipeline: QUEUED → CRAWLING → FETCHING → PARSING → SUCCESS/FAILED
- Features: OCR support, table detection, fast build status

### **AI Chat & Research**

**6. DocumentChatConversation (`doc_chat_conversation.py`)**
- Multi-document AI chat sessions
- Schema: `id`, `user_id`, `org_id`, `title`, `tag_id`, `is_deep_research`
- Features: conversation sharing, cloning, expiration, soft delete
- Related: `DocumentChatMessage`, `DocumentChatConversationDocuments`

### **Spreadsheet/Matrix System**

**7. Sheet (`sheet.py`)**
- Tabular reports/spreadsheets interface
- Schema: `id`, `version_id`, `org_id`, `name`, `sync_status`, `rows_type`
- Features: versioning, templates, document/company row types
- Storage: Metadata in DB, full content in S3

### **Key Relationships**

```
Tenant (1) → (n) Organization (1) → (n) Repository (1) → (n) Document
       ↘            ↓                    ↓
        TenantAdmin  OrgUser            UserRepository
                     ↓                    ↓  
                    User ← - - - - - - - - ┘
                     ↓
            DocumentChatConversation (1) → (n) DocumentChatMessage
                     ↓
                    Sheet
```

### **Critical Schema Patterns**

- **Multi-tenancy**: All models link to tenant/org for isolation
- **Soft deletes**: `deleted`/`delete` flags instead of hard deletes  
- **Versioning**: Sheets use `version_id` for immutable versions
- **Build tracking**: Documents have comprehensive build status pipeline
- **UUID primary keys**: All entities use UUID for distributed system compatibility
- **JSONB metadata**: Flexible schema extension via `data`, `meta`, `config` fields
- **Audit trails**: Most models have `created_at`/`updated_at` timestamps

### **Cross-Service Dependencies**

- **brain**: Owns all data models, provides centralized schema
- **doc_manager**: Manages document indexing, uses Document/Repository models  
- **agents**: AI processing, uses Chat/Document models
- **sheets**: Spreadsheet backend, uses Sheet/Document models
- **fastbuild**: Document processing pipeline, updates Document build status

The architecture ensures **data consistency** across microservices while maintaining **clear separation of concerns** and **multi-tenant security**.

## Model File Locations

All core models are located in `/brain/models/`:

- `tenant.py` - Tenant, TenantResource, TenantAdmin
- `org.py` - Organization, OrgUser  
- `user.py` - User, UserAuthKeys, BlocklistedUserTokens
- `repository.py` - Repository
- `document.py` - Document (with extensive enums and types)
- `doc_chat_conversation.py` - DocumentChatConversation (with complex async methods)
- `sheet.py` - Sheet
- Plus 70+ additional specialized models for features like artifacts, notifications, permissions, etc.

## Additional Model Categories

The codebase contains numerous specialized models for:

- **Artifacts & Templates**: `artifact.py`, `artifact_template.py`
- **Document Processing**: `build.py`, `fastbuild_crawl.py`, `detect_extract_table_jobs.py`
- **Permissions & Sharing**: `permission_group.py`, `sheet_share_settings.py`
- **Integrations**: `oauth_state.py`, `integration_refresh_token.py`
- **Search & Analytics**: `search_history.py`, `search_responses.py`
- **Financial Data**: `snp_company_id_to_company_name_mapping.py`, `form_8k_title.py`
- **Notifications**: `notification.py`, `mailman_notifications.py`