# Exact candidate source-review excerpts

Commit `79a9591350854373076e62a4707ec84edc803756`. These are **not verified PR line targets**; the supplied 41-character PR token is unresolved. These excerpts are source-location evidence, not a measured causal diagnosis or adoption of comments' historical quality/performance claims.

## `tools/art/arms_build.py`
Git blob `46a56f4877f16af03aeeae44d4d7f1b5b28743f1`; full-blob SHA-256 `8400e0fc3c9734ab8ac3c9d4a641cefa037d26ba66ac83fe171855d90df780df`.

### Lines 928-930
```text
928: _PATH = {'swing': (-0.070, 0.020, 0.004), 'hip': (-0.200, 0.040, -0.340), 'carry': (-0.115, 0.050, -0.110), 'hip_turn': (55, 0, 22),
929:          'rock': (-15, -9, -3), 'elbow_hip': (-0.35, 0.0, 0.30),
930:          'carry_at': (0.50, 0.0, 0.0)}
```

### Lines 942-943
```text
942: _PATH_CALM = {'hip': (-0.190, 0.040, -0.280), 'carry': (-0.115, 0.050, -0.050), 'hip_turn': (55, 0, 10), 'elbow_hip': (-0.35, 0.0, 0.30),
943:               'carry_at': (0.50, 0.0, 0.0)}
```

### Lines 965-972
```text
965:     carry_at = _PATH['carry_at'][0]
966:     new = (
967:         (P_ACQUIRE, 0.100, hip, hip_turn, 'hold'),                             # in the hand at the pouch, below the bottom edge of the frame
968:         (P_ACQUIRE + (P_ALIGN - P_ACQUIRE) * carry_at, 0.100, carry, (-22, 0, 14)),   # coming up into view, wrist turning
969:         (P_ALIGN, 0.088, ZERO3, (rock[0], 0, 0)),                              # under the well, tipped so its front lip goes in first
970:         (P_ENTER, 0.030, ZERO3, (rock[1], 0, 0)),                              # entering, rocking upright
971:         (P_ENTER + (P_SEAT - P_ENTER) * 0.60, 0.008, ZERO3, (rock[2], 0, 0)),
972:         (P_SEAT, 0.000, ZERO3, (0, 0, 0), 'hold'),                             # pushed to its stop
```

### Lines 1178-1190
```text
1178:     # While the hand is at the hip the elbow is swung out to the left and up, so the sleeve goes down into the
1179:     # bottom-left corner of the frame instead of dropping out of it with the hand; the bias fades by ALIGN.
1180:     ELBOW_HIP = Vector(_PATH['elbow_hip'])
1181: 
1182:     def elbow_bias(p):
1183:         if p < P_ACQUIRE:
1184:             return ELBOW_HIP * smooth((p - P_DROP) / (P_ACQUIRE - P_DROP))
1185:         return ELBOW_HIP * (1.0 - smooth((p - P_ACQUIRE) / (P_ALIGN - P_ACQUIRE)))
1186: 
1187:     def held(p):
1188:         """Hand matrix and elbow while it holds a magazine."""
1189:         M = mag_path(p, axis, holding(p))
1190:         return M @ grab_hand, grab_elbow + M.translation * 0.5 + (elbow_bias(p) if p > P_DROP else Vector())
```

