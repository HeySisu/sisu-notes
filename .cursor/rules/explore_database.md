# Hebbia Database Explorer

**Command:** `cd ~/Hebbia/sisu-notes && .venv/bin/python tools/db_explorer.py [--env staging|prod] "<query>"`

**Description:** Query and explore the Hebbia PostgreSQL database with complete table knowledge and **READ-ONLY** SQL execution from the sisu-notes repository. Uses readonly database users - write operations are blocked at the database level. **ALWAYS defaults to staging** unless production is specifically requested.

## Prerequisites: Tailscale VPN

**IMPORTANT:** Database access requires Tailscale VPN connection. The tool will automatically check VPN status before attempting connection.

### VPN Setup
```bash
# Install Tailscale (if not installed)
# macOS: brew install tailscale
# Linux: curl -fsSL https://tailscale.com/install.sh | sh

# Connect to VPN
tailscale up

# Check VPN status
tailscale status
```

The db_explorer.py tool will:
1. Check if Tailscale is installed and running
2. Verify database hosts are reachable through VPN
3. Only proceed with database connection if VPN is active
4. Provide helpful error messages if VPN is not connected

## Environment Selection

- **Default (Staging)**: `python tools/db_explorer.py "query"` - Safe for exploration and testing
- **Production**: `python tools/db_explorer.py --env prod "query"` - Only when explicitly needed for production data

## Quick Usage

```bash
# Default staging environment (recommended for exploration)
cd ~/Hebbia/sisu-notes && .venv/bin/python tools/db_explorer.py "SELECT * FROM users WHERE name = 'Sisu Xi'"

# Explicit staging environment
cd ~/Hebbia/sisu-notes && .venv/bin/python tools/db_explorer.py --env staging "SELECT id, name, email, last_login_at FROM users WHERE name ILIKE '%sisu%'"

# Production environment (only when specifically requested)
cd ~/Hebbia/sisu-notes && .venv/bin/python tools/db_explorer.py --env prod "SELECT id, name, email, created_at FROM users WHERE email = 'sisu.xi@hebbia.ai'"

# Search users by keyword (staging default)
cd ~/Hebbia/sisu-notes && .venv/bin/python tools/db_explorer.py "SELECT name, email FROM users WHERE name ILIKE '%john%' OR email ILIKE '%john%' LIMIT 10"
```

## Database Structure (127 Tables)

**Production Database Statistics (Updated):**
- **Total Database Size:** 862 GB
- **Total Base Tables:** 127 tables
- **Largest Tables by Size:**
  - `cells`: 304 GB (72.4M rows) - Matrix spreadsheet cells
  - `document_list_document_metadata`: 214 GB (5.8M rows) - Document metadata
  - `repository_documents`: 83 GB (343K rows) - Document collections
  - `audit_logs`: 67 GB (11.8M rows) - System activity logs
  - `document_chat_messages`: 67 GB (186K rows) - Chat messages and responses

**Performance & Index Information:**
- **Cells table indexes:** 12 indexes totaling ~117 GB (largest: `idx_cells_answer_trgm` at 39 GB for text search)
- **Documents table indexes:** 6 indexes totaling ~11 GB for hash lookups and parsing status
- **Critical performance indexes:** Full-text search on answers, hash-based document deduplication, row ordering in sheets

### Core Entities

#### **`users`** - User accounts
- **Schema:** `id` (uuid), `name` (varchar), `auth0_id` (varchar), `picture` (varchar), `email` (varchar), `platform_role` (platformrole), `is_locked` (boolean), `is_email_verified` (boolean), `last_login_at` (timestamp), `unlocked_at` (timestamp), `created_at` (timestamp), `updated_at` (timestamp)
- **Key Fields:** Platform roles include USER, ADMIN; Auth0 integration for authentication
- **Sample Data:** Users have profile pictures, email verification status, and login tracking

#### **`organizations`** - Customer organizations
- **Schema:** `id` (uuid), `name` (varchar), `email_domains` (array), `kms_key_id` (varchar), `logo_url` (varchar), `primary_color` (varchar), `secondary_color` (varchar), `font` (varchar), `requires_mfa` (boolean), `api_key` (varchar), `integrations` (jsonb), `auth0_id` (varchar), `config` (jsonb), `s3_bucket_info` (jsonb), `email_local_part` (varchar), `document_retention_in_seconds` (integer), `tenant_id` (uuid), `disable_document_cache_hits` (boolean), `created_at` (timestamp), `updated_at` (timestamp)
- **Key Fields:** Multi-tenant architecture with KMS encryption, customizable branding, SharePoint/email integrations
- **Sample Data:** Organizations have custom colors, fonts, MFA requirements, and document retention policies

#### **`tenants`** - Top-level tenant isolation
- **Schema:** `id` (uuid), `name` (varchar), `kms_key_arn` (varchar), `byok_enabled` (boolean), `created_at` (timestamp), `updated_at` (timestamp)
- **Key Fields:** Bring-your-own-key (BYOK) encryption support, KMS key management

