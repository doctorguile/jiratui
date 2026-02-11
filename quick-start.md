# JiraTUI Quick Start Guide

## Installation (macOS with Nix)

### Prerequisites

jiratui requires `libmagic` which isn't bundled. Install it via nix profile:

```bash
nix profile install nixpkgs#file
```

This installs libmagic to `~/.nix-profile/lib/`.

### Option A: Install from PyPI (Recommended)

```bash
# Install jiratui
uv tool install jiratui

# Patch python-magic to find libmagic in nix profile
# (Required after each reinstall)
./scripts/patch-libmagic.sh

# Verify
jiratui version
```

### Option B: Install from Local Repo (Development)

```bash
cd ~/Projects/jiratui

# Install from local source
uv tool install . --force

# Patch python-magic (required after each reinstall)
./scripts/patch-libmagic.sh

# Verify
jiratui version
```

### Option C: Development Mode (nix-shell)

For development without global install:

```bash
cd ~/Projects/jiratui
nix-shell  # provides libmagic + git, activates venv
jiratui version
```

Or one-liner:
```bash
nix-shell --run 'jiratui <command>'
```

### What the Patch Does

The `python-magic` library hardcodes search paths for `libmagic.dylib`:
- `/opt/homebrew/lib`
- `/usr/local/lib`
- `/opt/local/lib`

The patch adds `~/.nix-profile/lib` to this list. Run it after each
`uv tool install jiratui` or `uv tool install . --force`.

---

## CLI Commands

### Search Issues

```bash
# Search by project
jiratui issues search --project-key PROJ
jiratui issues search -p PROJ --limit 10

# Search by specific issue key (shows basic info)
jiratui issues search --key PROJ-7144
jiratui issues search -k PROJ-7144

# With date filters
jiratui issues search -p PROJ --created-from 2026-01-01
jiratui issues search -p PROJ --created-from 2026-01-01 --created-until 2026-02-01

# With assignee (requires account ID, not username)
jiratui issues search -p PROJ --assignee-account-id "$USER"
```

> **Note:** The CLI `issues search` does not support raw JQL queries - only the
> filter options above. For full JQL support, use the TUI with `-j <ID>` or
> use the Jira API directly (see `jdrs`/`jdit` functions in Shell Aliases section below).

### View Issue Details & Metadata

```bash
# Get status IDs, priority IDs, and valid transitions
jiratui issues metadata PROJ-7144
```

This shows:
- Valid work types (Story, Task, Bug, etc.)
- Priority IDs (P1=10300, P2=10301, P3=10302, P4=10303, P5=10400, P1-Blocker=10401)
- **Status IDs and valid transitions** (TODO=17200, In Progress=3, Blocked=10300, Resolved=5)

### Transition Issue Status

```bash
# TODO -> In Progress
jiratui issues update PROJ-7144 --status-id 3

# In Progress -> Resolved (Fixed)
jiratui issues update PROJ-7144 --status-id 5

# Any -> Blocked
jiratui issues update PROJ-7144 --status-id 10300

# Any -> TODO
jiratui issues update PROJ-7144 --status-id 17200
```

### Update Other Fields

```bash
# Update summary/title
jiratui issues update PROJ-7144 --summary "New title here"

# Update priority
jiratui issues update PROJ-7144 --priority-id 10301  # P2

# Update due date
jiratui issues update PROJ-7144 --due-date 2026-03-15

# Assign to someone (need account ID)
jiratui issues update PROJ-7144 --assignee-account-id "$USER"

# Unassign
jiratui issues update PROJ-7144 --assignee-account-id ""
```

### Comments

```bash
# List comments
jiratui comments list PROJ-7144

# Add comment
jiratui comments add PROJ-7144 "This is my comment"

# Show specific comment
jiratui comments show PROJ-7144 <comment-id>

# Delete comment
jiratui comments delete PROJ-7144 <comment-id>
```

### Users

```bash
# Find user by name/email (useful for getting account IDs)
jiratui users search $USER
jiratui users search "John Doe"
```

---

## TUI (Terminal UI)

### Launch with Predefined JQL Query

```bash
# Launch with your predefined JQL (by ID from config)
jiratui ui --jql-expression-id 1 --search-on-startup

# Short form
jiratui ui -j 1 --search-on-startup

# With theme
jiratui ui -j 1 --search-on-startup --theme dracula
```

