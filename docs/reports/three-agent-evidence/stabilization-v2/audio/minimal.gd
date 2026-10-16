extends SceneTree
func _initialize():
 run.call_deferred()
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
 samples.resize(22050)
 stream.data=samples
 await physics_frame
 await physics_frame
 for i in 20:
  if "--stop-before" in args: player.stop()
  player.stream=stream
  player.play()
  if "--yield" in args: await physics_frame
 player.stop()
 if "--before-free" in args: await create_timer(0.3).timeout
 world.queue_free()
 await process_frame
 await create_timer(0.3).timeout
 print("MINIMAL_DONE ",args)
 quit()
