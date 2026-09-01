import argparse
import json


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def obj_map(report):
    return {o["name"]: o for o in report.get("objects", [])}


def compact_obj(o):
    return {
        "type": o.get("type"),
        "location": o.get("location"),
        "rotation_euler_deg": o.get("rotation_euler_deg"),
        "scale": o.get("scale"),
        "dimensions": o.get("dimensions"),
        "material_slots": o.get("material_slots"),
        "mesh": o.get("mesh"),
        "modifiers": o.get("modifiers"),
        "constraints": o.get("constraints"),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("a")
    p.add_argument("b")
    p.add_argument("--out")
    args = p.parse_args()

    a, b = load(args.a), load(args.b)
    ao, bo = obj_map(a), obj_map(b)
    common = sorted(set(ao) & set(bo))
    changed = []
    for name in common:
        if compact_obj(ao[name]) != compact_obj(bo[name]):
            changed.append(
                {
                    "name": name,
                    "a": compact_obj(ao[name]),
                    "b": compact_obj(bo[name]),
                }
            )

    result = {
        "same_sha256": a["file"]["sha256"] == b["file"]["sha256"],
        "a": {
            "path": a["file"]["path"],
            "size_bytes": a["file"]["size_bytes"],
            "sha256": a["file"]["sha256"],
            "chair_validation": a.get("chair_validation"),
        },
        "b": {
            "path": b["file"]["path"],
            "size_bytes": b["file"]["size_bytes"],
            "sha256": b["file"]["sha256"],
            "chair_validation": b.get("chair_validation"),
        },
        "objects_only_in_a": sorted(set(ao) - set(bo)),
        "objects_only_in_b": sorted(set(bo) - set(ao)),
        "changed_common_objects": changed,
        "scene_settings_equal": a.get("scenes") == b.get("scenes"),
        "materials_equal": a.get("materials") == b.get("materials"),
        "libraries_equal": a.get("libraries") == b.get("libraries"),
        "images_equal": a.get("images") == b.get("images"),
    }

    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    print(text)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")


if __name__ == "__main__":
    main()
