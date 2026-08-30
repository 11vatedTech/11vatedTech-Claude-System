"""
ComfyUI Production Runner for 11vatedTech Visual Production Intelligence

Provides programmatic ComfyUI workflow execution:
- Text-to-image generation
- ControlNet-guided generation
- Reference-based generation (IP-Adapter when available)
- Image upscaling
- Image editing (inpaint/outpaint workflows)

Usage:
    from scripts.visual.comfyui_runner import ComfyUIRunner
    
    runner = ComfyUIRunner()
    result = runner.generate(
        prompt="cinematic portrait, dramatic lighting",
        model="dreamshaper_8",
        width=512, height=768, steps=20
    )
"""

import json
import time
import os
import urllib.request
from pathlib import Path
from typing import Optional, Dict, Any, List


COMFYUI_URL = os.environ.get("COMFYUI_URL", "http://127.0.0.1:8188")
COMFYUI_INPUT = Path(os.environ.get("COMFYUI_INPUT", 
    os.path.join(os.path.expanduser("~"), "ComfyUI", "input")))
COMFYUI_OUTPUT = Path(os.environ.get("COMFYUI_OUTPUT",
    os.path.join(os.path.expanduser("~"), "ComfyUI", "output")))

# Model aliases -> actual checkpoint filenames
MODEL_MAP = {
    "dreamshaper_8": "dreamshaper_8.safetensors",
    "dreamshaper_8_sd15": "dreamshaper_8.safetensors",
    "dreamshaper_xl": "dreamshaper_xl_turbo_v21.safetensors",
    "dreamshaper_xl_turbo": "dreamshaper_xl_turbo_v21.safetensors",
}

CONTROLNET_MAP = {
    "canny": "control_v11p_sd15_canny.pth",
    "depth": "control_v11f1p_sd15_depth.pth",
    "openpose": "control_v11p_sd15_openpose.pth",
}

UPSCALE_MAP = {
    "realesrgan_x4": "RealESRGAN_x4plus.pth",
    "realesrgan_anime": "RealESRGAN_x4plus_anime_6B.pth",
}

NEGATIVE_DEFAULT = "ugly, blurry, low quality, deformed, disfigured, watermark, text, logo, bad anatomy"


