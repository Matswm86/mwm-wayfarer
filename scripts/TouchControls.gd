class_name TouchControls
extends Control

## Left 45 % of the screen: a virtual stick that appears under the thumb.
## Right side: drag to orbit the camera. Buttons in the PerfOverlay take their touches first.

const STICK_RADIUS := 150.0

var move: Vector2 = Vector2.ZERO

var _stick_index: int = -1
var _stick_origin: Vector2 = Vector2.ZERO
var _stick_pos: Vector2 = Vector2.ZERO
var _orbit_index: int = -1
var _orbit_last: Vector2 = Vector2.ZERO
var _orbit_acc: Vector2 = Vector2.ZERO


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func take_orbit() -> Vector2:
	var o := _orbit_acc
	_orbit_acc = Vector2.ZERO
	return o


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventScreenTouch:
		var t := event as InputEventScreenTouch
		var left: bool = t.position.x < get_viewport_rect().size.x * 0.45
		if t.pressed:
			if left and _stick_index < 0:
				_stick_index = t.index
				_stick_origin = t.position
				_stick_pos = t.position
			elif not left and _orbit_index < 0:
				_orbit_index = t.index
				_orbit_last = t.position
		else:
			if t.index == _stick_index:
				_stick_index = -1
				move = Vector2.ZERO
			if t.index == _orbit_index:
				_orbit_index = -1
		queue_redraw()
	elif event is InputEventScreenDrag:
		var d := event as InputEventScreenDrag
		if d.index == _stick_index:
			_stick_pos = d.position
			var v := (_stick_pos - _stick_origin) / STICK_RADIUS
			move = v.limit_length(1.0)
			queue_redraw()
		elif d.index == _orbit_index:
			_orbit_acc += d.position - _orbit_last
			_orbit_last = d.position


func _draw() -> void:
	if _stick_index < 0:
		return
	draw_circle(_stick_origin, STICK_RADIUS, Color(1.0, 1.0, 1.0, 0.18))
	draw_circle(_stick_origin + move * STICK_RADIUS, 60.0, Color(1.0, 1.0, 1.0, 0.45))
