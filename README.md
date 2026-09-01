# AI-MPC-Blender-home

Minimal proof of concept for controlling a live Blender 5.2 session from Codex through the official Blender Lab MCP integration.

> Status: **POC v0.1 core path verified, including restart persistence.** Codex can read the live Blender scene and execute Blender Python through the official Blender MCP. A multi-object chair was created and read back successfully. After restarting Blender, the MCP add-on remained registered, Auto Start restored the listener on `127.0.0.1:9876`, and Codex again read the live scene through MCP. The only remaining formal acceptance checks are the exact `MCP_Test_Sphere` create/move/read-back steps from the original DoD.

## Architecture

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

POC v0.1 deliberately excludes STEP/CAD import, Creo integration, rendering workflows, custom MCP servers, Docker, web UI, and custom LLM orchestration.

## Verified environment

- Windows 11
- Blender 5.2.1 LTS
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
```

## Blender side

In Blender Preferences verify:

```text
MCP
Maintainer: Blender Lab
Version: 1.0.0
Host: localhost
Port: 9876
Auto Start: enabled
```

Keep the listener local only.

Connectivity check:

```powershell
Test-NetConnection 127.0.0.1 -Port 9876
Get-NetTCPConnection -LocalPort 9876 -State Listen -ErrorAction SilentlyContinue
```

Verified on the POC host, including after Blender restart:

```text
RemoteAddress    : 127.0.0.1
RemotePort       : 9876
TcpTestSucceeded : True
```

### Blender Lab repository persistence

The MCP extension is installed from the Blender Lab extension repository. During restart testing, the extension files remained on disk but the `lab_blender_org` repository was initially missing from Blender preferences, so MCP did not appear in Add-ons after restart.

The repository registration was restored and saved in Blender Preferences. Verified CLI state:

```text
lab_blender_org:
    name: "lab.blender.org"
    directory: "...\\extensions\\lab_blender_org"
    url: "https://lab.blender.org/"
