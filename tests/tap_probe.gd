extends Node

## Taps overlay buttons with synthetic screen touches (the event type a phone sends) and
## reports whether each button's action ran.

var main: Node


func _ready() -> void:
	main = (load("res://scenes/Main.tscn") as PackedScene).instantiate()
	add_child(main)
	for i in 90:
		await get_tree().process_frame
	await _tap("preset")
	print("PROBE preset_index after tap: ", main.preset_index)
	await _tap("bench_all")
	for i in 5:
		await get_tree().process_frame
	print("PROBE bench running after tap: ", main.bench.running)
	get_tree().quit()


func _tap(id: String) -> void:
	var b: Button = PerfOverlay._buttons[id]
	var c: Vector2 = b.get_global_rect().get_center()
	print(
		"PROBE tap ", id, " at ", c, " disabled=", b.disabled, " visible=", b.is_visible_in_tree()
	)
	var e := InputEventScreenTouch.new()
	e.index = 0
	e.position = c
	e.pressed = true
	Input.parse_input_event(e)
	await get_tree().process_frame
	var r := InputEventScreenTouch.new()
	r.index = 0
	r.position = c
	r.pressed = false
	Input.parse_input_event(r)
	for i in 3:
		await get_tree().process_frame