#### **`repositories`** - Document collections
- **Schema:** `id` (uuid), `name` (varchar), `private` (boolean), `description` (varchar), `image` (varchar), `color` (varchar), `questions` (array), `emoji` (jsonb), `last_built` (timestamp), `email_domains` (array), `organization_id` (uuid), `deleted_at` (timestamp), `has_docs` (boolean), `tags` (array), `is_claimed` (boolean), `active_build_id` (uuid), `migrated_to_pointer` (boolean), `integrations` (jsonb), `ticker` (varchar), `cron_schedule` (jsonb), `textract_enabled` (boolean), `num_docs` (integer), `weaviate_class_name` (varchar), `created_at` (timestamp), `updated_at` (timestamp)
- **Key Fields:** Custom emojis, color coding, scheduled builds, AWS Textract integration, Weaviate vector storage
- **Sample Data:** Repositories have visual customization, document counts, and integration status

#### **`documents`** - Individual documents
- **Schema:** `id` (uuid), `hash` (bytea), `repo_doc_id` (uuid), `integration` (integration), `sharepoint_drive_id` (varchar), `sharepoint_item_id` (varchar), `org_id` (uuid), `text_parse_status` (textparsestatus), `text_parse_failure_reason` (varchar), `integration_auth_context` (jsonb), `detect_tables_and_charts_status` (detecttablesandchartsstatus), `pdfjs_parse_key` (varchar), `user_defined_display_data` (jsonb), `image_data` (jsonb), `expired_at` (timestamp), `last_ingested_at` (timestamp), `expiry_status` (documentsv2expirystatus), `token_count` (integer), `pdf_convert_status` (pdfconvertstatus), `doc_viewer_page_count` (integer), `ingest_id` (uuid), `last_activity_at` (timestamp), `created_at` (timestamp), `updated_at` (timestamp)
- **Size:** 20 GB with 32.7M rows
- **Key Indexes:**
  - `documents_pkey`: Primary key on `id` (1.3 GB)
  - `ix_documents_hash`: Content deduplication (2.2 GB)
  - `ix_documents_repo_doc_id`: Repository document linkage (1.2 GB)
  - `ix_documents_group_by_existence_query`: Complex existence queries (4.3 GB)
- **Key Fields:** SharePoint integration, PDF parsing, table/chart detection, document expiration, token counting
- **Sample Data:** Documents track parsing status, failure reasons, and processing metadata

### Matrix/Sheets System

#### **`sheets`** - Matrix spreadsheet containers
- **Schema:** `id` (uuid), `version_id` (uuid), `template_id` (uuid), `org_id` (uuid), `name` (varchar), `active` (boolean), `delete` (boolean), `repo_id` (uuid), `restore_version_id` (uuid), `restore_version_timestamp` (timestamp), `sync_status` (varchar), `sync_failure_reason` (varchar), `is_empty` (boolean), `schema_version` (integer), `expired_at` (timestamp), `run_rows_mode` (varchar), `rows_type` (varchar), `created_at` (timestamp), `updated_at` (timestamp)
- **Key Fields:** Version control, template support, sync status tracking, schema versioning
- **Sample Data:** Sheets have version history, sync status, and can be restored from previous versions

#### **`rows`** - Matrix spreadsheet rows
- **Schema:** `id` (uuid), `y_value` (integer), `tab_id` (varchar), `sheet_id` (varchar), `repo_doc_id` (uuid), `deleted` (boolean), `row_order` (numeric), `provenance_id` (uuid), `provenance` (provenance), `entity_type` (entitytype), `entity_id` (varchar), `entity_metadata` (jsonb), `created_at` (timestamp), `updated_at` (timestamp)
- **Key Fields:** Row ordering, provenance tracking, entity relationships, document associations
- **Sample Data:** Rows track their position, source documents, and entity metadata

#### **`cells`** - Matrix spreadsheet cells ⭐ LARGEST TABLE
- **Schema:** `id` (uuid), `cell_hash` (varchar), `global_hash` (varchar), `global_hash_priority` (integer), `row_id` (uuid), `versioned_column_id` (uuid), `content` (jsonb), `tab_id` (varchar), `sheet_id` (varchar), `parent_hash` (varchar), `test_codes` (array), `not_found` (boolean), `answer_arr` (jsonb), `answer_numeric` (numeric), `answer_date` (timestamp), `answer` (varchar), `created_at` (timestamp), `updated_at` (timestamp)
- **Size:** 304 GB with 72.4M rows
- **Key Indexes:**
  - `cells_pkey`: Primary key on `id` (3 GB)
  - `idx_cells_answer_trgm`: Full-text search on `answer` (39 GB) - Critical for search performance
  - `ix_cells_cell_hash`: Hash lookups (13 GB) - Deduplication and caching
  - `ix_cells_cell_hash_updated_at_desc`: Hash + timestamp (34 GB) - Recent changes lookup
  - `ix_cells_sheet_tab_versioned_col`: Composite index for sheet navigation (2.4 GB)
- **Key Fields:** Content hashing for deduplication, versioned columns for schema evolution, multiple answer types, full-text search capability
- **Sample Data:** Cells contain AI-generated content, document summaries, and structured answers with comprehensive metadata

