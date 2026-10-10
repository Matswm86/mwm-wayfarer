#!/bin/bash
# Mark textures as VRAM-compressed (ETC2/ASTC on Android) with mipmaps; --normal for normal maps.
# Usage: tools/spike/vram_import.sh [--normal] file.png.import ...   then run godot --import.
nm=0
if [ "$1" = "--normal" ]; then nm=1; shift; fi
for f in "$@"; do
  sed -i 's/^compress\/mode=.*/compress\/mode=2/; s/^mipmaps\/generate=.*/mipmaps\/generate=true/; s/^detect_3d\/compress_to=.*/detect_3d\/compress_to=0/' "$f"
  if [ $nm = 1 ]; then sed -i "s/^compress\/normal_map=.*/compress\/normal_map=1/" "$f"; fi
done
