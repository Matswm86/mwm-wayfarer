"""Write assets/incoming/<asset>/NOTES.md: triangles per LOD node (read from the GLBs), texture sizes, source,
licence, placement and verdict. usage: python3 write_notes.py"""
import json
import struct
from pathlib import Path

from PIL import Image

INC = (Path.home() / "MWM/projects/mwm-wayfarer/assets/incoming")
SF = "https://sketchfab.com/3d-models/"
PHM = "https://polyhaven.com/a/"

META = {
    "scots_pine": {
        "title": "Scots pine (Pinus sylvestris), 3 variants + impostors",
        "source": f"Poly Haven `pine_tree_01` ({PHM}pine_tree_01), CC0, by Poly Haven. 2K source maps incl. `twig_alpha`.",
        "licence": "CC0 (no obligation; courtesy credit Poly Haven)",
        "how": "`tools/assets/cardify_tree.py` (trunk + biggest branches kept and re-baked to 2K; needles as cards showing 16 renders of real twig islands: 8 top views on near-flat cards, 8 side views on vertical radial cards). Impostors: `tools/assets/bake_impostors.py`.",
        "place": "Slopes and benches below about 500 m, dry ground, rock knolls; scattered or open stands (Scots pine is light-hungry, keep 6-12 m apart). Yaw random, scale 0.8-1.2 (a is 20 m, b 15 m, c 17.5 m). LOD0 to about 40 m, LOD1 to about 150 m, impostor beyond.",
        "verdict": "Good. Reads as Scots pine at 15 m and beyond (tall bare trunk, layered flat-topped crown). Within about 8 m the cards show as flat sprays; the crown is slightly sparser than the scan. Needle colour is the scan's olive green.",
        "godot": "Leaves: alpha scissor 0.4, cull disabled, albedo x COLOR_0 (crown AO), UV2.x = sway weight (0 trunk, 1 crown edge). Turn Godot's mesh LOD generation off for these GLBs.",
    },
    "norway_spruce": {
        "title": "Norway spruce (Picea abies), 3 variants + impostors",
        "source": "PlantCatalog on Sketchfab, CC BY 4.0: 'Realistic HD Norway spruce (3/43)' " + SF + "bf500546e2874f9ea086ba6abb11357e, '(13/43)' " + SF + "8bbf8b718c58458dbc8d78d6c6694be6, '(8/43)' " + SF + "8bb75d9faa3e46a184019ee639a08ef9",
        "licence": "CC BY 4.0. In-game credit lines: \"Realistic HD Norway spruce (3/43), (13/43), (8/43)\" by PlantCatalog, CC BY 4.0",
        "how": "Same card bake as the pine (`CF_SRC_GLB`, foliage materials `fol*` as twig source, voxel 0.24 m).",
        "place": "The dominant fjord forest tree: damp north slopes and valley floors, dense stands 3-6 m apart, mixed with birch at the edges. The models are 9.6-10.4 m young trees; scale 1.6-2.2 for mature 15-22 m spruce. LOD0 to about 40 m, LOD1 to 150 m, impostor beyond.",
        "verdict": "Good form (conical, branches to the ground) but the crown reads a little clumpy within about 10 m; dark green colour is right for spruce.",
        "godot": "As the pine.",
    },
    "fir_conifer": {
        "title": "Tall conifer (Poly Haven fir_tree_01), 3 variants (alternative)",
        "source": f"Poly Haven `fir_tree_01` ({PHM}fir_tree_01), CC0",
        "licence": "CC0",
        "how": "Card bake as the pine. Node and embedded image names still say norway_spruce_* (renamed folder only).",
        "place": "Optional mix-in for tall, narrow conifers on steep ground. Not a true Norway spruce silhouette (bare lower trunk).",
        "verdict": "Usable as filler; superseded by `norway_spruce` for the main forest.",
        "godot": "As the pine.",
    },
    "downy_birch": {
        "title": "Birch, 3 variants (c is multi-stemmed) + impostors",
        "source": "lolipop_1707 on Sketchfab, 'Five Birch trees pack (lowpoly, LODs)' " + SF + "five-birch-trees-pack-lowpoly-lods-08fe5117138e4fdaa7ca440ef1201e07 (variants Birch_3, Birch_4, Birch_5), author's 4K source maps reduced to 2K",
        "licence": "CC BY 4.0. In-game credit: \"Five Birch trees pack\" by lolipop_1707, CC BY 4.0",
        "how": "`tools/assets/pack_birch.py`: author's LOD0-2, our LOD3 (45 % of the leaf cards scaled 1.35x, bark decimated), COLOR_0 crown AO, UV2 sway, leaf albedo darkened and desaturated slightly (it was lime). `downy_birch_leaves_translucency.png` = author's subsurface map (use as backlight mask).",
        "place": "Replaces the broadleaf `island_tree_01` (an olive-like tree that is the 'hard square clipped edge' tree at spawn). Valley floor, stream sides, village edges, lower slopes; groups of 3-7. Yaw random, scale 0.85-1.2. LOD0 to 30 m, LOD1 to 60 m, LOD3 to 150 m, impostor beyond (LOD2 optional).",
        "verdict": "Good: real white bark with black lenticels, believable hanging crowns. Honest gap: leaves are silver birch (weeping), not the downy/mountain birch of the west coast; no realistic downy birch exists free.",
        "godot": "Leaves alpha scissor 0.5, cull disabled, albedo x COLOR_0, UV2.x sway.",
    },
    "rocks": {
        "title": "Cliff faces (8), scree and boulders",
        "source": "Poly Haven scans, CC0: namaqualand_cliff_01, namaqualand_cliff_02, mountainside, rock_face_01, rock_face_02, coastal_cliff_04, coast_land_rocks_02, coast_land_rocks_03, namaqualand_boulders_01, namaqualand_stones_01, boulder_01 (" + PHM + "<name>)",
        "licence": "CC0",
        "how": "`tools/assets/bake_rock.py`: welded, decimated to 8k / 2.4k / 0.6k (LOD0/1/2), unwrapped, albedo / normal (GL) / roughness baked from the 4K scan, ORM.R = scan AO x low-mesh AO; albedo graded to fjord gneiss (saturation 0.35, then darkened to mean sRGB about 0.28; the moss set keeps more colour). Sets split into separate stones (`<set>_a_LOD0` ...) sharing one atlas. Pivot: bottom centre.",
        "place": "cliff_*: on true cliff bands (above about 70 deg), rotated so the face points down-slope, overlapped and partly sunk; scale 0.6-3 (cliff_granite_b is 20 m wide). cliff_jagged_a and cliff_jagged_b are talus aprons with half-buried boulders: use them at cliff feet. boulder_a (1.8 m): meadow erratics. boulders_a are really cobbles (0.3-0.6 m) and stones_a pebbles (5-15 cm): shore and path edges, or scale cobbles 3-6x as extra boulders. LOD1 from about 80 m, LOD2 from about 250 m.",
        "verdict": "Good shape and detail, grey gneiss tone. Both Poly Haven moss-stone sets (rock_moss_set_01/02) were rejected: their scans render with black patches after baking (source geometry, not decimation), so there is no separate loose-scree set; the talus aprons cover cliff feet. cliff_coastal_a is an 87 m cliff line at 8k triangles, for distance only. UV islands are many and small (open scan sheets), fine for baked maps.",
        "godot": "Opaque, one material each; cliffs are one-sided scan sheets, so hide their backs in the slope or enable cull disabled on the material.",
    },
    "cliff_materials": {
        "title": "Tiling cliff material set, 4K",
        "source": "ambientCG Rock030, Rock028, Rock048 (https://ambientcg.com/a/RockXXX)",
        "licence": "CC0",
        "how": "`tools/assets/make_cliff_materials.py`: albedo graded towards fjord gneiss, normal OpenGL, ORM (AO, roughness, 0), height 16-bit.",
        "place": "Terrain steep layer (triplanar). gneiss_banded = default wall, gneiss_dark = wet or shaded walls, granite_lichen = sunny upper walls. `*_tile3x3.jpg` shows repetition.",
        "verdict": "Good: grey foliated rock without the wood-grain swirl. gneiss_banded tiles cleanly; gneiss_dark and granite_lichen show one repeating bright feature at 3 x 3, so break them with a macro noise or rotation.",
        "godot": "Use triplanar on faces steeper than about 48 deg; sample height for blend weights.",
    },
    "player_nathan": {
        "title": "Player character (scanned man), idle / walk / run / sprint / talk / interact / pickup / sit",
        "source": "Renderpeople 'Nathan Animated 003 - Walking 3D Man' on Sketchfab " + SF + "143a2b1ea5eb4385ae90a73657aca3bc (8K source albedo reduced to 4K). Animations: Quaternius Universal Animation Library (CC0).",
        "licence": "Model CC BY 4.0: credit \"Nathan Animated 003\" by Renderpeople, CC BY 4.0. Animations CC0 (courtesy credit Quaternius).",
        "how": "`tools/assets/retarget_char.py` (bone match by name, rest-pose alignment by chain direction, per-frame world-rotation transfer, hips scaled by leg ratio). Clips are NLA tracks = separate glTF animations, in place (no root motion). Check render: `player_nathan_check.jpg`.",
        "place": "Player. 1.80 m, origin at the feet, faces -Z in Godot (+Y forward in Blender was converted by the exporter). Has jaw, eye and eyelid bones (not animated yet).",
        "verdict": "Best realism of the set: scanned face holds at talk distance, motion reads natural. Gap: T-shirt and jeans, not outdoor clothes; add the existing backpack/jacket gear or accept a summer look. Only an albedo map (scan); no normal/ORM.",
        "godot": "Import with Skeleton BoneMap (Unreal-like names: hip, spine_01..03, upperleg/lowerleg ...). Use `idle`, `walk`, `run` for locomotion blend; drive speed by root velocity (walk about 1.4 m/s, run about 3.5 m/s).",
    },
    "player_mike": {
        "title": "Alternative player (hoodie jacket, jeans), same clips",
        "source": "mikealger 'Rigged T-Pose Human Male w 50 Face Blendshapes' " + SF + "cc7e4596bcd145208a6992c757854c07 (2K source albedo)",
        "licence": "CC BY 4.0: credit \"Rigged T-Pose Human Male w 50 Face Blendshapes\" by mikealger",
        "how": "As player_nathan. Keeps 50 face blend shapes (ARKit-style names) for talk lip-sync.",
        "place": "Alternative player or a village NPC.",
        "verdict": "Good body and clothing for travel; face slightly CG next to Nathan's scan. 2K albedo only.",
        "godot": "Mixamo bone names (mixamorig_*): Godot's BoneMap auto-detects them.",
    },
    "ingrid_farmer": {
        "title": "Ingrid (woman in work bibs, linen shirt, boots, straw hat), same clips",
        "source": "Natasha_Nabilah 'Woman Farmer Walking Left Turn' " + SF + "4f381bc2110941d6b17fe54a041a611c (2K source albedo)",
        "licence": "CC BY 4.0: credit \"Woman Farmer Walking Left Turn\" by Natasha_Nabilah",
        "how": "Welded (glTF had split every UV seam), decimated 142k -> 60k, re-unwrapped, albedo re-baked from the full mesh at 4K (`RT_REBAKE=1`), then retargeted.",
        "place": "Ingrid at the dock. 1.66 m.",
        "verdict": "Good at talk-camera distance (waist-up). Close-up shows some generated-texture smears on the cheek and mitten-like hands (rig has index fingers only). The straw hat is not Norwegian; remove or retexture if it bothers.",
        "godot": "Mixamo bone names; fingers other than index are not rigged.",
    },
    "ground_cover": {
        "title": "Meadow ground cover: clump cards + far cover atlas",
        "source": "Poly Haven (CC0): grass_medium_01, grass_medium_02, shrub_sorrel_01, dandelion_01, nettle_plant, fern_02, weed_plant_02, celandine_01, periwinkle_plant, shrub_04",
        "licence": "CC0",
        "how": "`tools/assets/ground_cover.py`: 16 Cycles renders (albedo, tangent-space normal, AO) packed 4 x 4 at 512; `meadow_atlas.json` lists tile, view and world size. `meadow_clumps.glb`: one node per side tile, 3 crossed quads, bent-up normals, COLOR_0 base AO (nodes are laid out in a row along X: reset their translation when instancing).",
        "place": "Clumps 35-120 m from the camera at about 1 per 2 m2, mixed by slope and wetness (sorrel, dandelion, celandine in meadows; nettle near houses; fern in shade). Far tiles (10-15) on flat cards facing up past about 80 m.",
        "verdict": "Adequate: real plant renders, but no heather (no realistic free heather found) and no shoreline kelp.",
        "godot": "Alpha scissor 0.4, cull disabled.",
    },
    "village_props": {
        "title": "Village props: boats, woodpiles, skigard fence, hjell fish rack",
        "source": "Sketchfab, CC BY 4.0: donnichols 'Wooden Boat' " + SF + "627ba38e06aa4536b90706a8626c74d4 (boat_tarred), donnichols 'Old Boat' " + SF + "a9ce4ca0cac14f448c72bb94ad193437 (boat_painted), Pabooklas 'Fishing boat' " + SF + "f4b38ccf5ffb46018aa7931c0e106654 (boat_fishing), apariciosilva3D 'Woodpile (game ready asset)' " + SF + "fcd5d5993be64ca38ef8ae2926574874 (woodpile_logs), Seth7Santos 'Stacked Firewood' " + SF + "24694d04c1704aa1838ac775e1013f07 (woodpile_split). Skigard and hjell: our own build (`tools/assets/build_skigard_hjell.py`) with Poly Haven rough_wood and pine_bark textures (CC0).",
        "licence": "Sketchfab items CC BY 4.0 (credit each: model name, author, CC BY 4.0). Skigard, hjell, textures: CC0 / ours.",
        "how": "`tools/assets/prep_prop_tex.py` (author's 2-4K maps, auto V-flip to the GLB, 2K, ORM packed) + `tools/assets/prep_prop.py` (real size, pivot bottom centre, LOD1 at 35 %).",
        "place": "Boats: pulled up on the shore by the boathouses, one or two at the pier (boat_tarred includes an oar). Woodpiles against house walls (scale split stack 1.5-2x or repeat along a wall). Skigard: 4 m segments end to end (+X), along field edges and the path. Hjell: on open ground near the pier, 6 m sections in a row.",
        "verdict": "Boats and woodpiles good. Skigard reads correctly at 10 m+. Hjell structure good; stockfish are simple procedural shapes, fine from about 15 m, plain up close.",
        "godot": "Opaque, one material each (skigard/hjell: wood, bark, stockfish).",
    },
}


