# Ověřené prompty pro Codex + Blender MCP

Tyto prompty vycházejí z praktického POC. Záměrně obsahují explicitní požadavek na provedení změny a následné znovunačtení live Blender scény přes MCP.

## 1. Read-only smoke test

```text
Using the Blender MCP tools, inspect the currently open Blender scene
and list all objects. Do not modify anything.
```

Ověřený výsledek pro default scénu:

```text
Camera
Cube
Light
```

Codex má skutečně zavolat Blender MCP tool, například:

```text
blender.get_objects_summary({})
```

---

## 2. Smazání výchozí kostky s ověřením

```text
Using Blender MCP, delete the object named Cube.
Then inspect the scene again and verify that Cube no longer exists.
Do not modify Camera or Light.
```

---

## 3. Jednoduchý create test

```text
Using Blender MCP, create a UV sphere named MCP_Test_Sphere
at location X=3, Y=0, Z=0.
Then inspect the live Blender scene again and verify that
MCP_Test_Sphere exists at X=3, Y=0, Z=0.
```

---

## 4. Move + read-back test

```text
Move MCP_Test_Sphere to X=5, Y=1, Z=0 using Blender MCP.
Then inspect the live Blender scene again and verify its final location.
```

---

## 5. Židle — modelovací POC

```text
Using Blender MCP, create a simple wooden chair in the currently open Blender scene.

Requirements:

- Do not modify Camera or Light.
- Delete any existing object named Cube if it exists.
- Build the chair from simple mesh primitives.
- Use meters as Blender units.

Chair dimensions approximately:
- overall width: 0.45 m
- overall depth: 0.45 m
- seat height: 0.45 m
- seat thickness: 0.05 m
- backrest top height: 0.90 m

Create:
1. Seat:
   - size 0.45 x 0.45 x 0.05 m
   - centered around X=0, Y=0
   - top surface approximately at Z=0.45

2. Four legs:
   - square cross-section approximately 0.05 x 0.05 m
   - extend from the floor to the underside of the seat
   - positioned near the four corners of the seat

3. Two rear vertical back supports:
   - continue upward from the rear legs
   - reach approximately Z=0.90 m

4. Backrest:
   - horizontal rectangular board between the rear supports
   - approximately 0.35 m wide
   - approximately 0.08 m high
   - approximately 0.04 m thick
   - centered around Z=0.78 m

Name the objects clearly, for example:
Chair_Seat
Chair_Leg_FL
Chair_Leg_FR
Chair_Leg_RL
Chair_Leg_RR
Chair_BackSupport_L
Chair_BackSupport_R
Chair_Backrest

Place the complete chair around the world origin.

After creating the chair:
- inspect the live Blender scene again using Blender MCP,
- list all Chair_* objects,
- verify their locations and approximate dimensions,
- report whether the chair was created successfully.

Do not only provide Python code or instructions. Actually execute the required changes in the currently open Blender scene through Blender MCP.
```

Ověřeno v POC:

- 8 `Chair_*` mesh objektů,
- seat ~ `0.45 x 0.45 x 0.05 m`,
- legs ~ `0.05 x 0.05 x 0.40 m`,
- rear supports do ~ `Z=0.90 m`,
- backrest ~ `0.35 x 0.04 x 0.08 m`, center ~ `Z=0.78 m`,
- následný MCP read-back proběhl úspěšně.

---

## 6. Kompletní one-shot: vyčistit scénu -> židle -> ověřit -> uložit

```text
Using Blender MCP, completely reset the current Blender scene, create a simple wooden chair, verify it, and save the Blender file.

Requirements:

1. Clear the scene
- Delete ALL existing objects in the current Blender scene.
- This includes Camera, Light, Cube, previous test objects, and any Chair_* objects.
- After deletion, inspect the live scene again and verify that there are no objects left.

2. Create a simple wooden chair
Use meters as Blender units.

Approximate overall dimensions:
- width: 0.45 m
- depth: 0.45 m
- seat height: 0.45 m
- total height: 0.90 m

Create these mesh objects:

Seat:
- name: Chair_Seat
- dimensions: 0.45 x 0.45 x 0.05 m
- centered at X=0, Y=0
- top surface at approximately Z=0.45 m

Four legs:
- Chair_Leg_FL
- Chair_Leg_FR
- Chair_Leg_RL
- Chair_Leg_RR
- square cross-section approximately 0.05 x 0.05 m
- extend from Z=0 to the underside of the seat
- place them near the four seat corners

Rear back supports:
- Chair_BackSupport_L
- Chair_BackSupport_R
- continue vertically upward from the rear leg positions
- top at approximately Z=0.90 m

Backrest:
- name: Chair_Backrest
- dimensions approximately 0.35 x 0.04 x 0.08 m
- centered horizontally between the rear supports
- centered around Z=0.78 m

3. Appearance
- Create one simple wood-colored material named Chair_Wood.
- Assign it to all chair mesh objects.

4. Verify the result
After modeling:
- inspect the live Blender scene again through Blender MCP,
- verify that exactly these 8 Chair_* objects exist,
- verify their approximate dimensions and positions,
- verify there are no unrelated scene objects,
- report any mismatch and fix it before continuing.

5. Save the result
Save the current Blender file as:

C:\git\AI-MPC-Blender-home\chair.blend

Use Blender MCP / Blender Python to perform the save.

After saving:
- verify the current Blender file path is exactly:
  C:\git\AI-MPC-Blender-home\chair.blend
- report that the chair was created, verified, and saved successfully.

Important:
- Do not merely provide Python code or instructions.
- Actually execute all changes in the currently open Blender scene through Blender MCP.
- Perform verification after destructive operations and after modeling.
- Do not finish until the .blend file is saved successfully.
```

---

## 7. Doporučený vzor pro další prompty

Pro spolehlivější práci používej strukturu:

```text
1. Inspect current state through Blender MCP.
2. Perform the requested change through Blender MCP.
3. Inspect the live scene again.
4. Verify names, transforms, dimensions and counts.
5. If verification fails, fix the scene and verify again.
6. Only then report success.
```

Pro úlohy, kde má vzniknout soubor, přidej:

```text
Save the result to the exact requested path and verify Blender's current file path after saving.
```

To snižuje riziko, že model pouze vygeneruje Python kód nebo deklaruje úspěch bez kontroly skutečné live scény.
