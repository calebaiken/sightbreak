# Neutral first assessment — before mapping, source diff, or candidate claims

Native engine: `4.7.2.stable.official.ed1daf0bf`. Both completed editor imports were checked by the runner for exit status and logged script/resource errors before any test began. Tests are recovered byte-for-byte V2 scripts, identical for both labels.

## Initial observations

| Retained probe | north | south |
|---|---|---|
| `module_probe.gd` | Executes. Damage-facing input unchanged by damage; all sound profiles hear exact coordinates; easy 18 m range bypassed by a 20 m raw event; 3 blocked anchor positions reported. | Cannot parse: base class `RelayYard` missing. No valid behavior measurement. |
| `authority_contract_probe.gd` | Failed purchase preserves all observed resources. | Failed purchase preserves all observed resources. |
| `integration_controls.gd` | Executes all checks. Native actor fails to arrive at blocked anchor after 10 s; native movable-anchor control moves successfully. LOS, smoke, bounded memory, team reports, resource checks pass. | Cannot parse: base class `RelayYard` missing. No valid integration measurement. |
| `objective_controls.gd` | Plant and defuse complete authoritative timers; human-carrier site adaptation passes. | Cannot parse: arena class member unresolved and `SBBotAI.nearest_defender()` missing. |
| `native_comparison_extended.gd` | Long-running sweep launched; not yet used in this first assessment. | Cannot parse: `TacticalMatch` unresolved. |

## Assessment at this stage

- north demonstrably retains anchor-arrival, hearing-range, damage-facing, and sound-precision problems. Some retained checks expect a defect, so their `pass=true` is NOT a gameplay acceptance result.
- south is incompatible with the retained integrated V2 API as tested. An import-only success must not be represented as a successful match run or bot improvement.
- The standalone failed-purchase equipment check discriminates neither tree and passes on both.
- Do not select a behavioral winner based on south's missing metrics. Reveal the frozen mapping and inspect the exact source API next; preserve these parse failures rather than silently adapting/replacing tests.
- No candidate claims/reports, candidate diff, or sealed label mapping have been read before this assessment was authored.
