
#!/usr/bin/env python3
"""
ransomware_dataset_mutator.py (Expanded)
--------------------------------
Now supports manipulation of: .pdf, .docx, .txt, .csv, .json, .doc

Same manipulations: random rename, metadata strip/alter, header corruption,
and mismatched extension.

See Appendix for details.
"""

import argparse, io, json, os, random, re, shutil, string, sys, zipfile
from datetime import datetime
from pathlib import Path

# Optional PDF dependency
try:
    from pypdf import PdfReader, PdfWriter
    PYPDF_AVAILABLE = True
except Exception:
    PYPDF_AVAILABLE = False

RAND_CHARS = string.ascii_letters + string.digits

def rand_name(length=12, rng=None):
    r = rng or random
    return "".join(r.choice(RAND_CHARS) for _ in range(length))

def safe_copy(src: Path, dst: Path, dry_run: bool):
    if dry_run: return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

def write_bytes(dst: Path, data: bytes, dry_run: bool):
    if dry_run: return
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, "wb") as f:
        f.write(data)

def choose_mismatched_extension(ext: str) -> str:
    ext = ext.lower()
    mapping = {
        ".pdf": [".jpg", ".png", ".docx"],
        ".docx": [".jpg", ".pdf", ".csv"],
        ".doc": [".txt", ".pdf"],
        ".csv": [".docx", ".pdf", ".json"],
        ".txt": [".jpg", ".pdf", ".json"],
        ".json": [".csv", ".txt", ".docx"],
    }
    return random.choice(mapping.get(ext, [".bin"]))

# ----- Metadata stripping -----

def strip_docx_metadata(data: bytes) -> bytes:
    in_mem = io.BytesIO(data)
    with zipfile.ZipFile(in_mem, "r") as zin:
        out_mem = io.BytesIO()
        with zipfile.ZipFile(out_mem, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                content = zin.read(item.filename)
                if item.filename == "docProps/core.xml":
                    content = (b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                               b'<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
                               b'xmlns:dc="http://purl.org/dc/elements/1.1/" '
                               b'xmlns:dcterms="http://purl.org/dc/terms/" '
                               b'xmlns:dcmitype="http://purl.org/dc/dcmitype/" '
                               b'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
                               b'<dc:title></dc:title><dc:subject></dc:subject><dc:creator></dc:creator>'
                               b'<cp:keywords></cp:keywords><dc:description></dc:description>'
                               b'<cp:lastModifiedBy></cp:lastModifiedBy>'
                               b'<dcterms:created xsi:type="dcterms:W3CDTF">1970-01-01T00:00:00Z</dcterms:created>'
                               b'<dcterms:modified xsi:type="dcterms:W3CDTF">1970-01-01T00:00:00Z</dcterms:modified>'
                               b'</cp:coreProperties>')
                elif item.filename == "docProps/app.xml":
                    content = (b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                               b'<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
                               b'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
                               b'<Application>Docx</Application></Properties>')
                zout.writestr(item, content)
    return out_mem.getvalue()

def strip_pdf_metadata(data: bytes) -> bytes:
    if PYPDF_AVAILABLE:
        src = io.BytesIO(data)
        reader = PdfReader(src)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        writer.add_metadata({})
        out = io.BytesIO()
        writer.write(out)
        return out.getvalue()
    text = data
    text = re.sub(br"(<\?xpacket begin=.*?</\?xpacket>)", b"", text, flags=re.DOTALL)
    for key in [b"/Author", b"/Creator", b"/Producer", b"/Title", b"/ModDate", b"/CreationDate"]:
        text = re.sub(key + br"\s*\(.*?\)", key + b"( )", text)
    return text

def strip_metadata(src: Path, outdir: Path, dry_run: bool) -> Path:
    dst = (outdir or src.parent) / (src.stem + ".sanitized" + src.suffix)
    if src.suffix.lower() == ".docx":
        data = src.read_bytes()
        new_bytes = strip_docx_metadata(data)
        write_bytes(dst, new_bytes, dry_run)
    elif src.suffix.lower() == ".pdf":
        data = src.read_bytes()
        new_bytes = strip_pdf_metadata(data)
        write_bytes(dst, new_bytes, dry_run)
    else:
        # txt, csv, json, doc fallback: copy and zero timestamps
        safe_copy(src, dst, dry_run)
    if not dry_run:
        ts = datetime(1970,1,1).timestamp()
        try: os.utime(dst,(ts,ts))
        except: pass
    return dst

# ----- Header corruption -----

def corrupt_header(src: Path, outdir: Path, mode: str, nbytes: int, dry_run: bool) -> Path:
    data = src.read_bytes()
    n = min(max(nbytes, 1), len(data))
    if mode=="truncate":
        new_bytes = data[n:]
    elif mode=="zero":
        new_bytes = b"\x00"*n + data[n:]
    else:
        prefix = bytes((b ^ 0xFF) for b in data[:n])
        new_bytes = prefix + data[n:]
    dst = (outdir or src.parent)/(src.stem+".corrupt"+src.suffix)
    write_bytes(dst,new_bytes,dry_run)
    return dst

# ----- Main -----

def find_files(paths):
    files=[]
    for p in paths:
        pth=Path(p)
        if pth.is_dir():
            for ext in ("*.docx","*.pdf","*.csv","*.txt","*.json","*.doc"):
                files.extend(pth.rglob(ext))
        else:
            if pth.exists(): files.append(pth)
    return list(dict.fromkeys(files))

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("paths",nargs="+")
    ap.add_argument("--out",default="")
    ap.add_argument("--seed",type=int)
    ap.add_argument("--dry-run",action="store_true")
    ap.add_argument("--rename",action="store_true")
    ap.add_argument("--stripmeta",action="store_true")
    ap.add_argument("--corrupt",action="store_true")
    ap.add_argument("--mismatch",action="store_true")
    ap.add_argument("--all",action="store_true")
    ap.add_argument("--mode",choices=["flip","zero","truncate"],default="flip")
    ap.add_argument("--bytes",type=int,default=8)
    args=ap.parse_args(argv)
    if args.all:
        args.rename=args.stripmeta=args.corrupt=args.mismatch=True
    rng=random.Random(args.seed) if args.seed is not None else random
    files=find_files(args.paths)
    outdir=Path(args.out) if args.out else None
    if outdir and not args.dry_run: outdir.mkdir(parents=True,exist_ok=True)
    for f in files:
        g=f
        if args.rename:
            new_name=rand_name(rng=rng)+f.suffix
            g=(outdir or f.parent)/new_name
            safe_copy(f,g,args.dry_run)
        if args.stripmeta: g=strip_metadata(g,outdir,args.dry_run)
        if args.corrupt: g=corrupt_header(g,outdir,args.mode,args.bytes,args.dry_run)
        if args.mismatch:
            bad=choose_mismatched_extension(g.suffix)
            dst=(outdir or g.parent)/(g.stem+bad)
            safe_copy(g,dst,args.dry_run)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
