"""Runner-side helper: turn the MOE 單字屬性聲音檔 index into CSV and copy the wavs for chosen characters.
usage: moe_dump.py AUDIO_ZIP OUT_DIR CHARS"""
import csv, re, sys, zipfile, io
import openpyxl
zpath, out, chars = sys.argv[1], sys.argv[2], set(sys.argv[3])
z = zipfile.ZipFile(zpath)
names = {n.rsplit('/', 1)[-1][:-4]: n for n in z.namelist() if n.endswith('.wav')}
xl = [n for n in z.namelist() if n.endswith('.xlsx')][0]
wb = openpyxl.load_workbook(io.BytesIO(z.read(xl)), read_only=True)
want = set()
with open(f'{out}/index.csv', 'w', newline='') as f:
    w = csv.writer(f)
    for ws in wb.worksheets:
        for row in ws.iter_rows(values_only=True):
            cells = ['' if c is None else str(c) for c in row]
            w.writerow(cells)
            if any(c.strip() in chars for c in cells):
                for c in cells:
                    for m in re.findall(r'\d{4}[A-Z]?', c):
                        if m in names: want.add(m)
for k in sorted(want):
    open(f'{out}/{k}.wav', 'wb').write(z.read(names[k]))
print(len(want), 'wavs')
