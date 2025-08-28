# Auto-sync Mono Analysis Repository

## Rule Description
Before executing any terminal command, automatically navigate to the `~/Hebbia/mono_analysis` repository and run `git pull` to ensure it's up to date.

## Trigger
- **When:** Before any `run_terminal_cmd` execution
- **Scope:** All terminal commands in this workspace

## Required Actions
1. Change directory to `~/Hebbia/mono_analysis`
2. Run `git pull` to fetch latest changes
3. Return to original working directory
4. Proceed with the requested command

## Implementation
```bash
# Auto-sync before any command
cd ~/Hebbia/mono_analysis && git pull && cd -
```

## Purpose
- Ensures the mono analysis repository is always synchronized with the latest changes
- Provides all commands with access to the most current information
- Maintains consistency between the linked `mono` directory and the actual repository

## Context
- This workspace contains notes, documentation, and analysis related to Hebbia's mono architecture
- The `mono` directory is a symlink to `~/Hebbia/mono_analysis`
- The mono_analysis repository contains the latest analysis and insights
- Keeping it synchronized ensures all commands have access to the most current information

## Priority
**High** - This rule should be executed before every terminal command to maintain data consistency.
