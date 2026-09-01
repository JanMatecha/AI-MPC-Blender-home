# AI-MPC-Blender-home

POC pro ovládání živého Blenderu 5.2 pomocí OpenAI Codex přes **oficiální Blender Lab MCP**.

## Stav

**POC v0.1 — core path PASS.**

Prakticky ověřeno:

```text
Codex CLI
   |
   | MCP / stdio
   v
Official Blender Lab MCP server
   |
   | TCP 127.0.0.1:9876
   v
Official Blender Lab MCP add-on
   |
   v
Blender 5.2.1 LTS
   |
   v
bpy
```

Ověřené funkce:

- Codex načte projektovou Blender MCP konfiguraci.
- MCP server se inicializuje.
- Codex čte živou Blender scénu přes `blender.get_objects_summary`.
- Codex provádí write operace přes Blender MCP / `bpy`.
- Po změně lze scénu znovu přečíst a výsledek ověřit.
- Byl vytvořen a ověřen vícedílný model židle.
- Blender MCP listener funguje i po restartu Blenderu.
- Codex -> MCP -> Blender read test funguje i po restartu.

## Dokumentace

### [Kompletní HOWTO](docs/HOWTO.md)

Reprodukovatelný postup od instalace až po restart test. Obsahuje také:

- architekturu,
- Codex a `uvx` konfiguraci,
- Blender Lab MCP instalaci,
- port 9876,
- MCP SDK compatibility pin,
- auto-approval nástrojů,
- perzistenci Blender Lab repository,
- ověřený E2E postup.

### [Troubleshooting](docs/TROUBLESHOOTING.md)

Konkrétní chyby a jejich ověřené řešení, mimo jiné:

- `codex is not recognized`,
- IPv6 `::1` vs. `127.0.0.1`,
- `No module named 'mcp.server.fastmcp'`,
- `MCP startup interrupted`,
- `Auth: Unsupported`,
- opakované `Allow` prompty,
- MCP zmizí po restartu, přestože soubory existují,
- chybějící `lab_blender_org` v Blender Preferences.

### [Ověřené testovací prompty](docs/TEST_PROMPTS.md)

Obsahuje:

- read-only scene test,
- delete + verify,
- create/move/read-back test,
- prompt pro modelování židle,
- kompletní one-shot `clear -> model -> verify -> save` workflow.

## Ověřené prostředí

```text
Windows 11
Blender 5.2.1 LTS
Blender Lab MCP add-on 1.0.0
Codex CLI 0.152.0
uvx 0.11.8
```

## Důležitá kompatibilita

Blender MCP 1.0.0 používá MCP Python SDK v1 API `FastMCP`. Bez omezení verze se během POC nainstalovalo MCP SDK 2.x a server spadl na:

```text
ModuleNotFoundError: No module named 'mcp.server.fastmcp'
```

Proto projektová konfigurace explicitně používá:

```text
mcp==1.27.2
```

Viz `.codex/config.toml`.

## Projektová Codex konfigurace

Aktuální konfigurace je v:

```text
.codex/config.toml
```

Používá:

- oficiální Blender Lab MCP Git repository,
- `127.0.0.1:9876`,
- `mcp==1.27.2`,
- auto-approval pouze pro Blender MCP server.

Kontrola:

```powershell
cd C:\git\AI-MPC-Blender-home
codex mcp list
```

Očekávaný stav obsahuje:

```text
blender ... enabled
```

`Auth: Unsupported` je u tohoto lokálního stdio MCP serveru očekávané.

## Rychlý start

### 1. Spusť Blender

V `Edit -> Preferences -> Add-ons -> MCP` ověř:

```text
Maintainer: Blender Lab
Version: 1.0.0
Host: localhost
Port: 9876
Auto Start: enabled
Server is running
```

### 2. Ověř listener

```powershell
Test-NetConnection 127.0.0.1 -Port 9876
```

PASS:

```text
TcpTestSucceeded : True
```

### 3. Spusť Codex

```powershell
cd C:\git\AI-MPC-Blender-home
git pull
codex
```

### 4. Smoke test

```text
Using the Blender MCP tools, inspect the currently open Blender scene
and list all objects. Do not modify anything.
```

PASS znamená skutečný Blender MCP call, například:

```text
Called blender.get_objects_summary({})
status: ok
```

## Důležitá zkušenost s restartem Blenderu

Během POC se stalo, že MCP soubory fyzicky zůstaly v:

```text
%APPDATA%\Blender Foundation\Blender\5.2\extensions\lab_blender_org\mcp
```

ale po restartu MCP zmizel z Add-ons. Příčinou bylo, že Blender Lab repository nebyla trvale uložená v Preferences.

Kontrola:

```powershell
$blender = Get-ChildItem "C:\Program Files\Blender Foundation" -Filter blender.exe -Recurse |
  Select-Object -First 1 -ExpandProperty FullName

& $blender --command extension repo-list
```

Správný stav obsahuje:

```text
lab_blender_org:
    name: "lab.blender.org"
```

Po explicitním `Save Preferences` registrace repository přežila restart a MCP se znovu automaticky spustil.

Podrobnosti jsou v [Troubleshooting](docs/TROUBLESHOOTING.md).

## Bezpečnost tool approval

Projekt používá:

```toml
default_tools_approval_mode = "approve"
```

jen pro lokální MCP server `blender`, aby nebylo nutné potvrzovat každý `execute_blender_code` call. Blender MCP může spouštět Python přes `bpy`, proto není vhodné toto nastavení bez rozmyslu používat pro nedůvěryhodné nebo vzdálené MCP servery.

## POC v0.1 — ověřené milníky

- [x] Repo bootstrap.
- [x] Blender 5.2.1 + Blender Lab MCP 1.0.0.
- [x] Listener `127.0.0.1:9876`.
- [x] Codex CLI a `uvx`.
- [x] Projektová `.codex/config.toml`.
- [x] MCP SDK v1/v2 problém diagnostikován a reprodukovatelně opraven.
- [x] Codex vidí `blender` MCP server jako enabled.
- [x] Read-only live scene test.
- [x] Write path přes `execute_blender_code` / `bpy`.
- [x] Víceobjektový model židle + MCP read-back.
- [x] Blender Lab repository persistence.
- [x] MCP Auto Start po restartu.
- [x] Codex -> MCP -> Blender read test po restartu.

## Scope další etapy

POC v0.1 záměrně neřeší:

- STEP/CAD import,
- Creo integraci,
- vlastní MCP server,
- automatické multi-view renderování,
- analýzu materiálů/barev,
- generování reportů,
- širší orchestraci nebo web UI.

Tyto body mohou navázat až na nyní ověřenou stabilní MCP komunikační vrstvu.
