#!/usr/bin/env python3
"""Seal original official artifact bytes and extracted originals, read-only."""
import hashlib
import json
from pathlib import Path
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CACHE = ROOT / '.local/windows40080238905'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def files(directory):
    return {path.relative_to(directory).as_posix(): dict(bytes=path.stat().st_size, sha256=sha(path.read_bytes()))
            for path in sorted(directory.rglob('*')) if path.is_file()}


def archive(path, destination, expected_size, expected_sha):
    data = path.read_bytes()
    assert len(data) == expected_size and sha(data) == expected_sha
    retained = files(destination)
    rows = []
    with zipfile.ZipFile(path) as bundle:
        entries = bundle.infolist()
        assert all(not entry.is_dir() for entry in entries)
        assert len({entry.filename for entry in entries}) == len(entries)
        assert set(retained) == {entry.filename for entry in entries}
        for entry in entries:
            original = bundle.read(entry)
            actual = retained[entry.filename]
            assert len(original) == entry.file_size == actual['bytes']
            assert sha(original) == actual['sha256']
            rows.append(dict(path=entry.filename, **actual, crc32=entry.CRC))
    return dict(path=path.relative_to(HERE).as_posix() if path.is_relative_to(HERE) else str(path),
                bytes=len(data), sha256=sha(data), members=len(rows), original_members=rows,
                expanded_bytes=sum(row['bytes'] for row in rows))


def main():
    full = archive(HERE / 'archives/windows-qa-12555082704.zip', CACHE / 'full', 24246833,
                   '372a2f7fd36f5d9611fa6ab76e4649230605ff16298e31a9e121c8448b4820ec')
    outer = archive(HERE / 'archives/windows-qa-receipts-12555082698.zip', CACHE / 'outer-receipts', 24256655,
                    '6c2935a7e7fc952649f90f61b11979f0330836667bfe0bf51401f0fe8eaa9f78')
    inner = archive(CACHE / 'outer-receipts/qa-receipts.zip', CACHE / 'receipts', 24256511,
                    '93add77d07fca467150d5711815bd417fbb0fbccf276d712f05b5e0bf71ace01')
    index = json.loads((CACHE / 'receipts/qa-receipts-index.json').read_text())
    assert index['schema'] == 1 and index['max_archive_bytes'] == 30 * 1024 * 1024
    canonical = files(CACHE / 'receipts/evidence')
    full_files = files(CACHE / 'full')
    assert len(index['files']) == len(canonical) == 237
    assert len({row['path'] for row in index['files']}) == len(canonical)
    for row in index['files']:
        assert row['archive_path'] == 'evidence/' + row['path']
        actual = canonical[row['path']]
        assert actual == dict(bytes=row['bytes'], sha256=row['sha256']) == full_files[row['path']]
    extra = {name: value for name, value in full_files.items() if name not in canonical}
    assert len(extra) == 83 and all(name.endswith('.png') for name in extra)
    terminal = (HERE / 'job-log-final.log').read_bytes()
    early = (HERE / 'job-log-early.log').read_bytes()
    assert terminal.startswith(early) and len(terminal) == 2828610
    assert sha(terminal) == '55f80c8d1ae378c4f83301398f6345af9e5ccd6d34c42d24e63ace866ad2bb42'
    assert terminal.endswith(b'\r\n') and b'Cleaning up orphan processes' in terminal[-5000:]
    metadata = json.loads((HERE / 'artifacts-final-connector.json').read_text())['value']['structuredContent']['artifacts']
    large = next(row for row in metadata if row['id'] == 12554384657)
    assert large['size_in_bytes'] == 146423542 > 32 * 1024 * 1024
    report = dict(scope='Exact original archive/extraction/index/replica conservation after all read-only audits',
                  source='c32415148db1f110bbc7eadfca3793d4693429ff', run_id=40080238905, job_id=120832097220,
                  full_QA=full, outer_receipts=outer, inner_receipts=inner,
                  every_237_indexed_raw_file_matches_full_QA=True, extra_original_PNGs=extra,
                  terminal_decoded_job_log=dict(bytes=len(terminal), sha256=sha(terminal), early_is_exact_prefix=True),
                  known_oversized_artifact_not_requested=large,
                  signed_transfer_urls_published=False,
                  limits=['This seals retained files, not complete native event/process lifetimes.',
                          'Shared userdata log was already a mixed/truncated auxiliary sink when officially archived; canonical process stdout records remain separate.',
                          'Independent EXE/PE/PCK/embedded UID reparse remains blocked by the supported transfer cap.'])
    (HERE / 'retention-manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(full_members=full['members'], bounded_members=inner['members'], indexed_raw=237,
                          original_PNGs=len(extra), official_archives_verified=True,
                          both_archives_total_bytes=full['bytes'] + outer['bytes'], originals_unchanged=True)))


if __name__ == '__main__':
    main()
