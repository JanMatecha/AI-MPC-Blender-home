# AI-MPC-Blender-home

Minimal proof of concept for controlling a live Blender 5.2 session from Codex through the official Blender Lab MCP integration.

> Status: **POC v0.1 in progress**. The complete read-only path `Codex -> official Blender MCP -> live Blender` is verified. Codex successfully called `blender.get_objects_summary` and read the default live scene (`Camera`, `Cube`, `Light`) without modifying it. The next step is the first write test: create `MCP_Test_Sphere`, then read the scene back and verify its position.

## Target architecture

```text
Codex
  |
  | MCP / stdio
  v
Official Blender Lab MCP server
  |
  | local TCP (127.0.0.1:9876)
  v
Official Blender Lab MCP add-on
  |
  v
Blender 5.2
  |
  v
bpy
```

The POC deliberately does **not** include STEP/CAD import, Creo integration, rendering workflows, custom MCP servers, a web UI, Docker, or a custom LLM orchestration layer.

## 1. Verified environment

Primary environment:

- Windows 11
- Blender 5.2
- official Blender Lab MCP add-on 1.0.0
- Codex CLI 0.152.0
- `uvx 0.11.8`
- Git
- PowerShell

Useful checks:

```powershell
git --version
uv --version
uvx --version
python --version
codex --version
Get-Command uvx
Get-Command codex
```

Verified on the POC host:

```text
codex-cli 0.152.0
uvx 0.11.8 (0e961dd9a 2026-04-27 x86_64-pc-windows-msvc)
```

If `codex` is not recognized, install the current official Windows Codex CLI, then fully restart PowerShell before retesting.

## 2. Blender side

Use the **official Blender Lab MCP** add-on, not the older community `MCPBlender/blender-mcp` project.

In Blender Preferences, verify:

```text
MCP
Maintainer: Blender Lab
Version: 1.0.0
Host: localhost
Port: 9876
Auto Start: enabled
```

Keep the endpoint local only.

Connectivity check:

```powershell
Test-NetConnection 127.0.0.1 -Port 9876
Get-NetTCPConnection -LocalPort 9876 -State Listen -ErrorAction SilentlyContinue
```

Verified result:

```text
RemoteAddress    : 127.0.0.1
RemotePort       : 9876
TcpTestSucceeded : True
```

A warning for IPv6 `::1` can appear when testing `localhost`; the successful IPv4 result is the relevant check. The Codex-side configuration therefore uses explicit `127.0.0.1`.

## 3. Codex MCP configuration

The project-scoped configuration is in `.codex/config.toml`.

The official Blender Lab MCP server is loaded directly from:

```text
git+https://projects.blender.org/lab/blender_mcp.git@v1.0.0#subdirectory=mcp
```

### Important compatibility pin

Blender MCP 1.0.0 imports the MCP Python SDK v1 API:

```python
from mcp.server.fastmcp import FastMCP
```

Without an explicit pin, current dependency resolution can install MCP Python SDK 2.x, where that API no longer exists. The observed failure was:

```text
ModuleNotFoundError: No module named 'mcp.server.fastmcp'
```

For reproducibility this POC therefore runs the official Blender MCP server with:

```text
mcp==1.27.2
```

The effective Codex server definition is equivalent to:

```powershell
uvx --with "mcp==1.27.2" `
  --from "git+https://projects.blender.org/lab/blender_mcp.git@v1.0.0#subdirectory=mcp" `
  blender-mcp
```

with:

```text
BLENDER_MCP_HOST=127.0.0.1
BLENDER_MCP_PORT=9876
```

### Direct stdio diagnostic

To isolate the Blender MCP server from Codex:

```powershell
$env:BLENDER_MCP_HOST="127.0.0.1"
$env:BLENDER_MCP_PORT="9876"
uvx --with "mcp==1.27.2" --from "git+https://projects.blender.org/lab/blender_mcp.git@v1.0.0#subdirectory=mcp" blender-mcp
```

A healthy stdio MCP server waits for MCP input. If it is manually stopped with `Ctrl+C`, an `asyncio.exceptions.CancelledError` traceback may appear during shutdown; that does not reproduce the earlier SDK import failure.

### Codex discovery

Verify project configuration:

```powershell
codex mcp list
```

Verified on the POC host:

```text
Name     Command  ...  Status   Auth
blender  uvx      ...  enabled  Unsupported
```

`Auth: Unsupported` is not a failure for this local stdio MCP server; there is no OAuth flow required here. The important result is that `blender` is present and `enabled` with the expected command, arguments, and environment variables.

Inside Codex, `/mcp` should show the `blender` server and its available tools once initialization succeeds.

## 4. First end-to-end smoke test

Start Blender and keep it open. A normal new scene should contain approximately:

```text
Camera
Cube
Light
```

Start Codex from this repository:

```powershell
cd C:\git\AI-MPC-Blender-home
codex
```

### Test A - read only — PASS

Prompt Codex:

```text
Using the Blender MCP tools, inspect the currently open Blender scene and list all objects. Do not modify anything.
```

