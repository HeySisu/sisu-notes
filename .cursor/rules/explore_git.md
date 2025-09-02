# Git Explorer

**Command:** `git`

**Description:** Query and explore the local Hebbia mono repository using git commands with comprehensive knowledge of your setup and common operations.

**Default Repository:** All commands operate on the **Hebbia mono repository** at `~/Hebbia/sisu-notes/mono/` exclusively.

**Repository Context:** Commands work from the mono directory within the current repository.

## Repository Setup

**Hebbia Mono Repository:** `~/Hebbia/sisu-notes/mono/`
- Local Path: `~/Hebbia/sisu-notes/mono/`
- Remote: `origin` (points to `hebbia/mono`)
- Default Branch: `main`
- SSH Configuration: Uses Hebbia SSH keys
- **Working Directory:** Navigate to mono directory first

## Quick Usage

> **Note:** All commands should be run from within the `~/Hebbia/sisu-notes/mono/` directory. Commands default to the remote `origin/main` branch.

### Team Analysis Integration

**Organizational Context:** When analyzing teams or individuals, reference `/Users/sisu/Hebbia/sisu-notes/tools/org_structure.md` to:
- Map team members to their Git commit authors
- Understand reporting structure and team composition
- Get comprehensive team activity summaries

**Team Query Pattern:**
1. Read `/Users/sisu/Hebbia/sisu-notes/tools/org_structure.md` → identify team members + Git author names
2. Query local Git history for each team member
3. Aggregate and summarize team contributions

### Repository Status
```bash
# Navigate to repo and check status
cd ~/Hebbia/sisu-notes/mono && git status

# Verify remote configuration
cd ~/Hebbia/sisu-notes/mono && git remote -v

# Check current branch and upstream
cd ~/Hebbia/sisu-notes/mono && git branch -vv
```

### My Recent Activity
```bash
# Get my commits from past 3 months on main
cd ~/Hebbia/sisu-notes/mono && git log --author="$(git config user.name)" --since="3 months ago" origin/main --oneline

# Get my recent commits (past 30 days) with details
cd ~/Hebbia/sisu-notes/mono && git log --author="$(git config user.name)" --since="30 days ago" origin/main --pretty=format:"%h %ad %s" --date=short

# My commits with file changes and statistics
cd ~/Hebbia/sisu-notes/mono && git log --author="$(git config user.name)" --since="1 month ago" origin/main --stat

# My recent activity with actual code changes
cd ~/Hebbia/sisu-notes/mono && git log --author="$(git config user.name)" --since="1 week ago" origin/main -p

# Quick summary of my changes (files and change types)
cd ~/Hebbia/sisu-notes/mono && git log --author="$(git config user.name)" --since="1 week ago" origin/main --name-status
```

### Search Commits by Author
```bash
# Find commits by Wilson from past week
cd ~/Hebbia/sisu-notes/mono && git log --author="wilson" --since="1 week ago" origin/main --oneline

# Search Wilson's commits with "logging" in message
cd ~/Hebbia/sisu-notes/mono && git log --author="wilson" --grep="logging" origin/main --oneline

# Search commits by author with specific terms (case-insensitive)
cd ~/Hebbia/sisu-notes/mono && git log --author="wilson" --grep="logging" --grep="update" --all-match origin/main --oneline
```

### Commit Details & Analysis
```bash
# Get detailed commit information
cd ~/Hebbia/sisu-notes/mono && git show <commit-hash>

# List files changed in a commit
cd ~/Hebbia/sisu-notes/mono && git show --name-only <commit-hash>

# Show commit statistics
cd ~/Hebbia/sisu-notes/mono && git show --stat <commit-hash>

# Show commit with word-level diff
cd ~/Hebbia/sisu-notes/mono && git show --word-diff <commit-hash>
```

### Change Analysis & Diffs

