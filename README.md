# AI-MPC-Blender-home

Minimal proof of concept for controlling a live Blender 5.2 session from Codex through the official Blender Lab MCP integration.

> Status: **POC v0.1 bootstrap**. Repository configuration is prepared, but the real end-to-end `Codex -> MCP -> Blender` test must still be executed on the Windows machine where Blender and Codex are running.

## Target architecture

```text
Codex
  |
  | MCP / stdio
  v
Official Blender Lab MCP server
  |
  | local TCP (localhost:9876)
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

## 1. Prerequisites

Primary environment:

- Windows 11
- Blender 5.2 LTS
- Codex local client (CLI and/or IDE extension)
- Git
- `uv` / `uvx`
- PowerShell

Check the local environment from PowerShell:

```powershell
git --version
uv --version
uvx --version
python --version
codex --version
Get-Command uvx
Get-Command codex
Get-Command blender -ErrorAction SilentlyContinue
```

If Blender is not on `PATH`, locate it for diagnostics:

```powershell
Get-ChildItem "C:\Program Files\Blender Foundation" -Filter blender.exe -Recurse -ErrorAction SilentlyContinue |
    Select-Object -First 5 FullName
```

## 2. Install and enable the official Blender Lab MCP add-on

Use the **official Blender Lab MCP** page:

https://www.blender.org/lab/mcp-server/

Blender 5.1 or newer is required.

Install the official Blender Lab MCP add-on using the procedure on that page. With the drag-and-drop method Blender may ask you to perform the operation twice: first to add the Blender Lab repository and then to install the add-on.

In Blender, verify that the MCP add-on is enabled and its local server is running. The expected local endpoint is:

```text
localhost:9876
```

Keep this endpoint local only.

PowerShell connectivity check:

```powershell
Test-NetConnection 127.0.0.1 -Port 9876
Get-NetTCPConnection -LocalPort 9876 -State Listen -ErrorAction SilentlyContinue
```

Expected result: TCP port `9876` is listening while Blender with the MCP add-on is running.

## 3. Codex MCP configuration

Codex supports project-scoped MCP configuration in `.codex/config.toml` for trusted projects. This repository contains that configuration.

The configured server is the **official Blender Lab MCP server**, installed directly from the Blender project repository with `uvx`:

```text
git+https://projects.blender.org/lab/blender_mcp.git@v1.0.0#subdirectory=mcp
```

The explicit `@v1.0.0` pin is intentional for POC reproducibility. If the installed Blender Lab add-on requires a newer server version, update the pin only after checking the matching official release/documentation and record the working version here.

After cloning the repository, trust/open it in the local Codex client and restart the Codex client/IDE extension so the project-scoped MCP configuration is reloaded.

Verify configuration:

```powershell
codex mcp list
codex mcp --help
```

Inside the Codex TUI, `/mcp` should show the `blender` server and its tools.

If project-scoped configuration is not being loaded, the equivalent user-level bootstrap command is:

```powershell
codex mcp add blender `
  --env BLENDER_MCP_HOST=localhost `
  --env BLENDER_MCP_PORT=9876 `
  -- uvx --from "git+https://projects.blender.org/lab/blender_mcp.git@v1.0.0#subdirectory=mcp" blender-mcp
```

Do not add both user-level and project-level `blender` definitions unless you intentionally want to override one of them.

## 4. First end-to-end smoke test

Start from a normal new Blender scene with approximately:

```text
Camera
Cube
Light
```

### Test A - read only

Prompt Codex:

```text
Using the Blender MCP tools, inspect the currently open Blender scene and list all objects. Do not modify anything.
```

PASS only if Codex obtains the object list through Blender MCP from the currently open scene.

### Test B - create

Prompt Codex:

```text
Using Blender MCP, create a UV sphere named MCP_Test_Sphere at location X=3, Y=0, Z=0.
```

PASS only if `MCP_Test_Sphere` is visibly present in the open Blender scene.

### Test C - verify

Prompt Codex:

```text
Inspect the Blender scene and verify that MCP_Test_Sphere exists at X=3, Y=0, Z=0.
```

PASS only if Codex reads the changed live scene through MCP and reports the correct location.

