# Project instructions

- This project targets Blender 5.2.x and the official Blender Lab MCP integration.
- Prefer Blender MCP tools over workarounds or custom bridge code.
- After every Blender scene change, read the live scene again and verify the requested state before reporting success.
- For destructive operations, verify the scene both before and after the change when practical.
- For tasks that create a `.blend` file, save to the exact requested path and verify Blender's current file path afterward.
- Keep MCP local-only; do not expose the Blender listener remotely.
- Prefer `uv` / `uvx` for Python tooling.
- Preserve the working MCP SDK compatibility pin in `.codex/config.toml` unless the official Blender MCP dependency model changes and a newer combination is verified.
- `default_tools_approval_mode = "approve"` is intentional only for the trusted local `blender` MCP server; do not generalize it to untrusted or remote MCP servers.
- Before changing the architecture, read `docs/HOWTO.md` and `docs/TROUBLESHOOTING.md` and preserve already verified behavior.
- Do not create a custom MCP server unless the official Blender MCP is proven insufficient for the next scope.
- STEP/CAD import, Creo integration, material/color analysis, multi-view rendering, report generation, and broader orchestration are post-v0.1 work and should be introduced incrementally.
- Treat GUI end-to-end checks separately from unit tests.
