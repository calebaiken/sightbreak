class_name SBReloadAudio
extends Node3D
## The sounds of a reload: a small pool of voices, so two sounds that land on the same tick (the seat clunk and the
## first shot, a pouch rustle over the tail of a slide) each get a voice of their own and none cuts another, and a
## table of original synthesized sounds, one per event of SBReloadPhases.EVENTS (two variants each, so a second
## reload is not the first one's recording played again).
##
## Presentation only. The actor decides WHEN (from the presentation clock; see Actor._fire_reload_cue, which also
## guarantees each event once per reload); this class decides which voice plays it, keeps a log of what played
## (for the tests and the audio capture) and stops everything when a reload is cancelled.
##
## No recorded samples: every sound is synthesized here from noise, resonances and envelopes, seeded, so the same
## build always plays the same bytes. They are a design, not a claim that they sound like a real rifle: nobody
## has listened to them yet (docs/art/VISUAL_QA.md says so too).
const VOICES := 4
const MIX_RATE := 22050
## Where each event sounds, relative to the actor (x right, y up from the feet, z forward is -z).
const SPOTS := {
	"unlatch": Vector3(0.05, -0.42, -0.45), "extract": Vector3(0.05, -0.50, -0.45), "pouch": Vector3(-0.22, -0.92, -0.10),
	"land": Vector3(-0.25, -1.60, -0.70), "enter": Vector3(0.05, -0.50, -0.45), "seat": Vector3(0.05, -0.45, -0.45),
}
## Loudness of each event relative to the base level, in dB: the seat is the loudest thing in a reload.
const LEVELS := {"unlatch": -3.0, "extract": -9.0, "pouch": -8.0, "land": -5.0, "enter": -9.0, "seat": 0.0}
static var _streams: Dictionary = {}

var _voices: Array[AudioStreamPlayer3D] = []
var _next := 0
var _reload_index := 0
## How many sounds have been played in all (the id of the last log entry).
var serial := 0
## What has played, oldest first: {id, event, progress, voice, variant, msec}. Kept to the last LOG_LIMIT.
var log: Array[Dictionary] = []
const LOG_LIMIT := 96

func _init() -> void:
	name = "ReloadAudio"
	_build_streams()
	for i in VOICES:
		var voice := AudioStreamPlayer3D.new()
		voice.name = "Voice%d" % i
		voice.max_distance = 16.0
		voice.unit_size = 1.5
		voice.volume_db = -15.0
		add_child(voice)
		_voices.append(voice)

## The bus every voice plays on, or one voice's (the audio capture gives each voice a bus of its own).
func route(bus: StringName, index := -1) -> void:
	for i in _voices.size():
		if index < 0 or i == index:
			_voices[i].bus = bus

## Plays `event` on a free voice, or, when all are busy, on the one furthest through its sound. Returns the voice
## index (-1 for an event with no sound). `head_height` places the SPOTS, which are relative to the head.
func play(event: String, progress: float, head_height: float) -> int:
	if not _streams.has(event):
		return -1
	var index := _free_voice()
	var voice := _voices[index]
	var variants: Array = _streams[event]
	var variant := _reload_index % variants.size()
	voice.stream = variants[variant]
	voice.volume_db = -15.0 + float(LEVELS.get(event, 0.0))
	var spot: Vector3 = SPOTS.get(event, Vector3.ZERO)
	voice.position = Vector3(spot.x, head_height + spot.y, spot.z)
	voice.play()
	serial += 1
	log.append({"id": serial, "event": event, "progress": progress, "voice": index, "variant": variant, "msec": Time.get_ticks_msec()})
	if log.size() > LOG_LIMIT:
		log.pop_front()
	return index

## A new reload starts: the variants alternate, and the log keeps only this reload's sounds.
func begin_reload() -> void:
	_reload_index += 1

## Everything stops now: a reload that was cancelled (weapon switch, death, round reset) must leave no sound behind.
func stop_all() -> void:
	for voice in _voices:
		voice.stop()