class ComfyUIRunner:
    """Programmatic ComfyUI execution engine."""
    
    def __init__(self, url: str = COMFYUI_URL):
        self.url = url
        self._check_connection()
    
    def _check_connection(self):
        """Verify ComfyUI is running."""
        try:
            urllib.request.urlopen(f"{self.url}/system_stats", timeout=5)
        except Exception as e:
            raise ConnectionError(f"ComfyUI not reachable at {self.url}: {e}")
    
    def _submit_and_wait(self, workflow: dict, timeout: int = 300) -> dict:
        """Submit workflow and wait for completion."""
        prompt_data = json.dumps({"prompt": workflow}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.url}/prompt",
            data=prompt_data,
            headers={"Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read().decode())
        prompt_id = result["prompt_id"]
        
        for i in range(timeout // 2):
            time.sleep(2)
            try:
                r = urllib.request.urlopen(f"{self.url}/history/{prompt_id}", timeout=5)
                history = json.loads(r.read().decode())
                if prompt_id in history:
                    entry = history[prompt_id]
                    status = entry.get("status", {})
                    if status.get("completed"):
                        return {
                            "success": True,
                            "prompt_id": prompt_id,
                            "outputs": entry.get("outputs", {}),
                        }
                    elif status.get("status_str") == "error":
                        error_msg = ""
                        for m in status.get("messages", []):
                            if m[0] == "execution_error":
                                error_msg = m[1].get("exception_message", "unknown")
                        return {
                            "success": False,
                            "prompt_id": prompt_id,
                            "error": error_msg,
                        }
            except Exception:
                pass
        
        return {"success": False, "prompt_id": prompt_id, "error": "timeout"}
    
    def _get_output_images(self, result: dict, save_node_id: str = "9") -> List[str]:
        """Extract output image filenames from a completed result."""
        images = []
        outputs = result.get("outputs", {})
        node_out = outputs.get(save_node_id, {})
        for img in node_out.get("images", []):
            images.append(img["filename"])
        return images
    
    def generate(
        self,
        prompt: str,
        negative: str = NEGATIVE_DEFAULT,
        model: str = "dreamshaper_8",
        width: int = 512,
        height: int = 768,
        steps: int = 20,
        cfg: float = 7.0,
        sampler: str = "euler_ancestral",
        scheduler: str = "normal",
        seed: int = -1,
        batch_size: int = 1,
        timeout: int = 300,
    ) -> dict:
        """
        Generate an image from a text prompt.
        
        Returns:
            dict with keys: success, output_files, prompt_id, error
        """
        if seed == -1:
            import random
            seed = random.randint(0, 2**32 - 1)
        
        ckpt = MODEL_MAP.get(model, model)
        
        workflow = {
            "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": ckpt}},
            "5": {"class_type": "EmptyLatentImage", "inputs": {
                "width": width, "height": height, "batch_size": batch_size
            }},
            "6": {"class_type": "CLIPTextEncode", "inputs": {
                "text": prompt, "clip": ["4", 1]
            }},
            "7": {"class_type": "CLIPTextEncode", "inputs": {
                "text": negative, "clip": ["4", 1]
            }},
            "3": {"class_type": "KSampler", "inputs": {
                "seed": seed, "steps": steps, "cfg": cfg,
                "sampler_name": sampler, "scheduler": scheduler, "denoise": 1.0,
                "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0],
                "latent_image": ["5", 0],
            }},
            "8": {"class_type": "VAEDecode", "inputs": {
                "samples": ["3", 0], "vae": ["4", 2]
            }},
            "9": {"class_type": "SaveImage", "inputs": {
                "filename_prefix": "vpi_gen", "images": ["8", 0]
            }},
        }
        
        result = self._submit_and_wait(workflow, timeout)
        if result["success"]:
            result["output_files"] = self._get_output_images(result)
        else:
            result["output_files"] = []
        return result
    
    def generate_controlnet(
        self,
        prompt: str,
        control_type: str = "canny",
        control_image: str = "",
        negative: str = NEGATIVE_DEFAULT,
        model: str = "dreamshaper_8",
        width: int = 512,
        height: int = 768,
        control_strength: float = 0.8,
        steps: int = 20,
        cfg: float = 7.0,
        seed: int = -1,
        timeout: int = 300,
    ) -> dict:
        """
        Generate an image guided by a ControlNet edge/pose/depth map.
        
        control_image: filename in ComfyUI input directory
        """
        if seed == -1:
            import random
            seed = random.randint(0, 2**32 - 1)
        
        ckpt = MODEL_MAP.get(model, model)
        cn_model = CONTROLNET_MAP.get(control_type, control_type)
        
        workflow = {
            "1": {"class_type": "LoadImage", "inputs": {"image": control_image}},
            "2": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": ckpt}},
            "10": {"class_type": "ControlNetLoader", "inputs": {"control_net_name": cn_model}},
            "11": {"class_type": "ControlNetApplyAdvanced", "inputs": {
                "strength": control_strength, "start_percent": 0.0, "end_percent": 1.0,
                "positive": ["6", 0], "negative": ["7", 0],
                "control_net": ["10", 0], "image": ["1", 0],
            }},
            "5": {"class_type": "EmptyLatentImage", "inputs": {
                "width": width, "height": height, "batch_size": 1
            }},
            "6": {"class_type": "CLIPTextEncode", "inputs": {
                "text": prompt, "clip": ["2", 1]
            }},
            "7": {"class_type": "CLIPTextEncode", "inputs": {
                "text": negative, "clip": ["2", 1]
            }},
            "3": {"class_type": "KSampler", "inputs": {
                "seed": seed, "steps": steps, "cfg": cfg,
                "sampler_name": "euler_ancestral", "scheduler": "normal", "denoise": 1.0,
                "model": ["2", 0], "positive": ["11", 0], "negative": ["11", 1],
                "latent_image": ["5", 0],
            }},
            "8": {"class_type": "VAEDecode", "inputs": {
                "samples": ["3", 0], "vae": ["2", 2]
            }},
            "9": {"class_type": "SaveImage", "inputs": {
                "filename_prefix": "vpi_cn", "images": ["8", 0]
            }},
        }
        
        result = self._submit_and_wait(workflow, timeout)
        if result["success"]:
            result["output_files"] = self._get_output_images(result)
        else:
            result["output_files"] = []
        return result
    
    def upscale(
        self,
        image_filename: str,
        model: str = "realesrgan_x4",
        timeout: int = 120,
    ) -> dict:
        """
        Upscale an image using Real-ESRGAN or similar.
        
        image_filename: filename in ComfyUI input directory
        """
        up_model = UPSCALE_MAP.get(model, model)
        
        workflow = {
            "1": {"class_type": "LoadImage", "inputs": {"image": image_filename}},
            "2": {"class_type": "UpscaleModelLoader", "inputs": {"model_name": up_model}},
            "3": {"class_type": "ImageUpscaleWithModel", "inputs": {
                "upscale_model": ["2", 0], "image": ["1", 0]
            }},
            "4": {"class_type": "SaveImage", "inputs": {
                "filename_prefix": "vpi_up", "images": ["3", 0]
            }},
        }
        
        result = self._submit_and_wait(workflow, timeout)
        if result["success"]:
            result["output_files"] = self._get_output_images(result, save_node_id="4")
        else:
            result["output_files"] = []
        return result
    
    def img2img(
        self,
        image_filename: str,
        prompt: str,
        negative: str = NEGATIVE_DEFAULT,
        model: str = "dreamshaper_8",
        denoise: float = 0.75,
        steps: int = 20,
        cfg: float = 7.0,
        seed: int = -1,
        timeout: int = 300,
    ) -> dict:
        """
        Image-to-image generation: encode existing image, add noise, denoise with prompt.
        Useful for style transfer, refinement, inpainting.
        """
        if seed == -1:
            import random
            seed = random.randint(0, 2**32 - 1)
        
        ckpt = MODEL_MAP.get(model, model)
        
        workflow = {
            "1": {"class_type": "LoadImage", "inputs": {"image": image_filename}},
            "2": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": ckpt}},
            "5": {"class_type": "VAEEncode", "inputs": {
                "pixels": ["1", 0], "vae": ["2", 2]
            }},
            "6": {"class_type": "CLIPTextEncode", "inputs": {
                "text": prompt, "clip": ["2", 1]
            }},
            "7": {"class_type": "CLIPTextEncode", "inputs": {
                "text": negative, "clip": ["2", 1]
            }},
            "3": {"class_type": "KSampler", "inputs": {
                "seed": seed, "steps": steps, "cfg": cfg,
                "sampler_name": "euler_ancestral", "scheduler": "normal",
                "denoise": denoise,
                "model": ["2", 0], "positive": ["6", 0], "negative": ["7", 0],
                "latent_image": ["5", 0],
            }},
            "8": {"class_type": "VAEDecode", "inputs": {
                "samples": ["3", 0], "vae": ["2", 2]
            }},
            "9": {"class_type": "SaveImage", "inputs": {
                "filename_prefix": "vpi_img2img", "images": ["8", 0]
            }},
        }
        
        result = self._submit_and_wait(workflow, timeout)
        if result["success"]:
            result["output_files"] = self._get_output_images(result)
        else:
            result["output_files"] = []
        return result
    
    def batch_generate(
        self,
        prompt: str,
        seeds: List[int],
        negative: str = NEGATIVE_DEFAULT,
        model: str = "dreamshaper_8",
        width: int = 512,
        height: int = 768,
        steps: int = 20,
        cfg: float = 7.0,
        timeout: int = 600,
    ) -> dict:
        """Generate multiple variations with different seeds for creative exploration."""
        all_files = []
        for i, seed in enumerate(seeds):
            r = self.generate(
                prompt=prompt, negative=negative, model=model,
                width=width, height=height, steps=steps, cfg=cfg,
                seed=seed, timeout=timeout,
            )
            if r["success"]:
                all_files.extend(r["output_files"])
            else:
                print(f"Seed {seed} failed: {r.get('error', '?')}")
        
        return {
            "success": len(all_files) > 0,
            "output_files": all_files,
            "count": len(all_files),
        }


