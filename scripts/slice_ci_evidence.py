#!/usr/bin/env python3
"""Republish byte-identical QA observations from a retained GitHub artifact.

Runs on GitHub only: no game execution, edits to observations, or qualification.
Each output directory stays below the managed artifact download size limit.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import zipfile


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def metadata(repository, endpoint):
    return json.loads(subprocess.check_output(
        ['gh', 'api', f'repos/{repository}/{endpoint}'], timeout=60))


def group_for(name):
    parts = PurePosixPath(name).parts
    if any(part in {'state', 'cache', 'shader_cache', '.godot'} for part in parts):
        return None
    if PurePosixPath(name).suffix.lower() not in {'.png', '.json', '.jsonl', '.log'}:
        return None
    if parts[0] == 'layouts':
        return 'layouts'
    if parts[0] == 'offline-full-match':
        return 'full-match'
    if parts[0] in {'offline-plant', 'offline-defuse'}:
        return 'objectives'
    if parts[0] in {'offline-input', 'native-input', 'verification', 'regressions'}:
        return 'other'
    return None


def slice_archive(archive, output, identity):
    require(not output.exists(), 'Use a new output directory')
    output.mkdir(parents=True)
    index = {**identity, 'original_archive_sha256': digest(archive), 'files': [],
             'excluded': [], 'method': 'Unchanged original ZIP entry bytes; no gameplay rerun or acceptance assertion'}
    sizes = {name: 0 for name in ['layouts', 'full-match', 'objectives', 'other']}
    with zipfile.ZipFile(archive) as source:
        seen = set()
        for info in source.infolist():
            name = info.filename
            path = PurePosixPath(name)
            require(not path.is_absolute() and '..' not in path.parts and '\\' not in name
                    and path.parts and name not in seen, 'Unsafe or duplicate original archive path')
            seen.add(name)
            require(not stat.S_ISLNK(info.external_attr >> 16), 'Symlink in original archive')
            if info.is_dir():
                continue
            group = group_for(name)
            if group is None:
                index['excluded'].append({'path': name, 'bytes': info.file_size})
                continue
            require(info.file_size <= 12 * 1024 * 1024, 'Individual observation exceeds bounded slice budget: ' + name)
            sizes[group] += info.file_size + 4096
            require(sizes[group] <= 28 * 1024 * 1024, 'Observation group exceeds 28 MiB upload budget: ' + group)
            content = source.read(info)  # ZIP CRC is verified; content is never transformed.
            target = output / group / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            index['files'].append({'path': name, 'group': group, 'bytes': len(content),
                                   'sha256': hashlib.sha256(content).hexdigest(),
                                   'original_zip_crc32': info.CRC})
    require(any(row['group'] == 'layouts' for row in index['files']), 'Missing original layout evidence')
    require(any(row['path'] == 'offline-full-match/results.json' for row in index['files']), 'Missing full-match receipt')
    index['group_budget_bytes'] = sizes
    encoded_index = json.dumps(index, indent=2) + '\n'
    for group in sizes:
        if (output / group).is_dir():
            require(sizes[group] + len(encoded_index.encode()) + 4096 <= 29 * 1024 * 1024,
                    'Observation group and index exceed bounded archive budget: ' + group)
            (output / group / 'slice-index.json').write_text(encoded_index)
    (output / 'index').mkdir()
    (output / 'index/slice-index.json').write_text(encoded_index)
    return index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', type=int, required=True)
    parser.add_argument('--artifact-id', type=int, required=True)
    parser.add_argument('--source-commit', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(os.environ.get('GITHUB_ACTIONS') == 'true', 'Download only inside the authorized GitHub workflow')
    repository = os.environ.get('GITHUB_REPOSITORY')
    require(repository == 'calebaiken/sightbreak', 'Unexpected repository')
    require(args.run_id > 0 and args.artifact_id > 0 and re.fullmatch('[0-9a-f]{40}', args.source_commit), 'Invalid source identity')
    run = metadata(repository, f'actions/runs/{args.run_id}')
    artifact = metadata(repository, f'actions/artifacts/{args.artifact_id}')
    require(run['head_sha'] == args.source_commit and run['status'] == 'completed', 'Source run is incomplete or has a different commit')
    require(artifact['workflow_run']['id'] == args.run_id
            and artifact['workflow_run']['head_sha'] == args.source_commit
            and artifact['name'].startswith('sightbreak-qa-') and not artifact['expired'], 'Artifact/source binding differs')
    require(0 < artifact['size_in_bytes'] <= 512 * 1024 * 1024, 'Original archive exceeds runner download budget')
    archive = args.output.parent / f'original-{args.artifact_id}.zip'
    require(not archive.exists(), 'Do not replace an earlier original archive')
    with archive.open('xb') as stream:
        subprocess.run(['gh', 'api', f'repos/{repository}/actions/artifacts/{args.artifact_id}/zip'],
                       stdout=stream, check=True, timeout=180)
    actual_digest = 'sha256:' + digest(archive)
    require(archive.stat().st_size == artifact['size_in_bytes'] and actual_digest == artifact['digest'], 'Original GitHub archive size/digest differs')
    index = slice_archive(archive, args.output, {
        'repository': repository, 'source_run_id': args.run_id, 'source_artifact_id': args.artifact_id,
        'source_artifact_name': artifact['name'], 'source_commit': args.source_commit,
        'original_archive_bytes': archive.stat().st_size, 'github_archive_digest': artifact['digest'],
        'diagnostic_run_id': os.environ['GITHUB_RUN_ID'], 'diagnostic_commit': os.environ['GITHUB_SHA']})
    print(json.dumps({key: index[key] for key in ['source_run_id', 'source_artifact_id', 'source_commit',
                                                'original_archive_sha256', 'group_budget_bytes']}, indent=2))


if __name__ == '__main__':
    main()