### Available Themes

```bash
jiratui themes
```

Common themes: `dracula`, `github-dark`, `monokai`, `nord`, `tokyo-night`

### Open Specific Ticket in TUI

```bash
# Open TUI with a specific ticket loaded
jiratui ui --work-item-key PROJ-7138
jiratui ui -w PROJ-7138

# With theme
jiratui ui -w PROJ-7138 --theme dracula
```

### Other UI Options

```bash
# Pre-select project
jiratui ui --project-key PROJ

# Auto-focus first result from a saved query
jiratui ui -j 1 --search-on-startup --focus-item-on-startup 1
```

---

## Config: Predefined JQL Queries (TUI Only)

> **Note:** These saved queries work with the TUI (`jiratui ui -j <ID>`), not
> the CLI `issues search`. For CLI JQL, see `jdrs`/`jdit` functions in Shell Aliases section.

Add to `~/.config/jiratui/config.yaml`:

```yaml
pre_defined_jql_expressions:
  1:
    label: 'My PROJ tickets (active)'
    expression: 'project = PROJ AND status in ("In Progress", Blocked, TODO) AND assignee = "jdoe" order by created desc'
  2:
    label: 'My PROJ tickets (v2026.2)'
    expression: 'project = PROJ AND status in ("In Progress", Blocked, TODO) AND assignee = "jdoe" AND fixVersion = v2026.2 order by created desc'
  3:
    label: 'My OPS tickets (active)'
    expression: 'project = OPS AND status in ("In Progress", Blocked, TODO) AND assignee = "jdoe" order by created desc'
```

Then launch with:
```bash
jiratui ui -j 1 --search-on-startup  # My PROJ tickets
jiratui ui -j 2 --search-on-startup  # PROJ + fixVersion
jiratui ui -j 3 --search-on-startup  # My OPS tickets
```

---

## Status ID Quick Reference (for your Jira)

| Status      | ID    | Command                                    |
|-------------|-------|--------------------------------------------|
| TODO        | 17200 | `jiratui issues update <KEY> --status-id 17200` |
| In Progress | 3     | `jiratui issues update <KEY> --status-id 3`     |
| Blocked     | 10300 | `jiratui issues update <KEY> --status-id 10300` |
| Resolved    | 5     | `jiratui issues update <KEY> --status-id 5`     |

---

## Shell Aliases & Functions (Optional)

Add to `~/.zshrc` or `~/.bashrc`:

