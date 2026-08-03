#!/usr/bin/env bash
# Enforces the clean architecture dependency rule: dependencies point inward.
# See CLAUDE.md and .claude/skills/django-project-structure/SKILL.md
set -uo pipefail

status=0

report() {
    local message="$1"
    local matches="$2"
    if [ -n "$matches" ]; then
        echo "ARCHITECTURE VIOLATION: $message"
        echo "$matches" | sed 's/^/  /'
        echo
        status=1
    fi
}

inner_layers=()
for layer in domain application; do
    [ -d "$layer" ] && inner_layers+=("$layer")
done

if [ ${#inner_layers[@]} -gt 0 ]; then
    report "framework imports in domain/ or application/ (must stay portable)" \
        "$(grep -rnE '^[[:space:]]*(from|import)[[:space:]]+(django|rest_framework)' \
            "${inner_layers[@]}" --include='*.py' 2>/dev/null)"

    report "inner layer importing an outer layer" \
        "$(grep -rnE '^[[:space:]]*(from|import)[[:space:]]+(infrastructure|interface|config)' \
            "${inner_layers[@]}" --include='*.py' 2>/dev/null)"
fi

if [ -d domain ]; then
    report "domain/ importing application/" \
        "$(grep -rnE '^[[:space:]]*(from|import)[[:space:]]+application' \
            domain --include='*.py' 2>/dev/null)"
fi

if [ -d interface ]; then
    report "ORM access in interface/ (query behind a repository instead)" \
        "$(grep -rn '\.objects' interface --include='*.py' 2>/dev/null)"
fi

if [ "$status" -eq 0 ]; then
    echo "Architecture boundaries OK."
fi

exit "$status"