### Lines 1232-1252
```text
1232:     for frame in range(fps + 1):
1233:         p = frame / fps
1234:         if holding(p) is not None:
1235:             H, elbow = held(p)
1236:         elif P_DROP < p < P_ACQUIRE:
1237:             H, elbow = transit(p)
1238:         elif p < P_GRASP:
1239:             loc, elbow = reach_at(p)
1240:             H = Matrix.LocRotScale(loc, rot_r.slerp(rot_g, smooth(p / P_REACH)), None)
1241:         else:
1242:             loc, elbow = return_at(p)
1243:             H = Matrix.LocRotScale(loc, rot_g.slerp(rot_r, smooth((p - P_LETGO) / (1.0 - P_LETGO))), None)
1244:         wrist = H.translation
1245:         new_y = (wrist - elbow).normalized()
1246:         turn = (rest_fore.to_3x3() @ Vector((0, 1, 0))).rotation_difference(new_y)
1247:         F = (turn.to_matrix() @ rest_fore.to_3x3()).to_4x4()
1248:         F.translation = wrist - new_y * rig.data.bones['L_forearm'].length
1249:         fore.matrix = F
1250:         bpy.context.view_layer.update()
1251:         hand.matrix = H
1252:         bpy.context.view_layer.update()
```

## `game/scripts/gameplay/actor.gd`
Git blob `5abbdaf0dd6f7bdbc2ea7b40cfa2214c3c4740f3`; full-blob SHA-256 `7904d351c5da8574f060fa823c6bcd8840a42e98bb121c9c84cf92e814383c13`.

### Lines 1091-1112
```text
1091: 		var reload_offset := ARMS_RELOAD_OFFSET if rigged else Vector3(0, -0.13, 0)
1092: 		var reload_rotation := ARMS_RELOAD_ROTATION if rigged else Vector3(-0.38, 0, 0.38)
1093: 		var profile: Dictionary = REDUCED_RELOAD_VARIANTS["current"]
1094: 		if reduced_motion and rigged:
1095: 			profile = REDUCED_RELOAD_VARIANTS.get(reduced_variant, REDUCED_RELOAD_VARIANTS["current"])
1096: 			reload_rotation *= float(profile.roll)
1097: 			reload_offset *= float(profile.lift)
1098: 		var kick := _kick * (float(profile.recoil) if reduced_motion and rigged else 1.0)
1099: 		_gun.position = Vector3(_gun_rest.x + sin(_bob) * 0.006 * bob_weight - _sway.x, _gun_rest.y + absf(cos(_bob)) * 0.006 * bob_weight - _sway.y - equip_motion * 0.19, _gun_rest.z + kick * (0.075 if weapon_id == "marksman" else 0.046) + equip_motion * 0.08) + reload_offset * reload_tilt + SEAT_KICK_OFFSET * _seat_kick * (0.25 if reduced_motion else 1.0)
1100: 		_gun.rotation = Vector3(kick * (0.13 if weapon_id == "sidearm" else 0.065) - equip_motion * 0.48, -_sway.x * 1.8, -_sway.x) + reload_rotation * reload_tilt + SEAT_KICK_TURN * _seat_kick * (0.25 if reduced_motion else 1.0)
1101: 		if is_instance_valid(_arms_player):
1102: 			# The clip's first frame is the hold, so 0 returns the hands to the rifle.
1103: 			var clip_time := reload_progress if reload_remaining > 0 else 0.0
1104: 			var clip_name := str(profile.clip) if _arms_player.has_animation(str(profile.clip)) else "reload"
1105: 			if _arms_player.assigned_animation != clip_name:
1106: 				_arms_player.assigned_animation = clip_name
1107: 				_arms_time = -1.0
1108: 			if clip_time != _arms_time:
1109: 				_arms_time = clip_time
1110: 				_arms_player.seek(clip_time, true)
1111: 		if is_instance_valid(_magazine):
1112: 			_pose_magazines(reload_progress if reload_remaining > 0 else 0.0)
```

### Lines 1178-1184
```text
1178: 	if is_instance_valid(_magazine_spare):
1179: 		# The replacement is drawn from the acquisition: the hand has it at the pouch, below the frame, and
1180: 		# brings it up into view (arms_build.py: the hip pouch). Before that it is not drawn.
1181: 		_magazine_spare.visible = progress >= SBReloadPhases.ACQUIRE
1182: 		_magazine_spare.transform = _magazine_rest_transform if progress > SBReloadPhases.LETGO else in_hand
1183: 		if progress >= SBReloadPhases.ACQUIRE and progress <= SBReloadPhases.LETGO:
1184: 			_magazine_in_hand = _magazine_spare # held from the acquisition, at the pouch
```

