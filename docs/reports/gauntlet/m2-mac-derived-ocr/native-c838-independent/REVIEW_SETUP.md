# Review setup observations

The first `git add` of the new criteria path was rejected because the path had
not yet been added to this own sparse definition. I added only that report
directory to the sparse paths, then committed and pushed criteria `0abfd19`.
This changed no source, evidence or other checkout.

Before the runner supplied its run ID, a supported GitHub Fetch probe of the
workflow-scoped run collection URL returned HTTP 400: `GitHub Fetch URL is not
an allowed public GitHub repository or search endpoint`. I did not bypass the
wrapper or any denied host. After the runner supplied run `39920948579`, the
supported run URL, jobs tool and run-scoped jobs subresource succeeded.

The own criteria commit was authored at 07:52:43 UTC and pushed successfully
before the runner's dispatch. The actual run metadata records creation at
07:54:40 UTC. Root's selection and dispatch receipts remain owned by root;
the critic did not dispatch, alter or retry the run.

The first actual-file audit stopped while counting the later native suites:
its regex recognized `checks=590` but omitted the JSON spelling `"checks":590`.
The exact traceback remains in `audit-first-failure.txt`. I corrected only the
read-only auditor's count parser, then completed the original-file audit and
added the remaining deadline/ownership/cleanup checks. Original ZIPs, receipts,
native logs and source were unchanged. The final result is in `audit.json`.
