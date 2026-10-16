extends SceneTree
func _initialize():run.call_deferred()
func run():
 var args=OS.get_cmdline_user_args()
 var world=Node3D.new()
 root.add_child(world)
 var actor=SBActor.new()
 actor.configure(1,0,"Probe",true)
 world.add_child(actor)
 var audio=actor._reload_audio
 await physics_frame
 await physics_frame
 for i in 10:
  for event in ["unlatch","extract","pouch","land","enter","seat"]:
   audio.play(event,0.5,1.62)
   if "--yield" in args: await physics_frame
  audio.stop_all()
 world.queue_free()
 await process_frame
 await create_timer(0.3).timeout
 print("MINIMAL_RELOAD_DONE ",args)
 quit()
