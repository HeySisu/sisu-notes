# GitHub Explorer

**Command:** `gh`

**Description:** Query and explore GitHub repositories using the GitHub CLI with comprehensive knowledge of your setup and common operations.

**Default Account:** All commands use your **Hebbia work account** (`sisuxi`) exclusively.

**Repository Context:** Commands work globally from any directory and default to `hebbia/mono` repository.

## Account Setup

**Hebbia Work Account:** `sisuxi` (github_hebbia)
- SSH Host: `github_hebbia`
- Identity: `~/.ssh/id_ed25519_hebbia`
- Organization: Hebbia
- Main Repository: `hebbia/mono`
- **Authentication:** Automatically confirmed before operations

## Quick Usage

> **Note:** All commands automatically ensure you're using the Hebbia work account (`sisuxi`) and confirm authentication before execution. Repository defaults to `hebbia/mono`.

### Team Analysis Integration

**Organizational Context:** When analyzing teams or individuals, reference `/Users/sisu/Hebbia/sisu-notes/tools/org_structure.md` to:
- Map team members to their GitHub usernames
- Understand reporting structure and team composition
- Get comprehensive team activity summaries

**Team Query Pattern:**
1. Read `/Users/sisu/Hebbia/sisu-notes/tools/org_structure.md` → identify team members + GitHub usernames
2. Query GitHub activity for each team member
3. Aggregate and summarize team contributions

### Account Verification
```bash
# Automatically switch to Hebbia account and confirm username
gh auth switch --hostname github.com --user sisuxi
gh auth status --hostname github.com | grep "Logged in to github.com as sisuxi"
```

### My Recent Activity
```bash
# Get my PRs from past 3 months (defaults to hebbia/mono)
gh pr list --author sisuxi --state all --limit 50 --json number,title,state,createdAt,updatedAt,url

# Get my recent PRs (past 30 days)
gh search prs --author=sisuxi --created=">=2024-07-22" --json number,title,state,createdAt,url

# My PRs in hebbia/mono (explicit repo specification)
gh pr list --repo hebbia/mono --author sisuxi --state all --limit 20
```

### Search PRs by Author
```bash
# Find PRs by Wilson from past week (in hebbia/mono)
gh search prs --author=wilson --repo=hebbia/mono --created=">=2024-08-15" --json number,title,createdAt,url

# Search Wilson's PRs with "logging" in title/body (in hebbia/mono)
gh search prs --author=wilson --repo=hebbia/mono "logging" --json number,title,createdAt,url

# Search PRs by author with specific terms (in hebbia/mono)
gh search prs --author=wilson --repo=hebbia/mono "logging update" --created=">=2024-08-15"
```

### PR Details & Analysis
```bash
# Get detailed PR information (in hebbia/mono)
gh pr view 123 --repo hebbia/mono --json number,title,body,state,author,reviews,commits

# List PR files and changes (in hebbia/mono)
gh pr view 123 --repo hebbia/mono --json files

# Get PR reviews (in hebbia/mono)
gh pr view 123 --repo hebbia/mono --json reviews

# Check PR status (defaults to hebbia/mono)
gh pr status --repo hebbia/mono
```

### Recent Repository Activity
```bash
# Recent commits (in hebbia/mono) - get last N commits
gh api repos/hebbia/mono/commits --jq '.[0:5] | .[] | {message: .commit.message, author: .commit.author.name, date: .commit.author.date}'

# Recent commits with filter by date
gh api repos/hebbia/mono/commits --jq '.[] | select(.commit.author.date >= "2025-08-15T00:00:00Z") | {message: .commit.message, author: .commit.author.name, date: .commit.author.date}'

# Recent commits by specific author (search API is more reliable)
gh search commits --author=sisuxi --repo=hebbia/mono --sort=committer-date --order=desc --json sha,commit

# Recent issues (in hebbia/mono)
gh issue list --repo hebbia/mono --state all --limit 20 --json number,title,state,createdAt,author

# Get issues assigned to me
gh issue list --repo hebbia/mono --assignee sisuxi --state open
```

## Common Query Examples

### PR Summary Queries

**Summarize my PRs for past 3 months:**
```bash
# Get comprehensive PR data
gh search prs --author=sisuxi --repo=hebbia/mono --created=">=2024-05-22" --json number,title,state,createdAt,updatedAt,url,author

# Count PRs by state
gh search prs --author=sisuxi --repo=hebbia/mono --created=">=2024-05-22" --state=open --json state | jq 'length'
gh search prs --author=sisuxi --repo=hebbia/mono --created=">=2024-05-22" --state=closed --json state | jq 'length'
```

