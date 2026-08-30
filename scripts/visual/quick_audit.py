import os, psutil, subprocess, shutil, json

r = {}
# RAM/Disk
m = psutil.virtual_memory()
d = shutil.disk_usage(os.environ.get('HOMEDRIVE', 'C:') + os.sep)
r['ram_gb'] = f"{m.total//1024**3} total / {m.available//1024**3} free"
r['disk_gb'] = f"{d.total//1024**3} total / {d.free//1024**3} free"

# GPU via nvidia-smi
try:
    out = subprocess.check_output(['nvidia-smi', '--query-gpu=name,memory.total,memory.free', '--format=csv,noheader'], timeout=5, stderr=subprocess.STDOUT).decode()
    r['gpu'] = out.strip()
except Exception as e:
    r['gpu'] = str(e)[:80]

# Key tools
for name, cmd in [('blender', 'blender --version'), ('inkscape', r'"C:\Program Files\Inkscape\bin\inkscape.exe" --version'), ('ffmpeg', 'ffmpeg -version'), ('krita', 'krita --version'), ('magick', 'magick --version'), ('python', 'python --version'), ('node', 'node --version'), ('torch', 'python -c "import torch; print(torch.__version__, torch.cuda.is_available())"'), ('ollama', 'ollama list')]:
    try:
        out = subprocess.check_output(cmd, shell=True, timeout=5, stderr=subprocess.STDOUT).decode(errors='replace')
        first = [l for l in out.split('\n') if l.strip()]
        r[name] = first[0][:80] if first else 'empty'
    except Exception as e:
        r[name] = 'not_found'

# Unreal
ue = r'C:\Program Files\Epic Games'
if os.path.isdir(ue):
    vers = os.listdir(ue)
    r['unreal'] = vers
else:
    r['unreal'] = 'not_found'

# ComfyUI
for p in [os.path.expanduser('~\\ComfyUI'), os.path.expanduser('~\\Desktop\\ComfyUI')]:
    if os.path.isdir(p):
        r['comfyui'] = p
        ckpt = os.path.join(p, 'models', 'checkpoints')
        if os.path.isdir(ckpt):
            r['checkpoints'] = os.listdir(ckpt)[:10]
        break
else:
    r['comfyui'] = 'not_found'

print(json.dumps(r, indent=2, default=str))
