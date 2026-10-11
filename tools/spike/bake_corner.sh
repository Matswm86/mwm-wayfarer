#!/usr/bin/env bash
# Beauty corner (pass 3): build scenes/BeautyCorner.tscn and bake its lightmap.
# Godot bakes LightmapGI only in the editor: addons/wf_bake presses the editor's own bake button
# when WF_BAKE_SCENE is set. Needs Xvfb (no visible window) and the GPU Vulkan driver.
#   tools/spike/bake_corner.sh            build + bake
#   tools/spike/bake_corner.sh --bake     bake only
set -euo pipefail
cd "$(dirname "$0")/../.."
GODOT=${GODOT:-$HOME/MWM/data/tools/godot/godot}
XVFB=${XVFB:-$HOME/MWM/data/tools/xvfb/root/usr/bin/Xvfb}
DISP=${WF_DISPLAY:-:94}
if ! [ -e "/tmp/.X11-unix/X${DISP#:}" ]; then
	"$XVFB" "$DISP" -screen 0 1920x1080x24 >/dev/null 2>&1 &
	sleep 1
fi
if [ "${1:-}" != "--bake" ]; then
	# twice: the first pass writes the ground mask PNG, which must be imported before the
	# ground material can reference it
	for pass in 1 2; do
		"$GODOT" --headless --audio-driver Dummy -s res://tools/spike/build_corner.gd
		"$GODOT" --headless --audio-driver Dummy --import >/dev/null 2>&1 || true
	done
fi
DISPLAY=$DISP WAYLAND_DISPLAY= VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/nvidia_icd.json \
	WF_BAKE_SCENE=res://scenes/BeautyCorner.tscn \
	"$GODOT" --audio-driver Dummy --display-driver x11 --editor --path . 2>&1 | grep -E "WFBAKE|Done baking|ERROR" || true
"$GODOT" --headless --audio-driver Dummy --import >/dev/null 2>&1 || true
