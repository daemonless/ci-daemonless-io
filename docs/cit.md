# Container Integration Test (CIT)

**CIT** is the quality assurance engine behind Daemonless. It goes beyond simple "build success" indicators to verify that every container is fully functional, accessible, and rendering its UI correctly before it is published.

## The Problem
In the container world, a "green build" only means the `podman build` command finished without error. It does not guarantee:
*   The application starts up correctly.
*   The web interface is accessible.
*   The .NET/Java/Node runtime is compatible with the host kernel.
*   The page isn't just a white "500 Error" screen.

## The Solution
CIT is a custom Python/Selenium tool designed for FreeBSD that performs **end-to-end black-box testing** on every container.

### Testing Pipeline
Every time a change is pushed, CIT executes the following validation chain:

1.  **Runtime Start:** Launches the container using `podman` (and `ocijail`).
2.  **Log Pattern Analysis:** Instead of sleeping for an arbitrary time, CIT watches the container logs for specific "Ready" signals (e.g., `listening on port`, `startup complete`).
3.  **Port Verification:** Ensures the TCP port is open and accepting connections.
4.  **Health Check:** Pings the application's API or health endpoint (e.g., `/ping` or `/api/v1/system/status`).
5.  **Visual Verification:** 
    *   Launches a headless Chromium instance.
    *   Navigates to the application's Web UI.
    *   Captures a high-resolution screenshot.
    *   **Computer Vision Analysis:** Uses `scikit-image` to analyze the screenshot.
        *   **Blank Check:** Fails if the screen is solid white/black (common with JS errors).
        *   **Edge Density:** Verifies there are "UI elements" (buttons, text boxes) present.
        *   **Baseline Compare:** (Optional) Compares against a "known good" reference image.

## Visual Verification in Action
CIT doesn't just check if the server returns `200 OK`; it looks at the page.

### 1. Success
The application rendered a login screen or dashboard.
*   **Edge Density:** High (many lines/contrasts).
*   **Result:** ✅ PASS

### 2. Failure (Blank Screen)
The server returned `200 OK`, but the JavaScript crashed, leaving a white page.
*   **Edge Density:** ~0.0 (No visual details).
*   **Result:** ❌ FAIL

## Running CIT Locally
You can run CIT on your own machine (FreeBSD required for full support) to verify images.

```bash
# Download and run against a local image
fetch https://github.com/daemonless/cit/releases/latest/download/cit.tar.gz
tar xzf cit.tar.gz
./cit ghcr.io/daemonless/radarr:latest --verify
```

### Example Output
```text
Testing: ghcr.io/daemonless/radarr:latest
  Mode: screenshot
  Port: 7878
  Health: /ping
Runtime: doas podman
Image exists locally
Labels: port=7878 health=http://localhost:7878/ping
Starting target...
Started: 1a2b3c4d5e
Target IP: 10.88.0.5
Waiting for ready signal (timeout: 30s)...
Ready signal after 3s
Waiting for port 7878...
Port ready after 0s
Port test: PASS
Health test: PASS
Screenshot captured: /tmp/cit-screenshot.png
PASS: ghcr.io/daemonless/radarr:latest (screenshot)
Cleaning up...
```