```

After saving Preferences and restarting Blender, the MCP add-on remained visible and enabled, and Auto Start restored the server listener.

## Codex MCP configuration

Project configuration is stored in `.codex/config.toml`.

The official Blender Lab MCP server is loaded from:

```text
git+https://projects.blender.org/lab/blender_mcp.git@v1.0.0#subdirectory=mcp
```

### MCP Python SDK compatibility pin

Blender MCP 1.0.0 uses the MCP Python SDK v1 `FastMCP` API. Without a pin, current dependency resolution installed MCP SDK 2.x and produced:

```text
ModuleNotFoundError: No module named 'mcp.server.fastmcp'
```

The working POC configuration therefore pins:

```text
mcp==1.27.2
```

Equivalent command:

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

### Tool approvals

For this isolated local POC, Blender MCP tools are auto-approved only for the `blender` MCP server:

```toml
default_tools_approval_mode = "approve"
```

This avoids repeated prompts for `execute_blender_code`. Do not generalize this to untrusted or remote MCP servers.

## MCP discovery

```powershell
codex mcp list
```

Verified result contains:

```text
blender ... enabled
```

`Auth: Unsupported` is expected for this local stdio MCP server and is not an error.

## Verified end-to-end tests

### Test A — live scene read — PASS

Prompt:

```text
Using the Blender MCP tools, inspect the currently open Blender scene
and list all objects. Do not modify anything.
```

Codex called:

```text
blender.get_objects_summary({})
```

and correctly read:

```text
Camera
Cube
Light
```

No scene changes were made.

### Additional write-path validation — chair — PASS

Codex was asked to create a simple chair from multiple mesh primitives and then re-read the live scene.

Verified result:

- eight `Chair_*` mesh objects created
- seat approximately `0.45 x 0.45 x 0.05 m`
- four legs approximately `0.05 x 0.05 x 0.40 m`
- rear supports reach approximately `Z = 0.90 m`
- backrest approximately `0.35 x 0.04 x 0.08 m`, centered around `Z = 0.78 m`
- Camera and Light preserved
- live scene re-read after creation

This validates the write path:

```text
Codex -> Blender MCP -> execute_blender_code -> bpy -> live Blender scene -> MCP read-back
```

### Restart persistence and read-back — PASS

After restarting Blender:

- MCP remained visible and enabled in Add-ons
- Blender Lab repository remained registered
- Auto Start restored the MCP listener
- `Test-NetConnection 127.0.0.1 -Port 9876` returned `TcpTestSucceeded : True`
- a fresh Codex session again called `blender.get_objects_summary({})`
- Codex received `status: ok` and correctly read `Camera`, `Cube`, and `Light`

This verifies restart persistence for the complete read-only path:

```text
Blender restart -> MCP Auto Start -> Codex -> MCP -> live Blender read
```

## Required v0.1 acceptance sequence

The exact original sphere acceptance sequence remains optional/formal cleanup; the core read/write path is already verified with the chair test and restart read-back.

### Test B — create sphere

```text
Using Blender MCP, create a UV sphere named MCP_Test_Sphere
at location X=3, Y=0, Z=0.
```

### Test C — verify sphere

```text
Inspect the Blender scene and verify that MCP_Test_Sphere exists
at X=3, Y=0, Z=0.
```

### Test D — move and verify

```text
Move MCP_Test_Sphere to X=5, Y=1, Z=0 and verify its final location.
```

PASS requires both visible Blender changes and MCP read-back of the final state.

## Troubleshooting

### Blender listener

```powershell
Test-NetConnection 127.0.0.1 -Port 9876
Get-NetTCPConnection -LocalPort 9876 -ErrorAction SilentlyContinue
```

### Blender Lab repository missing after restart

Check:

```powershell
& $blender --command extension repo-list
```

The output must include `lab_blender_org`. If MCP files exist under `...\\extensions\\lab_blender_org\\mcp` but the repository is missing, restore the Blender Lab repository and explicitly save Blender Preferences before restarting.

### Codex / uvx

```powershell
codex --version
uvx --version
codex mcp list
```

### MCP SDK v2 incompatibility

If you see:

```text
No module named 'mcp.server.fastmcp'
```

ensure the Blender server runs with:

```text
mcp==1.27.2
```

### Port ownership

```powershell
Get-NetTCPConnection -LocalPort 9876 -ErrorAction SilentlyContinue |
    Select-Object LocalAddress,LocalPort,State,OwningProcess
```

Identify the process before terminating or changing anything.

## Testing boundaries

- **Unit tests**: only for repository-owned Python code. None is needed yet.
- **MCP integration test**: Codex loads the MCP server and sees/calls its tools.
- **True E2E test**: live Blender GUI + official add-on + Codex + visible scene change + MCP read-back.

## POC v0.1 definition of done

- [x] Repository can be cloned.
- [x] Required environment documented.
- [x] Blender 5.2 has the official MCP add-on active.
- [x] Blender listener reachable on `127.0.0.1:9876`.
- [x] Codex CLI available (`0.152.0`).
- [x] `uvx` available (`0.11.8`).
- [x] Codex loads Blender MCP configuration.
- [x] MCP SDK v1/v2 compatibility problem diagnosed and pinned.
- [x] Codex initializes and calls Blender MCP tools.
- [x] Codex reads the live Blender scene.
- [x] Codex performs verified write operations in Blender (chair validation).
- [x] Blender Lab repository persists after restart.
- [x] Blender MCP add-on persists after restart.
- [x] Blender MCP Auto Start restores the listener after restart.
- [x] Codex reads the live Blender scene successfully after restart.
- [ ] Optional formal check: create `MCP_Test_Sphere` at `(3, 0, 0)`.
- [ ] Optional formal check: verify and move it to `(5, 1, 0)` with MCP read-back.
