#!/usr/bin/env bash
# Read-only session brief for Claude Code's SessionStart hook: prints where the mission stands.
# No network, no writes. Safe to run anywhere.
set -u
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root" || exit 0
printf 'SIGHTBREAK mission brief\n'
if git rev-parse --git-dir >/dev/null 2>&1; then
  printf 'branch: %s\nhead:   %s\n' "$(git rev-parse --abbrev-ref HEAD 2>/dev/null)" "$(git log -1 --format='%h %s' 2>/dev/null | cut -c1-100)"
  dirty="$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
  printf 'uncommitted files: %s\n' "$dirty"
fi
if [ -f docs/engineering/NEXT_SESSION.md ]; then
  printf '\n--- docs/engineering/NEXT_SESSION.md (top) ---\n'
  sed -n '1,40p' docs/engineering/NEXT_SESSION.md
else
  printf '\nNo docs/engineering/NEXT_SESSION.md on this branch. Check the claude/mission-foundation-v1 branch.\n'
fi
printf '\nRead CLAUDE.md, then docs/roadmap/SIGHTBREAK_V1_PROGRESS.md. Continue the next unfinished milestone.\n'
