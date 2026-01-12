#!/bin/sh
# Generate CI status page from daemonless repos

OUTPUT="docs/index.md"
mkdir -p docs

cat > "$OUTPUT" << 'EOF'
# CI Status

Build status for daemonless container images.

| App | Status | Last Commit |
|-----|--------|-------------|
EOF

# Get all public repos in daemonless org that have build.yaml
gh repo list daemonless --limit 100 --json name,isPrivate --jq '.[] | select(.isPrivate == false) | .name' | sort | while read -r repo; do
    # Skip non-container repos
    case "$repo" in
        daemonless|cit|ci-daemonless-io|freebsd-ports) continue ;;
    esac

    # Check if repo has build.yaml workflow
    if gh api "repos/daemonless/$repo/contents/.github/workflows/build.yaml" >/dev/null 2>&1; then
        echo "| $repo | [![build](https://img.shields.io/github/actions/workflow/status/daemonless/$repo/build.yaml?label=)](https://github.com/daemonless/$repo/actions/workflows/build.yaml) | [![commit](https://img.shields.io/github/last-commit/daemonless/$repo?label=)](https://github.com/daemonless/$repo/commits) |" >> "$OUTPUT"
    fi
done

echo "" >> "$OUTPUT"
echo "*Updated: $(date -u +"%Y-%m-%d %H:%M UTC")*" >> "$OUTPUT"

echo "Generated $OUTPUT"