**Critical Change Detection:**
```bash
# Show actual code changes (full diff)
cd ~/Hebbia/sisu-notes/mono && git show <commit-hash>

# Show changes with context (3 lines before/after)
cd ~/Hebbia/sisu-notes/mono && git show -U3 <commit-hash>

# Show only added/removed lines (no context)
cd ~/Hebbia/sisu-notes/mono && git show -U0 <commit-hash>

# Highlight function-level changes
cd ~/Hebbia/sisu-notes/mono && git show --function-context <commit-hash>

# Show changes in specific file
cd ~/Hebbia/sisu-notes/mono && git show <commit-hash> -- path/to/file.py
```

**Critical Pattern Detection:**
```bash
# Find commits that modified critical patterns
cd ~/Hebbia/sisu-notes/mono && git log -S "password\|secret\|key\|token" origin/main --oneline

# Find commits with database changes
cd ~/Hebbia/sisu-notes/mono && git log -G "CREATE\|ALTER\|DROP" origin/main --oneline

# Find API endpoint changes
cd ~/Hebbia/sisu-notes/mono && git log -G "@app.route\|@router\|def.*api" origin/main --oneline

# Find security-related changes
cd ~/Hebbia/sisu-notes/mono && git log -S "auth\|permission\|security" origin/main --oneline
```

**Activity Summary with Changes:**
```bash
# Get my recent activity with actual changes
cd ~/Hebbia/sisu-notes/mono && git log --author="$(git config user.name)" --since="1 week ago" origin/main --stat

# Show my changes with diff summary
cd ~/Hebbia/sisu-notes/mono && git log --author="$(git config user.name)" --since="1 week ago" origin/main --name-status

# Get full diffs for my recent commits
cd ~/Hebbia/sisu-notes/mono && git log --author="$(git config user.name)" --since="1 week ago" origin/main -p

# Critical changes only (added/removed lines with grep)
cd ~/Hebbia/sisu-notes/mono && git log --author="$(git config user.name)" --since="1 week ago" origin/main -p | grep "^[+-]" | grep -v "^[+-][+-][+-]"
```

### Recent Repository Activity
```bash
# Recent commits on main (last 20)
cd ~/Hebbia/sisu-notes/mono && git log origin/main --oneline -20

# Recent commits with author and date
cd ~/Hebbia/sisu-notes/mono && git log origin/main --pretty=format:"%h %an %ad %s" --date=short -20

# Commits since specific date
cd ~/Hebbia/sisu-notes/mono && git log --since="2024-08-15" origin/main --pretty=format:"%h %an %ad %s" --date=short

# Activity summary by author (recent commits)
cd ~/Hebbia/sisu-notes/mono && git log --since="1 week ago" origin/main --pretty=format:"%an" | sort | uniq -c | sort -rn
```

## Common Query Examples

### Commit Summary Queries

**Summarize my commits for past 3 months:**
```bash
# Get comprehensive commit data
cd ~/Hebbia/sisu-notes/mono && git log --author="$(git config user.name)" --since="3 months ago" origin/main --pretty=format:"%h|%ad|%s|%an" --date=iso

# Count commits by time period
cd ~/Hebbia/sisu-notes/mono && git log --author="$(git config user.name)" --since="3 months ago" origin/main --oneline | wc -l

# Group commits by week
cd ~/Hebbia/sisu-notes/mono && git log --author="$(git config user.name)" --since="3 months ago" origin/main --pretty=format:"%ad %s" --date=format:"%Y-%m-%d"
```

**Find Wilson's logging commits from past week:**
```bash
# Search with keywords in commit message
cd ~/Hebbia/sisu-notes/mono && git log --author="wilson" --grep="logging" --since="1 week ago" origin/main --pretty=format:"%h %ad %s" --date=short

# More specific search with multiple terms
cd ~/Hebbia/sisu-notes/mono && git log --author="wilson" --grep="logging.*update" --since="1 week ago" origin/main --oneline

# Search in commit message and show actual changes
cd ~/Hebbia/sisu-notes/mono && git log --author="wilson" --grep="log" --since="1 week ago" origin/main -p

# See what files were modified and how (A=added, M=modified, D=deleted)
cd ~/Hebbia/sisu-notes/mono && git log --author="wilson" --grep="log" --since="1 week ago" origin/main --name-status
```

