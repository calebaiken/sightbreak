"""Compare original full QA files to bounded receipts and inspect PNG integrity."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(bounded, full):
    evidence = bounded / 'evidence'
    files = sorted(path for path in evidence.rglob('*') if path.is_file())
    missing = []
    mismatches = []
    for path in files:
        relative = path.relative_to(evidence)
        other = full / relative
        if not other.is_file():
            missing.append(relative.as_posix())
        elif path.read_bytes() != other.read_bytes():
            mismatches.append(relative.as_posix())
    images = []
    failures = []
    for path in sorted(full.rglob('*.png')):
        relative = path.relative_to(full).as_posix()
        try:
            with Image.open(path) as image:
                dimensions = list(image.size)
                image.verify()
            images.append({'path': relative, 'bytes': path.stat().st_size,
                           'sha256': digest(path), 'dimensions': dimensions})
        except Exception as error:
            failures.append({'path': relative, 'error': str(error)})
    return {'bounded_files': len(files), 'all_match_full_QA': not missing and not mismatches,
            'missing': missing, 'mismatches': mismatches, 'PNGs': images,
            'all_original_PNGs_pass_integrity_check': not failures,
            'PNG_integrity_failures': failures,
            'scope': 'Byte comparison and image decoding only; no OCR or native rendering.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bounded', type=Path)
    parser.add_argument('full', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.bounded, args.full)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'bounded_files': result['bounded_files'],
                      'all_match_full_QA': result['all_match_full_QA'],
                      'PNG_count': len(result['PNGs']),
                      'all_original_PNGs_pass_integrity_check': result['all_original_PNGs_pass_integrity_check']}))