#### **`versioned_columns`** - Matrix column definitions
- **Schema:** `id` (uuid), `static_column_id` (varchar), `params` (jsonb), `prompt` (varchar), `tab_id` (varchar), `sheet_id` (varchar), `created_at` (timestamp), `updated_at` (timestamp)
- **Key Fields:** Column parameters, AI prompts, tab and sheet associations

### Chat & AI Systems

#### **`document_chat_conversation`** - AI chat sessions
- **Schema:** `id` (uuid), `user_id` (uuid), `org_id` (uuid), `title` (text), `deleted` (boolean), `expired_at` (timestamp), `tag_id` (uuid), `cloned_from_conversation_id` (uuid), `is_deep_research` (boolean), `created_at` (timestamp), `updated_at` (timestamp)
- **Key Fields:** Deep research mode, conversation cloning, tagging system, expiration management
- **Sample Data:** Conversations track research depth, can be cloned, and support tagging

#### **`document_chat_messages`** - Chat messages and responses
- **Schema:** `id` (uuid), `message_type` (messagetype), `repo_doc_id` (uuid), `user_id` (uuid), `message` (text), `meta` (jsonb), `deleted` (boolean), `conversation_id` (uuid), `selected_model` (model), `tool_name` (text), `sources` (jsonb), `org_id` (uuid), `expired_at` (timestamp), `turn_id` (uuid), `created_at` (timestamp), `updated_at` (timestamp)
- **Key Fields:** Message types, model selection, tool usage, source citations, turn tracking
- **Sample Data:** Messages include AI model info, tool usage, and source document references

#### **`matrix_chat_sessions`** - Matrix interface chats
- **Schema:** `id` (uuid), `user_id` (uuid), `sheet_id` (uuid), `org_id` (uuid), `created_at` (timestamp), `updated_at` (timestamp)
- **Key Fields:** Sheet-specific chat sessions

#### **`matrix_chat_messages`** - Matrix chat messages
- **Schema:** `id` (uuid), `session_id` (uuid), `message_type` (text), `content` (text), `tool_name` (text), `citation_map` (jsonb), `loading_state` (jsonb), `agent_type` (text), `turn_id` (uuid), `agent_prompt_version` (integer), `system_prompt` (text), `arguments` (jsonb), `created_at` (timestamp), `updated_at` (timestamp)
- **Key Fields:** Agent types, prompt versioning, citation mapping, loading states

### Permissions & Access Control

#### **`permission_groups`** - RBAC groups
- **Schema:** `id` (uuid), `name` (varchar), `role` (role), `org_id` (uuid), `all_members` (boolean), `all_repos` (boolean), `created_at` (timestamp), `updated_at` (timestamp)
- **Key Fields:** Organization-scoped permissions, all-members/all-repos flags

#### **`permission_group_users`** - User group assignments
- **Schema:** `id` (uuid), `user_id` (uuid), `group_id` (uuid), `created_at` (timestamp), `updated_at` (timestamp)

#### **`permission_group_repositories`** - Repository group access
- **Schema:** `id` (uuid), `group_id` (uuid), `repository_id` (uuid), `created_at` (timestamp), `updated_at` (timestamp)

#### **`user_organizations`** - User-org membership
- **Schema:** `user_id` (uuid), `org_id` (uuid), `role` (user_org_role), `created_at` (timestamp), `updated_at` (timestamp)
- **Key Fields:** User roles within organizations (MEMBER, ADMIN, etc.)

#### **`user_repositories`** - User repo access
- **Schema:** `id` (uuid), `user_id` (uuid), `repo_id` (uuid), `role` (role), `created_at` (timestamp), `updated_at` (timestamp)

#### **`user_sheets`** - User sheet access
- **Schema:** `id` (uuid), `user_id` (uuid), `sheet_id` (uuid), `role` (role), `unread` (boolean), `notifications_setting` (notificationsetting), `bookmarked` (boolean), `tag_id` (uuid), `last_access_at` (timestamptz), `automation_digest_setting` (varchar), `automation_notification_settings` (jsonb), `created_at` (timestamp), `updated_at` (timestamp)
- **Key Fields:** Read/unread status, notification preferences, bookmarking, automation settings

#### **`file_share_permissions`** - Document sharing permissions
- **Schema:** `entity_name` (varchar), `user_email` (varchar), `depth` (integer), `created_at` (timestamp), `updated_at` (timestamp)
- **Key Fields:** Hierarchical sharing with depth control

### Document Management

#### **`repository_documents`** - Docs in repos (comprehensive)
- **Schema:** `id` (uuid), `repo_id` (uuid), `type` (type), `mime` (varchar), `parent_id` (uuid), `source` (varchar), `data` (jsonb), `title` (varchar), `delete` (boolean), `timestamp` (timestamp), `npassages` (integer), `hash` (varchar), `build_status` (buildstatus), `topics` (array), `questions` (array), `last_built` (timestamp), `doc_viewer_url` (varchar), `meta` (jsonb), `path` (array), `uploaded_by` (uuid), `build_id` (uuid), `active` (boolean), `status_percentage` (integer), `failure_reason` (failurereason), `num_children` (integer), `file_size` (double precision), `md_doc_viewer_url` (varchar), `tables` (array), `display_title` (varchar), `has_tables` (boolean), `tables_updated_at` (timestamp), `doc_raw_content_json` (varchar), `fast_build_status` (documentfastbuildstatus), `sharepoint_id` (varchar), `created_at` (timestamp), `updated_at` (timestamp)
- **Key Fields:** Document types, build statuses, table detection, SharePoint integration, fast build processing
- **Sample Data:** Documents track processing status, table content, and multiple viewer URLs

