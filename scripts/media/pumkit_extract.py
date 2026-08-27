#!/usr/bin/env python3
"""Deterministic canonical PUMKIT asset extraction.

Secondary assets are only promoted when their object-level masks are explicitly
bounded and pass contrast/source-overlay QA. No generation or redraw is used.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
REF = ROOT / 'Frontend-Designs' / 'Pumkit-Frontend-Design' / 'Concept-Art_and_references'
OUT = ROOT / 'Frontend-Designs' / 'Pumkit-Frontend-Design' / 'assets' / 'pumkit'
CROPS = {'pumkit-primary': ('IMG_1168.png', (378, 74, 900, 690))}
ATTEMPTS = [
    {'semantic_state':'PRIMARY_STANDING','source':'IMG_1168.png','roi':[378,74,900,690],'technique':'light-paper color-distance matte','status':'APPROVED','output':'pumkit-primary.png'},
    {'semantic_state':'IDLE','source':'Pumkit.PNG','roi':None,'technique':'object-level recovery required','status':'REJECTED_PENDING_BOUNDED_MASK','output':None},
    {'semantic_state':'PLAYFUL','source':'IMG_1168.png','roi':None,'technique':'object-level recovery required','status':'REJECTED_PENDING_BOUNDED_MASK','output':None},
    {'semantic_state':'ALERT','source':'IMG_3470.png','roi':None,'technique':'object-level recovery required','status':'REJECTED_PENDING_BOUNDED_MASK','output':None},
    {'semantic_state':'SLEEP','source':'Pumkit.PNG','roi':None,'technique':'object-level recovery required','status':'REJECTED_PENDING_BOUNDED_MASK','output':None},
    {'semantic_state':'LIQUID_POOL','source':'IMG_3470.png','roi':None,'technique':'object-level recovery required','status':'REJECTED_PENDING_BOUNDED_MASK','output':None},
    {'semantic_state':'KIT','source':'Pumkit.PNG','roi':None,'technique':'object-level recovery required','status':'REJECTED_PENDING_BOUNDED_MASK','output':None},
    {'semantic_state':'KITTEN','source':'IMG_3470.png','roi':None,'technique':'object-level recovery required','status':'REJECTED_PENDING_BOUNDED_MASK','output':None},
    {'semantic_state':'KITTY','source':'IMG_3470.png','roi':None,'technique':'object-level recovery required','status':'REJECTED_PENDING_BOUNDED_MASK','output':None},
    {'semantic_state':'EYE_DETAIL','source':'IMG_1168.png','roi':None,'technique':'source detail crop pending','status':'REJECTED_PENDING_BOUNDED_MASK','output':None},
    {'semantic_state':'EAR_DETAIL','source':'IMG_1168.png','roi':None,'technique':'source detail crop pending','status':'REJECTED_PENDING_BOUNDED_MASK','output':None},
    {'semantic_state':'FOREHEAD_MARK','source':'IMG_1168.png','roi':None,'technique':'source detail crop pending','status':'REJECTED_PENDING_BOUNDED_MASK','output':None},
    {'semantic_state':'PAW_MARK','source':'Pumkit.PNG','roi':None,'technique':'source detail crop pending','status':'REJECTED_PENDING_BOUNDED_MASK','output':None},
    {'semantic_state':'LIQUID_TEXTURE','source':'IMG_3470.png','roi':None,'technique':'object-level recovery required','status':'REJECTED_PENDING_BOUNDED_MASK','output':None},
]

def sha(path: Path) -> str:
    h = hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()

def crop_mask(crop: Image.Image) -> Image.Image:
    rgb = crop.convert('RGB'); px = rgb.load(); alpha = Image.new('L', rgb.size, 0); ap = alpha.load()
    for y in range(rgb.height):
        for x in range(rgb.width):
            r,g,b = px[x,y]; mx,mn=max(r,g,b),min(r,g,b); chroma=mx-mn; lum=(r+g+b)/3
            paper = r > 164 and g > 158 and b > 148 and chroma < 32
            ap[x,y] = 0 if paper else (max(0, int((190-lum)*2.2)) if lum > 150 and chroma < 48 else 255)
    return alpha.filter(ImageFilter.MedianFilter(3)).filter(ImageFilter.GaussianBlur(.35))

def composite(asset: Image.Image, bg: tuple[int,int,int], size=(680,520)) -> Image.Image:
    base=Image.new('RGB',size,bg); item=asset.copy(); item.thumbnail((size[0]-40,size[1]-40),Image.Resampling.LANCZOS)
    base.paste(item,((size[0]-item.width)//2,(size[1]-item.height)//2),item.getchannel('A')); return base

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('--out',default=str(OUT)); args=ap.parse_args(); out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    records=[]
    for name,(filename,box) in CROPS.items():
        src=REF/filename; source=Image.open(src).convert('RGB'); crop=source.crop(box); alpha=crop_mask(crop); rgba=crop.convert('RGBA'); rgba.putalpha(alpha); bbox=alpha.getbbox()
        if not bbox: raise RuntimeError(f'No foreground detected for {name}')
        rgba=rgba.crop(bbox); png=out/f'{name}.png'; rgba.save(png,'PNG',optimize=True); qa=out/f'{name}-qa'; qa.mkdir(exist_ok=True)
        for key,bg in {'white':(255,255,255),'black':(0,0,0),'gray':(128,128,128),'bright':(30,180,220)}.items(): composite(rgba,bg).save(qa/f'{key}.png')
        overlay=crop.convert('RGBA'); overlay.putalpha(Image.new('L',crop.size,90))
        extracted=rgba.copy(); extracted.thumbnail(crop.size,Image.Resampling.LANCZOS); overlay.alpha_composite(extracted,((crop.width-extracted.width)//2,(crop.height-extracted.height)//2)); overlay.save(qa/'source-overlay.png')
        contact=Image.new('RGB',(1360,1040),(35,35,35)); draw=ImageDraw.Draw(contact)
        for i,(key,bg) in enumerate({'white':(255,255,255),'black':(0,0,0),'gray':(128,128,128),'bright':(30,180,220)}.items()):
            image=composite(rgba,bg); x=(i%2)*680; y=(i//2)*520; contact.paste(image,(x,y)); draw.text((x+18,y+18),key.upper(),fill=(255,210,120))
        contact.save(qa/'contact-sheet.png')
        records.append({'asset':name,'source_filename':filename,'source_sha256':sha(src),'source_dimensions':source.size,'crop_box_xyxy':box,'mask_method':'light-paper color-distance + median/low-radius gaussian alpha refinement','output_dimensions':rgba.size,'output_sha256':sha(png),'generative_modification':False,'qa_paths':[str(p.relative_to(ROOT)) for p in sorted(qa.iterdir())]})
    manifest={'package':'pumkit-canon-asset-recovery-v2','policy':'no primitive character proxies; no rectangular crop promoted without object-level QA','attempts':ATTEMPTS,'approved_assets':records,'rejected_assets':[a for a in ATTEMPTS if a['status']!='APPROVED'],'primitive_character_proxies_remaining':0}
    (out/'recovery-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    (out/'provenance.json').write_text(json.dumps({'package':'pumkit-canonical-extraction-v2','status':'primary-approved-secondary-recovery-pending','assets':records,'source_policy':'supplied sheets remain reference-only; outputs preserve canonical source pixels; no generation'},indent=2),encoding='utf-8')
    print(json.dumps(manifest,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