### Advanced Searches

**Commits by topic/keyword:**
```bash
# Search all commits with specific keywords
cd ~/Hebbia/sisu-notes/mono && git log --grep="database.*migration" --since="1 month ago" origin/main --oneline

# Search commits touching specific file types
cd ~/Hebbia/sisu-notes/mono && git log --since="1 month ago" origin/main -- "*.py" --oneline

# Search commits that modified specific directories
cd ~/Hebbia/sisu-notes/mono && git log --since="1 month ago" origin/main -- backend/ --oneline
```

**File history and changes:**
```bash
# History of specific file
cd ~/Hebbia/sisu-notes/mono && git log --follow origin/main -- path/to/file.py

# Who last modified specific files
cd ~/Hebbia/sisu-notes/mono && git log -1 --pretty=format:"%an %ad" origin/main -- path/to/file.py

# Changes to files matching pattern
cd ~/Hebbia/sisu-notes/mono && git log --since="1 week ago" origin/main -- "*.sql" --stat
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

# Query each member's recent activity (adjust author names as needed)
cd ~/Hebbia/sisu-notes/mono && git log --author="Adithya" --since="1 month ago" origin/main --oneline
cd ~/Hebbia/sisu-notes/mono && git log --author="Alex" --since="1 month ago" origin/main --oneline
cd ~/Hebbia/sisu-notes/mono && git log --author="Lucas" --since="1 month ago" origin/main --oneline
cd ~/Hebbia/sisu-notes/mono && git log --author="Tas" --since="1 month ago" origin/main --oneline
cd ~/Hebbia/sisu-notes/mono && git log --author="Sara" --since="1 month ago" origin/main --oneline

# Aggregate team commits summary
cd ~/Hebbia/sisu-notes/mono && git log --since="1 month ago" origin/main --pretty=format:"%an" | grep -E "(Adithya|Alex|Lucas|Tas|Sara)" | sort | uniq -c | sort -rn
```

**Security Team Analysis:**
```bash
# Reference /Users/sisu/Hebbia/sisu-notes/tools/org_structure.md:
# - Matt Aromatorio (Senior Director, Security)
# - Deepak Chauhan (ddanylc-hebbia) - IT Contract Admin
# - Dan Le - IT Contract Admin
# - Stanley Owolabi - IT Contract Admin
# - Eli Raich (ellis-hebbia) - GRC Analyst

# Security team commit activity
cd ~/Hebbia/sisu-notes/mono && git log --author="Matt\|Deepak\|Dan\|Stanley\|Eli" --since="1 month ago" origin/main --oneline

# Security-related commits by keyword
cd ~/Hebbia/sisu-notes/mono && git log --grep="security\|auth\|permission\|access" --since="1 month ago" origin/main --oneline
```

### Branch and Merge Analysis

**Branch information:**
```bash
# List all branches
cd ~/Hebbia/sisu-notes/mono && git branch -a

# Recent branches
cd ~/Hebbia/sisu-notes/mono && git for-each-ref --sort=-committerdate refs/heads/ --format='%(committerdate:short) %(refname:short)'

# Merged branches
cd ~/Hebbia/sisu-notes/mono && git branch --merged origin/main

# Unmerged branches
cd ~/Hebbia/sisu-notes/mono && git branch --no-merged origin/main
```

**Merge commit analysis:**
```bash
# Find merge commits
cd ~/Hebbia/sisu-notes/mono && git log --merges origin/main --oneline -20

# Commits between branches
cd ~/Hebbia/sisu-notes/mono && git log origin/main..origin/develop --oneline

# Files changed between branches
cd ~/Hebbia/sisu-notes/mono && git diff --name-only origin/main..origin/develop
```

### Repository Insights

