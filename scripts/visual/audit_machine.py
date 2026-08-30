"""Machine audit for Visual Production Intelligence upgrade."""
import subprocess, json, os, sys, shutil

info = {}

# GPU
try:
    r = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,memory.free,driver_version', '--format=csv,noheader'],
                       capture_output=True, text=True, timeout=8)
    if r.returncode == 0:
        gpus = []
        for line in r.stdout.strip().split('\n'):
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 4:
                gpus.append({'name': parts[0], 'vram_total_mb': int(parts[1]), 'vram_free_mb': int(parts[2]), 'driver': parts[3]})
        info['gpus'] = gpus
    else:
        info['gpus'] = [{'status': 'nvidia-smi failed', 'stderr': r.stderr[:200]}]
except Exception as e:
    info['gpus'] = [{'status': str(e)[:100]}]

# RAM
try:
    import psutil
    mem = psutil.virtual_memory()
    info['ram_total_gb'] = round(mem.total / (1024**3), 1)
    info['ram_available_gb'] = round(mem.available / (1024**3), 1)
except ImportError:
    info['ram'] = 'psutil not available'

# Disk
try:
    total, used, free = shutil.disk_usage('C:\\')
    info['disk_total_gb'] = round(total / (1024**3), 1)
    info['disk_free_gb'] = round(free / (1024**3), 1)
except:
    info['disk'] = 'unknown'

# Tools
tool_checks = {
    'blender': (['blender', '--version'], None),
    'inkscape': ([r'C:\Program Files\Inkscape\bin\inkscape.exe', '--version'], ['inkscape', '--version']),
    'imagemagick': (['magick', '--version'], ['convert', '--version']),
    'ffmpeg': (['ffmpeg', '-version'], None),
    'python': (['python', '--version'], None),
    'node': (['node', '--version'], None),
    'ollama': (['ollama', '--version'], None),
    'cmake': (['cmake', '--version'], None),
}
info['tools'] = {}
for name, (cmd1, cmd2) in tool_checks.items():
    found = False
    for cmd in [cmd1, cmd2]:
        if cmd is None:
            continue
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
            if r.returncode == 0:
                ver = (r.stdout or r.stderr).split('\n')[0][:80]
                info['tools'][name] = {'status': 'installed', 'version': ver}
                found = True
                break
        except:
            pass
    if not found:
        info['tools'][name] = {'status': 'not_found'}

# Check Unreal
ue_paths = [
    r'C:\Program Files\Epic Games\UE_5.8',
    r'C:\Program Files\Epic Games\UE_5.7',
    r'C:\Program Files\Epic Games\UE_5.6',
]
info['unreal'] = 'not_found'
for p in ue_paths:
    if os.path.exists(p):
        info['unreal'] = p
        break

# ComfyUI
comfyui_locations = []
for candidate in [
    os.path.expanduser('~\\ComfyUI'),
    os.path.expanduser('~\\Desktop\\ComfyUI'),
    os.path.expanduser('~\\AppData\\Local\\Programs\\ComfyUI'),
    'C:\\ComfyUI',
]:
    if os.path.exists(candidate):
        comfyui_locations.append(candidate)
        # Check for models dir
        models_dir = os.path.join(candidate, 'models', 'checkpoints')
        if os.path.exists(models_dir):
            comfyui_locations.append('models: ' + str([f for f in os.listdir(models_dir) if f.endswith(('.safetensors', '.ckpt'))][:10]))
info['comfyui'] = comfyui_locations if comfyui_locations else 'not_found'

# Torch / CUDA
try:
    r = subprocess.run(['python', '-c', 'import torch; print(torch.__version__, cuda=torch.cuda.is_available(), device=torch.cuda.get_device_name(0) if torch.cuda.is_available() else "no_gpu")'],
                       capture_output=True, text=True, timeout=10)
    info['torch'] = r.stdout.strip() if r.returncode == 0 else f'not_found: {r.stderr[:100]}'
except:
    info['torch'] = 'error'

# CUDA toolkit
try:
    r = subprocess.run(['nvcc', '--version'], capture_output=True, text=True, timeout=8)
    if r.returncode == 0:
        for line in r.stdout.split('\n'):
            if 'release' in line.lower():
                info['cuda_toolkit'] = line.strip()[:80]
                break
    else:
        info['cuda_toolkit'] = 'not_found'
except:
    info['cuda_toolkit'] = 'not_found'

# 9Router
try:
    import urllib.request
    r = urllib.request.urlopen('http://127.0.0.1:20128/api/health', timeout=5)
    info['nine_router'] = 'running'
except Exception as e:
    info['nine_router'] = f'down: {str(e)[:80]}'

# Ollama models
try:
    r = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=8)
    if r.returncode == 0:
        lines = [l.strip() for l in r.stdout.strip().split('\n')[1:] if l.strip()]
        info['ollama_models'] = [l.split()[0] for l in lines]
    else:
        info['ollama_models'] = 'error'
except:
    info['ollama_models'] = 'not_found'

# Existing model weights anywhere
weight_extensions = ('.safetensors', '.ckpt', '.pt', '.pth', '.bin')
model_locations = []
search_dirs = [
    os.path.expanduser('~\\ComfyUI'),
    os.path.expanduser('~\\AppData\\Local\\NVIDIA'),
    os.path.expanduser('~\\.cache'),
]
for sd in search_dirs:
    if os.path.exists(sd):
        for root, dirs, files in os.walk(sd):
            depth = root.replace(sd, '').count(os.sep)
            if depth > 3:
                dirs.clear()
                continue
            for f in files:
                if f.endswith(weight_extensions) and os.path.getsize(os.path.join(root, f)) > 100 * 1024 * 1024:
                    model_locations.append({'path': os.path.join(root, f), 'size_mb': round(os.path.getsize(os.path.join(root, f)) / (1024**2))})
                    if len(model_locations) > 20:
                        break
            if len(model_locations) > 20:
                break
info['existing_model_weights'] = model_locations

# Foundry creative skills
foundry_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if '__file__' in dir() else os.getcwd()
creative_skills = []
skills_dir = os.path.join(foundry_path, 'skills')
if os.path.exists(skills_dir):
    for f in os.listdir(skills_dir):
        if 'visual' in f.lower() or 'creative' in f.lower() or 'art' in f.lower():
            creative_skills.append(f)
info['foundry_creative_skills'] = creative_skills

print(json.dumps(info, indent=2, default=str))
