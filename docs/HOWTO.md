# HOWTO: Codex -> Blender 5.2 přes oficiální Blender Lab MCP

Tento dokument popisuje reprodukovatelný postup, který byl prakticky ověřen na Windows 11 s Blenderem 5.2.1 LTS, Codex CLI 0.152.0 a oficiálním Blender Lab MCP add-onem 1.0.0.

## 1. Cíl a architektura

```text
Codex CLI
   |
   | MCP / stdio
   v
Official Blender Lab MCP server
   |
   | local TCP 127.0.0.1:9876
   v
Official Blender Lab MCP add-on
   |
   v
Blender 5.2.x
   |
   v
bpy
```

POC ověřuje, že Codex dokáže:

- přečíst živou Blender scénu,
- měnit scénu přes Blender Python API,
- výsledek znovu přečíst a ověřit,
- fungovat znovu po restartu Blenderu a Codexu.

## 2. Ověřené prostředí

- Windows 11
- Blender 5.2.1 LTS
- official Blender Lab MCP add-on 1.0.0
- Codex CLI 0.152.0
- uv / uvx, ověřeno s `uvx 0.11.8`
- Git
- PowerShell

Ověření:

```powershell
git --version
uv --version
uvx --version
codex --version
Get-Command uvx
Get-Command codex
```

## 3. Instalace Codex CLI

Pokud PowerShell hlásí, že `codex` neexistuje, nainstaluj Codex CLI a potom otevři nové PowerShell okno. Po instalaci se změna PATH nemusí projevit ve starém terminálu.

Ověř:

```powershell
codex --version
Get-Command codex
```

Na ověřeném stroji:

```text
codex-cli 0.152.0
```

## 4. Instalace oficiálního Blender Lab MCP

Použij oficiální Blender Lab MCP, ne starší komunitní Blender MCP projekt.

V Blenderu má být v:

```text
Edit -> Preferences -> Add-ons -> MCP
```

ověřeno:

```text
Maintainer: Blender Lab
Version: 1.0.0
Host: localhost
Port: 9876
Auto Start: enabled
Server is running
```

Typická instalační cesta na Windows:

```text
%APPDATA%\Blender Foundation\Blender\5.2\extensions\lab_blender_org\mcp
```

Ověření souborů:

```powershell
Test-Path "$env:APPDATA\Blender Foundation\Blender\5.2\extensions\lab_blender_org\mcp"
```

## 5. Ověření Blender listeneru

Nech Blender otevřený a spusť:

```powershell
Test-NetConnection 127.0.0.1 -Port 9876
```

PASS:

```text
TcpTestSucceeded : True
```

Poznámka: při testu `localhost` může Windows nejdřív zkusit IPv6 `::1` a vypsat warning, ale následně uspět přes `127.0.0.1`. Proto Codex konfigurace používá explicitně `127.0.0.1`.

Detailnější kontrola:

```powershell
Get-NetTCPConnection -LocalPort 9876 -State Listen -ErrorAction SilentlyContinue
```

## 6. Codex MCP konfigurace

Repo obsahuje `.codex/config.toml`.

Ověřená konfigurace:

```toml
[mcp_servers.blender]
command = "uvx"
args = [
  "--with",
  "mcp==1.27.2",
  "--from",
  "git+https://projects.blender.org/lab/blender_mcp.git@v1.0.0#subdirectory=mcp",
  "blender-mcp",
]
env = { BLENDER_MCP_HOST = "127.0.0.1", BLENDER_MCP_PORT = "9876" }
startup_timeout_sec = 120
tool_timeout_sec = 60
default_tools_approval_mode = "approve"
```

### Proč je nutný `mcp==1.27.2`

Blender MCP 1.0.0 používá MCP Python SDK v1 API:

```python
from mcp.server.fastmcp import FastMCP
```

Bez pinu stáhl `uvx` MCP Python SDK 2.x a server skončil chybou:

```text
ModuleNotFoundError: No module named 'mcp.server.fastmcp'
```

Funkční řešení pro tento POC je:

```text
mcp==1.27.2
```

Ruční diagnostický start serveru:

```powershell
$env:BLENDER_MCP_HOST="127.0.0.1"
$env:BLENDER_MCP_PORT="9876"
uvx --with "mcp==1.27.2" --from "git+https://projects.blender.org/lab/blender_mcp.git@v1.0.0#subdirectory=mcp" blender-mcp
```

Zdravý stdio MCP server čeká na vstup. Při ručním ukončení přes `Ctrl+C` se může objevit `asyncio.exceptions.CancelledError`; to samo o sobě není chyba startu.

## 7. Ověření Codex MCP discovery

V rootu repozitáře:

```powershell
codex mcp list
```

Musí obsahovat server:

```text
blender ... enabled
```

`Auth: Unsupported` je pro tento lokální stdio MCP server očekávané a neznamená chybu.

Pak spusť:

```powershell
codex
```

V Codex TUI lze použít také:

```text
/mcp
```

## 8. První E2E read-only test

Do Codexu:

```text
Using the Blender MCP tools, inspect the currently open Blender scene
and list all objects. Do not modify anything.
```

