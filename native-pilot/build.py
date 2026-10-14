"""Package only native assets; no Python or browser runtime is shipped."""

from __future__ import annotations
import argparse
import hashlib
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES = ("index.html", "original.css", "style.css", "content.js", "engine.js", "app.js")


def build(output):
    output.mkdir(parents=True, exist_ok=True)
    hashes = {}
    sizes = {}
    for name in FILES:
        data = (HERE / name).read_bytes()
        (output / name).write_bytes(data)
        hashes[name] = hashlib.sha256(data).hexdigest()
        sizes[name] = len(data)
    manifest = {
        "source_reference": "81f1411b256f635b7c31698b81a32c68b91ca4fa",
        "files_sha256": hashes,
        "files_bytes": sizes,
        "application_bytes": sum(sizes.values()),
        "runtime_dependencies": [],
        "entrypoint": "index.html",
        "canonical_directory": "js/",
        "removed_legacy_directory": "native-pilot/",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))
    return manifest


def build_site(output):
    """Prepare only /js/; the old published native directory is deliberately removed."""
    legacy = output / "native-pilot"
    if legacy.exists():
        shutil.rmtree(legacy)
    return build(output / "js")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=HERE / "dist")
    parser.add_argument(
        "--site-output",
        type=Path,
        help="Package the native app under /js/ only",
    )
    args = parser.parse_args()
    build_site(args.site_output) if args.site_output else build(args.output)
