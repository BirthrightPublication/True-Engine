import ctypes as c
import os, subprocess, tempfile, time, re, json
from pathlib import Path
from PIL import Image
x=c.CDLL('libX11.so.6'); xt=c.CDLL('libXtst.so.6')
x.XOpenDisplay.restype=c.c_void_p
x.XOpenDisplay.argtypes=[c.c_char_p]
x.XFlush.argtypes=[c.c_void_p]
x.XSetInputFocus.argtypes=[c.c_void_p,c.c_ulong,c.c_int,c.c_ulong]
x.XStringToKeysym.argtypes=[c.c_char_p];x.XStringToKeysym.restype=c.c_ulong
x.XKeysymToKeycode.argtypes=[c.c_void_p,c.c_ulong];x.XKeysymToKeycode.restype=c.c_uint
xt.XTestFakeMotionEvent.argtypes=[c.c_void_p,c.c_int,c.c_int,c.c_int,c.c_ulong]
xt.XTestFakeButtonEvent.argtypes=[c.c_void_p,c.c_uint,c.c_int,c.c_ulong]
xt.XTestFakeKeyEvent.argtypes=[c.c_void_p,c.c_uint,c.c_int,c.c_ulong]
d=x.XOpenDisplay(b':99');assert d
with tempfile.TemporaryDirectory() as tmp:
    log=open('/workspace/.true-engine/native.log','w')
    p=subprocess.Popen(['/workspace/True-Engine/target/debug/true-engine-viewport'],cwd=tmp,env=dict(os.environ,DISPLAY=':99',WINIT_UNIX_BACKEND='x11',XDG_RUNTIME_DIR='/workspace/.true-engine/runtime',XDG_CACHE_HOME='/workspace/.true-engine/cache'),stdout=log,stderr=log)
    try:
        for _ in range(100):
            tree=subprocess.check_output(['xwininfo','-root','-tree'],env=dict(os.environ,DISPLAY=':99'),text=True)
            match=re.search(r'(0x[0-9a-f]+) "TRUE ENGINE',tree)
            if match:break
            assert p.poll() is None,'viewport exited; see native.log'
            time.sleep(.1)
        assert match,'viewport window not found'
        window=int(match[1],16);x.XSetInputFocus(d,window,1,0);x.XFlush(d);time.sleep(.5)
        def shot(name):
            dest=f'/workspace/.true-engine/{name}.png'
            subprocess.run(['import','-display',':99','-window',hex(window),dest],check=True)
            return Image.open(dest).convert('RGB')
        for _ in range(50):
            before=shot('viewport-before')
            if len(set(before.get_flattened_data()))>5:break
            time.sleep(.1)
        w,h=before.size
        assert len(set(before.get_flattened_data()))>5,'no visible geometry'
        xt.XTestFakeMotionEvent(d,-1,w//2,h//2,0);xt.XTestFakeButtonEvent(d,1,1,0);xt.XTestFakeButtonEvent(d,1,0,0);x.XFlush(d);time.sleep(.4)
        selected=shot('viewport-selected');assert before.tobytes()!=selected.tobytes(),'selection did not change pixels'
        for key in [b's',b'l']:
            code=x.XKeysymToKeycode(d,x.XStringToKeysym(key));xt.XTestFakeKeyEvent(d,code,1,0);xt.XTestFakeKeyEvent(d,code,0,0);x.XFlush(d);time.sleep(.3)
            if key==b's':assert json.loads(Path(tmp,'project.json').read_text())['schema_version']==1
        after=shot('viewport-loaded');assert after.tobytes()==before.tobytes(),'load did not restore scene rendering'
        # Orbit and pan via actual pointer events; wheel zoom via button 4.
        for button,name in [(1,'orbit'),(3,'pan')]:
            old=shot(name+'-before');xt.XTestFakeButtonEvent(d,button,1,0);xt.XTestFakeMotionEvent(d,-1,w//2+45,h//2+20,0);xt.XTestFakeButtonEvent(d,button,0,0);x.XFlush(d);time.sleep(.3)
            assert old.tobytes()!=shot(name+'-after').tobytes(),name+' produced no change'
            xt.XTestFakeMotionEvent(d,-1,w//2,h//2,0);x.XFlush(d);time.sleep(.1)
        old=shot('zoom-before');xt.XTestFakeButtonEvent(d,4,1,0);xt.XTestFakeButtonEvent(d,4,0,0);x.XFlush(d);time.sleep(.3)
        assert old.tobytes()!=shot('zoom-after').tobytes(),'zoom produced no change'
        print('PASS: native startup, rendered pixels, click selection, S/L project round trip, orbit, pan, zoom')
    finally:
        p.terminate();p.wait(timeout=10);log.close()
