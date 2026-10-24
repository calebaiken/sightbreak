import json, sys, time
from pathlib import Path
out = Path(sys.argv[sys.argv.index("--output") + 1])
print("synthetic CPython worker", flush=True)
print("ERROR: adversarial native error", flush=True)
(out / "results.json").write_text(json.dumps({"passed": True}))
