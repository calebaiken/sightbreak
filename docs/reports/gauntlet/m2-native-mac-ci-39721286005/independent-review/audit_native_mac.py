#!/usr/bin/env python3
"""Audit raw native log phase lines and optional feature draw traces."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from PIL import Image

ERROR = re.compile(r'^(?:SCRIPT ERROR|ERROR:)|Parse Error|ObjectDB.*leaked|Leaked instance', re.M)
DRAW = re.compile(r'^RENDER_DIAG phase=drawn frame=(\d+) case=(\S+) msec=(\d+) draws=(\d+(?:\.\d+)?) primitives=(\d+(?:\.\d+)?)$', re.M)


def inspect_group(directory, qa, feature=False):
    report = json.loads((directory / 'results.json').read_text())
    trials = []
    for recorded in report['trials']:
        name = recorded['label']
        log = (directory / (name + '.log')).read_text()
        result = {key: recorded.get(key) for key in ('label','passed','native_exit_code','timed_out','elapsed_before_cleanup','elapsed_total','surviving_owned_group','clean_log','marker_observed')}
        result['independent_log_clean'] = ERROR.search(log) is None
        result['renderer_lines'] = [line for line in log.splitlines() if any(word in line for word in ('OpenGL','Vulkan','Metal','ANGLE','Renderer'))]
        result['phase_lines'] = [line for line in log.splitlines() if any(word in line for word in ('MINIMAL_DIAG_','SIGHTBREAK_MAIN_READY','SIGHTBREAK_STARTUP','RENDER_DIAG'))]
        assert result['independent_log_clean'] == recorded['clean_log']
        result['samples'] = []
        for p in sorted(directory.glob(name+'-*.sample.txt')):
            sample = p.read_text()
            result['samples'].append({'path':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'software_draw_lines':[line.strip() for line in sample.splitlines() if any(term in line for term in ('glDrawElementsInstanced','gldRenderFillTriangles','fragment_shader','fragment_execute'))][:30]})
        if feature:
            frames = [{'frame':int(n),'case':c,'msec':int(t),'draws':float(d),'primitives':float(p)} for n,c,t,d,p in DRAW.findall(log)]
            complete = ([x['frame'] for x in frames] == list(range(1,16)) and all(x['case']==name for x in frames) and all(a['msec']<=b['msec'] for a,b in zip(frames,frames[1:])))
            result.update(independent_draw_trace=frames,independent_trace_complete=complete)
            assert frames == recorded['draw_trace']
            assert complete == recorded['trace_complete']
        capture = qa / (name + '.png')
        result['decoded_capture'] = None
        if capture.exists():
            with Image.open(capture) as im:
                im.load()
                result['decoded_capture'] = {'size':list(im.size),'format':im.format,'sha256':hashlib.sha256(capture.read_bytes()).hexdigest()}
                assert im.format=='PNG' and list(im.size)==[recorded['capture']['width'],recorded['capture']['height']]
                assert result['decoded_capture']['sha256']==recorded['capture']['sha256']
        trials.append(result)
    return {'status':report['status'],'exact_source_unchanged':report.get('exact_source_unchanged'),'source':report['source'],'trials':trials}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('evidence',type=Path)
    parser.add_argument('qa',type=Path)
    args = parser.parse_args()
    directory = args.evidence / 'macos-diagnostics'
    report={'startup':inspect_group(directory,args.qa/'macos-diagnostics')}
    feature = directory/'render-features'
    if (feature/'results.json').exists():
        report['render_features']=inspect_group(feature,args.qa/'macos-diagnostics/render-features',True)
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
