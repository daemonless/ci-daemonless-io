#!/usr/bin/env python3
"""
Generate CI status page from daemonless repos.
Organizes images by category and shows build status.
"""
import os
import json
import yaml
import datetime
from collections import defaultdict
from pathlib import Path

OUTPUT_FILE = "docs/index.md"
EXPLICIT_SKIP = {"daemonless", "cit", "ci-daemonless-io", "freebsd-ports", "daemonless-io", ".woodpecker"}

def get_local_repos(root_path):
    """Get list of subdirectories in the root path that look like repos."""
    repos = []
    root = Path(root_path)
    if not root.exists():
        print(f"Error: {root_path} does not exist.")
        return []

    for item in root.iterdir():
        if item.is_dir() and item.name not in EXPLICIT_SKIP and not item.name.startswith('.'):
            # Check if it has a build workflow, indicating it's a built image
            if (item / ".github" / "workflows" / "build.yaml").exists():
                 repos.append(item)
    return repos

def main():
    # daemonless/ci-daemonless-io/generate_status.py -> daemonless/
    root_path = Path("..") 
    repos = get_local_repos(root_path)
    
    if not repos:
        print("No repositories found.")
        return

    # Store list of config dicts
    by_category = defaultdict(list)
    
    print(f"Found {len(repos)} repositories.")
    
    for repo_path in repos:
        name = repo_path.name
        print(f"Processing {name}...")
        
        # Default Metadata
        category = "Uncategorized"
        icon = ":material-docker:"
        upstream_url = None
        description = ""
        
        compose_file = repo_path / "compose.yaml"
        if not compose_file.exists():
            compose_file = repo_path / "container-compose.yml"
            
        if compose_file.exists():
            try:
                with open(compose_file, 'r') as f:
                    data = yaml.safe_load(f)
                    meta = data.get('x-daemonless', {})
                    category = meta.get('category', 'Uncategorized')
                    icon = meta.get('icon', ':material-docker:')
                    upstream_url = meta.get('upstream_url')
                    description = meta.get('description', '')
            except Exception as e:
                print(f"  Error reading compose file for {name}: {e}")
        
        by_category[category].append({
            "name": name,
            "icon": icon,
            "upstream_url": upstream_url,
            "description": description
        })

    # Generate Markdown
    print("Generating Markdown...")
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    
    lines = [
        "# CI Status",
        "",
        "Build status for daemonless container images.",
        "",
        "[Main Documentation](https://daemonless.io){ .md-button }",
        ""
    ]

    # Sort categories (Base first, then alpha, Uncategorized last)
    cats = sorted(by_category.keys())
    if "Base" in cats:
        cats.remove("Base")
        cats.insert(0, "Base")
    if "Uncategorized" in cats:
        cats.remove("Uncategorized")
        cats.append("Uncategorized")

    for cat in cats:
        lines.append(f"## {cat}")
        lines.append("")
        # Updated columns: App | Description | Repo | Upstream | Build Status | Last Commit
        lines.append("| App | Description | Repo | Upstream | Build Status | Last Commit |")
        lines.append("|-----|-------------|------|----------|--------------|-------------|")
        
        # Sort by name
        for item in sorted(by_category[cat], key=lambda x: x['name']):
            name = item['name']
            icon = item['icon']
            upstream = item['upstream_url']
            desc = item['description']
            
            # Links
            doc_link = f"[{icon} {name}](https://daemonless.io/images/{name})"
            repo_link = f"[:simple-github:](https://github.com/daemonless/{name})"
            
            if upstream:
                upstream_link = f"[:material-link-variant:]({upstream})"
            else:
                upstream_link = "-"

            build_badge = f"[![build](https://img.shields.io/github/actions/workflow/status/daemonless/{name}/build.yaml?label=)](https://github.com/daemonless/{name}/actions/workflows/build.yaml)"
            commit_badge = f"[![commit](https://img.shields.io/github/last-commit/daemonless/{name}?label=)](https://github.com/daemonless/{name}/commits)"
            
            lines.append(f"| {doc_link} | {desc} | {repo_link} | {upstream_link} | {build_badge} | {commit_badge} |")
        
        lines.append("")

    lines.append("---")
    lines.append(f"*Last Updated: {timestamp}*")

    with open(OUTPUT_FILE, "w") as f:
        f.write("\n".join(lines))
    
    print(f"Generated {OUTPUT_FILE}")

if __name__ == "__main__":
    main()