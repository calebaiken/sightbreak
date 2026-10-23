# Complete frozen V2 regression

Source `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd`; **74/74 PASS**, clean at start and finish. Historical 64/70 evidence is unchanged.

The final two rows audit nested ObjectDB/playback leaks and frozen-source identity. Deliberate old-protocol handshake failures remain expected negative cases; staged historical source-tree logs are not new runtime output. See the independent final audit for diagnostic classification. This result does not erase separately retained failed attempts or the unexplained broad-wrapper cancellation baseline.

| Group | Result | Exit | Seconds | Raw evidence |
| --- | --- | ---: | ---: | --- |
| import | PASS | 0 | 7.943 | [import.log](import.log) |
| actor | PASS | 0 | 4.981 | [actor.log](actor.log) |
| world | PASS | 0 | 3.424 | [world.log](world.log) |
| hit-feedback | PASS | 0 | 3.574 | [hit-feedback.log](hit-feedback.log) |
| weapon-integrity | PASS | 0 | 8.586 | [weapon-integrity.log](weapon-integrity.log) |
| hit-volume | PASS | 0 | 7.584 | [hit-volume.log](hit-volume.log) |
| hit-history | PASS | 0 | 3.376 | [hit-history.log](hit-history.log) |
| render-budget | PASS | 0 | 3.878 | [render-budget.log](render-budget.log) |
| smoke-presentation | PASS | 0 | 3.675 | [smoke-presentation.log](smoke-presentation.log) |
| match | PASS | 0 | 3.928 | [match.log](match.log) |
| state-privacy | PASS | 0 | 3.676 | [state-privacy.log](state-privacy.log) |
| snapshot-buffer | PASS | 0 | 3.175 | [snapshot-buffer.log](snapshot-buffer.log) |
| input-stream | PASS | 0 | 3.275 | [input-stream.log](input-stream.log) |
| movement-replay | PASS | 0 | 9.244 | [movement-replay.log](movement-replay.log) |
| input-lifecycle | PASS | 0 | 6.982 | [input-lifecycle.log](input-lifecycle.log) |
| peer-lifecycle | PASS | 0 | 3.223 | [peer-lifecycle.log](peer-lifecycle.log) |
| result-outbox | PASS | 0 | 3.189 | [result-outbox.log](result-outbox.log) |
| reconnect-policy | PASS | 0 | 3.182 | [reconnect-policy.log](reconnect-policy.log) |
| reconnect-independent | PASS | 0 | 3.476 | [reconnect-independent.log](reconnect-independent.log) |
| resume-admission | PASS | 0 | 5.682 | [resume-admission.log](resume-admission.log) |
| lost-welcome | PASS | 0 | 4.079 | [lost-welcome.log](lost-welcome.log) |
| resume-alias | PASS | 0 | 4.841 | [resume-alias.log](resume-alias.log) |
| resume-auth-loss | PASS | 0 | 11.069 | [resume-auth-loss.log](resume-auth-loss.log) |
| bot-ai-regression | PASS | 0 | 4.865 | [bot-ai-regression.log](bot-ai-regression.log) |
| bots | PASS | 0 | 8.248 | [bots.log](bots.log) |
| bot-lifecycle | PASS | 0 | 99.194 | [bot-lifecycle.log](bot-lifecycle.log) |
| profile | PASS | 0 | 3.332 | [profile.log](profile.log) |
| touch | PASS | 0 | 3.33 | [touch.log](touch.log) |
| main | PASS | 0 | 4.535 | [main.log](main.log) |
| landscape | PASS | 0 | 163.557 | [landscape.log](landscape.log) |
| ux-contract | PASS | 0 | 25.653 | [ux-contract.log](ux-contract.log) |
| hud-overflow | PASS | 0 | 17.181 | [hud-overflow.log](hud-overflow.log) |
| economy-ui | PASS | 0 | 4.589 | [economy-ui.log](economy-ui.log) |
| armory-ui | PASS | 0 | 6.681 | [armory-ui.log](armory-ui.log) |
| armory-state | PASS | 0 | 13.068 | [armory-state.log](armory-state.log) |
| menu-state | PASS | 0 | 6.197 | [menu-state.log](menu-state.log) |
| economy-recovery | PASS | 0 | 3.381 | [economy-recovery.log](economy-recovery.log) |
| cosmetics | PASS | 0 | 3.475 | [cosmetics.log](cosmetics.log) |
| weapon-art | PASS | 0 | 4.076 | [weapon-art.log](weapon-art.log) |
| integration-actor-lifecycle | PASS | 0 | 4.026 | [integration-actor-lifecycle.log](integration-actor-lifecycle.log) |
| reload-sequence | PASS | 0 | 5.781 | [reload-sequence.log](reload-sequence.log) |
| reload-audio | PASS | 0 | 3.775 | [reload-audio.log](reload-audio.log) |
| reload-audio-capture | PASS | 0 | 7.034 | [reload-audio-capture.log](reload-audio-capture.log) |
| reload-audio-cancel | PASS | 0 | 7.084 | [reload-audio-cancel.log](reload-audio-cancel.log) |
| reload-audio-shot | PASS | 0 | 7.139 | [reload-audio-shot.log](reload-audio-shot.log) |
| reload-visibility | PASS | 0 | 145.834 | [reload-visibility.log](reload-visibility.log) |
| reload-finish-sunlit | PASS | 0 | 78.042 | [reload-finish-sunlit.log](reload-finish-sunlit.log) |
| reload-finish-shade | PASS | 0 | 83.568 | [reload-finish-shade.log](reload-finish-shade.log) |
| viewmodel-light | PASS | 0 | 68.28 | [viewmodel-light.log](viewmodel-light.log) |
| reload-finish-skin | PASS | 0 | 68.132 | [reload-finish-skin.log](reload-finish-skin.log) |
| account-output-unit | PASS | 0 | 0.114 | [account-output-unit.log](account-output-unit.log) |
| worker-unit | PASS | 0 | 0.766 | [worker-unit.log](worker-unit.log) |
| network | PASS | 0 | 10.841 | [network.log](network.log) |
| network-soak | PASS | 0 | 67.445 | [network-soak.log](network-soak.log) |
| network-soak-ten | PASS | 0 | 67.475 | [network-soak-ten.log](network-soak-ten.log) |
| connection-lifecycle | PASS | 0 | 46.545 | [connection-lifecycle.log](connection-lifecycle.log) |
| bridge-transport | PASS | 0 | 10.417 | [bridge-transport.log](bridge-transport.log) |
| build-manifest | PASS | 0 | 0.17 | [build-manifest.log](build-manifest.log) |
| reload-contact | PASS | 0 | 0.032 | [reload-contact.log](reload-contact.log) |
| protocol-matrix | PASS | 0 | 215.541 | [protocol-matrix.log](protocol-matrix.log) |
| hostile-handshake | PASS | 0 | 101.56 | [hostile-handshake.log](hostile-handshake.log) |
| catalog-fixture | PASS | 0 | 0.616 | [catalog-fixture.log](catalog-fixture.log) |
| postgresql | PASS | 0 | 5.338 | [postgresql.log](postgresql.log) |
| account-protocol | PASS | 0 | 23.727 | [account-protocol.log](account-protocol.log) |
| account-capacity | PASS | 0 | 20.628 | [account-capacity.log](account-capacity.log) |
| outbox-crash | PASS | 0 | 7.998 | [outbox-crash.log](outbox-crash.log) |
| native-economy | PASS | 0 | 8.637 | [native-economy.log](native-economy.log) |
| account-full-reconnect | PASS | 0 | 35.664 | [account-full-reconnect.log](account-full-reconnect.log) |
| economy-conservation | PASS | 0 | 0.867 | [economy-conservation.log](economy-conservation.log) |
| native-render-lifecycle | PASS | 0 | 56.069 | [native-render-lifecycle.log](native-render-lifecycle.log) |
| native-hud-overflow | PASS | 0 | 197.034 | [native-hud-overflow.log](native-hud-overflow.log) |
| native-paint-visibility | PASS | 0 | 16.221 | [native-paint-visibility.log](native-paint-visibility.log) |
| nested-resource-cleanup | PASS | audit | — | [nested-resource-cleanup.json](nested-resource-cleanup.json) |
| frozen-source-identity | PASS | audit | — | [source-identity.json](source-identity.json) |

Each execution row in [summary.json](summary.json) includes its exact source commit and command. All retained .log files, including child/userdata logs, remain alongside their records.