**Repository statistics:**
```bash
# Repository information
cd ~/Hebbia/sisu-notes/mono && git remote show origin

# Contributors list
cd ~/Hebbia/sisu-notes/mono && git shortlog -sn origin/main | head -20

# Commit frequency by author
cd ~/Hebbia/sisu-notes/mono && git log --since="3 months ago" origin/main --pretty=format:"%an" | sort | uniq -c | sort -rn | head -10

# Repository size and object count
cd ~/Hebbia/sisu-notes/mono && git count-objects -vH
```

**Code analysis:**
```bash
# Lines of code by file type
cd ~/Hebbia/sisu-notes/mono && git ls-files | grep -E '\.(py|js|ts|sql)$' | xargs wc -l

# Most changed files
cd ~/Hebbia/sisu-notes/mono && git log --pretty=format: --name-only origin/main | sort | uniq -c | sort -rg | head -20

# Recent file modifications
cd ~/Hebbia/sisu-notes/mono && git ls-files -z | xargs -0 -n1 -I{} git log -1 --format="%ai {}" -- {} | sort -r | head -20
```

## Comprehensive Analysis & Statistics

### Most Touched Files Analysis

**Global most touched files:**
```bash
# Most modified files overall (all time)
cd ~/Hebbia/sisu-notes/mono && git log --pretty=format: --name-only origin/main | sort | uniq -c | sort -rg | head -20

# Most modified files in past month
cd ~/Hebbia/sisu-notes/mono && git log --since="1 month ago" --pretty=format: --name-only origin/main | sort | uniq -c | sort -rg | head -20

# Most modified files by file type
cd ~/Hebbia/sisu-notes/mono && git log --since="3 months ago" --pretty=format: --name-only origin/main | grep '\.py$' | sort | uniq -c | sort -rg | head -10
cd ~/Hebbia/sisu-notes/mono && git log --since="3 months ago" --pretty=format: --name-only origin/main | grep '\.js$\|\.ts$' | sort | uniq -c | sort -rg | head -10
```

**Most touched files by specific person:**
```bash
# My most modified files
cd ~/Hebbia/sisu-notes/mono && git log --author="$(git config user.name)" --since="3 months ago" --pretty=format: --name-only origin/main | sort | uniq -c | sort -rg | head -20

# Wilson's most modified files
cd ~/Hebbia/sisu-notes/mono && git log --author="wilson" --since="3 months ago" --pretty=format: --name-only origin/main | sort | uniq -c | sort -rg | head -20

# Team member comparison (most active files)
cd ~/Hebbia/sisu-notes/mono && for author in "Adithya" "Alex" "Lucas" "Tas" "Sara"; do
  echo "=== $author's most modified files ==="
  git log --author="$author" --since="1 month ago" --pretty=format: --name-only origin/main | sort | uniq -c | sort -rg | head -5
  echo
done
```

**Directory-level analysis:**
```bash
# Most active directories
cd ~/Hebbia/sisu-notes/mono && git log --since="1 month ago" --pretty=format: --name-only origin/main | xargs -n1 dirname | sort | uniq -c | sort -rg | head -20

# Backend vs Frontend activity
cd ~/Hebbia/sisu-notes/mono && echo "Backend commits: $(git log --since="1 month ago" --pretty=format: --name-only origin/main | grep "^backend/" | wc -l)"
cd ~/Hebbia/sisu-notes/mono && echo "Frontend commits: $(git log --since="1 month ago" --pretty=format: --name-only origin/main | grep "^frontend/" | wc -l)"
cd ~/Hebbia/sisu-notes/mono && echo "Infra commits: $(git log --since="1 month ago" --pretty=format: --name-only origin/main | grep "^infra/" | wc -l)"
```

### Function & Code Pattern Analysis