### Analytics & Tracking

#### **`search_history`** - User search queries
- **Schema:** `id` (uuid), `query` (varchar), `user_id` (uuid), `repo_ids` (array), `page` (integer), `doc_ids` (array), `is_api` (boolean), `search_params` (jsonb), `created_at` (timestamp), `updated_at` (timestamp)
- **Key Fields:** Search parameters, repository scoping, API vs UI usage tracking

#### **`audit_logs`** - System activity logs
- **Schema:** `id` (uuid), `user_id` (uuid), `group_id` (uuid), `to_user_id` (uuid), `to_group_id` (uuid), `repo_id` (uuid), `doc_id` (uuid), `org_id` (uuid), `action` (varchar), `sheet_id` (uuid), `conversation_id` (uuid), `invocation_source` (varchar), `created_at` (timestamp), `updated_at` (timestamp)
- **Key Fields:** Comprehensive audit trail across all entities, invocation source tracking

#### **`activities`** - User activity tracking
- **Schema:** `id` (uuid), `user_id` (uuid), `user_name` (varchar), `org_id` (uuid), `repo_id` (uuid), `action_type` (actiontype), `repo_name` (varchar), `meta` (jsonb), `is_global` (boolean), `deleted_at` (timestamp), `created_at` (timestamp), `updated_at` (timestamp)
- **Key Fields:** Action type categorization, global vs organization-scoped activities

#### **`notifications`** - System notifications
- **Schema:** `id` (uuid), `user_id` (uuid), `new_documents` (newdocuments), `created_at` (timestamp), `updated_at` (timestamp)
- **Key Fields:** New document notifications with structured content

### Additional Important Tables

#### **`artifacts`** - Generated content artifacts
- **Schema:** Includes artifact generation, templates, and source tracking

#### **`bookmarks`** - User bookmarks
- **Schema:** User bookmarking system for documents and content

#### **`chat_shortcuts`** - Chat shortcut management
- **Schema:** Saved chat shortcuts and sharing

#### **`document_lists`** - Document list management
- **Schema:** Advanced document organization and filtering

#### **`folders`** - Document folder organization
- **Schema:** Hierarchical document organization

#### **`grid_state`** - UI grid state persistence
- **Schema:** User interface state management

#### **`hebbia_admins`** - Platform administrators
- **Schema:** System-wide administrative access

#### **`integrations`** - Third-party integrations
- **Schema:** Various integration configurations and statuses

#### **`labels`** - Content labeling system
- **Schema:** Document and content labeling

#### **`pins`** - Content pinning system
- **Schema:** User content pinning functionality

#### **`podcasts`** - Podcast content management
- **Schema:** Audio content handling

#### **`prompts`** - AI prompt management
- **Schema:** Prompt templates and versioning

#### **`reports`** - Report generation system
- **Schema:** Automated report creation and management

#### **`tokens`** - API token management
- **Schema:** Authentication and API access tokens

#### **`api_keys`** - Platform API keys
- **Schema:** `id` (uuid), `tenant_id` (uuid), `prefix` (varchar), `name` (varchar), `hashed_key` (varchar), `expires_at` (timestamp), `revoked_by` (uuid), `created_by` (uuid), `created_at` (timestamp), `updated_at` (timestamp)
- **Key Fields:** Tenant-scoped API key management with prefix matching, expiration tracking, and audit trail
- **Sample Data:** API keys have human-readable names, secure hashed storage, and revocation tracking

#### **`tenant_api_keys`** - Tenant-specific API keys
- **Schema:** `id` (uuid), `org_id` (uuid), `api_key` (varchar), `model` (varchar), `created_at` (timestamp), `updated_at` (timestamp)
- **Key Fields:** Organization-scoped API keys with model association for AI service access
- **Sample Data:** Keys are tied to specific AI models and organizations for service billing

#### **`rate_limits`** - Rate limiting configuration
- **Schema:** `id` (uuid), `org_id` (uuid), `time_period_seconds` (integer), `bucket_size` (integer), `bucket_name` (varchar), `rate_limit_key` (varchar), `created_at` (timestamp), `updated_at` (timestamp)
- **Key Fields:** Token bucket rate limiting with configurable time windows and bucket sizes per organization
- **Sample Data:** Organizations have different rate limits for various API endpoints and operations


#### **`user_invites`** - User invitation system
- **Schema:** `id` (uuid), `invitee_email` (varchar), `repo_id` (uuid), `repo_role` (role), `org_role` (user_org_role), `org_id` (uuid), `created_at` (timestamp), `updated_at` (timestamp)
- **Key Fields:** Email-based invitations with pre-assigned roles for repositories and organizations
- **Sample Data:** Pending invitations specify exact permissions users will receive upon acceptance

