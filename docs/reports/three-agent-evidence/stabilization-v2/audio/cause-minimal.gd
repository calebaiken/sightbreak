extends SceneTree
var args: PackedStringArray
var player: AudioStreamPlayer3D
func _initialize(): run.call_deferred()
func run():
 args=OS.get_cmdline_user_args()
 var world=Node3D.new()
 root.add_child(world)
 var camera=Camera3D.new()
 world.add_child(camera)
 camera.current=true
 player=AudioStreamPlayer3D.new()
 world.add_child(player)
 var stream=AudioStreamWAV.new()
 stream.mix_rate=22050
 stream.format=AudioStreamWAV.FORMAT_16_BITS
 var samples=PackedByteArray()
 samples.resize(22050*10*2)
 stream.data=samples
 player.stream=stream
 await physics_frame
 await physics_frame
 player.play()
 await physics_frame
 await physics_frame
 await create_timer(0.04).timeout
 print('BEFORE free=',player.playing,' paused=',player.stream_paused,' playback=',player.get_stream_playback().get_instance_id())
 if '--stop' in args: player.stop()
 if '--pause-stop' in args:
  player.stream_paused=true
  player.stop()
 world.queue_free()
 await process_frame
 await create_timer(0.3).timeout
 print('CAUSE_DONE ',args)
 quit()
