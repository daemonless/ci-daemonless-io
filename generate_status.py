#!/usr/bin/env python3
"""
Generate CI status page from daemonless repos.
Organizes images by category and shows build status.
"""
import subprocess
import json
import yaml
import datetime
from collections import defaultdict

OUTPUT_FILE = "docs/index.md"
SKIP_REPOS = {"daemonless", "cit", "ci-daemonless-io", "freebsd-ports", "daemonless-io"}

def gh_json(command):

    """Run gh command and return JSON."""

    try:

        result = subprocess.run(

            command, capture_output=True, text=True, check=True

        )

        if not result.stdout.strip():

            return None

        return json.loads(result.stdout)

    except (subprocess.CalledProcessError, json.JSONDecodeError):

        return None



def get_repos():

    """Get list of public repos."""

    print("Fetching repository list...")

    cmd = ["gh", "repo", "list", "daemonless", "--limit", "100", "--json", "name,isPrivate"]

    data = gh_json(cmd)

    if data:

        return [r for r in data if not r['isPrivate']]

    return []



def get_file_content(repo, path):

    """Fetch file content from repo."""

    cmd = ["gh", "api", f"repos/daemonless/{repo}/contents/{path}"]

    data = gh_json(cmd)

    if data and isinstance(data, dict) and 'content' in data:

        import base64

        try:

            return base64.b64decode(data['content']).decode('utf-8')

        except Exception as e:

            print(f"Error decoding {repo}/{path}: {e}")

    return None

def main():
    repos = get_repos()
    if not repos:
        print("No repositories found.")
        return

    by_category = defaultdict(list)
    
    print("Processing repositories...")
    for r in repos:
        name = r['name']
        if name in SKIP_REPOS:
            continue
            
        print(f"  - {name}")
        
        # Check if CI exists
        # We assume if build.yaml exists, CI is active
        # We can check existence efficiently via API without content
        has_ci = False
        try:
            subprocess.run(["gh", "api", f"repos/daemonless/{name}/contents/.github/workflows/build.yaml"], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            has_ci = True
        except:
            pass
            
        if not has_ci:
            continue

        # Get Category from compose.yaml or container-compose.yml
        category = "Uncategorized"
        compose_content = get_file_content(name, "compose.yaml")
        if not compose_content:
            compose_content = get_file_content(name, "container-compose.yml")
            
        if compose_content:
            try:
                data = yaml.safe_load(compose_content)
                category = data.get('x-daemonless', {}).get('category', 'Uncategorized')
            except:
                pass
        
        by_category[category].append(name)

    # Generate Markdown
    print("Generating Markdown...")
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    
    lines = [
        "# CI Status",
        "",
        "Build status for daemonless container images.",
        "",
        "!!! tip \"Gold Standard\"",
        "    Images in the **Media Management** and **Infrastructure** categories are prioritized for the highest quality standards.",
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
        lines.append("| App | Build Status | Last Commit |")
        lines.append("|-----|--------------|-------------|")
        
        for name in sorted(by_category[cat]):
            build_badge = f"[![build](https://img.shields.io/github/actions/workflow/status/daemonless/{name}/build.yaml?label=)](https://github.com/daemonless/{name}/actions/workflows/build.yaml)"
            commit_badge = f"[![commit](https://img.shields.io/github/last-commit/daemonless/{name}?label=)](https://github.com/daemonless/{name}/commits)"
            lines.append(f"| [{name}](https://github.com/daemonless/{name}) | {build_badge} | {commit_badge} |")
        
        lines.append("")

    lines.append("---")
    lines.append(f"*Last Updated: {timestamp}*")

    with open(OUTPUT_FILE, "w") as f:
        f.write("\n".join(lines))
    
    print(f"Generated {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
