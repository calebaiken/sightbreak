The first new publication matrix used non-JSON warning bytes to corrupt
`outputs.json`. Acquisition correctly rejected each change, but the unchanged
independent helper then tried to parse that rejected manifest for its result
summary. Five subtests ended in helper JSONDecodeError, so that run is retained
as harness errors, not passing evidence. The maintained correction uses valid
`{}` bytes for JSON mutations, allowing the helper to inspect the rejected raw
package. Neither acquisition source nor its gates changed to fix this harness.
