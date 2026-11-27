from pathlib import Path
import hashlib,json,csv,zipfile,importlib.util
from lxml import etree as E
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math','a':'http://schemas.openxmlformats.org/drawingml/2006/main','wp':'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def js(p,v):
 p=Path(p);p.parent.mkdir(exist_ok=True,parents=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf8')
def cs(p,rows,fields=None):
 rows=list(rows);p=Path(p);p.parent.mkdir(exist_ok=True,parents=True)
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields or list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def rd(p):
 with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def txt(n):return ''.join(x.text or '' for x in n.iter() if x.tag in ['{'+NS['w']+'}t','{'+NS['m']+'}t'])
def load(name,p):
 spec=importlib.util.spec_from_file_location(name,p);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def c14(n):return E.tostring(n,method='c14n')
def docroot(p):
 with zipfile.ZipFile(p) as z:return E.fromstring(z.read('word/document.xml'))
