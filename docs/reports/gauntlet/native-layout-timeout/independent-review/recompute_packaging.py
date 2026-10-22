#!/usr/bin/env python3
"""Review retained ZIP bytes against named native evidence; no OCR or rendering."""
import gzip
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'scripts'))
from package_qa_receipts import package


def digest(value):
    return hashlib.sha256(value).hexdigest()


def main():
    report = {'scope': 'Byte-fidelity packaging review only; no PNG aesthetics, OCR or new native generation.',
              'packager_commit': 'a9961a6d8566dbc7aa3f11a8900b72b60ffa0662', 'archives': [], 'ci_receipts': []}
    evidence = ROOT / 'docs/reports/gauntlet/native-layout-ocr/native-four-size-r1'
    native_manifest = json.loads((evidence / 'evidence.json').read_text())
    identities = {item['retained']: item for item in native_manifest['retained']}
    published = json.loads((ROOT / 'docs/reports/gauntlet/native-layout-timeout/PNG_PACKAGING.json').read_text())
    for item in published['reports']:
        archive_path = Path(item['archive'])
        raw_archive = archive_path.read_bytes()
        size = archive_path.stem
        source = evidence / size
        expected = {path.relative_to(source).as_posix(): path for path in source.rglob('*.png')}
        with zipfile.ZipFile(archive_path) as bundle:
            names = bundle.namelist()
            assert len(names) == len(set(names)), 'Duplicate ZIP entry'
            index = json.loads(bundle.read('qa-receipts-index.json'))
            entries = index['files']
            assert len(entries) == len({entry['path'] for entry in entries})
            assert {entry['path'] for entry in entries} == set(expected)
            assert set(names) == {'qa-receipts-index.json'} | {entry['archive_path'] for entry in entries}
            assert index['max_archive_bytes'] == 30 * 1024 * 1024
            for entry in entries:
                path = expected[entry['path']]
                value = bundle.read(entry['archive_path'])
                assert entry['archive_path'] == 'evidence/' + entry['path']
                assert entry['bytes'] == len(value) == path.stat().st_size
                assert digest(value) == entry['sha256'] == digest(path.read_bytes())
                assert identities[size + '/' + entry['path']]['original_sha256'] == digest(value)
            assert bundle.testzip() is None
        assert len(raw_archive) == item['bytes'] < 30 * 1024 * 1024
        assert digest(raw_archive) == item['sha256']
        with tempfile.TemporaryDirectory(prefix='layout-independent-') as temporary:
            # The source path is embedded in the index, so use the builder's source
            # to compare deterministic archives without rewriting provenance.
            first, second = Path(temporary) / 'one.zip', Path(temporary) / 'two.zip'
            package(Path(index['source_directory']), first, layout_pngs=True)
            package(Path(index['source_directory']), second, layout_pngs=True)
            assert first.read_bytes() == second.read_bytes() == raw_archive
        report['archives'].append({'size': size, 'bytes': len(raw_archive), 'sha256': digest(raw_archive),
                                   'original_files': len(entries), 'complete_native_manifest_binding': True,
                                   'unique_members': True, 'deterministic_rebuild_identical': True})
    report['tested_image_source'] = native_manifest['tested_source']
    retained_ci = ROOT / 'docs/reports/gauntlet/native-layout-timeout/native-ci-39719407304'
    for entry in json.loads((retained_ci / 'index.json').read_text()):
        value = gzip.decompress((ROOT / entry['retained']).read_bytes())
        assert digest(value) == entry['original_sha256']
        assert value == Path(entry['original']).read_bytes()
        report['ci_receipts'].append({'path': entry['retained'], 'sha256': digest(value), 'bytes': len(value)})
    report['png_total'] = sum(entry['original_files'] for entry in report['archives'])
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