def glb_info(path):
    f = path.read_bytes()
    ln = struct.unpack("<I", f[12:16])[0]
    g = json.loads(f[20:20 + ln])
    rows = []
    for n in g.get("nodes", []):
        if "mesh" not in n:
            continue
        m = g["meshes"][n["mesh"]]
        tris = sum(g["accessors"][p["indices"]]["count"] // 3 for p in m["primitives"] if "indices" in p)
        rows.append((n.get("name", "?"), tris, len(m["primitives"])))
    anims = [a.get("name") for a in g.get("animations", [])]
    return rows, anims


for folder, meta in META.items():
    d = INC / folder
    if not d.exists():
        continue
    lines = [f"# {meta['title']}", "", f"**Source:** {meta['source']}", "", f"**Licence:** {meta['licence']}", "",
             f"**How it was made:** {meta['how']}", "", "## Files and triangle counts", "",
             "| File | Node | Triangles | Surfaces |", "|---|---|---|---|"]
    anims_all = {}
    for glb in sorted(d.glob("*.glb")):
        rows, anims = glb_info(glb)
        if anims:
            anims_all[glb.name] = anims
        for name, tris, surf in rows:
            lines.append(f"| {glb.name} | {name} | {tris:,} | {surf} |")
    if anims_all:
        lines += ["", "Animations: " + "; ".join(f"{k}: {', '.join(v)}" for k, v in anims_all.items())]
    lines += ["", "## Textures (PNG source, Godot compresses)", "", "| File | Size |", "|---|---|"]
    stems = [g.stem for g in d.glob("*.glb")]
    for png in sorted(d.glob("*.png")):
        if "_shot" in png.name:
            continue
        rest = [png.name[len(st) + 1:] for st in stems if png.name.startswith(st + "_")]
        if any(r.startswith((folder, st2)) or (d / r).exists() for r in rest for st2 in stems):
            continue  # Godot's own extraction of an embedded texture (<glb>_<texture>.png)
        with Image.open(png) as im:
            lines.append(f"| {png.name} | {im.size[0]} x {im.size[1]} {im.mode} |")
    for js in sorted(d.glob("*.json")):
        lines.append(f"| {js.name} | metadata |")
    lines += ["", "(Godot extracts the GLB-embedded textures on import as `<glb>_<texture>.png`; those generated copies are not listed.)"]
    lines += ["", f"**Suggested placement:** {meta['place']}", "", f"**Godot import:** {meta['godot']}", "",
              f"**Verdict:** {meta['verdict']}", ""]
    (d / "NOTES.md").write_text("\n".join(lines))
    print("wrote", d / "NOTES.md")
