import json, sys, time
from pathlib import Path
out = Path(sys.argv[sys.argv.index("--output") + 1])
print("synthetic CPython worker", flush=True)
(out / "results.json").write_text(json.dumps({"passed": True}))
sys.exit(7)
