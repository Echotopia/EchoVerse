#!/usr/bin/env bash
set -e

if [ -z "$OPENROUTER_API_KEY" ]; then
  echo "Error: OPENROUTER_API_KEY is not set."
  exit 1
fi

echo "Watching for file changes..."
export OPENROUTER_API_KEY

watch_changes() {
  diff=$(git diff)
  if [ -z "$diff" ]; then
    echo "No changes to commit."
    return
  fi

  echo "Generating commit message via watch.py..."
  msg=$(python3 watch.py)


  echo "Commit message: $msg"
  git add -A
  git commit -m "$msg"
  git push
}
 

export -f watch_changes

# Watch all files recursively and trigger on changes, but ignore .git, watch-entr-commit.sh, and watch.py to avoid infinite loop
find . -type f -not -path "./.git/*" -not -path "./.*/*" -not -path "./.states/*" -not -name "watch-entr-commit.sh" -not -name "watch.py" | entr -d -p -r bash -c 'watch_changes'
