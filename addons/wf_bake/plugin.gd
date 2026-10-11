@tool
extends EditorPlugin

## Command-line lightmap bake. Godot bakes LightmapGI only inside the editor, so this plugin, when
## the editor starts with WF_BAKE_SCENE=res://...tscn, opens that scene, selects its LightmapGI
## node, presses the editor's own "Bake Lightmaps" button, saves the scene and quits.
## Inert otherwise. Run (Xvfb, GPU Vulkan; see tools/spike/bake_corner.sh):
##   WF_BAKE_SCENE=res://scenes/BeautyCorner.tscn godot --editor --path .


func _enter_tree() -> void:
	var scene_path: String = OS.get_environment("WF_BAKE_SCENE")
	if scene_path == "":
		return
	_run.call_deferred(scene_path)


func _run(scene_path: String) -> void:
	var tree := get_tree()
	for i in 120:
		await tree.process_frame
	EditorInterface.open_scene_from_path(scene_path)
	for i in 30:
		await tree.process_frame
	var root := EditorInterface.get_edited_scene_root()
	if root == null:
		_finish("WFBAKE ERROR: could not open %s" % scene_path, 1)
		return
	var lms := root.find_children("*", "LightmapGI", true, false)
	if lms.is_empty():
		_finish("WFBAKE ERROR: no LightmapGI in %s" % scene_path, 1)
		return
	var lm := lms[0] as LightmapGI
	EditorInterface.get_selection().clear()
	EditorInterface.get_selection().add_node(lm)
	EditorInterface.edit_node(lm)
	for i in 30:
		await tree.process_frame
	var button := _find_button(EditorInterface.get_base_control(), "Bake Lightmaps")
	if button == null:
		_finish("WFBAKE ERROR: Bake Lightmaps button not found", 1)
		return
	print("WFBAKE baking %s ..." % scene_path)
	var t0: int = Time.get_ticks_msec()
	for c: Dictionary in button.pressed.get_connections():
		var cb: Callable = c["callable"]
		var obj: Object = cb.get_object()
		print("WFBAKE button -> %s.%s" % [obj.get_class(), cb.get_method()])
		for m: Dictionary in obj.get_method_list():
			if String(m["name"]).contains("bake"):
				print("WFBAKE   method ", m["name"], " args ", m["args"].size())
	button.pressed.emit()
	for i in 10:
		await tree.process_frame
	# an unsaved bake asks for a file: answer the editor's dialog with <scene>.lmbake
	var dlg := _find_file_dialog(EditorInterface.get_base_control())
	if dlg:
		var out: String = scene_path.get_basename() + ".lmbake"
		print("WFBAKE answering file dialog with ", out)
		dlg.hide()
		dlg.file_selected.emit(out)
	for i in 60:
		await tree.process_frame
	_dump_dialogs(EditorInterface.get_base_control())
	var data := lm.light_data
	if data == null:
		_finish("WFBAKE ERROR: bake produced no light_data (see editor log above)", 1)
		return
	EditorInterface.save_scene()
	for i in 30:
		await tree.process_frame
	_finish(
		(
			"WFBAKE done in %d ms: %s, %d users"
			% [Time.get_ticks_msec() - t0, data.resource_path, data.get_user_count()]
		),
		0
	)


func _find_file_dialog(n: Node) -> EditorFileDialog:
	if n is EditorFileDialog and (n as Window).visible:
		return n as EditorFileDialog
	for c in n.get_children():
		var d := _find_file_dialog(c)
		if d:
			return d
	return null


func _dump_dialogs(n: Node) -> void:
	if n is AcceptDialog and (n as Window).visible:
		print("WFBAKE dialog: ", (n as AcceptDialog).dialog_text, " | ", (n as Window).title)
	for c in n.get_children():
		_dump_dialogs(c)


func _find_button(n: Node, text: String) -> Button:
	if n is Button and (n as Button).text == text:
		return n as Button
	for c in n.get_children():
		var b := _find_button(c, text)
		if b:
			return b
	return null


func _finish(msg: String, code: int) -> void:
	print(msg)
	get_tree().quit(code)
