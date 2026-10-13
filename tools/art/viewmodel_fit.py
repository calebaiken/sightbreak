"""Fit the first-person placement of an authored weapon (weapon_model.gd constants).

python3 viewmodel_fit.py

Projects landmarks of the weapon (model space, Blender axes) through the game camera
(82 degree vertical field of view, 16:9) and searches pitch, yaw and an offset in the
weapon node's space for the best match to screen targets given as fractions of the
frame. Roll and scale are fixed per run. Prints the screen position of every landmark
so the layout can be checked, then confirm in engine with tests/weapon_art_capture.gd.
Needs NumPy only. Re-run after changing the generator's proportions.
"""
import math, itertools, random
import numpy as np
W,H=1280,720; T=math.tan(math.radians(41)); A=W/H
GUN=np.array([0.235,-0.235,-0.42])
# Blender model (x,y,z) -> Godot model space (x, z, -y)
def g(b): return np.array([b[0], b[2], -b[1]])
P={'muzzle':g((0,0.676,0.025)),'palm':g((-0.014,0.425,-0.014)),'thumb':g((-0.036,0.47,0.014)),'optic':g((0,0.100,0.095)),
   'port':g((0.024,0.13,0.031)),'grip':g((0,-0.008,-0.060)),'handguard_front':g((0,0.585,0.03)),'stock_end':g((0,-0.274,0.0)),'mag':g((0,0.13,-0.17))}
def euler_yxz(x,y,z):
    cx,sx,cy,sy,cz,sz=math.cos(x),math.sin(x),math.cos(y),math.sin(y),math.cos(z),math.sin(z)
    Rx=np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]]); Ry=np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]]); Rz=np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])
    return Ry@Rx@Rz
def cam_point(p, s, rot, off):
    return GUN + off + euler_yxz(*rot)@(p*s)
def screen(q):
    if q[2] > -0.05: return None
    return np.array([W/2*(1+q[0]/(-q[2])/(T*A)), H/2*(1-q[1]/(-q[2])/T)])
TARGET={'muzzle':(0.55,0.53),'palm':(0.60,0.70),'optic':(0.76,0.60),'grip':(0.90,0.97)}
def cost(params, roll, s):
    pitch,yaw,ox,oy,oz=params
    rot=(pitch,yaw,roll); off=np.array([ox,oy,oz]); c=0
    for k,(tx,ty) in TARGET.items():
        sp=screen(cam_point(P[k],s,rot,off))
        if sp is None: return 1e9
        c+=np.hypot(sp[0]-tx*W, sp[1]-ty*H)
    # the stock end must be behind the camera plane or off-screen
    sp=screen(cam_point(P['stock_end'],s,rot,off))
    if sp is not None and 0<sp[0]<W and 0<sp[1]<H: c+=400
    return c
def fit(roll,s,seed=1):
    rng=random.Random(seed); best=None
    for _ in range(40):
        x=np.array([rng.uniform(-0.1,0.2),rng.uniform(-0.1,0.3),rng.uniform(-0.2,0.1),rng.uniform(-0.1,0.2),rng.uniform(-0.1,0.4)])
        step=np.array([0.05,0.05,0.04,0.04,0.06]); cur=cost(x,roll,s)
        for it in range(400):
            cand=x+np.random.default_rng(rng.randint(0,10**9)).normal(0,1,5)*step
            cc=cost(cand,roll,s)
            if cc<cur: x,cur=cand,cc
            if it%100==99: step*=0.5
        if best is None or cur<best[0]: best=(cur,x)
    return best
if __name__=='__main__':
    for roll in (-0.04,-0.10,-0.16):
        for s in (0.85,1.0):
            c,x=fit(roll,s)
            pitch,yaw,ox,oy,oz=x; rot=(pitch,yaw,roll); off=np.array([ox,oy,oz])
            pos={k:(None if screen(cam_point(P[k],s,rot,off)) is None else tuple(int(v) for v in screen(cam_point(P[k],s,rot,off)))) for k in P}
            print(f"roll={roll} s={s} err={c:.0f} pitch={pitch:.3f} yaw={yaw:.3f} off=({ox:.3f},{oy:.3f},{oz:.3f})", pos)