func playing_count() -> int:
	var count := 0
	for voice in _voices:
		if voice.playing:
			count += 1
	return count

func voice_playing(index: int) -> bool:
	return index >= 0 and index < _voices.size() and _voices[index].playing

func count_logged(event: String) -> int:
	var count := 0
	for entry in log:
		if entry.event == event:
			count += 1
	return count

## The events played since sound number `after_id` (the actor's `serial` before a tick), in order.
func heard_since(after_id: int) -> Array[String]:
	var out: Array[String] = []
	for entry in log:
		if int(entry.id) > after_id:
			out.append(String(entry.event))
	return out

func clear_log() -> void:
	log.clear()

func _free_voice() -> int:
	for step in VOICES:
		var index := (_next + step) % VOICES
		if not _voices[index].playing:
			_next = (index + 1) % VOICES
			return index
	# All busy: the one furthest through its sound is the one nearest its end.
	var best := 0
	var furthest := -1.0
	for i in VOICES:
		var played := _voices[i].get_playback_position()
		if played > furthest:
			furthest = played
			best = i
	_next = (best + 1) % VOICES
	return best

# ------------------------------------------------------------------ synthesis

static func _build_streams() -> void:
	if not _streams.is_empty():
		return
	for variant in 2:
		var shift := 0.94 if variant == 0 else 1.07
		var seed_base := 4100 + variant * 97
		_add("unlatch", _click(0.075, 1900.0 * shift, 760.0 * shift, seed_base + 1))
		_add("extract", _slide(0.17, 1700.0 * shift, 900.0 * shift, 105.0, seed_base + 2, false))
		_add("pouch", _rustle(0.23, seed_base + 3))
		_add("land", _thud(0.36, 125.0 * shift, seed_base + 4))
		_add("enter", _slide(0.14, 800.0 * shift, 1500.0 * shift, 140.0, seed_base + 5, true))
		_add("seat", _clunk(0.20, 190.0 * shift, 2400.0 * shift, seed_base + 6))

static func _add(event: String, stream: AudioStreamWAV) -> void:
	if not _streams.has(event):
		_streams[event] = []
	(_streams[event] as Array).append(stream)

static func _wav(samples: PackedFloat32Array) -> AudioStreamWAV:
	var stream := AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = MIX_RATE
	var data := PackedByteArray()
	data.resize(samples.size() * 2)
	var peak := 0.0
	for s in samples:
		peak = maxf(peak, absf(s))
	var gain := 0.9 / maxf(peak, 0.0001) # every sound peaks at the same level; LEVELS sets how loud it plays
	for i in samples.size():
		data.encode_s16(i * 2, int(clampf(samples[i] * gain, -1.0, 1.0) * 32767.0))
	stream.data = data
	return stream

## A band-pass (a biquad), one sample at a time; `state` carries the two delays.
static func _bandpass(x: float, state: Array, frequency: float, q: float) -> float:
	var w := TAU * frequency / MIX_RATE
	var alpha := sin(w) / (2.0 * q)
	var a0 := 1.0 + alpha
	var b0 := alpha / a0
	var b2 := -alpha / a0
	var a1 := -2.0 * cos(w) / a0
	var a2 := (1.0 - alpha) / a0
	var y: float = b0 * x + b2 * state[1] - a1 * state[2] - a2 * state[3]
	state[1] = state[0]
	state[0] = x
	state[3] = state[2]
	state[2] = y
	return y

static func _filter_state() -> Array:
	return [0.0, 0.0, 0.0, 0.0]

## A latch or button: a sharp noise transient and two ringing resonances.
static func _click(duration: float, ring_a: float, ring_b: float, seed_value: int) -> AudioStreamWAV:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	var count := int(duration * MIX_RATE)
	var out := PackedFloat32Array()
	out.resize(count)
	for i in count:
		var t := float(i) / MIX_RATE
		var transient := rng.randf_range(-1.0, 1.0) * exp(-t * 900.0)
		var ping := sin(TAU * ring_a * t) * exp(-t * 110.0) * 0.55 + sin(TAU * ring_b * t) * exp(-t * 60.0) * 0.45
		out[i] = transient * 0.8 + ping
	return _wav(out)

