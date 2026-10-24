# Arithmetic unit-input correction before execution

The first committed test draft7754cd16 was inspected before execution. Its
last nearest-defender assertion scored a dead candidate, which cannot enter
the source's eligible set. The corrected unit inputs keep candidates living,
use positions consistent with their supplied10m/20m/1m distances, and check the
next living nearest defender after the prior one dies. No old control, output
or production behavior changed. These are scalar-arithmetic unit inputs, not
claimed full engine frames or line-of-sight evidence. FOV remains blocking.

The first actual27-method run at2f2c4ac8 has one retained failure: the initial
nominal nearest defender inherited alive=false from pose122, so source correctly
gave no defuser bonus. Minimum correction explicitly makes actors used in these
arithmetic-only positive inputs alive/healthy. The exact failed test/output/source
remain preserved; scoring code and historical controls do not change.
