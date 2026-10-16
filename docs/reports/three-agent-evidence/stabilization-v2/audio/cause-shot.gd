extends SceneTree
func _initialize():run.call_deferred()
func run():
 var args=OS.get_cmdline_user_args()
 var world=Node3D.new()
 root.add_child(world)
 var actor=SBActor.new()
 actor.configure(1,0,'CauseShot',true)
 world.add_child(actor)
 actor.reset_for_round(Vector3.ZERO)
 actor.credits=5000
 actor.buy_weapon('rifle')
 var player=actor._shot_audio
 await physics_frame
 await physics_frame
 for i in 2:
  if '--direct' in args: player.play()
  else: actor.play_shot_effect()
  await physics_frame
  await physics_frame
  print('SHOT playing=',player.playing,' wav=',player.stream.get_instance_id(),' playback=',player.get_stream_playback().get_instance_id())
 if '--stop' in args: player.stop()
 if '--before' in args: await create_timer(0.3).timeout
 world.queue_free()
 await process_frame
 if '--after' in args: await create_timer(0.3).timeout
 print('CAUSE_SHOT_DONE ',args)
 quit()
