"""Synthetic UI entry/worker probe; actual OCR child is CPython, never Tesseract."""
from contextlib import ExitStack
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch
import json
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import review_after as reviewed


def synthetic_main(supervised=False):
    out = Path(sys.argv[sys.argv.index("--output") + 1])
    case = out.parent
    root, executable = reviewed.original.create_export(case)
    pil = ModuleType("PIL")
    pil.Image = SimpleNamespace(open=lambda path: reviewed.original.FixtureCrop())
    actual_ocr = reviewed.offline.ocr_text
    def stalled_ocr(command, image, deadline, output):
        print("SYNTHETIC actual offline main reached stalled CPython OCR", flush=True)
        body = ("from pathlib import Path; import json,os,sys,time; "
                f"Path({str(case / 'ocr-child-pid.json')!r}).write_text(json.dumps({{'pid':os.getpid()}})); "
                "print('partial real CPython OCR stdout',flush=True); "
                "print('partial real CPython OCR stderr',file=sys.stderr,flush=True); time.sleep(30); "
                f"Path({str(case / 'ocr-child-finished.txt')!r}).write_text('finished')")
        return actual_ocr([sys.executable, "-B", "-c", body], image, deadline, output)
    with ExitStack() as stack:
        reviewed.original.fixture_boundaries(stack, reviewed.offline, case, root, executable)
        stack.enter_context(patch.dict(sys.modules, {"PIL": pil}))
        stack.enter_context(patch.object(reviewed.offline, "ocr_text", stalled_ocr))
        reviewed.offline.main(supervised=supervised)


if __name__ == "__main__":
    raise SystemExit(reviewed.flow.entry(synthetic_main, __file__))
