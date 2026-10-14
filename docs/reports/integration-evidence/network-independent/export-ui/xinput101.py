import ctypes as c
from ctypes.util import find_library
import time
from PIL import ImageGrab
x=c.CDLL(find_library('X11')); t=c.CDLL(find_library('Xtst'))
x.XOpenDisplay.argtypes=[c.c_char_p];x.XOpenDisplay.restype=c.c_void_p
d=x.XOpenDisplay(b':101')
if not d: raise RuntimeError('Missing X100 display')
x.XDefaultRootWindow.argtypes=[c.c_void_p];x.XDefaultRootWindow.restype=c.c_ulong
x.XQueryTree.argtypes=[c.c_void_p,c.c_ulong,c.POINTER(c.c_ulong),c.POINTER(c.c_ulong),c.POINTER(c.POINTER(c.c_ulong)),c.POINTER(c.c_uint)]
x.XFetchName.argtypes=[c.c_void_p,c.c_ulong,c.POINTER(c.c_char_p)]
x.XSetInputFocus.argtypes=[c.c_void_p,c.c_ulong,c.c_int,c.c_ulong]
x.XFlush.argtypes=[c.c_void_p]
x.XKeysymToKeycode.argtypes=[c.c_void_p,c.c_ulong];x.XKeysymToKeycode.restype=c.c_uint
x.XStringToKeysym.argtypes=[c.c_char_p];x.XStringToKeysym.restype=c.c_ulong
for f,args in [('XTestFakeMotionEvent',[c.c_void_p,c.c_int,c.c_int,c.c_int,c.c_ulong]),('XTestFakeButtonEvent',[c.c_void_p,c.c_uint,c.c_int,c.c_ulong]),('XTestFakeKeyEvent',[c.c_void_p,c.c_uint,c.c_int,c.c_ulong])]:getattr(t,f).argtypes=args
root=c.c_ulong();parent=c.c_ulong();children=c.POINTER(c.c_ulong)();count=c.c_uint()
x.XQueryTree(d,x.XDefaultRootWindow(d),c.byref(root),c.byref(parent),c.byref(children),c.byref(count))
window=None
largest=0
x.XGetGeometry.argtypes=[c.c_void_p,c.c_ulong,c.POINTER(c.c_ulong),c.POINTER(c.c_int),c.POINTER(c.c_int),c.POINTER(c.c_uint),c.POINTER(c.c_uint),c.POINTER(c.c_uint),c.POINTER(c.c_uint)]
for i in range(count.value):
    name=c.c_char_p();x.XFetchName(d,children[i],c.byref(name))
    if name.value and b'SIGHTBREAK' in name.value:
        wr=c.c_ulong();wx=c.c_int();wy=c.c_int();ww=c.c_uint();wh=c.c_uint();border=c.c_uint();depth=c.c_uint()
        x.XGetGeometry(d,children[i],c.byref(wr),c.byref(wx),c.byref(wy),c.byref(ww),c.byref(wh),c.byref(border),c.byref(depth))
        print('XWINDOW',children[i],name.value,ww.value,wh.value,flush=True)
        if ww.value*wh.value>largest:
            largest=ww.value*wh.value
            window=children[i]
if window is None:raise RuntimeError('SIGHTBREAK window not found')
x.XSetInputFocus(d,window,1,0);x.XFlush(d)
def click(px,py):
    t.XTestFakeMotionEvent(d,0,px,py,0);t.XTestFakeButtonEvent(d,1,1,0);x.XFlush(d);time.sleep(.2);t.XTestFakeButtonEvent(d,1,0,0);x.XFlush(d)
def key(name,down=None):
    code=x.XKeysymToKeycode(d,x.XStringToKeysym(name.encode()))
    print('XKEY',name,code,window,down,flush=True)
    for state in ([1,0] if down is None else [int(down)]):t.XTestFakeKeyEvent(d,code,state,0)
    x.XFlush(d)
def capture(path): ImageGrab.grab(xdisplay=':101').save(path)
if __name__=='__main__':capture('/workspace/reviews/integration-20261013/export-menu.png')
class Data(c.Union):_fields_=[('b',c.c_char*20),('s',c.c_short*10),('l',c.c_long*5)]
class Message(c.Structure):_fields_=[('type',c.c_int),('serial',c.c_ulong),('send_event',c.c_int),('display',c.c_void_p),('window',c.c_ulong),('message_type',c.c_ulong),('format',c.c_int),('data',Data)]
class Event(c.Union):_fields_=[('client',Message),('pad',c.c_long*24)]
x.XInternAtom.argtypes=[c.c_void_p,c.c_char_p,c.c_int];x.XInternAtom.restype=c.c_ulong
x.XSendEvent.argtypes=[c.c_void_p,c.c_ulong,c.c_int,c.c_long,c.POINTER(Event)]
def close():
    event=Event();event.client.type=33;event.client.send_event=1;event.client.display=d;event.client.window=window;event.client.message_type=x.XInternAtom(d,b'WM_PROTOCOLS',0);event.client.format=32;event.client.data.l[0]=x.XInternAtom(d,b'WM_DELETE_WINDOW',0)
    x.XSendEvent(d,window,0,0,c.byref(event));x.XFlush(d)
