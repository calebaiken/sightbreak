# M1 native-window lifetime criteria

Declared before implementation on base `561d0cbba651514bfac96c50437a849d65843545`.
Builder: `/root/branch_recon`. Independent acceptance is assigned by the mission
coordinator to a separate critic; the builder cannot close that gate.

The reference is the actual Linux layout failure in [Actions run 39678945538](https://github.com/calebaiken/sightbreak/actions/runs/39678945538),
job `119496049540`, tested source `d6784ab2d81dae204b6a699f0177f7e9d70bec4e`.
After a successful 960×540 case, the 1280×720 case saved its menu and Python exited
on Xlib `BadWindow`, request 20 (`X_GetProperty`), resource `0x600003`.
The actual source and raw QA artifact were inspected. Linux QA artifact
`12384822538` has SHA-256 `ffd4272f3219c166a52531bd15b2be56d5db3b661baaba51b80c174347ac0f71`.

The engineering comparison runs the baseline and candidate against the same real
Xvfb windows. Destroying a window between enumeration and its name/geometry/focus
request must leave the controller alive and prevent a false focus/geometry result.
No shipped-game visual comparison applies to this native-controller component.

| Component | Required result |
| --- | --- |
| Candidate discovery | Real destruction after child enumeration is recoverable; another legitimate named window remains discoverable. |
| Focus lifetime | Destruction before focus returns false and clears the stale target. Focus is confirmed from the server, not merely from `XFlush`. |
| Diagnostics | A destroyed cached target cannot remain reported focused or trigger the default fatal Xlib handler. |
| Geometry and close | Destroyed windows produce Python failures so caller cleanup can run. Geometry bounds and advertised-close requirements remain enforced. |
| Error boundaries | Unrelated native errors remain Python failures with protocol details. The previous process-wide error handler is restored after successful and failed operations. |
| Positive control | The largest matching real window receives focus; unrelated windows are ignored; a legitimate close request remains available. |
| Resource/performance | Child cases finish within 10 seconds each. A repeated tiny-window query workload has a 5-second watchdog; record elapsed time without claiming game FPS. All created windows/connections and the owned Xvfb process are closed/reaped. |

Use display numbers at least 200 and tiny X windows to avoid competing with the
coordinator's gameplay render. Preserve baseline failures and candidate raw output.
No gameplay, package, visual-quality or platform release gate is accepted here.
The coordinator must repeat actual layout generation after integration.
