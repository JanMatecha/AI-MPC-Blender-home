# Project instructions

- This POC targets Blender 5.2 and the official Blender Lab MCP integration.
- Prefer Blender MCP tools over workarounds or custom bridge code.
- After every Blender scene change, read the live scene again and verify the requested state.
- Keep MCP local-only; do not expose the Blender listener remotely.
- Prefer `uv` / `uvx` for Python tooling.
- Do not create a custom MCP server unless the official Blender MCP is proven insufficient.
- Do not implement STEP/CAD import, Creo integration, material/color analysis, multi-view rendering, or report generation in POC v0.1.
- Treat GUI end-to-end checks separately from unit tests.
