"""Unchanged eight-family replay with the previously registered route seam."""
import ast
import importlib.util
import math
from pathlib import Path

REPORT=Path(__file__).resolve().parent


def main():
    spec=importlib.util.spec_from_file_location('v3_original_controls',REPORT/'consumer_controls.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    tree=ast.parse((module.ROOT/'scripts/native_settings_route.py').read_bytes())
    constants={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('SETTINGS_COVER','SETTINGS_SPAWN')}
    assert constants==dict(SETTINGS_COVER=(-7.8,-21.0),SETTINGS_SPAWN=(-4.4,-21.0));module.source_scope.update(constants)
    original=module.source_scope['key_pulse']
    def pulse(*args,**kwargs):
        sleep=kwargs['sleep'];calls=0
        def bounded(seconds):
            nonlocal calls
            calls+=1
            if calls>32:raise AssertionError('bounded fake pulse exceeded32 sleeps')
            sleep(math.ceil(seconds*10**9)/10**9)
        kwargs['sleep']=bounded;return original(*args,**kwargs)
    module.source_scope['key_pulse']=pulse
    return module.main()


if __name__=='__main__':raise SystemExit(main())