## `game/scripts/gameplay/weapon_model.gd`
Git blob `a57059afca863b69ec0824de08720f19017d8e52`; full-blob SHA-256 `30176d0f9d81f8d1986c49d6ac4788bdf917b0a683020d58711ee3a2f5c3670a`.

### Lines 31-50
```text
31: const ARMS_SHEEN := 0.0
32: ## How much of the studio the arms reflect (the rifle's metal uses ViewmodelShading's default, deliberately low): fabric and
33: ## rubber at this strength keep the brightness the sky's reflection gave them before the studio replaced it.
34: const ARMS_REFLECT := 0.05
35: ## The fill's albedo floor for the arms (ViewmodelShading.LIFT is the rifle's): higher, so the near-black gloves are
36: ## not left in a dark interior with nothing to read; the grip gets none, so it stays the darkest thing in the hand.
37: const ARMS_LIFT := 0.50
38: ## The arms' fill strength (ViewmodelShading.FLOOR is the rifle's), the dielectric specular of their fabric (the engine's default
39: ## 0.5 put a pale sheen on the dark gloves in sun, the "bare skin" look: a glove's median luma in sun was 89, about a third of it
40: ## additive) and their rim. The specular and the rim came down and the fill went up so that the gloves are darker in sun and
41: ## no darker in shade or a dark interior (measured with viewmodel_light_probe.gd; art-v9/materials).
42: const ARMS_FLOOR := 0.14
43: const ARMS_SPECULAR := 0.25
44: ## Rim light on the arms (ViewmodelShading.RIM is the rifle's): a pale edge on the silhouette so a dark forearm is an outline
45: ## against a dark floor.
46: const ARMS_RIM := 0.25
47: ## Ground bounce on what faces down (ViewmodelShading `viewmodel_bounce`, linear colour): the support forearm's underside in the hip
48: ## retrieval was a near-black wedge (median luma 33 of 255 in sun, art-v10/materials), the sleeve's form lost where it turns away from
49: ## the light. Zero for the rifle.
50: const ARMS_BOUNCE := Vector3(0.30, 0.28, 0.23)
```

### Lines 128-145
```text
128: static func _add_arms(parent: Node3D, placement: Transform3D, result: Dictionary) -> void:
129: 	if _arms_scene == null:
130: 		_arms_scene = load(RELAY_AR_ARMS)
131: 	var arms: Node3D = _arms_scene.instantiate()
132: 	arms.name = "arms"
133: 	arms.transform = placement
134: 	arms.set_meta("weapon_role", "arms")
135: 	var material := ViewmodelShading.surface(RELAY_AR_ARMS_TEXTURES)
136: 	material.set_shader_parameter("viewmodel_lift", ARMS_LIFT) # the arms' fill floor: charcoal gloves keep some form in shade
137: 	material.set_shader_parameter("viewmodel_rim", ARMS_RIM)
138: 	material.set_shader_parameter("viewmodel_floor", ARMS_FLOOR)
139: 	material.set_shader_parameter("viewmodel_specular", ARMS_SPECULAR)
140: 	material.set_shader_parameter("viewmodel_sheen", ARMS_SHEEN)
141: 	material.set_shader_parameter("viewmodel_reflect", ARMS_REFLECT)
142: 	material.set_shader_parameter("viewmodel_bounce", ARMS_BOUNCE)
143: 	for mesh: MeshInstance3D in arms.find_children("*", "MeshInstance3D", true, false):
144: 		mesh.material_override = material
145: 		mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
```

