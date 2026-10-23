#!/usr/bin/env python3
"""Run the critic's unchanged blocker expressions on old/new methods, no engine."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import types

REPORT=Path(__file__).resolve().parent
REPO=REPORT.parents[3]
sys.path.insert(0,str(REPO/"scripts"))
import analyze_touch_contrast_r4b as corrected
from test_touch_method_r4b import Ownership

original=REPORT/"retained-r4b-fresh-critic/checks.py"
text=original.read_text()
block=text[text.index("# BLOCKER:"):text.index('report["verdict"] =')]
old_bytes=subprocess.check_output(["git","-C",str(REPO),"show","2ea23f947aec6085449bced53c9b061618a67029:scripts/analyze_touch_contrast_r4b.py"])
old=types.ModuleType("rejected_touch_method")
old.__file__=str(REPO/"scripts/analyze_touch_contrast_r4b.py")
exec(compile(old_bytes,"rejected-exact-source","exec"),old.__dict__)


def run(method):
    findings={}
    def check(name,condition,**evidence):findings[name]={"condition":bool(condition),**evidence}
    namespace={"Ownership":Ownership,"method":method,"check":check}
    exec(compile(block,str(original)+":UNCHANGED_BLOCKER","exec"),namespace)
    return {"conditions":findings,"comparison_accepts_invalid_baseline":bool(namespace["false_accept"]),
        "false_zero_errors":namespace["ownership"]["errors"],"wrong_winner_errors":namespace["forged"]["errors"]}


rejected,now=run(old),run(corrected)
ok=(all(v["condition"] for v in rejected["conditions"].values()) and rejected["comparison_accepts_invalid_baseline"] and
    not now["comparison_accepts_invalid_baseline"] and bool(now["false_zero_errors"] and now["wrong_winner_errors"]))
result={"scope":"UNCHANGED INDEPENDENT FALSIFIER EXPRESSIONS, SYNTHETIC ONLY", "critic_commit":"ce3510e3776c8fec42ef1de648b14a453c221724",
    "original_falsifier_sha256":hashlib.sha256(original.read_bytes()).hexdigest(),"unchanged_blocker_sha256":hashlib.sha256(block.encode()).hexdigest(),
    "rejected_method_commit":"2ea23f947aec6085449bced53c9b061618a67029","rejected":rejected,"corrected":now,"correction_observed":bool(ok),"engine_invocations":0}
(REPORT/"r4b-r2-unchanged-falsifier-replay.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps({"correction_observed":bool(ok)}))
raise SystemExit(0 if ok else 1)
