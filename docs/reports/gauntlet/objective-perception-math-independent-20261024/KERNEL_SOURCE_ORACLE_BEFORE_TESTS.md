# Pinned kernel oracle recorded before math tests

Named source is Godot ed1daf0bf. All excerpts were fetched/preserved by research
fb5953c217c8a4112c9296334c65a9e1b95d0388; this reviewer read the retained exact
source excerpts, not a different version or model's description.

- core/variant/variant_utility.cpp43–49 sin/cos accepts/returns double through Math.
- core/math/math_funcs.h41–52 delegates double and float overloads to std libm.
- core/math/vector3.h63–73 stores real_t components; constructor226–227 converts
  scalars. Default single source configuration does not prove actual binary build.
- vector3.h405–407 subtracts stored Vector3 components and constructs a Vector3.
- vector3.h532–545 computes real_t x*x,y*y,z*z then their sum. normalize548–565
  first handles nonfinite input, computes length_squared, tests exact zero, takes
  real_t sqrt, then DIVIDES each x/y/z by that length. It does not first form a
  rounded reciprocal. normalized568–571 copies the vector then invokes normalize.
- vector3.h252–254 dot is the real_t sum of component products. The C++ expression
  alone does not prove compiled FMA/contraction, host rounding mode or libm error.
- Game bot_ai.gd361,377–379 constructs facing=(-sin(yaw),0,-cos(yaw)), normalizes
  full3D enemy-actor displacement, and compares dot>double fov_dot. Profile cutoffs
  are-.05,-.15,-.25. The recent-specific-attacker exception is separate. No LOS,
  scores, memory, reaction, team reports, ray casts or gameplay mutation is needed
  for this isolated numerical primitive acquisition.

The tiny native probe must use the actual Vector3 expressions as the reference.
A source-faithful explicit-f32 shadow must preserve division and intermediate
rounding, but even then remains a diagnostic model without a compiled error bound.
Exact-axis/equality/zero controls can expose semantic mistakes. Neighbor input
cases do not establish which side of a fractional cutoff the native dot reaches.
Only the actual case-specific native outputs can resolve those frozen cases;
portable inference beyond the measured table remains unverified.
