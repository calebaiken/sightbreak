class_name SBReloadPhases
extends RefCounted
## The authored reload, as fractions of its length: the ONE place its timing is written down.
## tools/art/arms_build.py reads this file (the `const NAME := number` lines) when it keys the
## arms' clip, actor.gd poses and times the presentation from these names, and the tests check
## the imported clip against them by measuring it. Presentation only: the authoritative reload
## (ammunition, completion) is Actor.reload_remaining and never reads these numbers.
##
##   0.00 - REACH     the support hand leaves the handguard and comes up under the magazine
##   REACH - GRASP    the fingers close on the seated magazine
##   GRASP - UNLATCH  the hand takes the weight; at UNLATCH the latch lets go (release click)
##   UNLATCH - CLEAR  the old magazine slides out along its own well and clears it
##   CLEAR - DROP     it swings out to the left; at DROP the fingers open and it is let go
##   DROP - ACQUIRE   the empty hand goes to the left and a little down (it stays in the frame); there is
##                    no pouch to show, so the replacement comes up out of the closing hand (below)
##   ACQUIRE - FETCH  from FETCH before ACQUIRE the replacement rises out of the palm as the fingers close
##   at ACQUIRE       the fingers close on the REPLACEMENT magazine (a second mesh)
##   ACQUIRE - ALIGN  the replacement is brought up into view and lined up under the well
##   ALIGN - ENTER    its top enters the well
##   ENTER - SEAT     it is pushed home; at SEAT it is seated (seat click, the same instant)
##   SEAT - LETGO     the hand stays closed on the seated magazine
##   LETGO - 1.0      the fingers open and the hand returns to the handguard
## The numbers below are the whole definition; keep each on its own `const NAME := number` line.
const REACH := 0.14
const GRASP := 0.20
const UNLATCH := 0.24
const CLEAR := 0.32
const DROP := 0.38
const ACQUIRE := 0.56
const ALIGN := 0.68
const ENTER := 0.74
const SEAT := 0.80
const LETGO := 0.85
## How long before ACQUIRE the replacement starts to come up out of the hand.
const FETCH := 0.08

## Presentation events, in order, and the phase each fires at. The audio follows the VISIBLE
## animation (the presentation clock), so a click lands on the frame the part moves.
const EVENTS := [["unlatch", UNLATCH], ["seat", SEAT]]

## The visual progress (0 to 1) of a reload from the presentation clock's remaining seconds.
static func progress(remaining: float, duration: float) -> float:
	return 1.0 - clampf(remaining / maxf(duration, 0.1), 0.0, 1.0)

## The events whose phase lies in (previous, current]: what the presentation clock crossed
## this tick. A jump forward crosses each event once; going backwards crosses none.
static func crossed(previous: float, current: float) -> Array[String]:
	var out: Array[String] = []
	if current <= previous:
		return out
	for event in EVENTS:
		# A hair of tolerance: a progress that is 0.8 to within float rounding has crossed 0.8.
		if previous + 1e-6 < float(event[1]) and current + 1e-6 >= float(event[1]):
			out.append(str(event[0]))
	return out
