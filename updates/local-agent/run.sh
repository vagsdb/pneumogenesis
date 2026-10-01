#!/usr/bin/env bash
# Run the Pneumogenesis updates agent once, headless, on this computer.
#
#   updates/local-agent/run.sh monwed     # Monday / Wednesday run (up to 8 items)
#   updates/local-agent/run.sh friday     # Friday weekly roundup (up to 12 + digest)
#
# Requirements: claude (Claude Code CLI, logged in), gh (logged in), git, python3, curl, flock.
# The agent only ever pushes an updates/YYYY-MM-DD branch and opens a pull request;
# AGENT.md forbids pushing to main or merging.
set -euo pipefail

MODE="${1:-}"
case "$MODE" in
  monwed|friday) ;;
  *) echo "usage: $0 monwed|friday" >&2; exit 2 ;;
esac

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(git -C "$HERE" rev-parse --show-toplevel)"
LOG_DIR="${PNEUMO_AGENT_LOG_DIR:-$HOME/.local/state/pneumogenesis-agent}"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/$(TZ=Europe/Athens date +%Y-%m-%d_%H%M)-$MODE.log"

# One run at a time, even if a timer fires while a manual run is going.
exec 9>"$LOG_DIR/.lock"
if ! flock -n 9; then
  echo "another agent run is in progress; skipping" | tee -a "$LOG"
  exit 0
fi

for tool in claude gh git python3 curl; do
  command -v "$tool" >/dev/null || { echo "missing: $tool" | tee -a "$LOG"; exit 1; }
done
gh auth status >/dev/null 2>&1 || { echo "gh is not logged in (run: gh auth login)" | tee -a "$LOG"; exit 1; }

cd "$REPO"
# The agent works on its own branches; never run on top of local edits.
if [ -n "$(git status --porcelain)" ]; then
  echo "working tree of $REPO is not clean; refusing to run" | tee -a "$LOG"
  exit 1
fi
git fetch -q origin main
git checkout -q --detach origin/main

PROMPT="$(cat "$HERE/prompt-$MODE.md")"

{
  echo "== Pneumogenesis agent: $MODE, $(TZ=Europe/Athens date '+%Y-%m-%d %H:%M %Z'), repo $REPO"
  # Tools the agent may use without asking. Bash is limited to the commands the run needs.
  claude -p "$PROMPT" \
    --permission-mode acceptEdits \
    --allowedTools \
      "Read" "Edit" "Write" "Glob" "Grep" "WebSearch" "WebFetch" \
      "Bash(git *)" "Bash(gh pr *)" "Bash(gh auth status*)" \
      "Bash(python3 updates/validate.py*)" "Bash(python3 -c *)" \
      "Bash(curl *)" "Bash(date*)" "Bash(TZ=* date*)" "Bash(ls*)" "Bash(cat *)" "Bash(jq *)"
  echo "== finished $(TZ=Europe/Athens date '+%H:%M %Z')"
} 2>&1 | tee -a "$LOG"

# Leave the clone on main for the next run.
git checkout -q --detach origin/main || true
