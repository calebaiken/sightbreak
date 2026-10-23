Created a new repository with `git init`, enabled sparse checkout, and fetched
the candidate with `--depth=1` from the local own source repository. The first
fetch used the abbreviated object name `525b17f1`; Git returned exit 128 with
`fatal: couldn't find remote ref 525b17f1` before checkout or test execution.
The successful fetch named the full source commit
`525b17f17fa8e1d500320198107553b42c9464ea`. Its checkout warned that the server
did not recognize filtering, then completed successfully; no checks were skipped.

`depth-one-identity.json` records one reachable commit, shallow=true, clean
status, and absence of the original `ec6b34ce` commit object with lazy fetching
disabled. The tests use directly retained original bytes and need no history.
All source and pure-test commands ran on CPU 4; no Godot or native process ran.
