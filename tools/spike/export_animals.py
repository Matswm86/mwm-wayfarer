"""Slim the owner's rigged animal GLBs (assets/_raw/animals/, Sketchfab; authors and licences in
assets/models/animals/CREDITS.md) into phone-sized GLBs in assets/models/animals/.

Per animal: keep only the clips the valley uses, cap textures (1024 px; 2048 for deer and doe),
decimate meshes above the triangle cap, re-export as GLB.
Run (about 2 min):
  BLENDER_USER_RESOURCES=~/MWM/data/tools/blender_user blender -b --factory-startup \
      -P tools/spike/export_animals.py
"""

from __future__ import annotations

import json
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "assets" / "_raw" / "animals"
OUT = ROOT / "assets" / "models" / "animals"
OUT.mkdir(parents=True, exist_ok=True)

# name: (source file, clips to keep {role: clip name}, texture cap px, triangle cap)
ANIMALS = {
    "deer": (
        "deer_-_realistic_3d_model_demo_free.glb",
        {"idle": "Deer|Deer_Idle", "walk": "Deer|Deer_WalkFast_F"},
        2048,
        12000,
    ),
    "doe": (
        "realistic_animated_doe_3d_model.glb",
        {"graze": "Stand_Eating_01", "walk": "Walk", "run": "Trot"},
        2048,
        12000,
    ),
    "elk": (
        "realistic_animated_elk_3d_model.glb",
        {"graze": "Stand_Eating_01", "walk": "Walk", "run": "Trot"},
        1024,
        10000,
    ),
    "moose": (
        "moose_-_realistic_3d_model_demo_free.glb",
        {"idle": "Moose|Moose_Idle", "walk": "Moose|Moose_WalkFast_F"},
        1024,
        10000,
    ),
    "wolf": (
        "wolf_-_realistic_3d_model_demo_free.glb",
        {"idle": "Wolf|Wolf_Howl", "walk": "Wolf|Wolf_WalkFast_F"},
        1024,
        10000,
    ),
    "fox": (
        "fox_-_realistic_3d_model_demo_free.glb",
        {"idle": "Fox|Fox_Stand", "walk": "Fox|Fox_WalkFast_F", "howl": "Fox|Fox_Howl"},
        1024,
        8000,
    ),
    "rabbit": (
        "rabbit_-_realistic_3d_model_demo_free.glb",
        {"idle": "Rabbit|Rabbit_Idle", "walk": "Rabbit|Rabbit_WalkSlow_F"},
        1024,
        6000,
    ),
    "bear": (
        "realistic_animated_bear_3d_model.glb",
        {"graze": "Stand_Eating_01", "idle": "Stand_Idle_01", "walk": "Walk"},
        1024,
        8000,
    ),
    "eagle": ("eagle.glb", {"fly": "Animation"}, 1024, 6500),
    "gull": ("seagull.glb", {"fly": "Animation"}, 1024, 6000),
}


def export(name: str, src: str, clips: dict, tex_cap: int, tri_cap: int) -> dict:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(RAW / src))
    keep = set(clips.values())
    names = [a.name for a in bpy.data.actions]
    for a in list(bpy.data.actions):
        if a.name not in keep:
            bpy.data.actions.remove(a)
    missing = keep - {a.name for a in bpy.data.actions}
    if missing:
        print(f"{name}: clips not found {missing}; available {names[:40]}")
    for img in bpy.data.images:
        if img.size[0] > tex_cap or img.size[1] > tex_cap:
            f = tex_cap / max(img.size[0], img.size[1])
            img.scale(max(1, int(img.size[0] * f)), max(1, int(img.size[1] * f)))
    tris = 0
    for o in bpy.data.objects:
        if o.type != "MESH":
            continue
        t = sum(len(p.vertices) - 2 for p in o.data.polygons)
        if t > tri_cap:
            d = o.modifiers.new("dec", "DECIMATE")
            d.ratio = tri_cap / t
            t = tri_cap
        tris += t
    # the armature plays each kept action as its own glTF animation
    arm = next((o for o in bpy.data.objects if o.type == "ARMATURE"), None)
    for o in bpy.data.objects:
        if o.animation_data:
            for tr in list(o.animation_data.nla_tracks):
                o.animation_data.nla_tracks.remove(tr)
            o.animation_data.action = None
    if arm is not None:
        arm.animation_data_create()
        for a in bpy.data.actions:
            tr = arm.animation_data.nla_tracks.new()
            tr.name = a.name
            tr.strips.new(a.name, int(a.frame_range[0]), a)
    path = OUT / f"{name}.glb"
    bpy.ops.export_scene.gltf(
        filepath=str(path),
        export_format="GLB",
        export_apply=True,
        export_animations=True,
        export_animation_mode="NLA_TRACKS",
        export_image_format="AUTO",
        export_skins=True,
    )
    print(
        f"ANIMAL {name}: {path.stat().st_size // 1024} KB, ~{tris} tris, clips {sorted(keep - missing)}"
    )
    return {"clips": clips, "tris": tris}


def main() -> None:
    out = {name: export(name, *spec) for name, spec in ANIMALS.items()}
    (OUT / "animals.json").write_text(json.dumps(out, indent=1))


main()
