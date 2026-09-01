# Troubleshooting: Codex + Blender Lab MCP

Tento dokument shrnuje problémy, které se během POC skutečně objevily, jejich symptomy, příčiny a ověřené opravy.

## 1. `codex` is not recognized

### Symptom

```text
The term 'codex' is not recognized...
```

### Příčina

Codex CLI není nainstalovaný, nebo nová PATH ještě není načtená v aktuálním PowerShellu.

### Ověření

```powershell
codex --version
Get-Command codex
where.exe codex
```

### Oprava

Po instalaci Codex CLI úplně zavři PowerShell a otevři nový terminál.

Ověřený stav:

```text
codex-cli 0.152.0
```

---

## 2. `uvx` není dostupný

```powershell
uvx --version
Get-Command uvx
where.exe uvx
```

Po instalaci/reinstalaci `uv` restartuj terminál a Codex session.

Ověřený stav:

```text
uvx 0.11.8
```

---

## 3. Blender port 9876 neodpovídá

### Ověření

```powershell
Test-NetConnection 127.0.0.1 -Port 9876
```

PASS:

```text
TcpTestSucceeded : True
```

Pokud je `False`:

1. Blender musí být otevřený.
2. `Preferences -> Add-ons -> MCP` musí být enabled.
3. `Auto Start` musí být enabled, nebo server ručně spuštěný.
4. V MCP panelu hledej `Server is running`.

Detail:

```powershell
Get-NetTCPConnection -LocalPort 9876 -ErrorAction SilentlyContinue |
    Select-Object LocalAddress,LocalPort,State,OwningProcess
```

Neukončuj cizí PID naslepo.

---

## 4. Warning pro `::1:9876`, ale výsledkem je `True`

Při:

```powershell
Test-NetConnection localhost -Port 9876
```

se může objevit:

```text
WARNING: TCP connect to (::1 : 9876) failed
```

ale výsledný řádek je:

```text
RemoteAddress    : 127.0.0.1
TcpTestSucceeded : True
```

To znamená, že IPv6 pokus selhal, ale IPv4 funguje. Pro stabilitu používá `.codex/config.toml`:

```text
BLENDER_MCP_HOST=127.0.0.1
```

---

## 5. `No module named 'mcp.server.fastmcp'`

### Symptom

```text
ModuleNotFoundError: No module named 'mcp.server.fastmcp'.
This is mcp 2.x...
```

### Příčina

Blender MCP 1.0.0 používá MCP Python SDK v1 API, ale `uvx` bez constraintu nainstaluje MCP SDK 2.x.

### Oprava

Použij explicitní v1 pin:

```powershell
uvx --with "mcp==1.27.2" --from "git+https://projects.blender.org/lab/blender_mcp.git@v1.0.0#subdirectory=mcp" blender-mcp
```

Repo už tento pin obsahuje v `.codex/config.toml`.

---

## 6. `IncompleteFieldDefinitionWarning`

Při přímém startu Blender MCP serveru s MCP SDK v1 se může objevit Pydantic warning typu:

```text
IncompleteFieldDefinitionWarning: Field 'lifespan' has an incomplete definition...
```

Během POC tento warning nezabránil startu serveru. Rozhodující je, zda následně server čeká na stdio MCP input a nespadne na import chybu.

---

## 7. `asyncio.exceptions.CancelledError` po ručním testu

Pokud spustíš Blender MCP server ručně a ukončíš ho přes `Ctrl+C`, může shutdown skončit tracebackem s:

```text
asyncio.exceptions.CancelledError
```

Pokud server předtím normálně běžel a chyba vznikla až po ručním přerušení, není to stejný problém jako neúspěšný start serveru.

---

## 8. Codex píše `MCP startup interrupted`

Postupuj po vrstvách:

### A. Blender listener

```powershell
Test-NetConnection 127.0.0.1 -Port 9876
```

### B. uvx

```powershell
uvx --version
```

### C. MCP server mimo Codex

