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
- **`users`** - User accounts (id, name, email, auth0_id, picture, platform_role, is_locked, last_login_at)
- **`organizations`** - Customer organizations (id, name, email_domains, tenant_id, config, integrations)
- **`tenants`** - Top-level tenant isolation (id, name, kms_key_arn, byok_enabled)
- **`repositories`** - Document collections (id, name, organization_id, has_docs, num_docs, integrations)
- **`documents`** - Individual documents (id, hash, org_id, text_parse_status, token_count, last_activity_at)
- **`sheets`** - Matrix spreadsheets (id, name, org_id, repo_id, active, sync_status)

### Relationships
- **`user_organizations`** - User-org membership (user_id, org_id, role)
- **`user_repositories`** - User repo access (user_id, repository_id)
- **`repository_documents`** - Docs in repos (repository_id, document_id)

### Chat & AI
- **`document_chat_conversation`** - AI chat sessions (id, user_id, org_id, title, is_deep_research)
- **`document_chat_messages`** - Chat messages and responses
- **`matrix_chat_sessions`** - Matrix interface chats
- **`cells`** - Matrix spreadsheet cells (id, row_id, content, answer, sheet_id)

### Permissions & Access
- **`permission_groups`** - RBAC groups
- **`permission_group_users`** - User group assignments
- **`file_share_permissions`** - Document sharing permissions

### Analytics & Tracking
- **`search_history`** - User search queries
- **`audit_logs`** - System activity logs
- **`activities`** - User activity tracking
- **`notifications`** - System notifications

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
```

## Database Connection Details

- **Host:** read-write-endpoint-staging.endpoint.proxy-cqyf4jsjudre.us-east-1.rds.amazonaws.com
- **Port:** 5432
- **Database:** hebbia
- **User:** postgres
- **Password:** [stored in tool]

## Tool Features

- ✅ Automatic virtual environment handling
- ✅ Secure database connection management
- ✅ JSON output format for easy parsing
- ✅ Error handling and user-friendly messages
- ✅ Support for any PostgreSQL query

## Usage Notes

- Use double quotes around SQL queries
- Results are returned as JSON
- UUIDs are used as primary keys throughout
- Most tables have created_at/updated_at timestamps
- Soft deletes are common (deleted_at, deleted fields)