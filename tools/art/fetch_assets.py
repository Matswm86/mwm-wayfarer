#!/usr/bin/env python3
"""Download the CC0 assets used by the MWM Wayfarer art drafts into assets/_raw/.

Usage: python3 -I tools/art/fetch_assets.py
Sources: Poly Haven (CC0 1.0) via api.polyhaven.com, Google Fonts repo (OFL 1.1).
The Blender Studio Human Base Meshes bundle (CC0) is copied from the Race Riders raw folder when present.
Every asset is listed in CREDITS.md. Pattern copied from Race Riders tools/art/fetch_polyhaven.py.
"""

import json
import pathlib
import shutil
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
RAW = ROOT / "assets" / "_raw"
PH = RAW / "polyhaven"
RR_RAW = ROOT.parent / "mwm-race-riders" / "assets" / "_raw"
UA = {"User-Agent": "mwm-wayfarer-art/1.0"}

HDRIS = {
    "qwantani_dusk_2_puresky": "4k",  # fjord: clear dusk, aurora sky
    "kloofendal_48d_partly_cloudy_puresky": "4k",  # archipelago: cumulus, blue
    "syferfontein_18d_clear_puresky": "4k",  # canyon: clear, warm afternoon
    "kloofendal_43d_clear_puresky": "4k",  # canyon (10-10): clear, 43 deg midday sun reaches the valley floor
    "evening_road_01_puresky": "4k",  # talk frame / alt fjord
}
TEXTURES = {
    # fjord
    "aerial_grass_rock": "2k",
    "rocky_terrain_02": "2k",
    "rock_face_03": "1k",
    "leafy_grass": "2k",
    "sparse_grass": "1k",
    "forest_ground_04": "1k",
    "wood_trunk_wall": "1k",
    "weathered_plank_siding": "1k",
    "weathered_brown_planks": "1k",
    "wood_planks_dirt": "1k",
    "coast_sand_rocks_02": "1k",
    "gray_rocks": "1k",
    "stone_wall": "1k",
    # archipelago
    "marble_cliff_02": "2k",
    "marble_cliff_04": "1k",
    "coast_sand_01": "2k",
    "white_sandstone_blocks_02": "1k",
    "seaworn_sandstone_brick": "1k",
    "aerial_rocks_02": "2k",
    "dry_ground_rocks": "1k",
    "aerial_beach_01": "2k",
    # canyon
    "red_sandstone_wall": "1k",
    "sandstone_cracks": "1k",
    "red_sand": "1k",
    "aerial_sand": "2k",
    "red_laterite_soil_stones": "1k",
    "palm_tree_bark": "1k",
    "clay_plaster": "1k",
    "patterned_clay_plaster": "1k",
    # 10-10 art pass: real limestone for R2, layered sandstone for R3
    "marble_cliff_05": "2k",
    "rock_ground_02": "2k",
    "aerial_rocks_04": "1k",
    "cliff_side": "2k",
    "rock_boulder_cracked": "2k",
    # cloth and character
    "rough_linen": "1k",
    "hessian_230": "1k",
    "denim_fabric": "1k",
    "brown_leather": "1k",
    "knitted_fleece": "1k",
    "poly_wool_herringbone": "1k",
    "fabric_pattern_07": "1k",
    "waffle_pique_cotton": "1k",
}
MODELS = {
    "mountainside": "2k",
    "coastal_cliff_02": "1k",
    "rock_face_01": "1k",
    "rock_face_02": "1k",
    "coast_rocks_01": "1k",
    "coast_rocks_05": "1k",
    "coast_land_rocks_04": "1k",
    "boulder_01": "1k",
    "rock_moss_set_01": "1k",
    "fir_tree_01": "1k",
    "pine_tree_01": "1k",
    "tree_small_02": "1k",
    "island_tree_03": "1k",
    "shrub_04": "1k",
    "searsia_lucida": "1k",
    "grass_medium_01": "1k",
    "grass_medium_02": "1k",
    "fern_02": "1k",
    "modular_wooden_pier": "1k",
    "wooden_barrels_01": "1k",
    "wooden_crate_01": "1k",
    "wooden_crate_02": "1k",
    "Barrel_01": "1k",
    "wicker_basket_01": "1k",
    "wicker_basket_02": "1k",
    "Lantern_01": "1k",
    "fishermans_hat": "1k",
    "namaqualand_cliff_01": "1k",
    "namaqualand_cliff_02": "1k",
    "namaqualand_boulder_02": "1k",
    "namaqualand_boulder_05": "1k",
    "quiver_tree_01": "1k",
    "ceramic_vase_01": "1k",
    "ceramic_vase_03": "1k",
    "antique_ceramic_vase_01": "1k",
    "brass_pot_01": "1k",
    "brass_vase_02": "1k",
    "food_pomegranate_01": "1k",
    "lemon": "1k",
    "wooden_table_02": "1k",
    "folding_wooden_stool": "1k",
    "marble_bust_01": "1k",
    "dry_branches_medium_01": "1k",
}
MAPS = ("Diffuse", "nor_gl", "Rough", "AO", "Displacement", "arm")
FONTS = {
    "Inter[opsz,wght].ttf": "https://github.com/google/fonts/raw/main/ofl/inter/Inter%5Bopsz,wght%5D.ttf",
    "Inter-OFL.txt": "https://github.com/google/fonts/raw/main/ofl/inter/OFL.txt",
    "SourceSerif4[opsz,wght].ttf": "https://github.com/google/fonts/raw/main/ofl/sourceserif4/SourceSerif4%5Bopsz,wght%5D.ttf",
    "SourceSerif4-Italic[opsz,wght].ttf": "https://github.com/google/fonts/raw/main/ofl/sourceserif4/SourceSerif4-Italic%5Bopsz,wght%5D.ttf",
    "SourceSerif4-OFL.txt": "https://github.com/google/fonts/raw/main/ofl/sourceserif4/OFL.txt",
}


def get(url: str, dest: pathlib.Path) -> None:
    if dest.exists() and dest.stat().st_size > 0:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA)) as r:
        dest.write_bytes(r.read())
    print("got", dest.relative_to(ROOT), dest.stat().st_size)


def files(asset: str) -> dict:
    req = urllib.request.Request(f"https://api.polyhaven.com/files/{asset}", headers=UA)
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def main() -> None:
    hb = RR_RAW / "human" / "human-base-meshes-bundle-v1.4.1"
    dst = RAW / "human" / "human-base-meshes-bundle-v1.4.1"
    if hb.exists() and not dst.exists():
        shutil.copytree(hb, dst)
        print("copied human base meshes")
    for h, s in HDRIS.items():
        f = files(h)
        get(f["hdri"][s]["hdr"]["url"], PH / "hdri" / f"{h}_{s}.hdr")
    for t, s in TEXTURES.items():
        f = files(t)
        for m in MAPS:
            if m in f and s in f[m]:
                fmt = "jpg" if "jpg" in f[m][s] else "png"
                get(f[m][s][fmt]["url"], PH / "textures" / t / f"{t}_{m.lower()}_{s}.{fmt}")
    for mdl, s in MODELS.items():
        f = files(mdl)
        g = f["gltf"][s]["gltf"]
        get(g["url"], PH / "models" / mdl / pathlib.Path(g["url"]).name)
        for rel, inc in g.get("include", {}).items():
            get(inc["url"], PH / "models" / mdl / rel)
    for name, url in FONTS.items():
        get(url, ROOT / "assets" / "fonts" / name)


if __name__ == "__main__":
    main()