#### **`oauth_state`** - OAuth flow state management
- **Schema:** `id` (uuid), `state` (varchar), `user_id` (uuid), `expiration_timestamp` (timestamp), `org_id` (uuid), `created_at` (timestamp), `updated_at` (timestamp)
- **Key Fields:** Temporary state tracking for OAuth flows with expiration and user context
- **Sample Data:** OAuth state tokens for SharePoint, Google Drive, and other third-party integrations

#### **`repository_builds`** - Build status tracking
- **Schema:** `id` (uuid), `repo_id` (uuid), `num_docs_queued` (integer), `num_docs_scheduled` (integer), `num_docs_crawling` (integer), `num_docs_fetching` (integer), `num_docs_parsing` (integer), `num_docs_encode_and_feeding` (integer), `num_docs_failed` (integer), `status` (buildstatus), `is_active` (boolean), `num_docs_total` (integer), `quarantined` (boolean), `created_at` (timestamp), `updated_at` (timestamp)
- **Key Fields:** Detailed build pipeline tracking with per-stage document counts and status monitoring
- **Sample Data:** Real-time visibility into document processing pipeline with failure tracking and quarantine support


#### **`web_crawls`** - Web crawling system
- **Schema:** Automated web content collection

## Production Database Analytics (Current Data)

### Table Size Distribution
```sql
-- Top 30 tables by size with row counts
SELECT relname as table_name,
       pg_size_pretty(pg_total_relation_size('public.'||relname)) as table_size,
       n_live_tup as live_tuples
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size('public.'||relname) DESC
LIMIT 30
```

**Key Findings:**
- **cells**: 304 GB (72.4M rows) - Dominant table storing all Matrix cell data
- **document_list_document_metadata**: 214 GB (5.8M rows) - Document metadata and relationships
- **repository_documents**: 83 GB (343K rows) - Comprehensive document information
- **audit_logs**: 67 GB (11.8M rows) - Complete system activity tracking
- **document_chat_messages**: 67 GB (186K rows) - AI chat conversations and responses

### Index Performance Analysis
```sql
-- Index sizes for major tables
SELECT t.relname as table_name, i.relname as index_name,
       ix.indisprimary as is_primary, ix.indisunique as is_unique,
       pg_size_pretty(pg_relation_size(i.oid)) as index_size
FROM pg_class t, pg_class i, pg_index ix
WHERE t.oid = ix.indrelid AND i.oid = ix.indexrelid
AND t.relname IN ('cells', 'documents', 'rows', 'sheets')
ORDER BY pg_relation_size(i.oid) DESC
```

**Critical Indexes:**
- **cells table**: 12 indexes totaling ~117 GB (larger than most entire databases)
  - `idx_cells_answer_trgm`: 39 GB - Full-text search on answers (PostgreSQL trigram)
  - `ix_cells_cell_hash_updated_at_desc`: 34 GB - Hash + timestamp for recent changes
  - `ix_cells_cell_hash`: 13 GB - Primary hash-based deduplication
- **Performance Impact**: Index maintenance represents significant I/O overhead during writes

### Data Growth Patterns
- **Total Database Size**: 862 GB (production as of current analysis)
- **Index-to-Data Ratio**: ~1:3 (indexes are ~38% of total size)
- **Largest Growth Areas**: Matrix system (cells/rows), document metadata, audit logs

## Database Connection Details

### Staging Environment (Default)
- **Host:** hebbia-backend-postgres-staging.cqyf4jsjudre.us-east-1.rds.amazonaws.com
- **Port:** 5432
- **Database:** hebbia
- **User:** readonly_user
- **Password:** [stored in config]

### Production Environment (Explicit --env prod)
- **Host:** hebbia-backend-postgres-prod.cqyf4jsjudre.us-east-1.rds.amazonaws.com
- **Port:** 5432
- **Database:** hebbia
- **User:** readonly_user
- **Password:** [stored in config]

## Key Features & Patterns

### Multi-Tenant Architecture
- **Tenant isolation** with KMS encryption
- **Organization-level** access control
- **User-organization** membership management

### AI & ML Integration
- **Document parsing** with multiple status tracking
- **Table/chart detection** in documents
- **AI chat** with conversation management
- **Matrix system** for structured AI analysis

### Document Processing Pipeline
- **Ingestion** with multiple integration types
- **Parsing** with status tracking and failure handling
- **Vector storage** with Weaviate integration
- **Expiration** and retention management

### Matrix System Architecture
- **Version control** for sheets and columns
- **Cell-level** content hashing and deduplication
- **Row ordering** and provenance tracking
- **Template system** for reusable structures

### Security & Compliance
- **RBAC** with permission groups
- **Audit logging** across all operations
- **KMS encryption** for sensitive data
- **MFA support** at organization level

## Performance Debugging with EXPLAIN ANALYZE

