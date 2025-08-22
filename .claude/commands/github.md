# GitHub Explorer

**Command:** `gh`

**Description:** Query and explore GitHub repositories using the GitHub CLI with comprehensive knowledge of your setup and common operations.

**Default Account:** All commands default to your **Hebbia work account** (`sisuxi`) unless explicitly specified otherwise.

## Account Setup

**Work GitHub (DEFAULT):** `sisuxi` (github_hebbia)
- SSH Host: `github_hebbia`
- Identity: `~/.ssh/id_ed25519_hebbia`
- Organization: Hebbia
- Main Repository: `hebbia/mono`
- **Current CLI auth:** ✓ Active account

**Personal GitHub:** `xisisu` (github_personal)
- SSH Host: `github_personal`
- Identity: `~/.ssh/id_ed25519_personal`
- Usage: For personal projects only

## Quick Usage

> **Note:** All commands below use your Hebbia work account by default. Repository defaults to `hebbia/mono`.

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
# Recent commits (in hebbia/mono)
gh api repos/hebbia/mono/commits --field since="2024-08-15T00:00:00Z" --jq '.[].commit | {message: .message, author: .author.name, date: .author.date}'

# Recent commits by specific author (in hebbia/mono)
gh api repos/hebbia/mono/commits --field author=sisuxi --field since="2024-08-15T00:00:00Z"

# Recent issues (in hebbia/mono)
gh issue list --repo hebbia/mono --state all --limit 20 --json number,title,state,createdAt,author
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

## Account Switching

> **Default:** You're already using your Hebbia work account. Only switch if you need to work with personal repositories.

### Switch to Personal Account (when needed)
```bash
# Switch to personal account for personal projects
gh auth switch --hostname github.com --user xisisu

# Set git remote for personal repos
git remote set-url origin git@github_personal:xisisu/repo-name.git
```

### Switch Back to Work Account (Hebbia)
```bash
# Switch back to work account (default)
gh auth switch --hostname github.com --user sisuxi

# Set git remote back for work repos
git remote set-url origin git@github_hebbia:hebbia/mono.git
```

## Date Helpers

**Common date ranges:**
- Past week: `--created=">=2024-08-15"`
- Past month: `--created=">=2024-07-22"`
- Past 3 months: `--created=">=2024-05-22"`
- Specific date range: `--created="2024-08-01..2024-08-22"`

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

## Authentication & Setup

**Current status:**
- **Authenticated as:** `sisuxi` (Hebbia work account - DEFAULT)
- **SSH keys configured** for both accounts
- **Default repo:** `hebbia/mono`
- **Git protocol:** SSH

**Key Commands:**
- `gh auth status` - Check current authentication
- `gh auth switch` - Switch between accounts
- `gh auth login` - Add new account authentication
- `gh repo set-default hebbia/mono` - Set default repository

## Notes

- **All commands default to your Hebbia work account (`sisuxi`) and `hebbia/mono` repository**
- Date ranges use ISO format (YYYY-MM-DD)
- Use `--json` flag for machine-readable output
- Use `--template` for custom formatting
- Search API has rate limits (5000 requests/hour)
- PR/Issue numbers are unique per repository
- **Only switch to personal account when working on personal projects**