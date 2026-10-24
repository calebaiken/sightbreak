The initial static audit incorrectly compared all123 inherited methods (including
18 pre-edit model methods) to the legacy105 count. The initial assertion failed.
The second attempt separated the model but assumed all226 legacy assertion calls
were inside test methods:224 are inside methods and two are helper assertions.
That assertion also failed. audit_source-v1.py and audit_source-v2.py preserve
those auditor scripts; source-audit.stderr retains the second assertion traceback.
The corrected static audit verifies all123 method ASTs, all226 legacy assertion
call ASTs across their files, and all71 model assertion calls within18 methods.
This is an audit count-definition correction, no candidate/source change or test
success. Earlier literal tracer v1 retained only20 failure metadata records because
its callbacks missed subtests; both original raw stderr and134/44/1 summary were
correct. Registered v2 captures the final44 failures plus one error, byte-identical
1114-call trace hashes. No original record was replaced.

Read-only discovery also retained failed guessed test/Match/manifest filenames in
tool transcripts; exact sources used are test_input_consumption_foundation_enforcement.py,
game/scripts/gameplay/match.gd and the db954 Git manifest, respectively.