### Understanding Query Performance
```bash
# Analyze query execution plan with timing - staging default (READ-ONLY, safe to run)
cd ~/Hebbia/sisu-notes && .venv/bin/python tools/db_explorer.py "EXPLAIN ANALYZE SELECT * FROM cells WHERE sheet_id = 'YOUR_UUID' LIMIT 100"

# Analyze with buffer usage (shows cache hits vs disk reads)
cd ~/Hebbia/sisu-notes && .venv/bin/python tools/db_explorer.py "EXPLAIN (ANALYZE, BUFFERS) SELECT c.*, r.y_value FROM cells c JOIN rows r ON c.row_id = r.id WHERE c.sheet_id = 'YOUR_UUID' LIMIT 100"

# Verbose analysis for complex queries
cd ~/Hebbia/sisu-notes && .venv/bin/python tools/db_explorer.py "EXPLAIN (ANALYZE, BUFFERS, VERBOSE) SELECT answer FROM cells WHERE answer ILIKE '%search_term%' LIMIT 10"

# Check existing indexes on a table (crucial for performance)
cd ~/Hebbia/sisu-notes && .venv/bin/python tools/db_explorer.py --env prod "SELECT indexname FROM pg_indexes WHERE tablename = 'cells' ORDER BY indexname"
```

### Key Performance Metrics
- **Actual Time**: Real execution time in milliseconds
- **Rows**: Planned vs actual row counts (large discrepancies = outdated statistics)
- **Buffers**: `shared hit` (cache) vs `read` (disk) - high disk reads = slow performance
- **Scan Types**: 
  - `Index Scan` = good for selective queries
  - `Seq Scan` = full table scan, slow on large tables
  - `Bitmap Index Scan` = good for OR conditions
- **Join Types**:
  - `Nested Loop` = good for small datasets
  - `Hash Join` = good for large unsorted data
  - `Merge Join` = good for pre-sorted data

### Common Performance Issues

#### Missing Index Detection
```bash
# Look for Sequential Scan on large tables
cd ~/Hebbia/sisu-notes && .venv/bin/python tools/db_explorer.py "EXPLAIN ANALYZE SELECT * FROM cells WHERE answer = 'specific_value'"
# Red flag: "Seq Scan on cells (cost=0.00..1234567.89 rows=1000000)"
```

#### Inefficient Join Performance
```bash
# Check join algorithm choice
cd ~/Hebbia/sisu-notes && .venv/bin/python tools/db_explorer.py "EXPLAIN ANALYZE SELECT * FROM documents d JOIN repository_documents rd ON d.repo_doc_id = rd.id WHERE d.org_id = 'UUID'"
# Watch for: Nested Loop with millions of iterations
```

#### Memory Pressure in Sorting
```bash
# Check for disk-based sorting
cd ~/Hebbia/sisu-notes && .venv/bin/python tools/db_explorer.py "EXPLAIN ANALYZE SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 1000"
# Red flag: "Sort Method: external merge Disk: 123456kB"
```

### Production Performance Monitoring

#### Currently Running Slow Queries
```bash
# Find queries running >5 seconds
cd ~/Hebbia/sisu-notes && .venv/bin/python tools/db_explorer.py --env prod "SELECT pid, now() - query_start AS duration, LEFT(query, 100) as query_preview, state FROM pg_stat_activity WHERE (now() - query_start) > interval '5 seconds' AND state != 'idle' ORDER BY duration DESC"
```

#### Table Bloat Analysis
```bash
# Identify tables needing VACUUM
cd ~/Hebbia/sisu-notes && .venv/bin/python tools/db_explorer.py "SELECT tablename, n_live_tup, n_dead_tup, ROUND(n_dead_tup::numeric / NULLIF(n_live_tup, 0) * 100, 2) AS dead_percent, pg_size_pretty(pg_total_relation_size('public.'||tablename)) AS size FROM pg_stat_user_tables WHERE n_dead_tup > 10000 ORDER BY n_dead_tup DESC LIMIT 10"
```

#### Index Usage Statistics
```bash
# Find unused or rarely used indexes
cd ~/Hebbia/sisu-notes && .venv/bin/python tools/db_explorer.py "SELECT schemaname, tablename, indexname, idx_scan, pg_size_pretty(pg_relation_size(indexrelid)) AS size FROM pg_stat_user_indexes WHERE idx_scan < 100 AND pg_relation_size(indexrelid) > 1000000 ORDER BY pg_relation_size(indexrelid) DESC"
```

#### Cache Hit Ratios
```bash
# Check cache effectiveness by table
cd ~/Hebbia/sisu-notes && .venv/bin/python tools/db_explorer.py "SELECT tablename, heap_blks_read as disk_reads, heap_blks_hit as cache_hits, ROUND(100.0 * heap_blks_hit / NULLIF(heap_blks_hit + heap_blks_read, 0), 2) AS cache_hit_ratio FROM pg_statio_user_tables WHERE heap_blks_read > 0 ORDER BY heap_blks_read DESC LIMIT 20"
```

#### Connection Pool Health
```bash
# Monitor connection states
cd ~/Hebbia/sisu-notes && .venv/bin/python tools/db_explorer.py "SELECT state, COUNT(*) as connections, MAX(now() - state_change) as longest_in_state FROM pg_stat_activity GROUP BY state ORDER BY connections DESC"

# Long-running transactions blocking others
cd ~/Hebbia/sisu-notes && .venv/bin/python tools/db_explorer.py "SELECT pid, now() - xact_start AS tx_duration, state, LEFT(query, 50) as query_preview FROM pg_stat_activity WHERE xact_start IS NOT NULL AND now() - xact_start > interval '1 minute' ORDER BY tx_duration DESC"
```

