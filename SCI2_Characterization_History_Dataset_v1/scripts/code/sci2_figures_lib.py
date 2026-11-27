from pathlib import Path
import sys,os,json,hashlib,csv,re,zipfile,io
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.deps'))
os.environ['MPLCONFIGDIR']=str(ROOT/'.mplconfig')
def digest(b):return hashlib.sha256(b).hexdigest()
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b)
 return h.hexdigest()
def js(path,obj):
 (ROOT/path).write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
def csvout(path,rows):
 with (ROOT/path).open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def style():
 import matplotlib
 matplotlib.use('Agg')
 matplotlib.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.labelsize':8,'axes.titlesize':9,'xtick.labelsize':8,'ytick.labelsize':8,'lines.linewidth':1,'pdf.fonttype':42,'svg.fonttype':'none','svg.hashsalt':'SCI2_FROZEN_20261025','path.simplify':False})
def save(fig,name):
 for ext in ['pdf','svg','png']:
  md={'Creator':'SCI2 frozen data Python'}
  if ext=='pdf':md.update(CreationDate=None,ModDate=None)
  if ext=='svg':md['Date']=None
  fig.savefig(ROOT/'figures'/(name+('_600dpi' if ext=='png' else '')+'.'+ext),dpi=600,metadata=md)
def number(s,params):
 s=s.strip("'{}\"").lower()
 if s in params:return number(params[s],params)
 m=re.fullmatch(r'([+-]?[\d.]+(?:e[+-]?\d+)?)([a-z]*)',s)
 if not m:raise ValueError('Unsupported numeric expression: '+s)
 return float(m[1])*{'':1,'n':1e-9,'p':1e-12,'u':1e-6,'m':1e-3,'k':1e3,'meg':1e6}[m[2]]
def parse_deck(b,source):
 text=b.decode();lines=[]
 for line in text.splitlines():
  line=line.strip()
  if line.startswith('+'):lines[-1]+=' '+line[1:]
  elif line and not line.startswith('*'):lines.append(line)
 params={};subs={};top=[];active=None
 meta=dict(re.findall(r'^\*\s*(\w+)=(.*)$',text,re.M))
 for line in lines:
  tok=line.split();cmd=tok[0].lower()
  if cmd=='.param':params.update({k.lower():v for k,v in re.findall(r'(\w+)\s*=\s*(\S+)',line)})
  elif cmd=='.subckt':active=tok[1].lower();subs[active]={'pins':[x.lower() for x in tok[2:]],'mos':[]}
  elif cmd=='.ends':active=None
  elif cmd.startswith('m'):
   assert active and len(tok)>=6,'Unsupported top-level MOS'
   subs[active]['mos'].append((tok,dict((k.lower(),v) for k,v in re.findall(r'(\w+)\s*=\s*(\S+)',line))))
  elif not active:top.append(tok)
 instances=[t for t in top if t[0].lower().startswith('x')];rows=[]
 for stage,t in enumerate(instances,1):
  sub=subs[t[-1].lower()];assert len(t[1:-1])==len(sub['pins'])
  binding=dict(zip(sub['pins'],[x.lower() for x in t[1:-1]]))
  for mt,mp in sub['mos']:
   local=[x.lower() for x in mt[1:5]]
   bound=[binding.get(n,t[0].lower()+'.'+n) for n in local]
   rows.append(dict(context=meta['run_id'],technology=meta['technology'],topology=meta['topology'],position=meta['position'],stage=stage,instance=t[0],device=mt[0],role=re.sub(r'^MXg\d+','',mt[0]),model=mt[5],d=bound[0],g=bound[1],s=bound[2],b=bound[3],local_d=local[0],local_g=local[1],local_s=local[2],local_b=local[3],W_m=number(mp['w'],params),L_m=number(mp['l'],params),switching=binding['sw'],fixed=binding['fix'],output=binding['y'],source=source,source_sha256=digest(b)))
 return {'meta':meta,'params':params,'top':top,'rows':rows,'instances':instances,'text':text}
def source_zip():
 return Path(__file__).resolve().parents[2] / 'data' / 'netlists' / 'SCI2_96_topology_netlists_only.zip'
