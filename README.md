# CI Results

Test results from daemonless container builds.

## Structure

```
results/
└── <app>/
    └── <tag>/
        └── result.json
```

## Result Format

```json
{
  "app": "sonarr",
  "tag": "pkg-latest",
  "version": "4.0.15.2941_1-pkg-latest",
  "image": "ghcr.io/daemonless/sonarr:pkg-latest",
  "timestamp": "2026-01-04T12:00:00Z",
  "health": "pass",
  "screenshot": "pass",
  "verify": "pass",
  "result": "pass"
}
```
