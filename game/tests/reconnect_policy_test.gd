extends SceneTree
var checks := 0
var failures := 0
func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		push_error(label)
func _initialize() -> void:
	var policy := SBReconnectPolicy.new()
	check(not policy.available(100), "new joins have no automatic recovery episode")
	policy.begin(100)
	check(policy.deadline == 20100 and policy.delay_seconds() == 2, "initial deadline and actual two-second path")
	for now in [200, 2000, 18000, 20099]:
		policy.begin(now)
		check(policy.deadline == 20100, "duplicate disconnect cannot extend window")
	check(policy.available(20099) and not policy.available(20100), "monotonic deadline is exclusive")
	for attempt in range(SBReconnectPolicy.MAX_ATTEMPTS):
		check(policy.take_attempt(100 + attempt), "bounded attempt accepted")
		check(policy.delay_seconds() >= 2 and policy.delay_seconds() <= 4, "backoff bounded")
	check(not policy.take_attempt(200) and policy.attempts == 5, "repeated transport failures cannot retry forever")
	policy.clear()
	check(policy.deadline == 0 and policy.attempts == 0, "welcome or terminal failure retires episode")
	policy.begin(30000)
	check(policy.deadline == 50000 and policy.take_attempt(30000), "later independent disconnect starts fresh episode")
	check(policy.attempt_started == 30000, "per-attempt timer is monotonic")
	print("RECONNECT_POLICY_TEST checks=%d failures=%d" % [checks, failures])
	quit(1 if failures else 0)