**Find Wilson's logging PRs from past week:**
```bash
# Search with keywords
gh search prs --author=wilson --repo=hebbia/mono "logging" --created=">=2024-08-15" --json number,title,createdAt,url,body

# More specific search
gh search prs --author=wilson --repo=hebbia/mono "logging update" --created=">=2024-08-15"
gh search prs --author=wilson --repo=hebbia/mono "log" --created=">=2024-08-15"
```

### Advanced Searches

**PRs by topic/keyword:**
```bash
# Search all PRs with specific keywords
gh search prs --repo=hebbia/mono "database migration" --created=">=2024-08-01"
gh search prs --repo=hebbia/mono "frontend" --state=open
gh search prs --repo=hebbia/mono "api endpoint" --created=">=2024-07-01"
```

**Team activity analysis:**
```bash
# PRs by multiple authors
gh search prs --repo=hebbia/mono --author=sisuxi --author=wilson --created=">=2024-08-01"

# Recent team activity
gh search prs --repo=hebbia/mono --created=">=2024-08-15" --json number,title,author,createdAt

# PRs with specific labels
gh pr list --repo hebbia/mono --label "backend" --state all --limit 20
```

### Team Summary Examples

**AI/ML Engineering Team Analysis:**
```bash
# Reference /Users/sisu/Hebbia/sisu-notes/tools/org_structure.md for team members:
# - Adithya Ramanathan (adithram) - Engineering Manager
# - Alex Flick (alex-hebbia/0xflick) - Software Engineer
# - Lucas Haarmann (Lucas-H1/lexheb) - Software Engineer
# - Tas Hasting (tascodes) - Senior Software Engineer
# - Sara Kemper (sarakemper) - Software Engineer

# Query each member's recent activity
gh search prs --author=adithram --repo=hebbia/mono --created=">=2024-08-01"
gh search prs --author=alex-hebbia --repo=hebbia/mono --created=">=2024-08-01"
gh search prs --author=Lucas-H1 --repo=hebbia/mono --created=">=2024-08-01"
gh search prs --author=tascodes --repo=hebbia/mono --created=">=2024-08-01"
gh search prs --author=sarakemper --repo=hebbia/mono --created=">=2024-08-01"

# Aggregate team commits
gh api repos/hebbia/mono/commits --field author=adithram --field since="2024-08-01T00:00:00Z"
```

**Security Team Analysis:**
```bash
# Reference /Users/sisu/Hebbia/sisu-notes/tools/org_structure.md:
# - Matt Aromatorio (Senior Director, Security)
# - Deepak Chauhan (ddanylc-hebbia) - IT Contract Admin
# - Dan Le - IT Contract Admin
# - Stanley Owolabi - IT Contract Admin
# - Eli Raich (ellis-hebbia) - GRC Analyst

# Security team PR activity
gh search prs --author=ddanylc-hebbia --author=ellis-hebbia --repo=hebbia/mono --created=">=2024-08-01"
```

### Issue Tracking

**Recent issues:**
```bash
# All recent issues
gh issue list --repo hebbia/mono --created=">=2024-08-15" --json number,title,state,author,createdAt

# Issues by keyword
gh search issues --repo=hebbia/mono "bug" --created=">=2024-08-01"
gh search issues --repo=hebbia/mono "performance" --state=open
```

### Repository Insights

**Repository statistics:**
```bash
# Repository info
gh repo view hebbia/mono --json name,description,createdAt,updatedAt,stargazerCount,language

# Contributors
gh api repos/hebbia/mono/contributors --jq '.[].login'

# Recent releases
gh release list --repo hebbia/mono --limit 10
```



## Account Management

**Automatic Hebbia Account Setup:**
```bash
# Ensure Hebbia account is active (run automatically before operations)
gh auth switch --hostname github.com --user sisuxi

# Verify authentication status
gh auth status --hostname github.com

# Set default repository
gh repo set-default hebbia/mono
```

## Date Helpers

**Common date ranges (adjust dates as needed):**
- Past week: `--created=">=2025-08-25"`
- Past month: `--created=">=2025-08-01"`
- Past 3 months: `--created=">=2025-06-01"`
- Specific date range: `--created="2025-08-01..2025-09-01"`

**Dynamic dates (use in scripts):**
```bash
# Past 7 days
WEEK_AGO=$(date -v-7d +%Y-%m-%d)
gh search prs --author=sisuxi --created=">=$WEEK_AGO"

# Past 30 days
MONTH_AGO=$(date -v-30d +%Y-%m-%d)
gh search prs --author=sisuxi --created=">=$MONTH_AGO"
```