Verified result: Codex called `blender.get_objects_summary({})` through MCP and received `status: ok` from the live Blender scene. It reported:

```text
Camera — Camera
Cube — Mesh (active and selected)
Light — Light
```

No scene changes were made.

### Test B - create

```text
Using Blender MCP, create a UV sphere named MCP_Test_Sphere at location X=3, Y=0, Z=0.
```

PASS only if the sphere visibly appears in Blender.

### Test C - verify

```text
Inspect the Blender scene and verify that MCP_Test_Sphere exists at X=3, Y=0, Z=0.
```

PASS only if Codex reads the changed scene through MCP and reports the correct location.

### Test D - modify and verify

```text
Move MCP_Test_Sphere to X=5, Y=1, Z=0 and verify its final location.
```

PASS only if the object visibly moves in Blender **and** Codex subsequently reads back approximately `(5, 1, 0)`.

## 5. Restart reproducibility test

After Tests A-D pass:

1. Fully close Codex and Blender.
2. Start Blender 5.2 again.
3. Verify the MCP add-on listener is active on port 9876.
4. Start Codex in this repository.
5. Run `codex mcp list` or `/mcp`.
6. Repeat Tests A-D.

POC v0.1 is not complete until the restart test passes.

## 6. Troubleshooting

### `uvx` is not found

```powershell
Get-Command uvx -ErrorAction SilentlyContinue
where.exe uvx
uvx --version
```

Restart the terminal after installation.

### `codex` is not found

```powershell
Get-Command codex -ErrorAction SilentlyContinue
where.exe codex
codex --version
```

Restart PowerShell after installation or PATH changes.

### Blender MCP import fails with `mcp.server.fastmcp`

Use the compatibility pin:

```powershell
uvx --with "mcp==1.27.2" --from "git+https://projects.blender.org/lab/blender_mcp.git@v1.0.0#subdirectory=mcp" blender-mcp
```

Do not remove the pin until the official Blender MCP server itself migrates to MCP SDK 2.x or publishes a compatible dependency constraint.

### Codex does not see Blender MCP

```powershell
codex mcp list
```

Ensure this repository is the current directory and that Codex trusts/loads the project `.codex/config.toml`. Fully restart Codex after config changes.

### Blender is not reachable

```powershell
Test-NetConnection 127.0.0.1 -Port 9876
Get-NetTCPConnection -LocalPort 9876 -ErrorAction SilentlyContinue
```

Diagnose the Blender add-on before changing the Codex configuration.

### Port 9876 is occupied

```powershell
Get-NetTCPConnection -LocalPort 9876 -ErrorAction SilentlyContinue |
    Select-Object LocalAddress,LocalPort,State,OwningProcess
```

Identify the owning process before changing or terminating anything.

## 7. Testing boundaries

There are three different test layers:

- **Unit tests**: only for Python code owned by this repository. There is currently no repository Python code, so no artificial unit-test scaffold is added.
- **MCP integration test**: verifies Codex loads the configured official MCP server and discovers its tools.
- **True end-to-end test**: requires Blender GUI, the official Blender Lab add-on, Codex MCP client, and visible/read-back scene changes. This is not a unit test.

## 8. POC v0.1 definition of done

- [x] Repository can be cloned.
- [x] Required environment is documented.
- [x] Blender 5.2 has the official MCP add-on active.
- [x] Blender MCP add-on listener is reachable locally on IPv4 port `9876`.
- [x] Codex CLI is installed and available in PowerShell (`0.152.0`).
- [x] `uvx` is installed and available in PowerShell (`0.11.8`).
- [x] Codex loads the project MCP definition and reports `blender` as enabled.
- [x] The Blender MCP SDK v1/v2 compatibility failure is diagnosed and pinned reproducibly (`mcp==1.27.2`).
- [x] Codex initializes the Blender MCP server in a live session.
- [x] Codex sees and calls Blender MCP tools.
- [x] Codex reads the live Blender scene.
- [ ] Codex creates `MCP_Test_Sphere`.
- [ ] Codex moves `MCP_Test_Sphere`.
- [ ] Codex reads back the changed state correctly.
- [ ] The full procedure passes again after restarting Blender and Codex.

## Current stage result

**Repository/bootstrap: PASS.**

**Blender add-on/listener: PASS.** Official Blender Lab MCP 1.0.0 is enabled in Blender 5.2 and `127.0.0.1:9876` is reachable.

**Codex CLI / uvx: PASS.** `codex-cli 0.152.0` and `uvx 0.11.8` are available.

**Blender MCP dependency compatibility: PASS after pin.** The MCP SDK 2.x incompatibility is fixed by `mcp==1.27.2`.

**Codex MCP configuration discovery: PASS.** `codex mcp list` reports `blender` as `enabled` with the expected configuration.

**Live Codex -> Blender scene read: PASS.** Codex called `blender.get_objects_summary` and correctly read `Camera`, `Cube`, and `Light` from the open Blender scene without modifying it.

**Next: Test B — create `MCP_Test_Sphere` at `(3, 0, 0)`.**