**Function modification tracking:**
```bash
# Find most modified functions (Python)
cd ~/Hebbia/sisu-notes/mono && git log --since="3 months ago" origin/main -p | grep "^[-+].*def " | sort | uniq -c | sort -rg | head -20

# Find most modified classes (Python)
cd ~/Hebbia/sisu-notes/mono && git log --since="3 months ago" origin/main -p | grep "^[-+].*class " | sort | uniq -c | sort -rg | head -10

# Find most modified API endpoints
cd ~/Hebbia/sisu-notes/mono && git log --since="3 months ago" origin/main -p | grep -E "^[-+].*(@app\.route|@router|def.*api)" | sort | uniq -c | sort -rg | head -10

# Database schema changes
cd ~/Hebbia/sisu-notes/mono && git log --since="3 months ago" origin/main -p | grep -E "^[-+].*(CREATE|ALTER|DROP)" | sort | uniq -c | sort -rg | head -10
```

**Configuration and critical file changes:**
```bash
# Configuration file changes
cd ~/Hebbia/sisu-notes/mono && git log --since="1 month ago" --name-only origin/main | grep -E "\.(json|yaml|yml|toml|conf|cfg|ini)$" | sort | uniq -c | sort -rg

# Critical security/auth related changes
cd ~/Hebbia/sisu-notes/mono && git log --since="1 month ago" origin/main -p | grep -E "^[-+].*(password|secret|key|token|auth|permission)" | head -20

# Environment and deployment changes
cd ~/Hebbia/sisu-notes/mono && git log --since="1 month ago" --name-only origin/main | grep -E "(docker|k8s|deploy|env|infra)" | sort | uniq -c | sort -rg
```

### Team Productivity Analysis

**Commit frequency by author:**
```bash
# Commits per author in past month
cd ~/Hebbia/sisu-notes/mono && git log --since="1 month ago" origin/main --pretty=format:"%an" | sort | uniq -c | sort -rg

# Lines changed per author (approximation)
cd ~/Hebbia/sisu-notes/mono && git log --since="1 month ago" origin/main --pretty=format:"%an" --numstat | awk '{if(NF==3) {print $3; lines+=$1+$2}} END {print "Total lines:", lines}' | sort | uniq -c | sort -rg

# File diversity per author (how many different files touched)
cd ~/Hebbia/sisu-notes/mono && for author in $(git log --since="1 month ago" origin/main --pretty=format:"%an" | sort -u | head -10); do
  count=$(git log --author="$author" --since="1 month ago" --pretty=format: --name-only origin/main | sort -u | wc -l)
  echo "$count $author"
done | sort -rg
```

**Team focus areas:**
```bash
# Who works on backend most
cd ~/Hebbia/sisu-notes/mono && git log --since="1 month ago" --pretty=format:"%an" origin/main -- backend/ | sort | uniq -c | sort -rg | head -10

# Who works on frontend most
cd ~/Hebbia/sisu-notes/mono && git log --since="1 month ago" --pretty=format:"%an" origin/main -- frontend/ | sort | uniq -c | sort -rg | head -10

# Who works on infrastructure most
cd ~/Hebbia/sisu-notes/mono && git log --since="1 month ago" --pretty=format:"%an" origin/main -- infra/ | sort | uniq -c | sort -rg | head -10
```

### Enhanced Activity Summary Commands

**Comprehensive personal summary:**
```bash
# Complete activity summary for a person
git_user_summary() {
  local author="${1:-$(git config user.name)}"
  local since="${2:-1 month ago}"

  echo "=== Activity Summary for $author (since $since) ==="
  echo

  echo "Commit count:"
  cd ~/Hebbia/sisu-notes/mono && git log --author="$author" --since="$since" origin/main --oneline | wc -l

  echo -e "\nMost modified files:"
  cd ~/Hebbia/sisu-notes/mono && git log --author="$author" --since="$since" --pretty=format: --name-only origin/main | sort | uniq -c | sort -rg | head -10

  echo -e "\nFile types worked on:"
  cd ~/Hebbia/sisu-notes/mono && git log --author="$author" --since="$since" --pretty=format: --name-only origin/main | grep -o '\.[^.]*$' | sort | uniq -c | sort -rg

  echo -e "\nDirectories worked on:"
  cd ~/Hebbia/sisu-notes/mono && git log --author="$author" --since="$since" --pretty=format: --name-only origin/main | xargs -n1 dirname | sort | uniq -c | sort -rg | head -10

  echo -e "\nRecent commits with changes:"
  cd ~/Hebbia/sisu-notes/mono && git log --author="$author" --since="$since" origin/main --pretty=format:"%h %ad %s" --date=short --stat | head -50
}

# Usage: git_user_summary "wilson" "2 weeks ago"
```