## `game/scripts/gameplay/viewmodel_shading.gd`
Git blob `ec7b33d1ace39df1e3ddbbcd29bc4ea3dab642fc`; full-blob SHA-256 `66612a72ea4b62c8e4be39c1fd30fa557910fcd65b4c17d822f4a2c8f78526ac`.

### Lines 104-124
```text
104: const STUDIO := """
105: 	if (viewmodel_fov > 0.0 && viewmodel_env > 0.0) {
106: 		vec3 detail_normal_ts = NORMAL_MAP * 2.0 - 1.0;
107: 		vec3 n = normalize(TANGENT * detail_normal_ts.x + BINORMAL * detail_normal_ts.y + NORMAL * detail_normal_ts.z);
108: 		float ndv = clamp(dot(n, VIEW), 0.0, 1.0);
109: 		float up = clamp(n.y * 0.5 + 0.5, 0.0, 1.0);
110: 		EMISSION += ALBEDO * (1.0 - METALLIC) * AO * viewmodel_ambient * viewmodel_env;
111: 		// Light bounced up from the ground onto what faces down (a forearm's underside, the underside of a fist): a constant of the
112: 		// viewmodel like the ambient, not read from the world, so it adds form without adding visibility in a dark place.
113: 		EMISSION += ALBEDO * (1.0 - METALLIC) * AO * viewmodel_bounce * clamp(-n.y, 0.0, 1.0) * viewmodel_env;
114: 		vec3 r = reflect(-VIEW, n);
115: 		float gloss = 1.0 - ROUGHNESS;
116: 		vec3 f0 = mix(vec3(0.08 * SPECULAR), ALBEDO, METALLIC);
117: 		vec3 fresnel = f0 + (max(vec3(gloss), f0) - f0) * pow(1.0 - ndv, 5.0);
118: 		vec3 gradient = mix(vec3(0.26, 0.29, 0.31), vec3(0.38, 0.42, 0.45), smoothstep(-1.0, 1.0, r.y));
119: 		gradient = mix(gradient, vec3(0.30, 0.33, 0.36), ROUGHNESS * 0.6);
120: 		float key = pow(max(dot(r, normalize(vec3(-0.50, 0.60, 0.62))), 0.0), mix(48.0, 5.0, ROUGHNESS)) * mix(1.0, 0.4, ROUGHNESS);
121: 		float strip = pow(max(dot(r, normalize(vec3(0.78, 0.15, -0.40))), 0.0), mix(24.0, 4.0, ROUGHNESS)) * mix(1.0, 0.4, ROUGHNESS);
122: 		vec3 radiance = gradient + vec3(1.0, 0.96, 0.90) * key * 3.0 * viewmodel_sheen + vec3(0.62, 0.76, 1.0) * strip * 1.2 * viewmodel_sheen;
123: 		EMISSION += fresnel * radiance * AO * viewmodel_env * viewmodel_reflect;
124: 	}
```

## `game/scripts/gameplay/reload_phases.gd`
Git blob `21c1c8046cb5182fce6233b7a81035753e10139e`; full-blob SHA-256 `8af430e76f3eda34ed0703c9ffb15cd68fec40a24e5ad3657ffe2f66a2936590`.

### Lines 23-38
```text
23: const REACH := 0.14
24: const GRASP := 0.20
25: const UNLATCH := 0.24
26: const CLEAR := 0.32
27: const DROP := 0.37
28: const ACQUIRE := 0.50
29: const ALIGN := 0.67
30: const ENTER := 0.74
31: const SEAT := 0.80
32: const LETGO := 0.85
33: ## The span in which the support hand is below the frame, at the magazine pouch on the hip: it leaves the
34: ## picture at HIP_OUT and is back in it at HIP_IN. The sleeve stays in the frame throughout, and the replacement
35: ## is first drawn inside this span, in the hand, with none of it in the picture. Everything outside it is held
36: ## to the stricter rules of reload_visibility_test.gd.
37: const HIP_OUT := 0.41
38: const HIP_IN := 0.60
```
