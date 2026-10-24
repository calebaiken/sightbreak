"""External control: unchanged bytes must not disguise a different source commit."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'sightbreak-v3/scripts'))
import build_manifest as manifest

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    current = dict(source_commit='frozen-A', source_game_tree='same-tree',
                   source_content_sha256='same-bytes', source_game_dirty=False)
    with patch.object(manifest, 'ROOT', root), patch.object(manifest, 'BUILDS', root / 'builds'), patch.object(manifest, 'source', lambda: dict(current)):
        for target in manifest.OUTPUTS:
            manifest.begin(target)
            output = manifest.BUILDS / manifest.OUTPUTS[target]
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(b'fixture-only; not a native export')
            manifest.finish(target)
        current['source_commit'] = 'different-B'
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                manifest.package()
        except SystemExit as error:
            result = dict(control='different commit, identical bytes and tree', rejected=True, error=str(error))
        else:
            data = json.loads((manifest.BUILDS / 'manifest.json').read_text())
            result = dict(control='different commit, identical bytes and tree', rejected=False,
                          package_commit=data['source_commit'], export_commits=[row['source_commit'] for row in data['exports']])
    print(json.dumps(result, indent=2))
    Path(__file__).with_name('result.json').write_text(json.dumps(result, indent=2) + '\n')
