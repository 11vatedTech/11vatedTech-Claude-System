from pathlib import Path
from PIL import Image
import hashlib, json

root = Path('Frontend-Designs/Pumkit-Frontend-Design')
out = Path('artifacts/frontend/wave-a-pumkit-before/pumkit-visual-canon.json')
assets = []
for path in sorted((root / 'assets' / 'pumkit').rglob('*')):
    if not path.is_file():
        continue
    try:
        image = Image.open(path)
    except Exception:
        continue
    assets.append({
        'path': path.relative_to(root).as_posix(),
        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'width': image.width,
        'height': image.height,
        'mode': image.mode,
        'bytes': path.stat().st_size,
    })
canon = {
    'schema_version': 1,
    'kind': 'pumkit-visual-canon',
    'source_project': root.as_posix(),
    'source_policy': 'actual image bytes; approved primary asset and concept-art sheets only',
    'assets': assets,
    'identity_anchors': ['authored silhouette', 'head/body proportion', 'ear geometry', 'facial structure', 'eyes', 'limbs and paws', 'tail/appendages', 'markings', 'palette and surface cues', 'cute/eerie balance'],
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(canon, indent=2), encoding='utf-8')
print(json.dumps({'assets': len(assets), 'output': out.as_posix()}, indent=2))
