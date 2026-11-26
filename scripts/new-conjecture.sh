#!/usr/bin/env bash
# Usage: scripts/new-conjecture.sh CamelCaseName "Human readable title"
set -euo pipefail
cd "$(dirname "$0")/.."

name="${1:-}"; title="${2:-$1}"
if [[ ! "$name" =~ ^[A-Z][A-Za-z0-9]*$ ]]; then
  echo "Name must be CamelCase letters/digits, starting with a capital (e.g. TwinPrimeVariant)." >&2
  exit 1
fi
dir="Conjectures/$name"
[[ -e "$dir" ]] && { echo "$dir already exists." >&2; exit 1; }

mkdir -p "$dir"
for f in README.md Main.lean; do
  sed -e "s/__NAME__/$name/g" -e "s/__TITLE__/$title/g" "templates/conjecture/$f" > "$dir/$f"
done
echo "- [$title]($dir/) — Open" >> README.md
echo "Created $dir/ (README.md + Main.lean) and added it to the index in README.md."
