extends SceneTree
func _initialize():run.call_deferred()
func run():
 var args=OS.get_cmdline_user_args()
 var world=Node3D.new()
 root.add_child(world)
 var camera=Camera3D.new()
 world.add_child(camera)
 camera.current=true
 var player=AudioStreamPlayer3D.new()
 world.add_child(player)
 var stream=AudioStreamWAV.new()
 stream.mix_rate=22050
 stream.format=AudioStreamWAV.FORMAT_16_BITS
 var samples=PackedByteArray()
 samples.resize(int(22050*0.18)*2)
 stream.data=samples
 player.stream=stream
 await physics_frame
 await physics_frame
 for i in 2:
  player.play()
  await physics_frame
  await physics_frame
  print('PLAY ',i,' wav=',stream.get_instance_id(),' playback=',player.get_stream_playback().get_instance_id())
 world.queue_free()
 await process_frame
 if '--drain' in args: await create_timer(0.5).timeout
 print('NATIVE_ONLY_DONE ',args)
 quit()