```bash
# Configuration
export JIRA_BASE_URL='https://jira.example.com'
export JIRA_TOKEN='your-token-here'  # or source from a secrets file

# Helper: auto-prefix PROJ- for pure numbers
_jt_ticket() { [[ "$1" =~ ^[0-9]+$ ]] && echo "PROJ-$1" || echo "$1"; }

# TUI aliases (global install - no nix-shell needed)
alias jtdrs='jiratui ui -j 1 --search-on-startup'
alias jtnr='jiratui ui -j 2 --search-on-startup'
alias jtdit='jiratui ui -j 3 --search-on-startup'

# Open ticket in TUI with details loaded
# Usage: jt 7138 or jt PROJ-7138 or jt OPS-1234
jt() {
  local ticket="$(_jt_ticket "$1")"
  jiratui ui --search-on-startup --focus-item-on-startup 1 -w "$ticket"
}

# Open ticket in browser
# Usage: jb 7138 or jb PROJ-7138 or jb OPS-1234
jb() {
  local ticket="$(_jt_ticket "$1")"
  open "$JIRA_BASE_URL/browse/$ticket"
}

# Quick status transitions
jstart() { jiratui issues update "$(_jt_ticket "$1")" --status-id 3; }     # -> In Progress
jdone() { jiratui issues update "$(_jt_ticket "$1")" --status-id 5; }      # -> Resolved
jblock() { jiratui issues update "$(_jt_ticket "$1")" --status-id 10300; } # -> Blocked
jtodo() { jiratui issues update "$(_jt_ticket "$1")" --status-id 17200; }  # -> TODO

# CLI with raw JQL (for queries not supported by jiratui CLI)
jdrs() {
  curl -s -H "Authorization: Bearer $JIRA_TOKEN" \
    "$JIRA_BASE_URL/rest/api/2/search" \
    --data-urlencode 'jql=project = PROJ AND status in ("In Progress", Blocked, TODO) AND assignee = "'"$USER"'" order by created desc' \
    --data-urlencode 'maxResults=50' \
    --data-urlencode 'fields=key,summary,status' \
    -G | jq -r '.issues[] | "\(.key)\t\(.fields.status.name)\t\(.fields.summary)"' | column -t -s $'\t'
}

jdit() {
  curl -s -H "Authorization: Bearer $JIRA_TOKEN" \
    "$JIRA_BASE_URL/rest/api/2/search" \
    --data-urlencode 'jql=project = OPS AND status in ("In Progress", Blocked, TODO) AND assignee = "'"$USER"'" order by created desc' \
    --data-urlencode 'maxResults=50' \
    --data-urlencode 'fields=key,summary,status' \
    -G | jq -r '.issues[] | "\(.key)\t\(.fields.status.name)\t\(.fields.summary)"' | column -t -s $'\t'
}

# =============================================================================
# CREATE TICKET FUNCTIONS
# =============================================================================

# Issue type and priority IDs (shared across projects)
_JIRA_TASK_ID=10100
_JIRA_BUG_ID=10102
_JIRA_P2_ID=10301

# Create PROJ ticket
# Usage: jcreate-drs "Summary" [-t task|bug] [-d "description"] [-f "fixVersion"] [-a assignee]
jcreate-drs() {
  local summary="" type="task" description="" fix_version="" assignee="$USER"
  local OPTIND opt
  while getopts "t:d:f:a:h" opt; do
    case $opt in
      t) type="$OPTARG" ;;
      d) description="$OPTARG" ;;
      f) fix_version="$OPTARG" ;;
      a) assignee="$OPTARG" ;;
      h) echo "Usage: jcreate-drs \"Summary\" [-t task|bug] [-d desc] [-f fixVersion] [-a assignee]"
         echo "Defaults: -t task, -a $USER"
         return 0 ;;
      *) return 1 ;;
    esac
  done
  shift $((OPTIND-1))
  summary="$1"

  if [[ -z "$summary" ]]; then
    echo "Usage: jcreate-drs \"Summary\" [-t task|bug] [-d desc] [-f fixVersion] [-a assignee]"
    echo "Defaults: -t task, -a $USER"
    return 1
  fi

  local issue_type_id=$_JIRA_TASK_ID
  [[ "$type" == "bug" ]] && issue_type_id=$_JIRA_BUG_ID

  local payload=$(jq -n \
    --arg proj "PROJ" \
    --arg summary "$summary" \
    --arg desc "$description" \
    --arg issueType "$issue_type_id" \
    --arg priority "$_JIRA_P2_ID" \
    --arg assignee "$assignee" \
    --arg fixVer "$fix_version" \
    '{
      fields: {
        project: { key: $proj },
        summary: $summary,
        issuetype: { id: $issueType },
        priority: { id: $priority },
        assignee: { name: $assignee }
      }
      + (if $desc != "" then { description: $desc } else {} end)
      + (if $fixVer != "" then { fixVersions: [{ name: $fixVer }] } else {} end)
    }')

  local response=$(curl -s -X POST \
    -H "Authorization: Bearer $JIRA_TOKEN" \
    -H "Content-Type: application/json" \
    "$JIRA_BASE_URL/rest/api/2/issue" \
    -d "$payload")

  local key=$(echo "$response" | jq -r '.key // empty')
  if [[ -n "$key" ]]; then
    echo "Created: $key"
    echo "$JIRA_BASE_URL/browse/$key"
  else
    echo "Error creating ticket:"
    echo "$response" | jq .
  fi
}

# Create SRE ticket
# Usage: jcreate-sreas "Summary" [-t task|bug] [-d "description"] [-a assignee]
jcreate-sreas() {
  local summary="" type="task" description="" assignee="jsmith"
  local OPTIND opt
  while getopts "t:d:a:h" opt; do
    case $opt in
      t) type="$OPTARG" ;;
      d) description="$OPTARG" ;;
      a) assignee="$OPTARG" ;;
      h) echo "Usage: jcreate-sreas \"Summary\" [-t task|bug] [-d desc] [-a assignee]"
         echo "Defaults: -t task, -a jsmith"
         echo "Assignees: jsmith, asmith, or any username"
         return 0 ;;
      *) return 1 ;;
    esac
  done
  shift $((OPTIND-1))
  summary="$1"

  if [[ -z "$summary" ]]; then
    echo "Usage: jcreate-sreas \"Summary\" [-t task|bug] [-d desc] [-a assignee]"
    echo "Defaults: -t task, -a jsmith"
    return 1
  fi

  local issue_type_id=$_JIRA_TASK_ID
  [[ "$type" == "bug" ]] && issue_type_id=$_JIRA_BUG_ID

  local payload=$(jq -n \
    --arg proj "SRE" \
    --arg summary "$summary" \
    --arg desc "$description" \
    --arg issueType "$issue_type_id" \
    --arg priority "$_JIRA_P2_ID" \
    --arg assignee "$assignee" \
    '{
      fields: {
        project: { key: $proj },
        summary: $summary,
        issuetype: { id: $issueType },
        priority: { id: $priority },
        assignee: { name: $assignee }
      }
      + (if $desc != "" then { description: $desc } else {} end)
    }')

  local response=$(curl -s -X POST \
    -H "Authorization: Bearer $JIRA_TOKEN" \
    -H "Content-Type: application/json" \
    "$JIRA_BASE_URL/rest/api/2/issue" \
    -d "$payload")

  local key=$(echo "$response" | jq -r '.key // empty')
  if [[ -n "$key" ]]; then
    echo "Created: $key"
    echo "$JIRA_BASE_URL/browse/$key"
  else
    echo "Error creating ticket:"
    echo "$response" | jq .
  fi
}
```

