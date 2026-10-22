#!/usr/bin/env python3
"""Recompute the packaging edge controls for a9961a6 versus 021e493.

Run:
    python3 /workspace/reviews/layout-timeout-edge/recompute_edges.py

The sibling package_qa_receipts.py is the exact a9961a6 source. The sibling
package_qa_receipts_baseline.py is the exact 021e493 source. This reproduces the
previously run filesystem/ZIP and workflow-loop controls without native work.
It writes edge-results.json and workflow-loop-control.json beside this script.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import zipfile

import package_qa_receipts as candidate


EVIDENCE_ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    'baseline', EVIDENCE_ROOT / 'package_qa_receipts_baseline.py'
)
baseline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(baseline)


def filesystem_controls():
    results = {}
    with tempfile.TemporaryDirectory(dir=EVIDENCE_ROOT) as temporary:
        root = Path(temporary).resolve()
        source = root / 'source'
        source.mkdir()
        for name, data in {
            'a.json': b'{}\n',
            'b.log': b'original\n',
            'image.png': b'png bytes',
            'frame.PNG': b'uppercase png',
            'nested/fail.png': b'failed OCR original',
            'cache/excluded.png': b'cached png',
            '.godot/a.png': b'import png',
            'b.app/a.png': b'payload png',
        }.items():
            path = source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

        baseline.package(source, root / 'baseline.zip')
        candidate.package(source, root / 'default.zip')
        assert (root / 'baseline.zip').read_bytes() == (root / 'default.zip').read_bytes()
        results['default_archive_identical_to_baseline'] = True

        one = candidate.package(source, root / 'one.zip', layout_pngs=True, max_bytes=9999)
        candidate.package(source, root / 'two.zip', layout_pngs=True, max_bytes=9999)
        assert (root / 'one.zip').read_bytes() == (root / 'two.zip').read_bytes()
        with zipfile.ZipFile(root / 'one.zip') as bundle:
            assert len(set(bundle.namelist())) == len(bundle.namelist())
            index = json.loads(bundle.read('qa-receipts-index.json'))
            assert {entry['path'] for entry in index['files']} == {
                'image.png', 'frame.PNG', 'nested/fail.png'
            }
            for entry in index['files']:
                original = (source / entry['path']).read_bytes()
                assert bundle.read(entry['archive_path']) == original
                assert hashlib.sha256(original).hexdigest() == entry['sha256']
        results['png_only_case_nested_exclusions_hashes_determinism_unique_members'] = True

        for kind in ('file', 'directory', 'dangling'):
            link = source / ('linked-' + kind + '.png')
            target = root / ('outside-' + kind)
            if kind == 'file':
                target.write_bytes(b'outside')
            elif kind == 'directory':
                target.mkdir()
                (target / 'secret.png').write_bytes(b'outside')
            link.symlink_to(target, target_is_directory=(kind == 'directory'))
            output = root / ('rejected-' + kind + '.zip')
            try:
                candidate.package(source, output, layout_pngs=True)
            except RuntimeError as error:
                assert 'Symlinked' in str(error)
            else:
                raise AssertionError(kind + ' accepted')
            assert not output.exists()
            link.unlink()
        results['file_directory_dangling_links_rejected_without_output'] = True

        # The bound is serialized into the index, so use equal-width integers
        # when comparing an exact final ZIP boundary and one byte below it.
        assert len(str(one['bytes'])) == len(str(9999))
        exact = candidate.package(
            source, root / 'exact.zip', layout_pngs=True, max_bytes=one['bytes']
        )
        assert exact['bytes'] == one['bytes']
        output = root / 'one-byte-over.zip'
        try:
            candidate.package(source, output, layout_pngs=True, max_bytes=one['bytes'] - 1)
        except RuntimeError as error:
            assert 'download bound' in str(error)
        else:
            raise AssertionError('final archive overflow accepted')
        assert not output.exists()
        results['exact_final_zip_bound_accepts_boundary_rejects_one_byte_lower'] = True

        empty = root / 'empty'
        empty.mkdir()
        try:
            candidate.package(empty, root / 'empty.zip', layout_pngs=True)
        except RuntimeError as error:
            assert 'No QA receipts' in str(error)
        else:
            raise AssertionError('empty package created')
        assert not (root / 'empty.zip').exists()
        assert not list(root.glob('sightbreak-qa-receipts-*'))
        results['empty_input_no_partial_output_temporary_cleanup'] = True
    return results


def workflow_loop_control():
    results = {'hard_bound_bytes': candidate.MAX_ARCHIVE_BYTES}
    with tempfile.TemporaryDirectory(dir=EVIDENCE_ROOT) as temporary:
        root = Path(temporary).resolve()
        failures = []
        sizes = ('960x540', '1280x720', '1920x1080', '1280x800')
        for size in sizes:
            source = root / 'layouts' / size
            source.mkdir(parents=True)
            frame = source / 'original.png'
            if size == '1280x720':
                with frame.open('wb') as stream:
                    stream.truncate(candidate.MAX_ARCHIVE_BYTES)
            else:
                frame.write_bytes(b'original-' + size.encode())
            try:
                candidate.package(
                    source, root / 'layout-images' / (size + '.zip'), layout_pngs=True
                )
            except Exception as error:
                failures.append(size + ': ' + str(error))
        results['failed_sizes'] = [failure.split(':')[0] for failure in failures]
        results['successful_sizes'] = [
            size for size in sizes if (root / 'layout-images' / (size + '.zip')).exists()
        ]
        assert results['failed_sizes'] == ['1280x720']
        assert results['successful_sizes'] == ['960x540', '1920x1080', '1280x800']
        assert not (root / 'layout-images' / '1280x720.zip').exists()
        assert not list((root / 'layout-images').glob('sightbreak-qa-receipts-*'))
    return results


def main():
    controls = (
        ('edge-results.json', filesystem_controls()),
        ('workflow-loop-control.json', workflow_loop_control()),
    )
    for name, result in controls:
        serialized = json.dumps(result, indent=2) + '\n'
        (EVIDENCE_ROOT / name).write_text(serialized)
        print(name)
        print(serialized, end='')


if __name__ == '__main__':
    main()
