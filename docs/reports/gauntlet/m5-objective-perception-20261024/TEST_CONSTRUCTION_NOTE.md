# Arithmetic unit-input correction before execution

The first committed test draft7754cd16 was inspected before execution. Its
last nearest-defender assertion scored a dead candidate, which cannot enter
the source's eligible set. The corrected unit inputs keep candidates living,
use positions consistent with their supplied10m/20m/1m distances, and check the
next living nearest defender after the prior one dies. No old control, output
or production behavior changed. These are scalar-arithmetic unit inputs, not
claimed full engine frames or line-of-sight evidence. FOV remains blocking.
