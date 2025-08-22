# Hebbia Database Explorer

**Command:** `.venv/bin/python tools/db_explorer.py`

**Description:** Query and explore the Hebbia PostgreSQL database with complete table knowledge and flexible SQL execution.

## Quick Usage

```bash
# Execute any SQL query
.venv/bin/python tools/db_explorer.py "SELECT * FROM users WHERE name = 'Sisu Xi'"

# Find user by name
.venv/bin/python tools/db_explorer.py "SELECT id, name, email, last_login_at FROM users WHERE name ILIKE '%sisu%'"

# Find user by email
.venv/bin/python tools/db_explorer.py "SELECT id, name, email, created_at FROM users WHERE email = 'sisu.xi@hebbia.ai'"

# Search users by keyword
.venv/bin/python tools/db_explorer.py "SELECT name, email FROM users WHERE name ILIKE '%john%' OR email ILIKE '%john%' LIMIT 10"
```

## Database Structure (146 Tables)

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

#### **`cells`** - Matrix spreadsheet cells
- **Schema:** `id` (uuid), `cell_hash` (varchar), `global_hash` (varchar), `global_hash_priority` (integer), `row_id` (uuid), `versioned_column_id` (uuid), `content` (jsonb), `tab_id` (varchar), `sheet_id` (varchar), `parent_hash` (varchar), `test_codes` (array), `not_found` (boolean), `answer_arr` (jsonb), `answer_numeric` (numeric), `answer_date` (timestamp), `answer` (varchar), `created_at` (timestamp), `updated_at` (timestamp)
- **Key Fields:** Content hashing, versioned columns, multiple answer types (array, numeric, date, text), test codes
- **Sample Data:** Cells contain AI-generated content, document summaries, and structured answers with metadata

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

#### **`web_crawls`** - Web crawling system
- **Schema:** Automated web content collection

## Database Connection Details

- **Host:** read-write-endpoint-staging.endpoint.proxy-cqyf4jsjudre.us-east-1.rds.amazonaws.com
- **Port:** 5432
- **Database:** hebbia
- **User:** postgres
- **Password:** [stored in tool]

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

## Common Query Examples

### User Information
```sql
-- Find user by name (case-insensitive)
SELECT id, name, email, platform_role, last_login_at
FROM users
WHERE name ILIKE '%sisu%'

-- Find user by email
SELECT id, name, email, created_at, last_login_at
FROM users
WHERE email = 'sisu.xi@hebbia.ai'

-- Search users by keyword in name or email
SELECT name, email, last_login_at
FROM users
WHERE name ILIKE '%keyword%' OR email ILIKE '%keyword%'
ORDER BY last_login_at DESC NULLS LAST
LIMIT 20

-- Recent user activity
SELECT name, email, last_login_at
FROM users
WHERE last_login_at IS NOT NULL
ORDER BY last_login_at DESC
LIMIT 20
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

## Tool Features

- ✅ Automatic virtual environment handling
- ✅ Secure database connection management
- ✅ JSON output format for easy parsing
- ✅ Error handling and user-friendly messages
- ✅ Support for any PostgreSQL query
- ✅ Comprehensive table schema knowledge
- ✅ Sample data insights for all major tables

## Usage Notes

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