```powershell
$env:BLENDER_MCP_HOST="127.0.0.1"
$env:BLENDER_MCP_PORT="9876"
uvx --with "mcp==1.27.2" --from "git+https://projects.blender.org/lab/blender_mcp.git@v1.0.0#subdirectory=mcp" blender-mcp
```

### D. Codex discovery

```powershell
codex mcp list
```

Až když A-C fungují, řeš Codex integraci.

---

## 9. `codex mcp list`: `Auth: Unsupported`

Pro lokální stdio Blender MCP server je to očekávané. Tento server nepotřebuje OAuth.

Rozhodující je:

```text
blender ... enabled
```

---

## 10. Codex se pořád ptá `Allow`

Pokud `.codex/config.toml` obsahuje:

```toml
default_tools_approval_mode = "prompt"
```

Codex bude chtít ruční potvrzení nástrojů.

Pro izolovaný lokální POC bylo ověřeno:

```toml
default_tools_approval_mode = "approve"
```

Po změně restartuj Codex session.

Pozor: `execute_blender_code` může spouštět Python uvnitř Blenderu. Auto-approval používej pouze pro důvěryhodný lokální MCP server.

---

## 11. MCP po restartu zmizí z Blender Add-ons, ale soubory existují

### Symptom

`Preferences -> Add-ons` neukazuje MCP, ale:

```powershell
Test-Path "$env:APPDATA\Blender Foundation\Blender\5.2\extensions\lab_blender_org\mcp"
```

vrací:

```text
True
```

### Příčina zjištěná v POC

Blender Lab repository `lab_blender_org` nebyla uložená v Blender Preferences. Samotné soubory extension tedy nestačily.

### Diagnostika

```powershell
$blender = Get-ChildItem "C:\Program Files\Blender Foundation" `
  -Filter blender.exe -Recurse |
  Select-Object -First 1 -ExpandProperty FullName

& $blender --command extension repo-list
```

Chybový stav neobsahoval `lab_blender_org`.

### Oprava

1. Znovu přidej Blender Lab repository oficiálním instalačním postupem.
2. Ověř MCP v Add-ons.
3. V Preferences vlevo dole otevři menu.
4. Ověř `Auto-Save Preferences`.
5. Explicitně klikni `Save Preferences`.
6. Znovu spusť:

```powershell
& $blender --command extension repo-list
```

Správný stav:

```text
lab_blender_org:
    name: "lab.blender.org"
    directory: "...\extensions\lab_blender_org"
    url: "https://lab.blender.org/"
```

Potom MCP po restartu zůstal.

---

## 12. `extension list` hlásí chybějící `user_default` cestu

Během diagnostiky se objevilo:

```text
[WinError 3] ... extensions\user_default
```

To nesouviselo s Blender Lab MCP. Rozhodující byla přítomnost a persistence `lab_blender_org` a funkční MCP listener.

---

## 13. MCP je vidět, ale potřebuji ověřit repository

```powershell
& $blender --command extension repo-list
```

A pro extension seznam:

```powershell
& $blender --command extension list | Select-String -Pattern "MCP|mcp"
```

---

## 14. Po změně `.codex/config.toml` se nic nezměnilo

Ukonči aktuální Codex session a spusť novou:

```text
Ctrl+C
```

pak v PowerShellu:

```powershell
git pull
codex
```

Projektová MCP konfigurace se načítá při startu Codex session.

---

## 15. Rychlá diagnostická sekvence

```powershell
# 1. Nástroje
codex --version
uvx --version

# 2. Blender listener
Test-NetConnection 127.0.0.1 -Port 9876

# 3. Codex MCP config
cd C:\git\AI-MPC-Blender-home
codex mcp list

# 4. Blender repository persistence
$blender = Get-ChildItem "C:\Program Files\Blender Foundation" -Filter blender.exe -Recurse |
  Select-Object -First 1 -ExpandProperty FullName
& $blender --command extension repo-list
```

Pokud všechny čtyři vrstvy projdou, spusť `codex` a proveď read-only scene test.