## Common Query Examples

### User Information
```bash
# Find user by name (case-insensitive) - staging default
cd ~/Hebbia/sisu-notes && .venv/bin/python tools/db_explorer.py "SELECT id, name, email, platform_role, last_login_at FROM users WHERE name ILIKE '%sisu%'"

# Find user by email - production if needed
cd ~/Hebbia/sisu-notes && .venv/bin/python tools/db_explorer.py --env prod "SELECT id, name, email, created_at, last_login_at FROM users WHERE email = 'sisu.xi@hebbia.ai'"

# Search users by keyword in name or email - staging default
cd ~/Hebbia/sisu-notes && .venv/bin/python tools/db_explorer.py "SELECT name, email, last_login_at FROM users WHERE name ILIKE '%keyword%' OR email ILIKE '%keyword%' ORDER BY last_login_at DESC NULLS LAST LIMIT 20"

# Recent user activity - staging default
cd ~/Hebbia/sisu-notes && .venv/bin/python tools/db_explorer.py "SELECT name, email, last_login_at FROM users WHERE last_login_at IS NOT NULL ORDER BY last_login_at DESC LIMIT 20"
```

### Organization Analytics
```sql
-- Organizations by user count
SELECT o.name as org_name, COUNT(uo.user_id) as user_count
FROM organizations o
LEFT JOIN user_organizations uo ON o.id = uo.org_id
GROUP BY o.id, o.name
ORDER BY user_count DESC

-- User's organizations
SELECT o.name as org_name, uo.role
FROM user_organizations uo
JOIN organizations o ON uo.org_id = o.id
WHERE uo.user_id = 'USER_UUID_HERE'

-- Organization details
SELECT id, name, email_domains, created_at
FROM organizations
WHERE name ILIKE '%company%'
```

### Document & Repository Analytics
```sql
-- Repository document counts
SELECT r.name as repo_name, r.num_docs, r.has_docs
FROM repositories r
WHERE r.organization_id = 'ORG_UUID_HERE'
ORDER BY r.num_docs DESC

-- User's accessible repositories
SELECT r.name, r.description, r.num_docs
FROM user_repositories ur
JOIN repositories r ON ur.repository_id = r.id
WHERE ur.user_id = 'USER_UUID_HERE'

-- Documents by organization
SELECT COUNT(*) as doc_count, o.name as org_name
FROM documents d
JOIN organizations o ON d.org_id = o.id
GROUP BY o.id, o.name
ORDER BY doc_count DESC
```

### Matrix/Sheets Analytics
```sql
-- Active sheets by organization
SELECT o.name as org_name, COUNT(s.id) as sheet_count
FROM sheets s
JOIN organizations o ON s.org_id = o.id
WHERE s.active = true
GROUP BY o.id, o.name
ORDER BY sheet_count DESC

-- User's sheets
SELECT s.name, s.created_at, s.sync_status
FROM user_sheets us
JOIN sheets s ON us.sheet_id = s.id
WHERE us.user_id = 'USER_UUID_HERE'
AND s.active = true

-- Sheet content analysis
SELECT s.name, COUNT(c.id) as cell_count, COUNT(r.id) as row_count
FROM sheets s
LEFT JOIN rows r ON s.id = r.sheet_id
LEFT JOIN cells c ON r.id = c.row_id
WHERE s.active = true
GROUP BY s.id, s.name
ORDER BY cell_count DESC
```

### Chat & AI Analytics
```sql
-- Recent chat conversations
SELECT dcc.title, u.name as user_name, dcc.created_at, dcc.is_deep_research
FROM document_chat_conversation dcc
JOIN users u ON dcc.user_id = u.id
ORDER BY dcc.created_at DESC
LIMIT 20

-- User's chat history
SELECT title, created_at, is_deep_research
FROM document_chat_conversation
WHERE user_id = 'USER_UUID_HERE'
ORDER BY created_at DESC

-- Chat activity by organization
SELECT o.name as org_name, COUNT(dcc.id) as chat_count
FROM document_chat_conversation dcc
JOIN organizations o ON dcc.org_id = o.id
GROUP BY o.id, o.name
ORDER BY chat_count DESC
```

### Document Processing Analytics
```sql
-- Document parsing status
SELECT text_parse_status, COUNT(*) as count
FROM documents
GROUP BY text_parse_status
ORDER BY count DESC

-- Failed document parsing
SELECT id, text_parse_failure_reason, created_at
FROM documents
WHERE text_parse_status = 'FAILED'
ORDER BY created_at DESC
LIMIT 20

-- Document expiration analysis
SELECT expiry_status, COUNT(*) as count
FROM documents
GROUP BY expiry_status
ORDER BY count DESC
```

