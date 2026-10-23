# One verbose bot-probe leak diagnostic

The original b87afb7 baseline reports two leaked ObjectDB instances. Its source,
raw output and strict rejection remain retained at 700abf8. The new diagnostic
asks only which object types and names appear in one verbose execution. Its
own output cannot retroactively identify the original leaked objects.

Use the exact original source in a clean separate checkout at b87afb7 and a
fresh staged project, private state and output. The reviewed controller diff
changes source location, diagnostic labels/provenance, and adds only --verbose
to the actual probe argv. Engine, import argv, fixture, seed, DT, every case,
positive control, clean/fresh guard and identity/group cleanup stay unchanged.
There is no audio-driver change. Import and probe each retain 120-second caps;
the wrapper retains 240 seconds plus the original bounded cleanup. Stop if the
import fails. Preserve all stdout, stderr, commands, hashes and PID receipts.

Native execution remains unreleased until the independent actual-output critic
reviews the concrete controller and command. Then root may run it exactly once.
The wrapper exit is a receipt-generation result, never a clean-native verdict.
Retain all warnings and typed leak records even if authority checks pass.
No product edit, policy selection, acceptance threshold or performance claim is
part of this diagnostic. The separate ARM WAV leak is independent evidence and
cannot identify this probe's objects.