## Output Formatting

**JSON output for processing:**
```bash
# Get specific fields
gh pr list --repo hebbia/mono --json number,title,author,createdAt

# Process with jq
gh search prs --author=sisuxi --json title,createdAt | jq '.[] | {title, date: .createdAt[:10]}'

# Count results
gh search prs --author=sisuxi --json number | jq 'length'
```

**Table output for reading:**
```bash
# Default table format
gh pr list --repo hebbia/mono --author sisuxi

# Custom table format
gh pr list --repo hebbia/mono --json number,title,author,createdAt --template '{{range .}}{{.number}}\t{{.title}}\t{{.author.login}}\t{{.createdAt}}\n{{end}}'
```

## Advanced Queries

### Code Review Analytics

```bash
# PRs reviewed by me
gh search prs --repo=hebbia/mono --reviewed-by=sisuxi --created=">=2025-08-01"

# PRs waiting for my review
gh pr list --repo hebbia/mono --search "review-requested:sisuxi"

# PRs with conflicts
gh pr list --repo hebbia/mono --state open --json number,title,mergeable --jq '.[] | select(.mergeable == "CONFLICTING")'
```

### Workflow & CI/CD

```bash
# Recent workflow runs
gh run list --repo hebbia/mono --limit 10

# Failed workflow runs
gh run list --repo hebbia/mono --status failure --limit 5

# View specific workflow run details
gh run view --repo hebbia/mono <run-id>
```

### Branch Management

```bash
# List all branches
gh api repos/hebbia/mono/branches --jq '.[].name'

# Find stale branches (not updated in 30 days)
gh api repos/hebbia/mono/branches --jq '.[] | select((.commit.commit.author.date | fromdate) < (now - 2592000)) | .name'

# Delete a remote branch
gh api -X DELETE repos/hebbia/mono/git/refs/heads/<branch-name>
```

### PR Metrics

```bash
# Average PR merge time (last 20 merged PRs)
gh pr list --repo hebbia/mono --state merged --limit 20 --json mergedAt,createdAt --jq '[.[] | ((.mergedAt | fromdate) - (.createdAt | fromdate)) / 86400] | add/length | floor'

# PR approval patterns
gh pr list --repo hebbia/mono --state all --limit 50 --json reviews --jq '.[] | .reviews | group_by(.author.login) | map({author: .[0].author.login, count: length})'
```

## Troubleshooting

### Common Issues & Solutions

**Authentication Issues:**

```bash
# If getting 401/403 errors
gh auth refresh
gh auth switch --hostname github.com --user sisuxi

# Verify token scopes
gh auth status --show-token
```

**Rate Limiting:**

```bash
# Check rate limit status
gh api rate_limit

# If rate limited, wait or use pagination
gh pr list --repo hebbia/mono --limit 10 --paginate
```

**API Errors:**

```bash
# Debug API calls with verbose output
GH_DEBUG=api gh pr list --repo hebbia/mono

# Check API response headers
gh api repos/hebbia/mono -i | head -20
```

## Authentication & Setup

**Current status:**

- **Authenticated as:** `sisuxi` (Hebbia work account - ONLY)
- **SSH keys configured** for Hebbia account
- **Default repo:** `hebbia/mono`
- **Git protocol:** SSH

**Key Commands:**

- `gh auth status` - Check current authentication
- `gh auth switch --hostname github.com --user sisuxi` - Ensure Hebbia account
- `gh repo set-default hebbia/mono` - Set default repository

## Notes

- **All commands use your Hebbia work account (`sisuxi`) and `hebbia/mono` repository exclusively**
- **Automatic account verification** ensures you're always on the correct account
- Date ranges use ISO format (YYYY-MM-DD)
- Use `--json` flag for machine-readable output
- Use `--template` for custom formatting
- Search API has rate limits (5000 requests/hour)
- PR/Issue numbers are unique per repository

### Important: Account Management

**GitHub CLI Configuration:**

- GitHub CLI authentication automatically uses the Hebbia account (`sisuxi`)
- SSH host configuration uses `github_hebbia` for all operations
- All operations are scoped to Hebbia organization and repositories

**Best Practices:**

1. **Single account workflow:** All operations use Hebbia account exclusively
2. **Automatic verification:** Account switching and verification happens automatically
3. **Repository access:** All commands default to `hebbia/mono` repository
4. **Authentication check:** Username `sisuxi` is confirmed before operations
