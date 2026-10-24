# Individual retained events

All references bind exactb5a3; details/actual reports/original tracebacks and full method hashes are in CLASSIFICATION.json. No new reader/model/test executed.

| # | Original test/subcase | Actual selected result | Classification / first source fact |
| --- | --- | --- | --- |
| 0 | test_missing_legacy_connected_foundation_stays_unknown_then_later_invalid | INVALID | historical-expiry-target-conflict |
| 1 | test_new_positive_lifecycle_projection_and_old_helper_unchanged | no reader call | legacy-reference-current-reader-target-conflict |
| 2 | test_definite_prefix_faults_are_not_hidden_by_unknown_lifecycle | INVALID | source-impossible-control-permitted-proposal-unapplied; fully-acknowledged-accept |
| 3 | test_known_schema_valid_source_negatives_are_frozen_as_preedit_false_completes (id='connected/missing-age') | INVALID | historical-preedit-target |
| 4 | test_known_schema_valid_source_negatives_are_frozen_as_preedit_false_completes (id='connected/wrong-sum') | INVALID | historical-preedit-target |
| 5 | test_known_schema_valid_source_negatives_are_frozen_as_preedit_false_completes (id='connected/joined-before-admission') | INVALID | historical-preedit-target |
| 6 | test_known_schema_valid_source_negatives_are_frozen_as_preedit_false_completes (id='generation/skipped-first') | INVALID | historical-preedit-target |
| 7 | test_known_schema_valid_source_negatives_are_frozen_as_preedit_false_completes (id='bound/future-last') | INVALID | historical-preedit-target |
| 8 | test_known_schema_valid_source_negatives_are_frozen_as_preedit_false_completes (id='received/invented-active') | INVALID | historical-preedit-target |
| 9 | test_known_schema_valid_source_negatives_are_frozen_as_preedit_false_completes (id='tick/future-rejection') | INVALID | historical-preedit-target |
| 10 | test_known_schema_valid_source_negatives_are_frozen_as_preedit_false_completes (id='tick/joined-lost') | INVALID | historical-preedit-target |
| 11 | test_minimal_authority_delta_preserves_original_whole_rows_and_other_fields | no reader call | historical-preedit-target |
| 12 | test_preedit_reader_false_complete_baseline_and_versioned_positive_are_separate | CONSISTENT | historical-preedit-target |
| 13 | test_old_generation_or_actor_alias_cannot_qualify_current_consumption | INVALID | negative-message-priority-conflict; persistent-metadata-counter-contradiction |
| 14 | test_fresh_peer_needs_acceptance_progress_but_not_a_direct_accept_row | INVALID | source-impossible-derived-construction; row8 age+remaining=13000≠20000 |
| 15 | test_queued_duplicate_accepts_without_queue_growth_or_command_replacement | INVALID | source-impossible-derived-construction; row6 D24000 implies future reject23500>now10000 |
| 16 | test_empty_array_has_no_endpoints_but_nondictionaries_are_observable (count=0, first=-1, last=-1) | INVALID | source-impossible-derived-construction; row5 D22500 implies future reject22000>now8500 |
| 17 | test_empty_array_has_no_endpoints_but_nondictionaries_are_observable (count=2, first=-1, last=-1) | INVALID | source-impossible-derived-construction; row5 D22500 implies future reject22000>now8500 |
| 18 | test_hidden_metadata_calls_stay_inside_observed_time_interval (offset=0) | INVALID | source-impossible-derived-construction; row8 D23000 implies future reject22500>now12000 |
| 19 | test_hidden_metadata_calls_stay_inside_observed_time_interval (offset=500) | INVALID | source-impossible-derived-construction; row8 D23000 implies future reject22500>now12000 |
| 20 | test_hidden_metadata_calls_stay_inside_observed_time_interval (offset=1000) | INVALID | source-impossible-derived-construction; row8 D23000 implies future reject22500>now12000 |
| 21 | test_live_binding_round_epoch_change_keeps_rejection_state | INVALID | source-impossible-derived-construction; row5 D22500 implies future reject22000>now8500 |
| 22 | test_only_fully_exposed_batches_need_a_fresh_endpoint (first=2, last=1, count=2) | INVALID | source-impossible-derived-construction; row8 D23000 implies future reject22500>now12000 |
| 23 | test_only_fully_exposed_batches_need_a_fresh_endpoint (first=2, last=2, count=2) | INVALID | source-impossible-derived-construction; row8 D23000 implies future reject22500>now12000 |
| 24 | test_only_fully_exposed_batches_need_a_fresh_endpoint (first=1, last=1, count=3) | INVALID | source-impossible-derived-construction; row8 D23000 implies future reject22500>now12000 |
| 25 | test_queue_window_bound_includes_valid_full_queue_and_later_ticks | INVALID | source-impossible-derived-construction; row24 D22001 implies future reject21501>now3001 |
| 26 | test_rejection_state_and_calls_agree_in_both_directions | INVALID | source-impossible-derived-construction; row5 D22500 implies future reject22000>now8500 |
| 27 | test_single_command_is_fresh_and_inside_ack_window (sequence=2) | INVALID | source-impossible-derived-construction; row8 D23000 implies future reject22500>now12000 |
| 28 | test_single_command_is_fresh_and_inside_ack_window (sequence=121) | INVALID | source-impossible-derived-construction; row8 D23000 implies future reject22500>now12000 |
| 29 | test_unchanged_metadata_can_remain_older_than_current_interval | INVALID | source-impossible-derived-construction; row8 D23000 implies future reject22500>now12000 |
| 30 | test_zero_peer_lobby_reset_retains_history_and_allows_new_rejections | INVALID | source-impossible-derived-construction; row5 D22500 implies future reject22000>now8500 |
| 31 | test_delayed_selected_stream_uses_its_owned_header_not_global_latest | INVALID | source-impossible-derived-construction; row8 age+remaining=13000≠20000 |
| 32 | test_epoch_boundary_uses_acceptance_epoch_and_preserves_new_receipts (accepted_epoch=1, queued=0) | INVALID | source-impossible-derived-construction; row8 D23000 implies future reject22500>now12000 |
| 33 | test_epoch_boundary_uses_acceptance_epoch_and_preserves_new_receipts (accepted_epoch=2, queued=1) | INVALID | source-impossible-derived-construction; row8 D23000 implies future reject22500>now12000 |
| 34 | test_explicit_unselected_pop_is_inferred_when_prior_state_proves_it | INVALID | source-impossible-derived-construction; row8 D23000 implies future reject22500>now12000 |
| 35 | test_exposed_queue_pops_oldest_instead_of_latest_accepted_packet | INVALID | source-impossible-derived-construction; row8 D22001 implies future reject21501>now9001 |
| 36 | test_hidden_accept_before_hidden_pop_uses_pre_pop_ack_interval | INVALID | source-impossible-derived-construction; row8 D23000 implies future reject22500>now12000 |
| 37 | test_large_duplicate_batch_cannot_erase_earlier_immutable_intent | INVALID | source-impossible-derived-construction; row6 D23000 implies future reject22500>now10000 |
| 38 | test_multi_peer_forced_flow_passes_but_ambiguous_header_is_unknown | INVALID | source-impossible-derived-construction; row8 age+remaining=13000≠20000 |
| 39 | test_receipt_aggregate_retains_one_joint_payload_history_across_pops (total=1, first=False, second=True, hidden=False) | INVALID | source-impossible-derived-construction; row6 D22001 implies future reject21501>now9001 |
| 40 | test_receipt_aggregate_retains_one_joint_payload_history_across_pops (total=0, first=False, second=False, hidden=True) | INVALID | source-impossible-derived-construction; row6 D22001 implies future reject21501>now9001 |
| 41 | test_receipt_aggregate_retains_one_joint_payload_history_across_pops (total=2, first=True, second=True, hidden=True) | INVALID | source-impossible-derived-construction; row6 D22001 implies future reject21501>now9001 |
| 42 | test_same_stream_ack_and_queue_need_corresponding_calls | INVALID | source-impossible-derived-construction; row8 D23000 implies future reject22500>now12000 |
| 43 | test_shared_accepted_validation_covers_hidden_calls (sequence=2, count=1, epoch=1) | INVALID | source-impossible-derived-construction; row8 D23000 implies future reject22500>now12000 |
| 44 | test_shared_accepted_validation_covers_hidden_calls (sequence=1, count=3, epoch=1) | INVALID | source-impossible-derived-construction; row8 D23000 implies future reject22500>now12000 |
| 45 | test_fresh_generation_after_retirement_can_reuse_peer_and_actor | raised ValueError | source-impossible-derived-construction; row8 D23000 implies future reject22500>now12000 |
