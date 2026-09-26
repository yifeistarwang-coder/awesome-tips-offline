#!/usr/bin/env python3
"""Extract per-slide text and images from a .pptx (stdlib only)."""
import json, re, shutil, sys, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'rel': 'http://schemas.openxmlformats.org/package/2006/relationships',
}

def slide_num(name):
    return int(re.findall(r'(\d+)', name)[0])

def extract(pptx_path, outdir):
    outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    z = zipfile.ZipFile(pptx_path)
    slides = sorted([n for n in z.namelist() if re.match(r'ppt/slides/slide\d+\.xml$', n)], key=slide_num)
    result = []
    for sn in slides:
        num = slide_num(sn)
        xml = z.read(sn)
        root = ET.fromstring(xml)
        texts = [t.text or '' for t in root.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}t')]
        # gather images referenced by this slide in document order
        rels_name = f'ppt/slides/_rels/slide{num}.xml.rels'
        rels = {}
        if rels_name in z.namelist():
            rr = ET.fromstring(z.read(rels_name))
            for rel in rr:
                rid = rel.get('Id'); target = rel.get('Target', '')
                if 'media/' in target:
                    rels[rid] = target
        images = []
        for blip in root.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}blip'):
            rid = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
            if rid and rid in rels:
                target = rels[rid]
                media_name = target.split('/')[-1]
                source = 'ppt/media/' + media_name
                if source in z.namelist():
                    ext = Path(media_name).suffix.lower()
                    out_name = f'slide{num:02d}-{len(images)+1}{ext}'
                    dest = outdir / out_name
                    if not dest.exists():
                        with z.open(source) as fsrc, open(dest, 'wb') as fdst:
                            shutil.copyfileobj(fsrc, fdst)
                    images.append(out_name)
        # notes
        notes = []
        notes_name = f'ppt/notesSlides/notesSlide{num}.xml'
        if notes_name in z.namelist():
            nr = ET.fromstring(z.read(notes_name))
            notes = [t.text or '' for t in nr.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}t')]
        result.append({'slide': num, 'texts': [t for t in texts if t.strip()], 'images': images, 'notes': [t for t in notes if t.strip()]})
    (outdir / 'slides.json').write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding='utf-8')
    return result

if __name__ == '__main__':
    data = extract(sys.argv[1], sys.argv[2])
    imgs = sum(len(s['images']) for s in data)
    chars = sum(sum(len(t) for t in s['texts']) for s in data)
    print(f"slides={len(data)} images={imgs} chars={chars}")
