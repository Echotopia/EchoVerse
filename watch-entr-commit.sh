#!/usr/bin/env bash
set -e
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

if [ -z "$OPENROUTER_API_KEY" ]; then
  echo "Error: OPENROUTER_API_KEY is not set."
  exit 1
fi

echo "Watching for file changes..."
export OPENROUTER_API_KEY

watch_changes() {
  count=$(git diff --name-only | wc -l)
  if [ "$count" -eq 0 ]; then
    echo -e "${YELLOW}No changes to commit.${NC}"
    return
  fi

  echo -e "${GREEN}Generating commit message via watch.py...${NC}"
  msg=$(python3 watch.py)

  echo -e "${GREEN}Commit message: $msg${NC}"
  git add -A >/dev/null 2>&1
  git commit -m "$msg" >/dev/null 2>&1
  git push >/dev/null 2>&1

  echo -e "${GREEN}$count files changed.${NC}"
}
 

export -f watch_changes

# Watch all files recursively and trigger on changes, but ignore .git, watch-entr-commit.sh, and watch.py to avoid infinite loop
find . -type f -not -path "./.git/*" -not -path "./.*/*" -not -path "./.states/*" -not -name "watch-entr-commit.sh" -not -name "watch.py" | entr -d -p -r bash -c 'watch_changes'