Ověřený PASS vypadal takto:

```text
Called blender.get_objects_summary({})
status: ok
```

pro default scénu:

```text
Camera
Cube
Light
```

Tím je potvrzená cesta:

```text
Codex -> Blender MCP -> live Blender
```

## 9. Write test

Byl ověřen vícekrokový modelovací test: Codex vytvořil židli z osmi mesh objektů, následně scénu znovu přečetl a ověřil rozměry.

Ověřená cesta:

```text
Codex
  -> Blender MCP
  -> execute_blender_code
  -> bpy
  -> live Blender scene
  -> MCP read-back
```

Důležité pravidlo pro prompty: po každé změně požaduj nové přečtení live scény a ověření výsledku.

## 10. Auto-approval Blender nástrojů

Při:

```toml
default_tools_approval_mode = "prompt"
```

se Codex ptal na `Allow` prakticky při každém Blender MCP tool callu.

Pro tento izolovaný lokální POC používáme:

```toml
default_tools_approval_mode = "approve"
```

Tím se automaticky schvalují Blender MCP tools pro server `blender`. Nedoporučuje se toto nastavení bez rozmyslu přenášet na nedůvěryhodné nebo vzdálené MCP servery, protože Blender MCP obsahuje `execute_blender_code` a může spouštět Python uvnitř Blenderu.

Po změně `.codex/config.toml` ukonči a znovu spusť Codex, protože konfigurace se načítá při startu session.

## 11. Persistence Blender Lab repository

Během testu nastal důležitý problém: po restartu Blenderu fyzicky zůstaly soubory MCP extension na disku, ale MCP zmizel z `Preferences -> Add-ons`.

Soubory stále existovaly:

```powershell
Test-Path "$env:APPDATA\Blender Foundation\Blender\5.2\extensions\lab_blender_org\mcp"
# True
```

Ale Blender neměl uloženou registraci repository `lab_blender_org`.

Zjisti cestu Blenderu:

```powershell
$blender = Get-ChildItem "C:\Program Files\Blender Foundation" `
  -Filter blender.exe -Recurse |
  Select-Object -First 1 -ExpandProperty FullName
```

Zkontroluj repositories:

```powershell
& $blender --command extension repo-list
```

Správný stav musí obsahovat:

```text
lab_blender_org:
    name: "lab.blender.org"
    directory: "...\extensions\lab_blender_org"
    url: "https://lab.blender.org/"
```

Pokud MCP soubory existují, ale repository chybí:

1. znovu přidej Blender Lab repository oficiálním instalačním postupem,
2. v Blender Preferences otevři menu vlevo dole,
3. ověř `Auto-Save Preferences`,
4. explicitně klikni `Save Preferences`,
5. znovu spusť `extension repo-list`.

Toto bylo rozhodující pro to, aby MCP zůstal po restartu.

Další užitečný příkaz:

```powershell
& $blender --command extension list
```

Pro filtrování:

```powershell
& $blender --command extension list | Select-String -Pattern "MCP|mcp"
```

## 12. Restart reproducibility test

Finálně byl ověřen tento postup:

1. zavřít Codex,
2. zavřít Blender,
3. znovu spustit Blender 5.2,
4. ověřit, že `MCP` zůstal v Add-ons,
5. ověřit `Auto Start`,
6. spustit:

```powershell
Test-NetConnection 127.0.0.1 -Port 9876
```

7. z rootu repo spustit:

```powershell
codex
```

8. zadat read-only scene test.

Po restartu Codex znovu úspěšně zavolal:

```text
blender.get_objects_summary({})
```

a přečetl `Camera`, `Cube`, `Light`.

Restart persistence a E2E read jsou tedy ověřené.

## 13. Doporučený pracovní postup

Pro běžnou práci:

```text
1. Spusť Blender.
2. Ověř, že MCP Auto Start běží.
3. Volitelně: Test-NetConnection 127.0.0.1 -Port 9876.
4. cd C:\git\AI-MPC-Blender-home
5. git pull
6. codex
7. Zadávej úlohy s explicitní podmínkou "execute + verify by reading the live scene again".
8. U důležitých výsledků ulož .blend soubor explicitně přes Blender MCP.
```

## 14. Co POC prokázal

Ověřeno:

- oficiální Blender Lab MCP funguje s Blenderem 5.2.1 LTS,
- Codex CLI může MCP server načíst projektově z `.codex/config.toml`,
- Codex čte živou Blender scénu,
- Codex provádí write operace přes `bpy`,
- Codex umí stav následně znovu přečíst a ověřit,
- spojení funguje znovu po restartu,
- Blender Lab repository musí být skutečně uložena v Preferences,
- pro Blender MCP 1.0.0 je v tomto POC nutný MCP SDK v1 pin.

## 15. Scope mimo v0.1

Záměrně zatím neřešeno:

- STEP/CAD import,
- Creo integrace,
- vlastní MCP server,
- automatické reporty,
- více pohledů/rendering pipeline,
- materiálová/barevná analýza,
- Docker/web orchestrace.