### Create Ticket Examples (Shell Functions)

```bash
# PROJ tickets (defaults: -t task, -a jdoe, priority P2)
jcreate-drs "Implement new feature"
jcreate-drs "Fix auth bug" -t bug
jcreate-drs "Add caching" -d "Improve API response time"
jcreate-drs "Release prep" -f "v2026.2"
jcreate-drs "Complex task" -t task -d "Full description" -f "v2026.2"

# SRE tickets (defaults: -t task, -a jsmith, priority P2)
jcreate-sreas "Deploy vault changes"
jcreate-sreas "Update configs" -a asmith
jcreate-sreas "Fix prod issue" -t bug
jcreate-sreas "New service" -a asmith -d "Full deploy details"

# Show help
jcreate-drs -h
jcreate-sreas -h
```

---

## Python Script: jcreate.py

A standalone Python script (no 3rd party dependencies) for creating tickets.

### Setup

```bash
# Add to PATH or create alias
ln -s ~/Projects/jiratui/scripts/jcreate.py ~/.local/bin/jcreate
ln -s ~/Projects/jiratui/scripts/jcreate.py ~/.local/bin/jc

# Or alias in ~/.zshrc
alias jcreate='~/Projects/jiratui/scripts/jcreate.py'
```

### Usage

```bash
jcreate.py "Summary" [-p PROJ|SRE] [-t task|bug] [-d "description"] [-f "fixVersion"] [-a assignee]
jcreate.py -l [-p PROJECT] [--all]   # List available fix versions
```

| Flag | Description | Default |
|------|-------------|---------|
| `-p, --project` | Project key | PROJ |
| `-t, --type` | Issue type (task, bug) | task |
| `-d, --description` | Issue description | - |
| `-f, --fix-version` | Fix version (PROJ only) | - |
| `-l, --list-fix-versions` | List available fix versions | - |
| `--all` | With -l: include released/archived | - |
| `-a, --assignee` | Assignee username | jdoe (PROJ), jsmith (SRE) |
| `--dry-run` | Print payload without creating | - |

### Examples

```bash
# PROJ tickets (default project)
jcreate "Fix login bug" -t bug
jcreate "Add feature" -d "Detailed description" -f "v2026.2"
jcreate "Task for someone else" -a jsmith

# SRE tickets
jcreate "Deploy service" -p SRE
jcreate "Config update" -p SRE -a asmith
jcreate "Prod fix" -p SRE -t bug -d "Urgent production issue"

# Preview without creating
jcreate "Test ticket" -t bug --dry-run

# List available fix versions
jcreate -l                 # Unreleased versions for PROJ
jcreate -l --all           # All versions (including released/archived)
jcreate -l -p SRE        # Versions for SRE (if any)
```

### Environment Variables

```bash
# Required
export JIRA_TOKEN='your-bearer-token'

# Optional (has default)
export JIRA_BASE_URL='https://jira.example.com'
```

