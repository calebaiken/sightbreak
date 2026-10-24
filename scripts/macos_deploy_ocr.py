"""Bind one explicit derived Deploy analysis to unchanged native observations."""
import copy
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import re
import struct

PROFILE = 'sightbreak-deploy-full-window-2x-v1'
SCOPE = 'Derived analysis of the same native full-window pixels; no new capture or events'
LABEL = 'DEPLOY · OFFLINE 5V5'
BINDING = '_validated_deploy_analysis'


def png_dimensions(path):
    with Path(path).open('rb') as stream:
        header = stream.read(24)
    if (len(header) != 24 or header[:8] != b'\x89PNG\r\n\x1a\n'
            or header[8:16] != b'\x00\x00\x00\rIHDR'):
        raise RuntimeError('Retained native/analysis file lacks a PNG IHDR')
    dimensions = list(struct.unpack('>II', header[16:24]))
    if min(dimensions) <= 0:
        raise RuntimeError('Retained PNG dimensions are empty')
    return dimensions


def receipt_digest(capture):
    try:
        raw = {name: value for name, value in capture.items() if name != BINDING}
        return hashlib.sha256(json.dumps(raw, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    except (TypeError, ValueError) as error:
        raise RuntimeError('Native/derived receipt is not finite JSON') from error


@dataclass(frozen=True)
class DeployAnalysisBinding:
    receipt_sha256: str


def bind_analysis(capture, source_sha256, analysis_sha256, source_dimensions, analysis_dimensions):
    """Only the controller supplies actual file digests/dimensions, never JSON."""
    analysis = capture.get('derived_deploy_analysis')
    if (BINDING in capture or not isinstance(analysis, dict)
            or capture.get('passed') is not True
            or capture.get('scope') != 'OS window screenshot from ScreenCaptureKit; read-only helper'
            or capture.get('permissions', {}).get('CGPreflightScreenCaptureAccess') is not True):
        raise RuntimeError('Unbound or spoofed focused Deploy analysis')
    if (not all(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value)
                for value in (source_sha256, analysis_sha256))
            or not isinstance(source_dimensions, list) or len(source_dimensions) != 2
            or not all(type(value) is int and value > 0 for value in source_dimensions)):
        raise RuntimeError('Invalid retained Deploy image identity')
    width, height = source_dimensions
    expected = {'schema': 1, 'profile': PROFILE, 'scope': SCOPE,
                'source_png_sha256': source_sha256, 'analysis_png_sha256': analysis_sha256,
                'owner_pid': capture.get('owner_pid'), 'window_id': capture.get('window_id'),
                'bounds_points_including_chrome': capture.get('bounds_points_including_chrome'),
                'source_point_pixel_scale': capture.get('point_pixel_scale'),
                'source_image_dimensions': source_dimensions,
                'analysis_image_dimensions': [width*2, height*2],
                'source_crop_pixels_top_left': [0, 0, width, height], 'scale': 2,
                'normalized_box_space': 'native-full-window-bottom-left', 'resampling': 'CoreGraphics-high',
                'recognition_level': 'accurate', 'recognition_languages': ['en-US'],
                'uses_language_correction': False, 'custom_words': []}
    # Type-sensitive JSON equality also rejects boolean stand-ins for numbers.
    if (width*height > 4_194_304 or max(width*2, height*2) > 8192
            or not isinstance(analysis_dimensions, list)
            or not all(type(value) is int for value in analysis_dimensions)
            or analysis_dimensions != [width*2, height*2]
            or json.dumps(capture.get('image_dimensions')) != json.dumps(source_dimensions)
            or not isinstance(analysis.get('text'), list)
            or not isinstance(capture.get('text'), list)
            or not all(isinstance(row, dict) for row in capture['text']+analysis['text'])
            or any(type(capture.get(name)) is not int or capture[name] <= 0 for name in ('owner_pid', 'window_id'))):
        raise RuntimeError('Derived Deploy dimensions or ownership do not bind the native capture')
    for name, value in expected.items():
        if json.dumps(analysis.get(name), sort_keys=True) != json.dumps(value, sort_keys=True):
            raise RuntimeError('Derived Deploy provenance mismatch: '+name)
    capture[BINDING] = DeployAnalysisBinding(receipt_digest(capture))


def canonical_caption(text):
    if not isinstance(text, str):
        return None
    return ' '.join(text.upper().split()).replace('•', '·')


def valid_box(entry):
    box = entry.get('box_normalized_bottom_left')
    if (not isinstance(box, list) or len(box) != 4
            or not all(isinstance(value, (int, float)) and not isinstance(value, bool)
                       and math.isfinite(value) for value in box)
            or min(box[:2]) < 0 or min(box[2:]) <= 0
            or box[0]+box[2] > 1 or box[1]+box[3] > 1):
        raise RuntimeError('Deploy text box is outside the original native window')
    return box


def confident(entry, minimum):
    value = entry.get('confidence')
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and minimum <= value <= 1)


def derived_deploy_row(capture):
    binding = capture.get(BINDING)
    if (type(binding) is not DeployAnalysisBinding or binding.receipt_sha256 != receipt_digest(capture)):
        raise RuntimeError('Deploy analysis is unbound, spoofed or changed after validation')
    raw = [row for row in capture.get('text', []) if canonical_caption(row.get('text')) == LABEL]
    derived = [row for row in capture['derived_deploy_analysis']['text']
               if canonical_caption(row.get('text')) == LABEL]
    if len(raw) != 1 or len(derived) != 1 or not confident(raw[0], 0) or not confident(derived[0], .8):
        raise RuntimeError('Deploy requires unique native corroboration and one exact derived caption at confidence .8')
    native_box, analysis_box = valid_box(raw[0]), valid_box(derived[0])
    def center(box): return box[0]+box[2]/2, box[1]+box[3]/2
    def contains(box, point):
        return box[0] <= point[0] <= box[0]+box[2] and box[1] <= point[1] <= box[1]+box[3]
    if not contains(native_box, center(analysis_box)) or not contains(analysis_box, center(native_box)):
        raise RuntimeError('Derived Deploy caption does not agree at the original native target center')
    return copy.deepcopy(raw[0])


def deploy_provenance(capture):
    derived_deploy_row(capture)
    analysis = capture['derived_deploy_analysis']
    result = {name: copy.deepcopy(analysis[name]) for name in
            ('profile', 'source_png_sha256', 'analysis_png_sha256', 'source_image_dimensions',
             'analysis_image_dimensions', 'source_crop_pixels_top_left', 'source_point_pixel_scale', 'scale', 'normalized_box_space')}
    result['derived_caption'] = copy.deepcopy(next(row for row in analysis['text'] if canonical_caption(row.get('text')) == LABEL))
    return result
