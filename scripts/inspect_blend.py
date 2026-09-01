import argparse
import hashlib
import json
import math
import os
import sys
from collections import defaultdict

import bpy
from mathutils import Vector

EXPECTED_CHAIR = {
    "Chair_Seat": (0.45, 0.45, 0.05),
    "Chair_Leg_FL": (0.05, 0.05, 0.40),
    "Chair_Leg_FR": (0.05, 0.05, 0.40),
    "Chair_Leg_RL": (0.05, 0.05, 0.40),
    "Chair_Leg_RR": (0.05, 0.05, 0.40),
    "Chair_Backrest": (0.35, 0.04, 0.08),
}
EXPECTED_NAMES = {
    "Chair_Seat",
    "Chair_Leg_FL",
    "Chair_Leg_FR",
    "Chair_Leg_RL",
    "Chair_Leg_RR",
    "Chair_BackSupport_L",
    "Chair_BackSupport_R",
    "Chair_Backrest",
}


def _json_value(value):
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if hasattr(value, "to_list"):
        try:
            return value.to_list()
        except Exception:
            pass
    if isinstance(value, (list, tuple)):
        return [_json_value(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _json_value(v) for k, v in value.items()}
    return repr(value)


def _vec(v, digits=6):
    return [round(float(x), digits) for x in v]


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _mesh_topology(mesh):
    edge_face_count = defaultdict(int)
    used_vertices_by_edges = set()
    used_edges_by_faces = set()

    edge_key_to_index = {tuple(sorted(e.vertices[:])): e.index for e in mesh.edges}
    for edge in mesh.edges:
        used_vertices_by_edges.update(edge.vertices[:])

    zero_area_faces = 0
    for poly in mesh.polygons:
        if poly.area <= 1e-12:
            zero_area_faces += 1
        for key in poly.edge_keys:
            key = tuple(sorted(key))
            edge_face_count[key] += 1
            idx = edge_key_to_index.get(key)
            if idx is not None:
                used_edges_by_faces.add(idx)

    loose_vertices = sum(1 for v in mesh.vertices if v.index not in used_vertices_by_edges)
    loose_edges = sum(1 for e in mesh.edges if e.index not in used_edges_by_faces)
    boundary_edges = sum(1 for e in mesh.edges if edge_face_count[tuple(sorted(e.vertices[:]))] == 1)
    nonmanifold_edges = sum(1 for e in mesh.edges if edge_face_count[tuple(sorted(e.vertices[:]))] != 2)

    return {
        "vertices": len(mesh.vertices),
        "edges": len(mesh.edges),
        "polygons": len(mesh.polygons),
        "triangles": sum(max(0, len(p.vertices) - 2) for p in mesh.polygons),
        "loose_vertices": loose_vertices,
        "loose_edges": loose_edges,
        "boundary_edges": boundary_edges,
        "nonmanifold_edges": nonmanifold_edges,
        "zero_area_faces": zero_area_faces,
        "has_uv_layers": bool(mesh.uv_layers),
        "uv_layers": [uv.name for uv in mesh.uv_layers],
        "color_attributes": [attr.name for attr in mesh.color_attributes],
        "shape_keys": [kb.name for kb in mesh.shape_keys.key_blocks] if mesh.shape_keys else [],
    }


def _material_info(mat):
    info = {
        "name": mat.name,
        "users": mat.users,
        "use_nodes": bool(mat.use_nodes),
        "diffuse_color": _vec(mat.diffuse_color),
    }
    for attr in ("metallic", "roughness"):
        if hasattr(mat, attr):
            try:
                info[attr] = round(float(getattr(mat, attr)), 6)
            except Exception:
                pass
    if mat.use_nodes and mat.node_tree:
        info["nodes"] = [node.bl_idname for node in mat.node_tree.nodes]
    return info


def _object_info(obj):
    info = {
        "name": obj.name,
        "type": obj.type,
        "location": _vec(obj.location),
        "rotation_euler_rad": _vec(obj.rotation_euler),
        "rotation_euler_deg": _vec([math.degrees(x) for x in obj.rotation_euler]),
        "scale": _vec(obj.scale),
        "dimensions": _vec(obj.dimensions),
        "parent": obj.parent.name if obj.parent else None,
        "hide_viewport": bool(obj.hide_viewport),
        "hide_render": bool(obj.hide_render),
        "visible_get": bool(obj.visible_get()),
        "data_name": obj.data.name if obj.data else None,
        "library": obj.library.filepath if obj.library else None,
        "override_library": bool(obj.override_library),
        "modifiers": [
            {
                "name": mod.name,
                "type": mod.type,
                "show_viewport": bool(mod.show_viewport),
                "show_render": bool(mod.show_render),
            }
            for mod in obj.modifiers
        ],
        "constraints": [{"name": c.name, "type": c.type} for c in obj.constraints],
        "material_slots": [slot.material.name if slot.material else None for slot in obj.material_slots],
        "custom_properties": {
            k: _json_value(obj[k]) for k in obj.keys() if k != "_RNA_UI"
        },
        "animation_action": obj.animation_data.action.name
        if obj.animation_data and obj.animation_data.action
        else None,
        "has_drivers": bool(obj.animation_data and obj.animation_data.drivers),
    }

    try:
        corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        info["world_bbox_min"] = _vec([min(c[i] for c in corners) for i in range(3)])
        info["world_bbox_max"] = _vec([max(c[i] for c in corners) for i in range(3)])
    except Exception:
        info["world_bbox_min"] = None
        info["world_bbox_max"] = None

    if obj.type == "MESH" and obj.data:
        info["mesh"] = _mesh_topology(obj.data)

    return info


def _chair_validation(objects):
    by_name = {o["name"]: o for o in objects}
    names = set(by_name)
    missing = sorted(EXPECTED_NAMES - names)
    unrelated = sorted(names - EXPECTED_NAMES)
    chair_names = sorted(n for n in names if n.startswith("Chair_"))

    dimension_checks = []
    for name, expected in EXPECTED_CHAIR.items():
        obj = by_name.get(name)
        if not obj:
            dimension_checks.append({"name": name, "status": "missing", "expected": expected})
            continue
        actual = tuple(obj["dimensions"])
        ok = all(abs(a - e) <= 0.01 for a, e in zip(actual, expected))
        dimension_checks.append(
            {
                "name": name,
                "status": "pass" if ok else "mismatch",
                "expected": expected,
                "actual": actual,
            }
        )

    supports = []
    for name in ("Chair_BackSupport_L", "Chair_BackSupport_R"):
        obj = by_name.get(name)
        if obj:
            supports.append(
                {
                    "name": name,
                    "top_z": obj.get("world_bbox_max", [None, None, None])[2],
                    "status": "pass"
                    if obj.get("world_bbox_max") and abs(obj["world_bbox_max"][2] - 0.90) <= 0.01
                    else "mismatch",
                }
            )
        else:
            supports.append({"name": name, "status": "missing", "top_z": None})

    all_mesh = all(by_name[n]["type"] == "MESH" for n in EXPECTED_NAMES if n in by_name)
    all_wood = all(
        "Chair_Wood" in (by_name[n].get("material_slots") or [])
        for n in EXPECTED_NAMES
        if n in by_name
    )

    pass_basic = (
        not missing
        and not unrelated
        and len(chair_names) == 8
        and all_mesh
        and all_wood
        and all(c["status"] == "pass" for c in dimension_checks)
        and all(c["status"] == "pass" for c in supports)
    )

    return {
        "overall_status": "pass" if pass_basic else "review",
        "expected_object_count": 8,
        "actual_object_count": len(objects),
        "chair_object_count": len(chair_names),
        "missing_expected_objects": missing,
        "unrelated_objects": unrelated,
        "all_expected_objects_are_meshes": all_mesh,
        "all_expected_objects_use_Chair_Wood": all_wood,
        "dimension_checks": dimension_checks,
        "back_support_top_checks": supports,
    }


def build_report(filepath):
    objects = [_object_info(o) for o in bpy.data.objects]
    materials = [_material_info(m) for m in bpy.data.materials]

    images = []
    for img in bpy.data.images:
        images.append(
            {
                "name": img.name,
                "filepath": img.filepath,
                "filepath_raw": img.filepath_raw,
                "source": img.source,
                "packed": bool(img.packed_file),
                "users": img.users,
            }
        )

    libraries = [
        {"name": lib.name, "filepath": lib.filepath, "users": lib.users}
        for lib in bpy.data.libraries
    ]

    scenes = []
    for scene in bpy.data.scenes:
        scenes.append(
            {
                "name": scene.name,
                "objects": sorted(o.name for o in scene.objects),
                "camera": scene.camera.name if scene.camera else None,
                "frame_start": scene.frame_start,
                "frame_end": scene.frame_end,
                "fps": scene.render.fps,
                "render_engine": scene.render.engine,
                "unit_system": scene.unit_settings.system,
                "unit_scale_length": scene.unit_settings.scale_length,
                "length_unit": scene.unit_settings.length_unit,
                "world": scene.world.name if scene.world else None,
            }
        )

    orphan_data = {
        "meshes": sorted(x.name for x in bpy.data.meshes if x.users == 0),
        "materials": sorted(x.name for x in bpy.data.materials if x.users == 0),
        "images": sorted(x.name for x in bpy.data.images if x.users == 0),
        "curves": sorted(x.name for x in bpy.data.curves if x.users == 0),
        "cameras": sorted(x.name for x in bpy.data.cameras if x.users == 0),
        "lights": sorted(x.name for x in bpy.data.lights if x.users == 0),
    }

    file_version = getattr(bpy.data, "version", None)
    file_subversion = getattr(bpy.data, "subversion", None)

    return {
        "audit_schema": 1,
        "file": {
            "path": os.path.abspath(filepath),
            "size_bytes": os.path.getsize(filepath),
            "sha256": _sha256(filepath),
            "saved_blender_version": list(file_version) if file_version else None,
            "saved_blender_subversion": file_subversion,
            "opened_with_blender_version": list(bpy.app.version),
            "opened_with_blender_version_string": bpy.app.version_string,
        },
        "counts": {
            "scenes": len(bpy.data.scenes),
            "collections": len(bpy.data.collections),
            "objects": len(bpy.data.objects),
            "meshes": len(bpy.data.meshes),
            "materials": len(bpy.data.materials),
            "images": len(bpy.data.images),
            "libraries": len(bpy.data.libraries),
            "actions": len(bpy.data.actions),
        },
        "scenes": scenes,
        "collections": [
            {
                "name": c.name,
                "objects": sorted(o.name for o in c.objects),
                "children": sorted(ch.name for ch in c.children),
                "library": c.library.filepath if c.library else None,
            }
            for c in bpy.data.collections
        ],
        "objects": sorted(objects, key=lambda x: x["name"]),
        "materials": sorted(materials, key=lambda x: x["name"]),
        "images": sorted(images, key=lambda x: x["name"]),
        "libraries": sorted(libraries, key=lambda x: x["name"]),
        "orphan_data": orphan_data,
        "chair_validation": _chair_validation(objects),
    }


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1 :] if "--" in argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    return parser.parse_args(argv)


def main():
    args = parse_args()
    filepath = bpy.data.filepath
    if not filepath:
        raise SystemExit("The audit requires an opened .blend file.")
    report = build_report(filepath)
    out = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, sort_keys=True)
    print(f"BLEND_AUDIT_JSON={out}")
    print(f"CHAIR_VALIDATION={report['chair_validation']['overall_status']}")
    print(json.dumps(report["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