### API Key Management
```sql
-- Active API keys by tenant
SELECT t.name as tenant_name, COUNT(ak.id) as key_count
FROM api_keys ak
JOIN tenants t ON ak.tenant_id = t.id
WHERE ak.expires_at IS NULL OR ak.expires_at > NOW()
AND ak.revoked_by IS NULL
GROUP BY t.id, t.name
ORDER BY key_count DESC

-- API key usage by organization
SELECT o.name as org_name, COUNT(tak.id) as key_count
FROM tenant_api_keys tak
JOIN organizations o ON tak.org_id = o.id
GROUP BY o.id, o.name
ORDER BY key_count DESC

-- Expiring API keys (next 30 days)
SELECT ak.name, ak.prefix, t.name as tenant_name, ak.expires_at
FROM api_keys ak
JOIN tenants t ON ak.tenant_id = t.id
WHERE ak.expires_at BETWEEN NOW() AND (NOW() + INTERVAL '30 days')
AND ak.revoked_by IS NULL
ORDER BY ak.expires_at
```

### Rate Limiting Analytics
```sql
-- Rate limit configuration by organization
SELECT o.name as org_name, rl.bucket_name, rl.bucket_size, rl.time_period_seconds
FROM rate_limits rl
JOIN organizations o ON rl.org_id = o.id
ORDER BY o.name, rl.bucket_name

-- Organizations without rate limits
SELECT o.name as org_name
FROM organizations o
LEFT JOIN rate_limits rl ON o.id = rl.org_id
WHERE rl.id IS NULL
ORDER BY o.name
```

### User Invitation Analytics
```sql
-- Pending invitations by organization
SELECT o.name as org_name, COUNT(ui.id) as pending_invites
FROM user_invites ui
JOIN organizations o ON ui.org_id = o.id
GROUP BY o.id, o.name
ORDER BY pending_invites DESC

-- Recent invitations
SELECT ui.invitee_email, o.name as org_name, ui.org_role, ui.created_at
FROM user_invites ui
JOIN organizations o ON ui.org_id = o.id
WHERE ui.created_at > (NOW() - INTERVAL '7 days')
ORDER BY ui.created_at DESC
```


### Build Status Analytics
```sql
-- Repository build status overview
SELECT r.name as repo_name, rb.status, rb.num_docs_total, rb.num_docs_failed, rb.is_active
FROM repository_builds rb
JOIN repositories r ON rb.repo_id = r.id
WHERE rb.is_active = true
ORDER BY rb.created_at DESC

-- Build pipeline bottlenecks
SELECT r.name as repo_name,
       rb.num_docs_parsing,
       rb.num_docs_encode_and_feeding,
       rb.num_docs_failed
FROM repository_builds rb
JOIN repositories r ON rb.repo_id = r.id
WHERE rb.is_active = true
AND (rb.num_docs_parsing > 100 OR rb.num_docs_encode_and_feeding > 100)
ORDER BY (rb.num_docs_parsing + rb.num_docs_encode_and_feeding) DESC
```

## Tool Features

- ✅ **Environment Selection**: Staging (default) and production environments
- ✅ **Readonly Database Users**: Write operations blocked at database level
- ✅ Automatic virtual environment handling
- ✅ Secure database connection management
- ✅ JSON output format for easy parsing
- ✅ Error handling and user-friendly messages
- ✅ Support for **READ-ONLY** PostgreSQL queries (SELECT statements only)
- ✅ Comprehensive table schema knowledge
- ✅ Sample data insights for all major tables
- 🚫 **NO WRITE OPERATIONS** - Database-level readonly protection

## Key Learnings from Investigation

### What Works Well
- **pg_indexes query**: Fast way to verify missing indexes
- **pg_settings query**: Reveals configuration issues (work_mem, etc.)
- **JSON output**: Easy to parse with jq for analysis
- **--env flag**: Seamless switching between staging/prod

### Common Use Cases
```bash
# Check if specific indexes exist (performance debugging)
.venv/bin/python tools/db_explorer.py --env prod \
  "SELECT indexname FROM pg_indexes WHERE tablename = 'cells' AND indexname LIKE '%hash%'"

# Get database configuration settings
.venv/bin/python tools/db_explorer.py --env prod \
  "SELECT name, setting, unit FROM pg_settings WHERE name IN ('work_mem', 'effective_io_concurrency')"

# Count rows for performance analysis
.venv/bin/python tools/db_explorer.py --env prod \
  "SELECT COUNT(*) FROM cells WHERE sheet_id = 'UUID'"
```

### Limitations Discovered
- **EXPLAIN ANALYZE on prod**: Can be slow on large tables, use with care
- **UUID placeholders**: Using fake UUIDs in EXPLAIN queries returns empty plans
- **Large result sets**: Tool truncates output, use LIMIT for control

## Usage Notes

- **🏠 STAGING DEFAULT**: Always defaults to staging environment unless `--env prod` is explicitly specified
- **⚠️ READ-ONLY ACCESS**: Uses readonly database users - write operations blocked at database level
- **🔒 PRODUCTION ACCESS**: Only use `--env prod` when specifically requested for production data
- **📊 CURRENT DATA**: Documentation updated with production statistics as of latest analysis (127 tables, 862 GB total size)
- Use double quotes around SQL queries
- Results are returned as JSON
- UUIDs are used as primary keys throughout
- Most tables have created_at/updated_at timestamps
- Soft deletes are common (deleted_at, deleted fields)
- JSONB fields contain structured metadata and configuration
- Array fields support PostgreSQL array operations
- User-defined types provide domain-specific validation
- Multi-tenant architecture with organization-level isolation
- Comprehensive audit logging across all operations