### Test D - modify and verify

Prompt Codex:

```text
Move MCP_Test_Sphere to X=5, Y=1, Z=0 and verify its final location.
```

PASS only if the object visibly moves in Blender **and** Codex subsequently reads back approximately `(5, 1, 0)` from the live scene.

## 5. Restart reproducibility test

After Tests A-D pass:

1. Save or discard the Blender test scene as appropriate.
2. Fully close Codex and Blender.
3. Start Blender 5.2 again.
4. Verify the official MCP add-on is enabled/running.
5. Start Codex in this repository.
6. Run `codex mcp list` or `/mcp`.
7. Repeat Tests A-D.

POC v0.1 is not complete until this restart test passes.

## 6. Troubleshooting

### `uvx` is not found

```powershell
Get-Command uvx -ErrorAction SilentlyContinue
where.exe uvx
uv --version
uvx --version
```

If `uv` was just installed, fully restart the terminal, VS Code/Codex client, and retry. Prefer the official `uv` installer rather than installing `uv` with `pip`.

### Blender MCP server cannot start in Codex

Check:

```powershell
codex mcp list
codex mcp --help
uvx --version
git --version
```

The first server start may need network access because `uvx` has to obtain the official MCP package from the Blender Git repository. Subsequent starts should use the uv cache.

If startup exceeds the default Codex timeout, this repo sets `startup_timeout_sec = 120`.

### Codex does not see the MCP server or tools

1. Ensure the repository is trusted so project `.codex/config.toml` is loaded.
2. Fully restart the Codex CLI/IDE extension after configuration changes.
3. Run:

```powershell
codex mcp list
```

4. In the Codex TUI use:

```text
/mcp
```

### Blender is not reachable

```powershell
Test-NetConnection 127.0.0.1 -Port 9876
Get-NetTCPConnection -LocalPort 9876 -ErrorAction SilentlyContinue
```

If the test fails, diagnose the Blender add-on before changing Codex configuration.

### Port 9876 is occupied

```powershell
Get-NetTCPConnection -LocalPort 9876 -ErrorAction SilentlyContinue |
    Select-Object LocalAddress,LocalPort,State,OwningProcess

Get-Process -Id <PID>
```

Do not kill an unknown process blindly. Identify it first. Keep the MCP listener local.

### MCP process exists but Blender does not answer

Check in this order:

1. Blender is open.
2. The official Blender Lab MCP add-on is enabled.
3. The add-on reports its server as running.
4. Port `9876` is listening locally.
5. Codex MCP server is enabled.
6. Retry a read-only scene inspection before any write operation.

### Restart breaks the connection

The Codex-side stdio MCP server and the Blender-side local TCP listener have independent lifecycles. After restarting Blender, verify the Blender add-on listener first; after restarting Codex, verify `codex mcp list` / `/mcp` again.

## 7. Testing boundaries

There are three different test layers:

- **Unit tests**: only for Python code owned by this repository. There is currently no repository Python code, so no artificial unit-test scaffold is added.
- **MCP integration test**: verifies that Codex starts the configured official MCP server and discovers its tools.
- **True end-to-end test**: requires the Blender GUI, the official Blender Lab add-on, the Codex MCP client, and visible/read-back scene changes. This is not a unit test.

## 8. POC v0.1 definition of done

- [x] Repository can be cloned.
- [x] Required environment is documented.
- [ ] Blender 5.2 has the official MCP add-on active.
- [ ] Codex starts/uses the official Blender MCP server.
- [ ] MCP server initializes successfully.
- [ ] Codex sees Blender MCP tools.
- [ ] Codex reads the live Blender scene.
- [ ] Codex creates `MCP_Test_Sphere`.
- [ ] Codex moves `MCP_Test_Sphere`.
- [ ] Codex reads back the changed state correctly.
- [ ] The full procedure passes again after restarting Blender and Codex.

## Current stage result

**Repository/bootstrap stage: PASS** for repository setup and documented configuration.

**Live MCP/Blender stage: NOT YET EXECUTED**. It must be run on the Windows host with the user's live Blender and Codex processes; GitHub access alone cannot inspect those local processes.
