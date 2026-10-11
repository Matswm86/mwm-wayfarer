extends SceneTree

## Corner pass (2026-10-11): a third, light LOD of the scanned storehouse for distance views and for
## the sun-shadow proxy (the scans came with LOD0 64k and LOD1 11k triangles only). Godot's own
## simplifier stops early on these scans (UV seams split nearly every vertex), so Blender
## collapse-decimates first (UVs kept):
##   blender -b --factory-startup -P tools/spike/house_lod2_blender.py -- <dir>
## then this loads <dir>/<kind>_LOD2.glb at run time (no project import), puts the house
## material on it and saves assets/models/corner/baked/<kind>_LOD2.res. LOD2 is probe-lit like
## LOD1, so the corner lightmap needs no rebake. Run headless from the project dir:
##   godot --headless --audio-driver Dummy -s res://tools/spike/house_lod2.gd -- <dir>

const BAKED := "res://assets/models/corner/baked/"
## Only the Evju storehouse (see house_lod2_blender.py: the cabin scan tears open when decimated).
const KINDS: Array[String] = ["evju"]


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var dir: String = args[0] if args.size() > 0 else ""
	for kind in KINDS:
		var doc := GLTFDocument.new()
		var state := GLTFState.new()
		var err := doc.append_from_file(dir.path_join(kind + "_LOD2.glb"), state)
		if err != OK:
			print("HOUSE LOD2 %s: load failed %s" % [kind, error_string(err)])
			continue
		var root := doc.generate_scene(state)
		var mi: MeshInstance3D = root.find_children("*", "MeshInstance3D", true, false)[0]
		var lod1: ArrayMesh = load(BAKED + kind + "_LOD1.res")
		var src: Mesh = mi.mesh
		var out := ArrayMesh.new()
		out.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, src.surface_get_arrays(0))
		out.surface_set_material(0, lod1.surface_get_material(0))
		ResourceSaver.save(out, BAKED + kind + "_LOD2.res")
		print(
			(
				"HOUSE LOD2 %s: %d triangles (LOD1 %d), node transform %s, aabb %s vs LOD1 %s"
				% [
					kind,
					out.get_faces().size() / 3,
					lod1.get_faces().size() / 3,
					mi.transform,
					out.get_aabb(),
					lod1.get_aabb()
				]
			)
		)
		root.free()
	quit()
