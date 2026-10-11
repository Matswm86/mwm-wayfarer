"""Sketchfab search + download helper (token read from ~/.config/sketchfab/token, never printed).

usage:
  python3 sketchfab.py search "scots pine" [--max-faces 60000] [--count 24]
  python3 sketchfab.py info <uid>
  python3 sketchfab.py get <uid> <out_dir> [source]  # glb (or gltf zip); 'source' = the author's original upload
"""
import json
import sys
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

API = "https://api.sketchfab.com/v3"
TOKEN = (Path.home() / ".config/sketchfab/token").read_text().strip()


def _get(url: str, auth: bool = False) -> dict:
    req = urllib.request.Request(url)
    if auth:
        req.add_header("Authorization", f"Token {TOKEN}")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def search(q: str, max_faces: int = 0, count: int = 24) -> None:
    params = {"type": "models", "q": q, "downloadable": "true", "count": count, "sort_by": "-likeCount"}
    if max_faces:
        params["max_face_count"] = max_faces
    data = _get(f"{API}/search?{urllib.parse.urlencode(params)}")
    for m in data.get("results", []):
        lic = (m.get("license") or {}).get("label", "?")
        print(f"{m['uid']}  faces={m.get('faceCount')}  likes={m.get('likeCount')}  anim={m.get('animationCount')}  "
              f"lic={lic}  by={m['user']['username']}  | {m['name']}")


def info(uid: str) -> None:
    m = _get(f"{API}/models/{uid}")
    keep = {k: m.get(k) for k in ("name", "faceCount", "vertexCount", "animationCount", "isDownloadable", "viewerUrl")}
    keep["license"] = (m.get("license") or {}).get("label")
    keep["author"] = m["user"]["username"]
    keep["thumb"] = max(m["thumbnails"]["images"], key=lambda i: i["width"])["url"]
    print(json.dumps(keep, indent=1))
    print(m.get("description", "")[:600])


def get(uid: str, out: str, fmt: str = "glb") -> None:
    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)
    d = _get(f"{API}/models/{uid}/download", auth=True)
    if fmt == "source" and "source" in d:
        url, name = d["source"]["url"], f"{uid}_source.zip"
    elif "glb" in d:
        url, name = d["glb"]["url"], f"{uid}.glb"
    else:
        url, name = d["gltf"]["url"], f"{uid}_gltf.zip"
    dst = out_dir / name
    urllib.request.urlretrieve(url, dst)
    if name.endswith(".zip"):
        with zipfile.ZipFile(dst) as z:
            z.extractall(out_dir / (uid + ("_source" if fmt == "source" else "")))
    m = _get(f"{API}/models/{uid}")
    (out_dir / f"{uid}.json").write_text(json.dumps({
        "uid": uid, "name": m["name"], "author": m["user"]["username"],
        "author_url": m["user"]["profileUrl"], "url": m["viewerUrl"],
        "license": (m.get("license") or {}).get("label"), "faces": m.get("faceCount")}, indent=1))
    print(dst, dst.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "search":
        mf = int(sys.argv[sys.argv.index("--max-faces") + 1]) if "--max-faces" in sys.argv else 0
        n = int(sys.argv[sys.argv.index("--count") + 1]) if "--count" in sys.argv else 24
        search(sys.argv[2], mf, n)
    elif cmd == "info":
        info(sys.argv[2])
    elif cmd == "get":
        get(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "glb")
