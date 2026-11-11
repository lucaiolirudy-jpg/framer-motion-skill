#!/usr/bin/env bash
# Downloads three.js modules and fonts used by the pipeline (not vendored in git).
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p r3d/lib fonts
for f in build/three.module.js examples/jsm/loaders/TTFLoader.js examples/jsm/geometries/TextGeometry.js \
         examples/jsm/loaders/FontLoader.js examples/jsm/environments/RoomEnvironment.js \
         examples/jsm/libs/opentype.module.js examples/jsm/utils/BufferGeometryUtils.js \
         examples/jsm/geometries/RoundedBoxGeometry.js; do
  mkdir -p "r3d/lib/$(dirname "$f")"
  curl -sSfo "r3d/lib/$f" "https://cdn.jsdelivr.net/npm/three@0.160.0/$f"
done
UA="Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.2 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.2"
get_font() { curl -s -A "$UA" "https://fonts.googleapis.com/css2?family=$1" | grep -oE "https://fonts.gstatic.com[^)]+" | head -1 | xargs curl -sSfo "$2"; }
get_font "Montserrat:wght@900" r3d/lib/mont.woff        # 3D text (Black)
get_font "Montserrat:wght@800" r3d/lib/mont9.woff       # 3D text (ExtraBold)
get_font "Poppins:wght@700" fonts/pop700.woff           # subtitle replica