**Critical change detection for summaries:**
```bash
# Detect critical changes in recent activity
detect_critical_changes() {
  local author="${1:-$(git config user.name)}"
  local since="${2:-1 week ago}"

  echo "=== Critical Changes Detection for $author ==="

  echo -e "\nSecurity-related changes:"
  cd ~/Hebbia/sisu-notes/mono && git log --author="$author" --since="$since" origin/main -p | grep -E "^[-+].*(password|secret|key|token|auth|permission)" || echo "None found"

  echo -e "\nDatabase changes:"
  cd ~/Hebbia/sisu-notes/mono && git log --author="$author" --since="$since" origin/main -p | grep -E "^[-+].*(CREATE|ALTER|DROP|migration)" || echo "None found"

  echo -e "\nAPI endpoint changes:"
  cd ~/Hebbia/sisu-notes/mono && git log --author="$author" --since="$since" origin/main -p | grep -E "^[-+].*(@app\.route|@router|def.*api)" || echo "None found"

  echo -e "\nConfiguration changes:"
  cd ~/Hebbia/sisu-notes/mono && git log --author="$author" --since="$since" --name-only origin/main | grep -E "\.(json|yaml|yml|toml|conf|cfg|ini|env)$" || echo "None found"
}
```

## Remote Operations

**Fetching updates:**
```bash
# Fetch latest from origin
cd ~/Hebbia/sisu-notes/mono && git fetch origin

# Fetch all remotes
cd ~/Hebbia/sisu-notes/mono && git fetch --all

# Fetch with prune (remove deleted remote branches)
cd ~/Hebbia/sisu-notes/mono && git fetch --prune
```

**Remote branch analysis:**
```bash
# Compare local main with remote main
cd ~/Hebbia/sisu-notes/mono && git log HEAD..origin/main --oneline

# Show remote tracking branches
cd ~/Hebbia/sisu-notes/mono && git branch -vv

# Remote branch activity
cd ~/Hebbia/sisu-notes/mono && git for-each-ref --sort=-committerdate refs/remotes/ --format='%(committerdate:short) %(refname:short) %(subject)'
```

## Date Helpers

**Common date ranges:**
- Past week: `--since="1 week ago"`
- Past month: `--since="1 month ago"`
- Past 3 months: `--since="3 months ago"`
- Specific date: `--since="2024-08-15"`
- Date range: `--since="2024-08-01" --until="2024-08-22"`

**Dynamic dates (use in scripts):**
```bash
# Past 7 days
WEEK_AGO=$(date -v-7d +%Y-%m-%d)
cd ~/Hebbia/sisu-notes/mono && git log --author="$(git config user.name)" --since="$WEEK_AGO" origin/main --oneline

# Past 30 days
MONTH_AGO=$(date -v-30d +%Y-%m-%d)
cd ~/Hebbia/sisu-notes/mono && git log --author="$(git config user.name)" --since="$MONTH_AGO" origin/main --oneline

# This week (Monday to now)
THIS_MONDAY=$(date -v-$(( $(date +%u) - 1 ))d +%Y-%m-%d)
cd ~/Hebbia/sisu-notes/mono && git log --since="$THIS_MONDAY" origin/main --oneline
```

## Output Formatting

**Custom formatting:**
```bash
# Commit hash, author, date, subject
cd ~/Hebbia/sisu-notes/mono && git log origin/main --pretty=format:"%h|%an|%ad|%s" --date=short -20

# JSON-like output for processing
cd ~/Hebbia/sisu-notes/mono && git log origin/main --pretty=format:'{"hash":"%H","author":"%an","date":"%ai","subject":"%s"}' -10

# CSV format
cd ~/Hebbia/sisu-notes/mono && git log origin/main --pretty=format:"%h,%an,%ad,%s" --date=short -20
```