def copy_to_comfyui_input(source_path: str, filename: str = "") -> str:
    """Copy an external image into ComfyUI's input directory for use in workflows."""
    import shutil
    if not filename:
        filename = os.path.basename(source_path)
    dest = COMFYUI_INPUT / filename
    shutil.copy2(source_path, dest)
    return filename


if __name__ == "__main__":
    runner = ComfyUIRunner()
    
    print("=== VPI Generation Test Suite ===\n")
    
    # Test 1: DreamShaper 8 generation
    print("1. DreamShaper 8 (512x768)...")
    r1 = runner.generate(
        prompt="cinematic portrait, dramatic volumetric lighting, golden hour, bokeh, 35mm film, professional fashion",
        model="dreamshaper_8", width=512, height=768, steps=20, seed=42,
    )
    print(f"   Result: {'SUCCESS' if r1['success'] else 'FAIL'} - {r1['output_files']}\n")
    
    # Test 2: DreamShaper XL generation
    print("2. DreamShaper XL Turbo (1024x1024)...")
    r2 = runner.generate(
        prompt="cinematic portrait, dramatic volumetric lighting, golden hour, bokeh, 35mm film, professional fashion",
        model="dreamshaper_xl", width=1024, height=1024, steps=15, cfg=2.0,
        scheduler="sgm_uniform", seed=42,
    )
    print(f"   Result: {'SUCCESS' if r2['success'] else 'FAIL'} - {r2['output_files']}\n")
    
    print("=== All tests complete ===")