## Friction as one part slides on another: band-passed noise whose centre moves, with the stick-slip ripple of
## `ripple` Hz in its level, rising in or falling away.
static func _slide(duration: float, from_hz: float, to_hz: float, ripple: float, seed_value: int, rising: bool) -> AudioStreamWAV:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	var count := int(duration * MIX_RATE)
	var out := PackedFloat32Array()
	out.resize(count)
	var state := _filter_state()
	for i in count:
		var u := float(i) / count
		var envelope := sin(PI * pow(u, 0.7 if rising else 1.4)) # in fast and out slow, or the reverse
		var centre := lerpf(from_hz, to_hz, u)
		var rough := 0.65 + 0.35 * sin(TAU * ripple * u * duration + rng.randf() * 0.2)
		out[i] = _bandpass(rng.randf_range(-1.0, 1.0), state, centre, 1.6) * envelope * rough
	return _wav(out)

## Cloth: three overlapping grains of low-passed noise at random places, and a small plastic tick at the start.
static func _rustle(duration: float, seed_value: int) -> AudioStreamWAV:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	var count := int(duration * MIX_RATE)
	var out := PackedFloat32Array()
	out.resize(count)
	var grains := []
	for g in 3:
		grains.append(Vector2(rng.randf_range(0.0, 0.55), rng.randf_range(0.25, 0.45))) # start, length (fractions)
	var low := 0.0
	for i in count:
		var u := float(i) / count
		var level := 0.0
		for grain in grains:
			var local: float = (u - grain.x) / grain.y
			if local >= 0.0 and local <= 1.0:
				level = maxf(level, sin(PI * local))
		low += (rng.randf_range(-1.0, 1.0) - low) * 0.32
		var tick := rng.randf_range(-1.0, 1.0) * exp(-u * duration * 700.0) * 0.9
		out[i] = low * level * 1.4 + tick
	return _wav(out)

## A magazine dropping on a hard floor: a low body that falls in pitch, a noise crack, and a lighter bounce.
static func _thud(duration: float, body_hz: float, seed_value: int) -> AudioStreamWAV:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	var count := int(duration * MIX_RATE)
	var out := PackedFloat32Array()
	out.resize(count)
	var state := _filter_state()
	var phase := 0.0
	for i in count:
		var t := float(i) / MIX_RATE
		phase += TAU * (body_hz * (0.45 + 0.55 * exp(-t * 28.0))) / MIX_RATE
		var body := sin(phase) * exp(-t * 26.0)
		var crack := _bandpass(rng.randf_range(-1.0, 1.0), state, 2100.0, 1.0) * exp(-t * 190.0)
		var bounce := 0.0
		var tb := t - 0.19
		if tb >= 0.0:
			bounce = (sin(TAU * body_hz * 1.7 * tb) * exp(-tb * 45.0) + rng.randf_range(-0.3, 0.3) * exp(-tb * 260.0)) * 0.42
		out[i] = body * 0.9 + crack * 0.7 + bounce
	return _wav(out)

## A magazine driven home: a heavy low knock, a hard click on top, and a short noise tail of the parts settling.
static func _clunk(duration: float, body_hz: float, click_hz: float, seed_value: int) -> AudioStreamWAV:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	var count := int(duration * MIX_RATE)
	var out := PackedFloat32Array()
	out.resize(count)
	var state := _filter_state()
	for i in count:
		var t := float(i) / MIX_RATE
		var knock := sin(TAU * body_hz * (1.0 - t * 1.6) * t) * exp(-t * 34.0)
		var click := (sin(TAU * click_hz * t) * 0.6 + rng.randf_range(-1.0, 1.0) * 0.6) * exp(-t * 420.0)
		var settle := _bandpass(rng.randf_range(-1.0, 1.0), state, 900.0, 1.2) * exp(-t * 55.0) * 0.35
		out[i] = knock * 1.0 + click * 0.85 + settle
	return _wav(out)