**Processing with standard tools:**
```bash
# Count commits by author
cd ~/Hebbia/sisu-notes/mono && git log origin/main --pretty=format:"%an" | sort | uniq -c | sort -rn

# Group commits by day
cd ~/Hebbia/sisu-notes/mono && git log --since="1 month ago" origin/main --pretty=format:"%ad" --date=short | sort | uniq -c

# Extract file extensions from recent changes
cd ~/Hebbia/sisu-notes/mono && git log --since="1 week ago" origin/main --name-only | grep -o '\.[^.]*$' | sort | uniq -c | sort -rn
```

## Repository Configuration

**Current status:**
- **Repository Path:** `~/Hebbia/sisu-notes/mono/`
- **Default Remote:** `origin` (hebbia/mono)
- **Default Branch:** `main`
- **SSH Configuration:** Uses Hebbia SSH keys
- **Local Access:** Commands require navigation to mono directory

**Key Commands:**
- `cd ~/Hebbia/sisu-notes/mono && git status` - Check repository status
- `cd ~/Hebbia/sisu-notes/mono && git remote -v` - Verify remote configuration
- `cd ~/Hebbia/sisu-notes/mono && git fetch origin` - Update remote tracking branches

## Advanced Git Operations

**Search and filter:**
```bash
# Search commit messages with regex
cd ~/Hebbia/sisu-notes/mono && git log --grep="^fix:" origin/main --oneline

# Search file content in history
cd ~/Hebbia/sisu-notes/mono && git log -S "function_name" origin/main --oneline

# Search for commits that added or removed specific text
cd ~/Hebbia/sisu-notes/mono && git log -G "class.*User" origin/main --oneline

# Find commits that touched specific paths
cd ~/Hebbia/sisu-notes/mono && git log origin/main -- "backend/**/*.py" --oneline
```

**Blame and annotation:**
```bash
# Show who last modified each line
cd ~/Hebbia/sisu-notes/mono && git blame path/to/file.py

# Blame with commit details
cd ~/Hebbia/sisu-notes/mono && git blame -c path/to/file.py

# Show changes to specific line ranges
cd ~/Hebbia/sisu-notes/mono && git log -L 10,20:path/to/file.py origin/main
```

## Notes

- **All commands require navigating to `~/Hebbia/sisu-notes/mono/` directory first**
- **Default operations target `origin/main` branch**
- **Activity summaries include actual code changes via `git diff` and `git show` commands**
- Date ranges support natural language (e.g., "1 week ago", "3 months ago")
- Git log supports extensive formatting options via `--pretty=format:`
- Repository operations default to remote tracking branches for latest state
- File searches support glob patterns and directory filtering
- **Critical change detection** automatically identifies security, database, and API modifications
- **Comprehensive analysis** includes file touch frequency, function modifications, and team productivity metrics

### Important: Path Management

**Git Command Structure:**
- All git commands must be run from within `~/Hebbia/sisu-notes/mono/`
- Use `cd ~/Hebbia/sisu-notes/mono && git ...` pattern for consistency
- Remote operations target `origin` (hebbia/mono repository)
- Default branch operations use `origin/main` for latest remote state

**Best Practices:**
1. **Directory navigation:** Always cd to mono directory before git operations
2. **Remote branch targeting:** Default to `origin/main` for latest state
3. **Command chaining:** Use `&&` to ensure commands run from correct directory
4. **Consistent formatting:** Use standard format options for machine processing

### Team Integration Workflow

**Standard team analysis pattern:**
1. **Reference org structure:** Check `/Users/sisu/Hebbia/sisu-notes/tools/org_structure.md`
2. **Map authors:** Match team members to git author names
3. **Query activity:** Use `git log --author` with appropriate time ranges
4. **Aggregate results:** Use contributor statistics for summary views
5. **Analyze changes:** Focus on specific directories or file patterns relevant to team responsibilities