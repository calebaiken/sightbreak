# Late owned-window ambiguity correction

The independent rejection at `bfe7b5a` applies to source `01464976ab77bd446265a848e9f3b56560af27d1`. Its exact report, raw controls and three counterexamples are retained in `rejected-review/`, indexed by SHA-256. These are pure source counterexamples; actual ARM run `39906639650` remains a separate failed native attempt.

Before changing runtime source, replay the independent controls byte-for-byte against the rejected source. Correct only the owned-visible-window selection predicate: startup discovery, fresh post-focus pin validation and every later window/input guard must require exactly one currently visible layer-zero window with the selected PID, and that unique window must retain the selected ID and original bounds. The complete current rows must be traced before rejection. A hidden or foreign extra row must not count as another owned visible window.

Keep the existing zero-event barrier, one permanent pin, one menu deadline of 60 seconds, one focus budget of five seconds, inherited half-point bounds tolerance, selected ID/bounds and every gameplay/cleanup budget unchanged. No runtime helper, original strict journey, game or workflow change is planned.

Add pure actual-method positive and negative controls for unique selection, late ambiguity at pin and after pin, hidden/foreign rows and invalid visibility. Replay the independent controls unchanged, including their full synthetic Deploy falsifier. Preserve all raw commands/results and original failures, run the maintained pure suites and aliased-temp controls, then freeze source for independent review. No native API/input, engine, OCR, export or CI dispatch is authorized here.
