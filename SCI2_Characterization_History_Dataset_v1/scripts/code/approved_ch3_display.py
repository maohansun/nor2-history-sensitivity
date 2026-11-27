#!/usr/bin/env python3
"""SCI2 frozen numeric figures. Stdlib + NumPy + Matplotlib only. No simulation/RAW/fit."""
import argparse,collections,csv,datetime,hashlib,json,math,os,re,shutil,struct,subprocess,sys,zipfile
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt, font_manager, image as mpimg
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.ticker import LogLocator, NullFormatter

COEF_SHA='fbca987626f71b6ee822f2df2aea72878192d5af0c71ff54d57d54988a99c789'
THETA_S=1.4557735994458199e-05
THETA_A=5.179560445477447
MODELS=['P0','P_R','P_R2','P_IS1','P_IS2','P_DIR2']
BLUE='#0072B2';RED='#D55E00';GREEN='#009E73';GRAY='#9A9A9A'
FIXED=datetime.datetime(2000,1,1,tzinfo=datetime.timezone.utc)
GROUPS=[(top,pos,edge) for top in ['NOR2','NAND2'] for pos in ['POS-A','POS-B'] for edge in ['td_phl','td_plh']]
FILES={'records':'data/frozen/RECORDS_ALL96.csv','amp':'data/statistics/AMP_RELATIVE_RECORDS.csv','pred':'data/frozen/PRED_RECORDS_RERUN.csv','v2b':'data/local_found/SCI2_MECH_MODEL_V1/D_V2B_PER_STAGE.csv','allocation':'data/frozen/allocation_96.csv'}
EDGE={'td_phl':r'$t_\mathrm{pHL}$','td_plh':r'$t_\mathrm{pLH}$'}
MM=1/25.4
VERSION='V1R3_DISPLAY_OPT'
V1R2_PRESERVED_HASHES={'Fig2.pdf': '1863d16cab716cfcd1cee79d43d0de0e8a2f4d3e7ed91b169a1662d7f62faf83', 'Fig2.png': '819e32c513039ae486255ce1dfc8702e36cf35af57df04c7a981d8dac958e511', 'grayscale_preview/Fig2_gray.png': '75beece977b7e798fc516965f0d64ddcb425b3723710ae6e2384c0dcb3245de8', 'Fig3.pdf': '6619c2e3dc9e40880fed15c361479d790edd321bfe40db68ed0d3e4142fc57ed', 'Fig3.png': '6dcd41b0e0782cf491e297f2ab70ccb57393388662fe13327441d9d153173af1', 'grayscale_preview/Fig3_gray.png': 'a7fc445a28af7b8a7026d42be7863762ae12904e0b3fbb78cf81631263ed8b47', 'Fig4.pdf': 'fa00d6b5129a8f0c13e23af31c88b22cc732a36ae9729b5c0258de31de0f67f2', 'Fig4.png': 'b81688da931b7a0be83d83945f4a0aa9633c6cbf40f0aced7265d9af35e3d2ad', 'grayscale_preview/Fig4_gray.png': 'febb67f4e1bcdeac8479e83723c625c8424c3d5e4bfdce60450b17f8953d4b09', 'Fig5.pdf': '07c2bc91567767ee73b53176fff7f3704cfab05f27eb793aa62d5da1ec5b63cd', 'Fig5.png': 'c6ca9f29b3cceb8017b87dfcdcb781ab15a23f9c9ea6d55b7cf2901ba1d897fd', 'grayscale_preview/Fig5_gray.png': '6667fc15159c01f5c579b378b1fd3909739648488462ee5a9c5e2327539613e7'}
BASELINE_ARCHIVE_SHA256='f25c706270fc3908b6a9f9108c9120d407f7cfe000c3180261b9bf10b22b6357'
PATCH_ARCHIVE_SHA256='024a8ef73283f0a4504be1a3e72742669d7f12ed93235ab2a2c586583edeb5e4'
PATCH_INSTRUCTION_SHA256='c685e2880cac7c691c3453e234b6636c11c746e85600bf5eccd011bf9af8c4e4'
V1_FIGURE_HASHES={'Fig2.pdf': '737349384c81c36b30a321a04f48879cbea788cda302fcff23f2bb17e612e253', 'Fig2.png': 'dbacd311b335555375888307ec50dbe0b6fb94e5475b6e64b0b13ff84899bd27', 'Fig3.pdf': '9e95510d48d155c3c783fde4239c5eed343bea4c1822f5534864abd35990e888', 'Fig3.png': '72f29fb71566c60f4bf1117578c8cdeb303657a99a76abc42411bbeb117f6755', 'Fig4.pdf': '013ba84d3ff2bbe9120c1650799f8f3248ea859f2c108930ec51532e38bda775', 'Fig4.png': '81ba50966351138fbbe3dfd8a2dc44a8dab39126ab2bd0aa575331a22d776bae', 'Fig5.pdf': 'b234856c652b43bdcd760237c0709a0eb46873ac6eb9f185d033395726a56a7b', 'Fig5.png': 'db27f56bcf65bd00d2cd0be12b1e60778ff920852504d029047757cfd02ef21c'}

class GateError(Exception):pass
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write_json(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf8')
def write_csv(p,rows,fields=None):
 rows=list(rows)
 if fields is None:fields=list(rows[0])
 with Path(p).open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)
def fnum(x):
 z=float(x)
 if not math.isfinite(z):raise GateError('Nonfinite numeric input: '+str(x))
 return z
def quant(a):return np.percentile(np.asarray(a,dtype=float),[0,5,25,50,75,95,100]).tolist()
def check(name,condition,actual,expected,qa):
 qa['scientific_gates'].append({'gate':name,'status':'PASS' if condition else 'FAIL','actual':actual,'expected':expected})
 if not condition:raise GateError('{}: expected {}; actual {}'.format(name,expected,actual))
 print('[PASS] '+name,flush=True)
def load_csv(name,path,required,locks):
 p=Path(path).resolve();data=p.read_bytes()
 with p.open(encoding='utf-8-sig',newline='') as f:
  reader=csv.DictReader(f);cols=reader.fieldnames;rows=list(reader)
 missing=set(required)-set(cols or [])
 locks.append({'logical_source':name,'absolute_path':str(p),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'records':len(rows),'fields':cols,'read_scope':'frozen CSV numeric records only'})
 if missing:raise GateError('{} missing required fields {}'.format(p,sorted(missing)))
 return rows
def unique_meta(records):
 d={}
 for r in records:
  v={k:r[k] for k in ['topology','position','tech','corner','duty']}
  if r['src'] in d and d[r['src']]!=v:raise GateError('Ambiguous configuration metadata '+r['src'])
  d[r['src']]=v
 return d

def science(a,out,qa,locks,fieldmap):
 locks.append({'logical_source':'V1R1_engineering_baseline','archive':'SCI2_CH3_FIGURES_V1R1.zip','sha256':'2873a035fc8c8a302e23eb77dc3454d77ee4858be0fbf6bf24a317ea96418ecf','read_scope':'sole V1R2 plotting baseline; unchanged frozen CSV bytes'})
 locks.extend([{'logical_source':'V1_engineering_baseline_archive','file':'SCI2_CH3_FIGURES_V1.zip','sha256':BASELINE_ARCHIVE_SHA256,'read_scope':'verified original archive; its exact CSV bytes were extracted without editing; original manifest checked'}, {'logical_source':'V1R1_author_patch_archive','file':'SCI2_CH3_V1R1_CODEX_PATCH.zip','sha256':PATCH_ARCHIVE_SHA256,'read_scope':'author instructions, not numeric replacement data'}, {'logical_source':'V1R1_governing_patch_markdown','file':'CODEX_CH3_FIGURES_V1R1_PATCH.md','sha256':PATCH_INSTRUCTION_SHA256,'read_scope':'bounded changes to Fig2 low display and Fig5 raw plotting population'}])
 req={'records':['src','role','edge','P0','P_IS1','topology','position','tech','corner','duty'],
      'amp':['src','role','edge','a','model','error_fs','dref_fs','relative_error'],
      'pred':['source_context_id','topology','position','stage','mos','edge','predicted_class','absW'],
      'v2b':['src','mos','edge','stage','floating_at_event','stim_at_1','stim_at_4','win_at_MF','win_at_E1'],
      'allocation':['source_context_id','tech','topology','position','corner','duty'],
      'coef':['src','mos','edge','S_E1','S_IS','q','role']}
 paths={k:(a.input_dir/(k+'.csv') if a.input_dir else a.r7/v) for k,v in FILES.items()}
 paths['coef']=a.input_dir/'coef.csv' if a.input_dir else a.coef
 for k,p in paths.items():
  if not p.exists():raise GateError('Missing frozen source {}: {}'.format(k,p))
 data={k:load_csv(k,p,req[k],locks) for k,p in paths.items()}
 # Priority A is immutable. B reconstruction is deliberately not attempted when A exists.
 check('priority_A_exact_SHA256',locks[-1]['sha256']==COEF_SHA,locks[-1]['sha256'],COEF_SHA,qa)
 if not a.input_dir:
  manifest=a.r7/'SHA256SUMS.txt';raw=manifest.read_bytes();locks.append({'logical_source':'R7_manifest','absolute_path':str(manifest.resolve()),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'records':len(raw.splitlines()),'read_scope':'source identity checks'})
  sums=dict((line.split('  ',1)[1],line.split('  ',1)[0]) for line in raw.decode('utf8').splitlines())
  for k,rel in FILES.items():
   measured=next(x['sha256'] for x in locks if x['logical_source']==k)
   check('R7_manifest_'+k,measured==sums.get(rel),measured,sums.get(rel),qa)
 else:
  expected=json.loads((a.input_dir/'EXPECTED_INPUT_HASHES.json').read_text(encoding='utf8'))
  for k,p in paths.items():check('portable_input_'+k,sha(p)==expected[k],sha(p),expected[k],qa)
 fieldmap.update({
  'coef':{'src':'src','mos':'mos','edge':'edge (td_phl/td_plh)','S_E1_fs_per_V':{'field':'S_E1','unit':'fs/V','factor':1},'S_IS_fs_per_V':{'field':'S_IS','unit':'fs/V','factor':1},'q_V':{'field':'q','unit':'V','factor':1,'meaning':'per-device nonnegative synthetic |ΔVth| already present in authoritative frozen PERMOS table; not common rounded amplitude'},'role':'role; existing transistor/role identity used without reassignment','stage':'integer captured by ^MXg(\\d{2}) from mos; 01..07','topology_position':'unique join src -> RECORDS_ALL96.src; topology/position'},
  'records':{'P0':'P0 [fs]','P_IS1':'P_IS1 [fs]','abs_transfer':'abs(P0-P_IS1) [fs]','keys':['src','role','edge']},
  'amp':{'amplitude':'float(a)','model':'model; identity aliases (none)','abs_error':'abs(error_fs) [fs]; verified against relative_error*abs(dref_fs)','keys':['src','role','edge','a','model']},
  'v2b':{'filter':'floating_at_event == True only','stimulus_k1':'stim_at_1 [fs/V]','stimulus_k4':'stim_at_4 [fs/V]','window_T':'win_at_MF [fs/V]','window_E':'win_at_E1 [fs/V]','plotted':'absolute value of each contrast; exact zero retained'},
  'pred':{'src':'source_context_id','mos':'mos','stage':'stage (integer)','edge':'edge','abs_window':'absW [fs/V]','predicted_class':{'Candidate':'SENSITIVE','Other':'NONFLOATING_STAGE'},'scientific_population':'raw 56 transistor-edge records; NOT stage maxima','plot_population':'56 RAW transistor records; same exact list passed to figure5 and ratio calculation','filter':"position == 'POS-B' and edge == 'td_phl'",'source_fields_retained':['source_context_id','topology','stage','mos','predicted_class','absW','position','edge'],'plot_y':'float(absW), original string also retained verbatim in FIG5_RAW_TRANSISTOR_RECORDS.csv','candidate_rule':"predicted_class == 'SENSITIVE'; topology/stage parity checked independently",'stage_aggregation_for_plot':False},
  'allocation':{'join':'unique source_context_id','node':'tech: PTM45 -> 45 nm; PTM65 -> 65 nm','VDD_V':'numeric prefix of corner ending V','temperature_C':'numeric suffix of corner ending C','duty':'duty, dimensionless'},
  'quantiles':{'method':'NumPy percentile default linear (Hyndman-Fan type 7)','used_for':'medians/Q1/Q3/5th/95th; all raw values including exact zero included'},
  'E_T_labels':{'E':'periodically repeated E1-type waveform','T':'target periodic waveform; MF in source names','stimulus_direction':'C(E,k)-C(T,k)','I':'[C(T,4)-C(T,1)]-[C(E,4)-C(E,1)]; not changed'}
 })
 records=data['records'];coef=data['coef'];amp=data['amp'];pred=data['pred'];v2b=data['v2b'];alloc=data['allocation']
 check('records_480',len(records)==480,len(records),480,qa)
 check('records_unique_keys',len(set((r['src'],r['role'],r['edge']) for r in records))==480,len(set((r['src'],r['role'],r['edge']) for r in records)),480,qa)
 meta=unique_meta(records);check('configurations_96',len(meta)==96,len(meta),96,qa)
 check('coef_rows_4032',len(coef)==4032,len(coef),4032,qa)
 check('coef_unique_keys',len(set((r['src'],r['mos'],r['edge']) for r in coef))==4032,len(set((r['src'],r['mos'],r['edge']) for r in coef)),4032,qa)
 normalized=[]
 for r in coef:
  if r['src'] not in meta:raise GateError('Coefficient metadata missing '+r['src'])
  st=re.match(r'^MXg(\d{2})([A-Za-z]+)$',r['mos'])
  if not st or not 1<=int(st[1])<=7:raise GateError('Unmapped stage/device '+r['mos'])
  c=dict(src=r['src'],topology=meta[r['src']]['topology'],position=meta[r['src']]['position'],mos=r['mos'],stage=int(st[1]),edge=r['edge'],S_E1_fs_per_V=fnum(r['S_E1']),S_IS_fs_per_V=fnum(r['S_IS']),q_V=fnum(r['q']),role=r['role'])
  if c['q_V']<=0:raise GateError('Nonpositive q in expected 21 nonzero devices: '+str((r['src'],r['mos'],r['edge'])))
  c['deltaS']=abs(c['S_E1_fs_per_V']-c['S_IS_fs_per_V']);c['serial']=(c['topology']=='NOR2' and st[2] in ['PTop','PBottom']) or (c['topology']=='NAND2' and st[2] in ['NTop','NBottom']);normalized.append(c)
 check('coef_21_per_context_edge',set(collections.Counter((r['src'],r['edge']) for r in normalized).values())=={21},sorted(set(collections.Counter((r['src'],r['edge']) for r in normalized).values())),[21],qa)
 serial=[r for r in normalized if r['serial']];check('serial_rows_2688',len(serial)==2688,len(serial),2688,qa)
 coefficient_groups=collections.defaultdict(list)
 for r in normalized:coefficient_groups[(r['src'],r['role'],r['edge'])].append(r)
 reproduction=[]
 for r in records:
  key=(r['src'],r['role'],r['edge']);rr=coefficient_groups.get(key)
  if not rr:raise GateError('Missing role coefficient set '+str(key))
  p0=math.fsum(x['S_E1_fs_per_V']*x['q_V'] for x in rr);pi=math.fsum(x['S_IS_fs_per_V']*x['q_V'] for x in rr)
  d0=abs(p0-fnum(r['P0']));di=abs(pi-fnum(r['P_IS1']))
  reproduction.append(dict(src=key[0],role=key[1],edge=key[2],n_devices=len(rr),P0_original=fnum(r['P0']),P0_reproduced=p0,P0_abs_error_fs=d0,P_IS1_original=fnum(r['P_IS1']),P_IS1_reproduced=pi,P_IS1_abs_error_fs=di))
  # Immediate fail with the precise frozen key; never continue to plotting on a row failure.
  if d0>1e-6 or di>1e-6:check('P0_P_IS1_480_row_reproduction',False,reproduction[-1],'both <=1e-6 fs',qa)
 max0=max(r['P0_abs_error_fs'] for r in reproduction);maxi=max(r['P_IS1_abs_error_fs'] for r in reproduction)
 check('P0_P_IS1_480_row_reproduction',True,{'rows':480,'P0_max_abs_error_fs':max0,'P_IS1_max_abs_error_fs':maxi},'480/480 both <=1e-6 fs',qa)
 qa['coefficient_reproduction']={'source_priority':'A','source_sha256':COEF_SHA,'rows':4032,'serial_rows':2688,'P0_max_abs_error_fs':max0,'P_IS1_max_abs_error_fs':maxi,'q_unit':'V','S_unit':'fs/V','roles':'frozen role membership; distinct per-device q; math.fsum'}
 write_csv(out/'coef_E1_IS_96.csv',normalized,['src','topology','position','mos','stage','edge','S_E1_fs_per_V','S_IS_fs_per_V','q_V','role','deltaS','serial'])
 write_csv(out/'PREDICTION_REPRODUCTION_480.csv',reproduction)
 # Fig2 stage grouping: first take max of exactly two serial transistors per configuration-edge-stage.
 sg=collections.defaultdict(list)
 for r in serial:sg[(r['src'],r['topology'],r['position'],r['edge'],r['stage'])].append(r['deltaS'])
 check('serial_pair_group_size',set(map(len,sg.values()))=={2},sorted(set(map(len,sg.values()))),[2],qa)
 stages=[dict(src=k[0],topology=k[1],position=k[2],edge=k[3],stage=k[4],deltaS=max(v)) for k,v in sorted(sg.items())]
 counts=collections.Counter((r['topology'],r['position'],r['edge'],r['stage']) for r in stages)
 qa['fig2_stage_configuration_counts']=[{'topology':k[0],'position':k[1],'edge':k[2],'stage':k[3],'n_configurations':v} for k,v in sorted(counts.items())]
 check('fig2_configuration_counts',set(counts.values())=={24},sorted(set(counts.values())),[24],qa)
 validate_fig2(stages,out,qa)
 contrast=[r for r in v2b if r['floating_at_event']=='True']
 cc=collections.Counter(r['edge'] for r in contrast);check('fig2c_floating_rows',dict(cc)=={'td_phl':12,'td_plh':16},dict(cc),{'td_phl':12,'td_plh':16},qa)
 for r in contrast:
  for k in ['stim_at_1','stim_at_4','win_at_MF','win_at_E1']:fnum(r[k])
 allE=np.array([abs(fnum(r['P0'])-fnum(r['P_IS1'])) for r in records]);posa=np.array([abs(fnum(r['P0'])-fnum(r['P_IS1'])) for r in records if r['position']=='POS-A'])
 check('fig3_POS_A_max',abs(max(posa)-4.579e-8)<=1e-10,float(max(posa)),'4.579e-8 +/-1e-10 fs',qa)
 check('fig3_global_max',abs(max(allE)-24.0589)<=1e-3,float(max(allE)),'24.0589 +/-0.001 fs',qa)
 p95=float(np.percentile(allE,95));check('fig3_global_p95',3.64<=p95<=3.65,p95,'3.64..3.65 fs, linear quantile',qa)
 qa['fig3']={'zero_count':int(np.count_nonzero(allE==0)),'min_positive_fs':float(min(allE[allE>0])),'max_fs':float(max(allE)),'p95_fs':p95,'POS_A_max_fs':float(max(posa))}
 check('AMP_rows_1440',len(amp)==1440,len(amp),1440,qa)
 check('AMP_unique_keys',len(set((r['src'],r['role'],r['edge'],r['a'],r['model']) for r in amp))==1440,len(set((r['src'],r['role'],r['edge'],r['a'],r['model']) for r in amp)),1440,qa)
 for r in amp:
  er=abs(fnum(r['error_fs']));ref=abs(fnum(r['dref_fs']));rel=fnum(r['relative_error'])
  if ref==0 or abs(er/ref-rel)>1e-9:raise GateError('AMP error/relative/unit inconsistency '+str((r['src'],r['a'],r['model'])))
 scale_counts=collections.Counter((fnum(r['a']),r['model']) for r in amp)
 check('AMP_each_scale_model_80',set(scale_counts)==set((a,m) for a in [2.,4.,8.] for m in MODELS) and set(scale_counts.values())=={80},[{ 'a':k[0],'model':k[1],'n':v} for k,v in sorted(scale_counts.items())],'2/4/8 x 6 models x80',qa)
 amp8={m:np.array([abs(fnum(r['error_fs'])) for r in amp if fnum(r['a'])==8 and r['model']==m]) for m in MODELS}
 zeroerrors=sum(int(np.count_nonzero(v==0)) for v in amp8.values());check('fig4_no_exact_zero_errors',zeroerrors==0,zeroerrors,0,qa)
 for m,want,nfail in [('P_R2',389.5,10),('P_IS2',237.9,9),('P_DIR2',145.1,4)]:
  check('fig4_max_'+m,abs(float(max(amp8[m]))-want)<=.1,float(max(amp8[m])),'{} +/-0.1 fs'.format(want),qa)
  check('fig4_over_5fs_'+m,int(np.count_nonzero(amp8[m]>5))==nfail,int(np.count_nonzero(amp8[m]>5)),nfail,qa)
 qa['fig4']={m:{'n':len(v),'max_fs':float(max(v)),'over_5fs':int(np.count_nonzero(v>5)),'zero_count':int(np.count_nonzero(v==0))} for m,v in amp8.items()}
 pb=[r for r in pred if r['position']=='POS-B' and r['edge']=='td_phl'];check('fig5_raw_rows',len(pb)==56,len(pb),56,qa)
 byctx=collections.defaultdict(list)
 for r in pb:
  st=int(r['stage']);parity=(st%2==0 if r['topology']=='NOR2' else st%2==1);expected='SENSITIVE' if parity else 'NONFLOATING_STAGE'
  if r['predicted_class']!=expected:raise GateError('Fig5 predicted_class mismatch '+str((r['source_context_id'],r['stage'],r['mos'],r['predicted_class'],expected)))
  cand=r['predicted_class']=='SENSITIVE'
  rr={k:r[k] for k in ['source_context_id','topology','stage','mos','predicted_class','absW','position','edge']}
  rr.update(src=r['source_context_id'],candidate=cand,absW_source=r['absW'],absW=fnum(r['absW']))
  byctx[rr['src']].append(rr)
 points=[r for rows in byctx.values() for r in rows]
 validate_fig5(points,qa,'before_plot')
 write_csv(out/'FIG5_RAW_TRANSISTOR_RECORDS.csv',[{k:(r['absW_source'] if k=='absW' else r[k]) for k in ['source_context_id','topology','stage','mos','predicted_class','absW','position','edge']} for r in points])
 # Pred contains no model/corner metadata: one-to-one join on frozen allocation table only.
 amap={}
 for r in alloc:
  key=r['source_context_id']
  if key in amap:raise GateError('Allocation join not unique '+key)
  amap[key]=r
 predmeta={}
 for src in sorted(byctx):
  if src not in amap:raise GateError('Fig5 allocation metadata missing '+src)
  r=amap[src];corner=re.fullmatch(r'([0-9.]+)V_(-?[0-9.]+)C',r['corner']);node={'PTM45':'45 nm','PTM65':'65 nm'}.get(r['tech'])
  if not corner or not node:raise GateError('Ambiguous Fig5 metadata '+str(r))
  if r['position']!='POS-B' or r['topology']!=byctx[src][0]['topology']:raise GateError('Fig5 metadata topology/position conflict '+src)
  predmeta[src]={'topology':r['topology'],'node':node,'tech':r['tech'],'VDD_V':fnum(corner[1]),'temperature_C':fnum(corner[2]),'duty':fnum(r['duty'])}
 qa['fig5']['metadata']=predmeta
 # Snapshot only the exact frozen CSV bytes; the originals are never written.
 portable=out/'inputs';portable.mkdir()
 expected={}
 for k,p in paths.items():shutil.copyfile(p,portable/(k+'.csv'));expected[k]=sha(p)
 write_json(portable/'EXPECTED_INPUT_HASHES.json',expected)
 write_csv(out/'FIG2_STAGE_MAX_RECORDS.csv',stages)
 derived=[]
 for r in records:derived.append({'src':r['src'],'role':r['role'],'edge':r['edge'],'topology':r['topology'],'position':r['position'],'absE_fs':abs(fnum(r['P0'])-fnum(r['P_IS1']))})
 write_csv(out/'FIG3_RECORDS.csv',derived)
 write_csv(out/'FIG4_ERRORS_A8.csv',[{'model':m,'order':i+1,'abs_error_fs':v} for m in MODELS for i,v in enumerate(sorted(amp8[m]))])
 qa['scientific_release_status']='PASS';write_json(out/'QA.json',qa);write_json(out/'SOURCE_LOCK.json',locks);write_json(out/'FIELD_MAP.json',fieldmap)
 fieldmap['Fig2c_V1R2_display_labels']={'Stimulus / k=1':'abs(stim_at_1), unchanged frozen fs/V','Stimulus / k=4':'abs(stim_at_4), unchanged frozen fs/V','Window / IS':'abs(win_at_MF), unchanged frozen fs/V','Window / E1':'abs(win_at_E1), unchanged frozen fs/V','vertical_label':'|Delta S| (fs/V); display rename only, no numerical redefinition','exact_zero':'gray x in categorical zero band; no epsilon'}
 print('[PASS] ALL Fig2-Fig5 SCIENTIFIC GATES; Fig6 input status checked separately',flush=True)
 return normalized,stages,contrast,derived,amp8,points,predmeta


def validate_fig2(stages,out,qa):
 check('fig2_stage_max_rows_1344',len(stages)==1344,len(stages),1344,qa)
 counts=[]
 for top,pos,edge in GROUPS:
  rr=[r for r in stages if (r['topology'],r['position'],r['edge'])==(top,pos,edge)]
  low=sum(r['deltaS']<=THETA_S for r in rr);high=sum(r['deltaS']>THETA_S for r in rr)
  expected=168 if pos=='POS-A' else 0
  if top=='NAND2' and pos=='POS-A' and edge=='td_phl':expected=167
  if top=='NAND2' and pos=='POS-B':expected=1
  check('fig2_band_'+top+'_'+pos+'_'+edge,len(rr)==168 and low==expected and low+high==len(rr),{'input':len(rr),'bottom':low,'main':high},{'input':168,'bottom':expected,'main':168-expected},qa)
  counts.append({'topology':top,'position':pos,'edge':edge,'input_records':len(rr),'bottom_band_records':low,'main_axis_records':high,'population':'configuration-stage-edge maxima of exactly two serial devices'})
 qa['fig2_band_record_counts']=counts
 critical=[]
 for src,pos,edge,stage,value,band,marker in [('SCI2-RUN-15668','POS-B','td_phl',6,4.767246082337806e-06,'bottom','blue filled circle'),('SCI2-RUN-15670','POS-B','td_plh',3,1.2820785741496366e-05,'bottom','vermilion hollow square'),('SCI2-RUN-15514','POS-A','td_phl',6,1.6709216197341448e-05,'main','gray actual-value point')]:
  rr=[r for r in stages if (r['src'],r['topology'],r['position'],r['edge'],r['stage'])==(src,'NAND2',pos,edge,stage)]
  check('fig2_critical_'+src,len(rr)==1 and rr[0]['deltaS']==value and ('bottom' if rr[0]['deltaS']<=THETA_S else 'main')==band,rr,{'deltaS':value,'band':band,'marker':marker},qa)
  critical.append(dict(rr[0],display_band=band,marker=marker))
 qa['fig2_critical_observations']=critical
 qa['fig2_main_encoding']='POS-B main-axis curves remain original configuration medians/IQR, using all unmodified observations; low individual observations additionally retained in bottom band. POS-A above-threshold observations shown individually at actual y.'
 write_csv(out/'FIG2_DISPLAY_RECORDS.csv',[dict(r,display_band='bottom' if r['deltaS']<=THETA_S else 'main',unit='fs/V') for r in stages])

def validate_fig5(points,qa,phase):
 # This exact object is returned by science() and passed directly to figure5().
 # Ratios are calculated here on the plotting argument, never on an alternate table.
 check('fig5_'+phase+'_raw_population',len(points)==56 and len({(r['src'],r['mos'],r['edge']) for r in points})==56,len(points),56,qa)
 c=[r for r in points if r['predicted_class']=='SENSITIVE'];o=[r for r in points if r['predicted_class']=='NONFLOATING_STAGE']
 check('fig5_'+phase+'_candidate_other',len(c)==28 and len(o)==28 and all(r['candidate']==(r['predicted_class']=='SENSITIVE') for r in points),[len(c),len(o)],[28,28],qa)
 check('fig5_'+phase+'_28_of_28',all(r['absW']>THETA_A for r in c),sum(r['absW']>THETA_A for r in c),28,qa)
 ratios={};targets={'15488':122.4608723,'15542':27.214,'15600':101.261,'15663':94.840}
 expected_counts={'15488':(6,8),'15542':(8,6),'15600':(6,8),'15663':(8,6)}
 for src in sorted({r['src'] for r in points}):
  cc=[r['absW'] for r in points if r['src']==src and r['candidate']];oo=[r['absW'] for r in points if r['src']==src and not r['candidate']];key=src.rsplit('-',1)[-1]
  check('fig5_'+phase+'_counts_'+key,key in expected_counts and (len(cc),len(oo))==expected_counts.get(key),[len(cc),len(oo)],expected_counts.get(key),qa)
  ratio=float(np.median(cc)/max(float(np.median(oo)),THETA_A))
  check('fig5_'+phase+'_separation_'+key,key in targets and abs(ratio-targets.get(key,0))<=.01,ratio,str(targets.get(key))+' +/-0.01',qa)
  ratios[src]={'candidate_n':len(cc),'other_n':len(oo),'candidate_sensitive_n':sum(v>THETA_A for v in cc),'candidate_median':float(np.median(cc)),'other_median':float(np.median(oo)),'denominator':max(float(np.median(oo)),THETA_A),'ratio':ratio,'population':'RAW transistor records passed to figure5'}
 fingerprint=hashlib.sha256(json.dumps([{k:r[k] for k in ['source_context_id','topology','stage','mos','predicted_class','absW_source','position','edge']} for r in points],sort_keys=True).encode()).hexdigest()
 if phase=='actual_plot_argument':check('fig5_plot_argument_identical_to_science',fingerprint==qa['fig5']['population_sha256'],fingerprint,qa['fig5']['population_sha256'],qa)
 qa.setdefault('fig5',{}).update({'population_identity':'plotted population == ratio population == RAW transistor records','plot_records':56,'candidate_records':28,'other_records':28,'candidate_sensitive':28,'stage_aggregation_for_plot':False,'theta_A':THETA_A,'ratios':ratios,'population_sha256':fingerprint,'last_ratio_validation_phase':phase})

def style_font(qa,locks):
 selected=None
 for family in ['Arial','Helvetica','Liberation Sans']:
  try:p=font_manager.findfont(font_manager.FontProperties(family=family),fallback_to_default=False);selected=(family,p);break
  except ValueError:pass
 if selected is None:raise RuntimeError('No permitted font: Arial/Helvetica/Liberation Sans')
 fam,p=selected
 qa['font']={'family':fam,'path':str(Path(p).resolve()),'sha256':sha(p),'parent_sizes_pt':[6.5,7,8],'math_scripts':'natural script scaling; parent size >=6 pt','non_scientific_deviation':None if fam in ['Arial','Helvetica'] else 'Arial/Helvetica unavailable; permitted Liberation Sans fallback'}
 locks.append({'logical_source':'selected_font','absolute_path':str(Path(p).resolve()),'bytes':Path(p).stat().st_size,'sha256':sha(p),'records':None,'read_scope':'typography only'})
 plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':[fam],'font.size':7,'axes.labelsize':7,'xtick.labelsize':7,'ytick.labelsize':7,'legend.fontsize':6.5,'axes.linewidth':.6,'lines.linewidth':1.,'lines.markersize':3.5,'xtick.direction':'in','ytick.direction':'in','xtick.major.size':2.5,'ytick.major.size':2.5,'xtick.major.width':.6,'ytick.major.width':.6,'xtick.minor.width':.5,'ytick.minor.width':.5,'xtick.top':True,'ytick.right':True,'axes.grid':False,'figure.facecolor':'white','axes.facecolor':'white','pdf.fonttype':42,'ps.fonttype':42,'mathtext.fontset':'custom','mathtext.rm':fam,'mathtext.it':fam+':italic','mathtext.bf':fam+':bold','mathtext.fallback':'stix','savefig.dpi':1000,'path.simplify':False,'svg.hashsalt':'SCI2-CH3-V1'})

def logaxis(ax,which='y'):
 if which=='y':ax.set_yscale('log',nonpositive='mask');ax.yaxis.set_major_locator(LogLocator(base=10,numticks=6));ax.yaxis.set_minor_formatter(NullFormatter())
 else:ax.set_xscale('log',nonpositive='mask');ax.xaxis.set_major_locator(LogLocator(base=10,numticks=6));ax.xaxis.set_minor_formatter(NullFormatter())
def panel_label(ax,s):ax.text(-.18,1.035,s,transform=ax.transAxes,ha='left',va='bottom',fontsize=8,fontweight='bold')
def figure2(stages,contrast,qa):
 fig=plt.figure(figsize=(190*MM,55*MM));rng=np.random.RandomState(0);zcounts=[];stats=[];individual=[]
 positions=[(.068,.257),(.395,.260),(.74,.24)]
 main=[];bottom=[]
 for left,width in positions:
  ax=fig.add_axes([left,.365,width,.565]);bo=fig.add_axes([left,.225,width,.095],sharex=ax);main.append(ax);bottom.append(bo);logaxis(ax);bo.set_ylim(0,1);bo.set_yticks([]);bo.tick_params(axis='x',top=False,pad=1);ax.tick_params(axis='x',labelbottom=False);ax.set_ylim(THETA_S,1e5)
 for ii,top in enumerate(['NOR2','NAND2']):
  ax=main[ii];bo=bottom[ii];panel_label(ax,'('+chr(97+ii)+')');ax.set_xlim(.5,7.5);bo.set_xticks(range(1,8));bo.set_xlabel('Stage',labelpad=1)
  for stage in range(1,8):
   if (stage%2==0)==(top=='NOR2'):ax.axvspan(stage-.36,stage+.36,color='#EDEDED',zorder=-10,lw=0)
   a=np.array([r['deltaS'] for r in stages if r['topology']==top and r['position']=='POS-A' and r['stage']==stage]);q=quant(a);stats.append(dict(topology=top,position='POS-A',edge='pooled',stage=stage,n=len(a),min=q[0],q1=q[2],median=q[3],q3=q[4],max=q[6]))
   # Only POS-A actual above-threshold observations appear on the main axis.
   high=a[a>THETA_S]
   observed=ax.scatter(np.full(len(high),stage),high,marker='o',s=7,color=GRAY,linewidths=.5,zorder=4,clip_on=False)
   original=[r for r in stages if r['topology']==top and r['position']=='POS-A' and r['stage']==stage and r['deltaS']>THETA_S]
   for r,xy in zip(original,observed.get_offsets()):
    if float(xy[1])!=r['deltaS']:raise GateError('Fig2 POS-A main y differs from original observation')
    individual.append(dict(r,display_band='main',marker='gray circle',plot_x=float(xy[0]),plot_y=float(xy[1])))
   low=a[a<=THETA_S];observed=bo.scatter(stage+rng.uniform(-.16,.16,len(low)),np.full(len(low),.50),marker='o',s=7,color=GRAY,linewidths=.5)
   original=[r for r in stages if r['topology']==top and r['position']=='POS-A' and r['stage']==stage and r['deltaS']<=THETA_S]
   if len(observed.get_offsets())!=len(original):raise GateError('Missing Fig2 POS-A bottom observation')
   for r,xy in zip(original,observed.get_offsets()):individual.append(dict(r,display_band='bottom',marker='gray circle',plot_x=float(xy[0]),plot_y=float(xy[1])))
   zcounts.append({'panel':top,'position':'POS-A','stage':stage,'exact_zero':int(sum(a==0)),'nonzero_at_or_below_theta_S':int(sum((a>0)&(a<=THETA_S)))})
  for edge,color,linestyle,marker,filled in [('td_phl',BLUE,'-','o',True),('td_plh',RED,'--','s',False)]:
   med=[];q1=[];q3=[]
   for stage in range(1,8):
    vals=np.array([r['deltaS'] for r in stages if r['topology']==top and r['position']=='POS-B' and r['edge']==edge and r['stage']==stage]);qs=quant(vals);med.append(qs[3]);q1.append(qs[2]);q3.append(qs[4]);stats.append(dict(topology=top,position='POS-B',edge=edge,stage=stage,n=len(vals),min=qs[0],q1=qs[2],median=qs[3],q3=qs[4],max=qs[6]))
    low=vals[vals<=THETA_S];observed=bo.scatter(stage+rng.uniform(-.16,.16,len(low)),np.full(len(low),.78 if edge=='td_phl' else .20),s=7,marker=marker,facecolors=color if filled else 'none',edgecolors=color,linewidths=.5)
    original=[r for r in stages if r['topology']==top and r['position']=='POS-B' and r['edge']==edge and r['stage']==stage and r['deltaS']<=THETA_S]
    if len(observed.get_offsets())!=len(original):raise GateError('Missing Fig2 POS-B bottom observation')
    for r,xy in zip(original,observed.get_offsets()):individual.append(dict(r,display_band='bottom',marker='blue filled circle' if filled else 'vermilion hollow square',plot_x=float(xy[0]),plot_y=float(xy[1])))
   med=np.array(med);ax.errorbar(range(1,8),med,yerr=[med-np.array(q1),np.array(q3)-med],fmt=marker,ls=linestyle,color=color,ms=3.5,mfc=color if filled else 'white',mec=color,mew=.8,lw=1,elinewidth=.6,capsize=1.5)
  ax.text(.5,1.025,top,transform=ax.transAxes,ha='center',va='bottom',fontsize=7)
  bo.text(-.025,.50,r'$\leq\theta_\mathrm{S}$',transform=bo.transAxes,fontsize=6.5,ha='right',va='center')
  ax.set_ylabel(r'$|S_i^\mathrm{E1}-S_i^\mathrm{IS}|$ (fs/V)',labelpad=1.5)
 main[0].legend(handles=[Line2D([],[],color=BLUE,marker='o',ls='-',ms=3.5,label=r'POS-B, $t_\mathrm{pHL}$'),Line2D([],[],color=RED,marker='s',mfc='white',ls='--',ms=3.5,label=r'POS-B, $t_\mathrm{pLH}$'),Line2D([],[],color=GRAY,marker='o',ls='',ms=3,label='POS-A')],loc='lower left',frameon=False,borderaxespad=.3,handlelength=1.7,labelspacing=.15)
 ax=main[2];bo=bottom[2];panel_label(ax,'(c)');ax.set_xlim(-.6,8.6);ax.axvline(4,color='#777777',lw=.4);ax.set_ylabel(r'$|\Delta S|$ (fs/V)',labelpad=1.5)
 cols=['stim_at_1','stim_at_4','win_at_MF','win_at_E1'];bottom_counts=[];contrast_stats=[]
 for ei,edge in enumerate(['td_phl','td_plh']):
  for j,col in enumerate(cols):
   x=ei*5+j;vals=np.array([abs(fnum(r[col])) for r in contrast if r['edge']==edge]);pos=vals>THETA_S
   jitter=rng.uniform(-.13,.13,len(vals));ax.scatter(x+jitter[pos],vals[pos],s=7,color=GRAY,edgecolors='none',zorder=2)
   z=vals==0;small=(vals>0)&(vals<=THETA_S);bo.scatter(x+jitter[z],np.full(sum(z),.23),marker='x',s=9,color=GRAY,linewidths=.5);bo.scatter(x+jitter[small],np.full(sum(small),.76),marker='o',s=7,facecolors='none',edgecolors=GRAY,linewidths=.5)
   med=float(np.median(vals))
   if med>THETA_S:ax.plot([x-.2,x+.2],[med,med],color='black',lw=1)
   else:bo.plot([x-.2,x+.2],[.23 if med==0 else .76]*2,color='black',lw=1)
   bottom_counts.append({'edge':edge,'contrast':col,'n':len(vals),'exact_zero':int(sum(z)),'nonzero_at_or_below_theta_S':int(sum(small)),'median':med})
   contrast_stats.append({'edge':edge,'contrast':col,'n':len(vals),'min':float(min(vals)),'q1':float(np.percentile(vals,25)),'median':med,'q3':float(np.percentile(vals,75)),'max':float(max(vals))})
 ticks=[0,1,2,3,5,6,7,8];bo.set_xticks(ticks);bo.set_xticklabels([r'$k$=1',r'$k$=4','IS','E1']*2);bo.tick_params(labelsize=7)
 for xx,label in [(0.5,'Stimulus'),(2.5,'Window'),(5.5,'Stimulus'),(7.5,'Window')]:bo.text(xx,-.80,label,transform=bo.get_xaxis_transform(),ha='center',va='top',fontsize=7)
 for xx,edge in [(1.5,'td_phl'),(6.5,'td_plh')]:ax.text(xx,.975,EDGE[edge],transform=ax.get_xaxis_transform(),ha='center',va='top',fontsize=7)
 bo.text(-.025,.23,'= 0',transform=bo.transAxes,ha='right',va='center',fontsize=6.5);bo.text(-.025,.76,r'$\leq\theta_\mathrm{S}$',transform=bo.transAxes,ha='right',va='center',fontsize=6.5,color='#666666')
 qa['fig2c_labels']={'axis':r'$|\Delta S|$ (fs/V)','ticks':['k=1','k=4','IS','E1']*2,'second_line':['Stimulus','Window']*2,'edge_titles':'inside top of each half','exact_zero_marker':'gray x','exact_zero_color':GRAY,'in_plot_explanation_removed':True}
 expected={(r['src'],r['stage'],r['edge']) for r in stages if r['deltaS']<=THETA_S}
 actual={(r['src'],r['stage'],r['edge']) for r in individual if r['display_band']=='bottom'}
 check('fig2_all_low_observations_have_actual_scatter_offsets',actual==expected and len([r for r in individual if r['display_band']=='bottom'])==len(expected),len(actual),len(expected),qa)
 for critical in qa['fig2_critical_observations']:
  found=[r for r in individual if (r['src'],r['stage'],r['edge'])==(critical['src'],critical['stage'],critical['edge'])]
  check('fig2_drawn_critical_'+critical['src'],len(found)==1 and found[0]['deltaS']==critical['deltaS'] and found[0]['display_band']==critical['display_band'],found,critical,qa)
 qa['fig2_actual_individual_offsets']=individual
 qa['fig2_bottom_band_counts']=zcounts;qa['fig2c_bottom_band_counts']=bottom_counts;qa['fig2_axes']={'main_y_limits':[THETA_S,1e5],'bottom_band':'categorical only; original values used in statistics; no clipping-to-threshold/epsilon substitution','POS_A':'individual categorical low values and actual above-threshold gray observations; former min-max columns removed; no CI implied'}
 return fig,stats,contrast_stats

def figure3(records,qa):
 zeros=sum(r['absE_fs']==0 for r in records);fig=plt.figure(figsize=(90*MM,60*MM));ax=fig.add_axes([.18,.34 if zeros else .28,.79,.61 if zeros else .67]);logaxis(ax);rng=np.random.RandomState(0);stats=[]
 if zeros:bo=fig.add_axes([.18,.235,.79,.065],sharex=ax);bo.set_ylim(0,1);bo.set_yticks([]);ax.tick_params(labelbottom=False);bo.text(.01,.62,'= 0',transform=bo.transAxes,fontsize=6.5)
 else:bo=ax
 for i,key in enumerate(GROUPS,1):
  vals=np.array([r['absE_fs'] for r in records if (r['topology'],r['position'],r['edge'])==key]);qs=quant(vals);color=GRAY if key[1]=='POS-A' else BLUE;jitter=rng.uniform(-.18,.18,len(vals));pos=vals>0
  ax.scatter(i+jitter[pos],vals[pos],s=3.5**2,facecolors='none',edgecolors=color,lw=.45,alpha=.45,zorder=2)
  if zeros:bo.scatter(i+jitter[~pos],np.full(sum(~pos),.42),s=5,marker='o',facecolors='none',edgecolors=color,lw=.5)
  # Manually calculated percentiles; no matplotlib boxplot and no extra outlier symbols.
  if qs[2]>0:ax.add_patch(Rectangle((i-.27,qs[2]),.54,qs[4]-qs[2],facecolor=color+'20',edgecolor=color,lw=.8,ls='--' if key[1]=='POS-A' else '-',zorder=3))
  if qs[1]>0:ax.plot([i,i],[qs[1],qs[5]],color=color,lw=.7,zorder=3)
  for v in [qs[1],qs[3],qs[5]]:
   if v>0:ax.plot([i-.23,i+.23],[v,v],color=color,lw=.8,zorder=4)
  stats.append({'topology':key[0],'position':key[1],'edge':key[2],'n':len(vals),'zero_n':int(sum(vals==0)),'min':qs[0],'p5':qs[1],'q1':qs[2],'median':qs[3],'q3':qs[4],'p95':qs[5],'max':qs[6]})
 ymin=min(1e-10,min(r['absE_fs'] for r in records if r['absE_fs']>0)*.7);ax.set_ylim(ymin,1e2);ax.set_xlim(.4,8.6);ax.set_ylabel(r'$|E_\mathrm{transfer}|$ (fs)',labelpad=1)
 bo.set_xticks(range(1,9));bo.set_xticklabels([EDGE[x[2]] for x in GROUPS]);bo.tick_params(axis='x',pad=2,top=False if zeros else True)
 group_texts=[]
 for i,label in enumerate(['NOR2 POS-A','NOR2 POS-B','NAND2 POS-A','NAND2 POS-B']):group_texts.append(bo.text((1.5+2*i-.4)/8.2,-1.3 if zeros else -.12,label,transform=bo.transAxes,ha='center',va='top',fontsize=7))
 qa['fig3']['group_labels']=[t.get_text() for t in group_texts]
 qa['fig3']['actual_y_limits']=[ymin,1e2];qa['fig3']['range_note']='lower bound extended only if necessary to show every actual positive value; no epsilon or data replacement'
 return fig,stats

def figure4(errors,qa):
 fig=plt.figure(figsize=(90*MM,60*MM));ax=fig.add_axes([.18,.20,.79,.75]);logaxis(ax,'x')
 styles={'P0':('black','--'),'P_R':(RED,'--'),'P_R2':(RED,'-'),'P_IS1':(BLUE,'--'),'P_IS2':(BLUE,'-'),'P_DIR2':(GREEN,'-.')}
 names={'P0':r'$P_0$','P_R':r'$P_\mathrm{R}$','P_IS1':r'$P_\mathrm{IS1}$','P_R2':r'$P_\mathrm{R2}$','P_IS2':r'$P_\mathrm{IS2}$','P_DIR2':r'$P_\mathrm{DIR2}$'}
 xmin=min(min(v) for v in errors.values())*.7;xmax=max(max(v) for v in errors.values())*1.08;lines={}
 for m in MODELS:
  vals=np.sort(errors[m]);xx=np.r_[xmin,vals,xmax];yy=np.r_[0,np.arange(1,len(vals)+1)/len(vals),1.];color,ls=styles[m]
  lines[m]=ax.step(xx,yy,where='post',color=color,ls=ls,lw=1,label=names[m],zorder=2)[0];lines[m].set_gid(m)
 ax.set_xlim(xmin,xmax);ax.set_ylim(0,1);ax.set_xlabel(r'$|e|$ (fs)',labelpad=1);ax.set_ylabel('Cumulative fraction',labelpad=1)
 ax.axvline(5,color=GRAY,ls='--',lw=.6,zorder=0);ax.annotate('5 fs',xy=(5,1),xytext=(3,3),textcoords='offset points',ha='left',va='bottom',fontsize=6.5,color='#666666',annotation_clip=False)
 order=['P0','P_R','P_IS1','P_R2','P_IS2','P_DIR2']
 legend=ax.legend(handles=[lines[m] for m in order],loc='lower right',bbox_to_anchor=(.99,.015),ncol=2,frameon=False,handlelength=1.9,columnspacing=.8,handletextpad=.4,labelspacing=.3,borderpad=.2)
 checks=[]
 for m,handle,label in zip(order,legend.legend_handles,legend.get_texts()):
  curve=lines[m];actual={'model':m,'curve_color':matplotlib.colors.to_hex(curve.get_color()),'legend_color':matplotlib.colors.to_hex(handle.get_color()),'curve_linestyle':curve.get_linestyle(),'legend_linestyle':handle.get_linestyle(),'label':label.get_text()}
  ok=actual['curve_color']==actual['legend_color']==matplotlib.colors.to_hex(styles[m][0]) and actual['curve_linestyle']==actual['legend_linestyle']==styles[m][1] and actual['label']==names[m]
  check('fig4_curve_legend_style_'+m,ok,actual,{'color':styles[m][0],'linestyle':styles[m][1],'label':names[m]},qa);checks.append(actual)
 qa['fig4']['curve_legend_style_checks']=checks;qa['fig4']['legend']={'frame':False,'rows':3,'columns':2,'left_column':order[:3],'right_column':order[3:],'position':'inside lower right','direct_leaders':False,'axes_width_fraction':.79}
 return fig


def figure5(points,meta,qa):
 validate_fig5(points,qa,'actual_plot_argument')
 plotted=[];median_marks=[]
 fig=plt.figure(figsize=(90*MM,60*MM));ax=fig.add_axes([.18,.30,.79,.59]);logaxis(ax);rng=np.random.RandomState(0);srcs=sorted(meta)
 for i,src in enumerate(srcs,1):
  for cand,offset in [(True,-.18),(False,.18)]:
   vals=[r['absW'] for r in points if r['src']==src and r['candidate']==cand]
   xx=i+offset+rng.uniform(-.045,.045,len(vals))
   collection=ax.scatter(xx,vals,s=3.5**2,marker='o',facecolors=BLUE if cand else 'none',edgecolors=BLUE if cand else GRAY,lw=.8,zorder=3)
   med=float(np.median(vals));ratio_median=qa['fig5']['ratios'][src]['candidate_median' if cand else 'other_median']
   bar=ax.hlines(med,i+offset-.125,i+offset+.125,color=BLUE if cand else GRAY,lw=.8,zorder=4)
   actual_y=float(bar.get_segments()[0][0,1])
   check('fig5_median_bar_'+src+('_Candidate' if cand else '_Other'),actual_y==med==ratio_median,actual_y,ratio_median,qa)
   median_marks.append({'source_context_id':src,'class':'Candidate' if cand else 'Other','median_absW_fs_per_V':med,'ratio_calculation_median':ratio_median,'actual_artist_y':actual_y,'x_start':i+offset-.125,'x_end':i+offset+.125,'width_group_spacing':.25,'linewidth_pt':.8})
   rr=[r for r in points if r['src']==src and r['candidate']==cand]
   for row,x,y in zip(rr,xx,collection.get_offsets()[:,1]):
    if float(y)!=row['absW']:raise GateError('Fig5 scatter y differs from raw absW')
    plotted.append({'source_context_id':row['source_context_id'],'topology':row['topology'],'stage':row['stage'],'mos':row['mos'],'predicted_class':row['predicted_class'],'absW':row['absW_source'],'plot_x':float(x),'plot_y':float(y)})
 ax.set_xlim(.5,4.5);ax.set_ylim(min(r['absW'] for r in points)*.65,max(r['absW'] for r in points)*2.5);ax.set_ylabel(r'$|W_i|$ (fs/V)',labelpad=1);ax.axhline(THETA_A,color=GRAY,ls='--',lw=.6,zorder=0);ax.text(4.43,THETA_A*1.13,r'$\theta_\mathrm{A}$',ha='right',fontsize=7,color='#666666')
 ax.set_xticks(range(1,5));ax.set_xticklabels([src.rsplit('-',1)[-1]+'\n'+meta[src]['topology']+' · '+meta[src]['node'] for src in srcs]);ax.tick_params(axis='x',pad=10,labelsize=7)
 ax.legend(handles=[Line2D([],[],color=BLUE,marker='o',ls='',label='Candidate stage',ms=3.5),Line2D([],[],color=GRAY,marker='o',mfc='none',ls='',label='Other stage',ms=3.5)],loc='lower center',bbox_to_anchor=(.5,1.035),ncol=2,frameon=False,handletextpad=.3,columnspacing=.8,borderpad=0)
 check('fig5_actual_scatter_offsets_56',len(plotted)==56,len(plotted),56,qa)
 qa['fig5']['plotted_offsets']=plotted
 qa['fig5']['median_marks']=median_marks
 qa['fig5']['median_marks_equal_ratio_medians']=True
 qa['fig5']['actual_scatter_y_equals_raw_absW']=True
 qa['fig5']['stage_points_connected']=False
 return fig

def export_one(fig,n,out,a,qa):
 name='Fig'+str(n);pdf=out/(name+'.pdf');png=out/(name+'.png')
 tool=lambda key: str((a.pdf_tools/(key+'.exe')).resolve()) if a.pdf_tools else shutil.which(key)
 if not tool('pdffonts') or not tool('pdfinfo'):raise RuntimeError('pdffonts/pdfinfo required')
 metadata={'Title':name,'Author':'','Subject':'Frozen SCI2 numeric records','Creator':'make_ch3_figs.py','Producer':'Matplotlib','CreationDate':FIXED,'ModDate':FIXED}
 wantw={2:190,6:140}.get(n,90)
 # Tight export changes the page size. Solve physical width by changing only
 # the plotting canvas; font point sizes and all data coordinates are retained.
 iterations=[];original_tightbbox=fig.get_tightbbox;captured={}
 def capture_pdf_crop(renderer,*args,**kwargs):
  box=original_tightbbox(renderer,*args,**kwargs);captured['bbox']=box.frozen();return box
 for iteration in range(10):
  fig.get_tightbbox=capture_pdf_crop
  try:fig.savefig(pdf,bbox_inches='tight',pad_inches=0.01,metadata=metadata)
  finally:fig.get_tightbbox=original_tightbbox
  info=subprocess.run([tool('pdfinfo'),'-box',str(pdf)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
  if info.returncode:raise RuntimeError('pdfinfo failed '+name)
  mb=re.search(r'MediaBox:\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)',info.stdout)
  if not mb:raise RuntimeError('MediaBox missing '+name)
  width=(float(mb[3])-float(mb[1]))*25.4/72;height=(float(mb[4])-float(mb[2]))*25.4/72
  iterations.append({'canvas_width_mm':float(fig.get_figwidth()*25.4),'PDF_width_mm':width,'PDF_height_mm':height})
  if abs(width-wantw)<=.005:break
  fig.set_size_inches(fig.get_figwidth()*wantw/width,fig.get_figheight(),forward=True)
 else:raise RuntimeError('Tight PDF physical width did not converge '+name)
 if height>70 or abs(width-wantw)>.005:raise RuntimeError('PDF physical dimension FAIL '+name)
 (out/'logs'/(name+'_pdfinfo.txt')).write_text(info.stdout+info.stderr,encoding='utf8')
 fig.set_dpi(1000);fig.canvas.draw();renderer=fig.canvas.get_renderer()
 # Capture the actual PDF backend crop and use that same physical page for PNG.
 # This prevents backend glyph-metric differences from changing the PNG width.
 bbox=captured['bbox'];expected_png=[int((bbox.width+.02)*1000),int((bbox.height+.02)*1000)]
 nondrawn=set()
 for ax in fig.axes:
  for axis,limits in [(ax.xaxis,ax.get_xlim()),(ax.yaxis,ax.get_ylim())]:
   lo,hi=sorted(limits)
   for tick in list(axis.get_major_ticks())+list(axis.get_minor_ticks()):
    if not lo<=tick.get_loc()<=hi:nondrawn.update([tick.label1,tick.label2])
 visible_text=[t for t in fig.findobj(matplotlib.text.Text) if t not in nondrawn and t.get_visible() and t.get_text()]
 outside=[]
 # Actual final export box, rather than discarded canvas whitespace.
 document=bbox.padded(.01).transformed(fig.dpi_scale_trans)
 for t in visible_text:
  b=t.get_window_extent(renderer)
  if b.x0<document.x0-.5 or b.y0<document.y0-.5 or b.x1>document.x1+.5 or b.y1>document.y1+.5:outside.append(t.get_text())
 if outside:raise RuntimeError('Text outside tight document: '+str(outside))
 if n==6:
  column=fig.axes[2];centers=[float(column.transData.transform((r['x'],r['response_ratio']))[0]) for r in qa['fig6']['PLH_artist_positions']]
  minimum_separation=min(np.diff(sorted(centers)));ink_width=(3.5+.8)*fig.dpi/72
  if minimum_separation<=ink_width:raise RuntimeError('Fig6 category triangles still overlap')
  qa['fig6']['category_marker_clearance']={'centers_separation_pt':float(minimum_separation*72/fig.dpi),'marker_plus_edge_width_pt':4.3,'positive_ink_gap_pt':float((minimum_separation-ink_width)*72/fig.dpi),'category_positions_unchanged':[.35,.5,.65]}
 if n==3:
  ax=fig.axes[-1];tickboxes=[t.get_window_extent(renderer) for t in ax.get_xticklabels() if t.get_visible()];gaps=[]
  for t in ax.texts:
   if t.get_text() in qa['fig3']['group_labels']:
    b=t.get_window_extent(renderer);gap=min(x.y0 for x in tickboxes)-b.y1
    if not -.5<=gap<=b.height+.5:raise RuntimeError('Fig3 group label gap exceeds one line or overlaps')
    gaps.append({'label':t.get_text(),'gap_pt':gap*72/fig.dpi,'one_line_height_pt':b.height*72/fig.dpi})
  qa['fig3']['actual_group_label_spacing']=gaps
 fig.savefig(png,dpi=1000,bbox_inches=bbox.padded(.01),pad_inches=0,metadata={'Software':'make_ch3_figs.py; fixed numeric data and deterministic RNG'})
 with png.open('rb') as f:header=f.read(24)
 pixels=list(struct.unpack('>II',header[16:24]))
 if any(abs(x-y)>2 for x,y in zip(pixels,expected_png)):raise RuntimeError('1000dpi tight PNG pixel dimension FAIL '+name)
 font_run=subprocess.run([tool('pdffonts'),str(pdf)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
 (out/'logs'/(name+'_pdffonts.txt')).write_text(font_run.stdout+font_run.stderr,encoding='utf8')
 if font_run.returncode:raise RuntimeError('pdffonts failed '+name)
 embedded=[]
 for line in font_run.stdout.splitlines()[2:]:
  if line.strip():
   m=re.search(r'\s+(yes|no)\s+(yes|no)\s+(yes|no)\s+\d+\s+\d+\s*$',line)
   if not m:raise RuntimeError('Unparsed font row '+line)
   embedded.append(m[1]=='yes')
 if not embedded or not all(embedded) or 'Type 3' in font_run.stdout:raise RuntimeError('Font embedding/type FAIL '+name)
 image_check=subprocess.run([tool('pdfimages'),'-list',str(pdf)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
 (out/'logs'/(name+'_pdfimages.txt')).write_text(image_check.stdout+image_check.stderr,encoding='utf8')
 if image_check.returncode or any(re.match(r'^\s*\d+\s+\d+\s+',line) for line in image_check.stdout.splitlines()[2:]):raise RuntimeError('Raster image in vector PDF '+name)
 rgba=mpimg.imread(png)[::4,::4,:3];gray=np.sum(rgba*np.array([.2126,.7152,.0722]),axis=2)
 mpimg.imsave(out/'grayscale_preview'/(name+'_gray.png'),gray,cmap='gray',vmin=0,vmax=1)
 qa['graphics'][name]={'width_mm':width,'height_mm':height,'target_width_mm':wantw,'bbox_inches':'tight','pad_inches':.01,'tight_width_calibration':iterations,'png_pixels':pixels,'target_pixels_1000dpi':expected_png,'png_width_mm_at_1000dpi':pixels[0]*25.4/1000,'png_height_mm_at_1000dpi':pixels[1]*25.4/1000,'all_fonts_embedded':True,'type3_fonts':False,'outside_canvas_text':outside,'font_report':'logs/'+name+'_pdffonts.txt','vector_pdf':True,'raster_image_objects':0,'color_pdf_sha256':sha(pdf),'color_png_sha256':sha(png),'grayscale_preview':'grayscale_preview/'+name+'_gray.png','grayscale_method':'0.2126R+0.7152G+0.0722B, quarter-size preview only','visual_check':'PENDING_NEW_V1R3_REVIEW','typography':'V1R1 parent font sizes unchanged; math scripts shrink naturally','redundancy':{2:'filled circle/solid versus hollow square/dashed, neutral gray POS-A/zero crosses',3:'hollow records, dashed gray POS-A boxes versus solid blue POS-B',4:'source colors paired with first-order dashed/second-order solid/directional dash-dot and exact matching legend',5:'filled Candidate/hollow Other with actual class median horizontal marks',6:'SPICE solid/fit hollow circles2.5pt without line; three filled observed/hollow predicted pairs and three horizontally separated gray triangles'}[n]}
 plt.close(fig);print('[GENERATED] '+name+' tight vector PDF/1000dpi PNG; size/fonts PASS '+str([width,height]),flush=True)


SYNC='# SCI2 V1R3 全文图号及引用同步\n\n作者已决定删除 Methods 原图2。最终编号：图1为结构；本工程 Fig2–Fig5 即全文图2–图5；第4章机理图为图6。取消先前的加一映射，不再生成别名目录或映射清单。\n\n## 正文引用\n- 2.2：删除已删除Methods图的图2(a)、图2(b)引用；保留方法文字，不将新图2当成原Methods图。\n- 3.1：逐级剖面引用图2(a)、(b)；双因素引用图2(c)，不再引用(c)、(d)两面板。\n- 3.2：引用图3；该图只承载绝对迁移量，不用来展示29.8%相对参考增量。\n- 3.3：引用图4；3.4：引用图5。\n- 4.x：机理图引用图6；涉及第三章双因素对比时引用图2(c)。\n\n本轮任务修改图件及此同步文件，未指定Word母版，因此没有实际编辑Word；上述为已决定的全文同步要求。\n\n## 图注\n图2. 灵敏度迁移的级号与边沿分布。(a) NOR2；(b) NAND2：POS-B各级串联管系数差的配置间中位数，误差棒为四分位距，浅灰竖带为候选级；底带为不高于θS=1.456×10⁻⁵ fs/V的单配置值（灰色为POS-A，彩色为POS-B）。超过底带门限的观测值仍按原值显示。(c) 四组NOR2 POS-B配置浮空级PTop的激励对比与窗口对比；k=1、k=4对应Stimulus，IS、E1对应Window，分别对应冻结字段stim_at_1、stim_at_4、win_at_MF、win_at_E1。横线为中位数，底带灰色叉号为精确零值，低于显示分辨率的非零值另行编码。所有值均来自冻结系数，未按qi加权。\n\n图3. E1→IS链端迁移量|E_transfer|按拓扑、栈位置与传播边沿的分布。箱体为四分位距，中线为中位数，须线为第5至第95百分位；所有记录均以空心点显示。\n\n图4. 八倍扰动下六种预测器绝对误差的经验累积分布。黑色虚线为P0，朱红虚线/实线分别为P_R/P_R2，蓝色虚线/实线分别为P_IS1/P_IS2，绿色点划线为P_DIR2；竖虚线为5 fs绝对误差限。无框图例左列为一阶模型，右列为二阶及方向标定模型。\n\n图5. 四组POS-B测试配置在t_pHL弧上的单管窗口差幅值|Wi|。每组14条串联管记录逐条绘制，实心点为候选级、空心点为其余级，同色短横线为各类中位数，虚线为θA。幅值分离倍数由图中相同56条原始逐管记录计算，分母为其余级中位数与θA的较大值；不进行逐级最大值聚合。\n\n图6. NOR2 POS-B浮空内部节点的事后诊断。(a) 电源轨侧管截止后第4级节点的弛豫，实线为SPICE波形，同色空心圆为式（7）在τ=0.5、1.0、1.5…ns处的冻结参数预测（标记2.5pt，不连线，第2/4/6级联合拟合，第2/6级波形与第4级最大差小于0.15 mV，经逐配置核对）；(b) 首次与第四次交叉前节点阈值响应之比，曲线为式（8）的g(λ)，实心与空心圆分别为t_pHL的SPICE比值与拟合预测，三角为t_pLH的SPICE比值（两次驻留相同，不对应g(λ)）。\n\nFig6(a)只读作者提供FIG7A_NODE_WAVEFORMS.csv（SHA256 8a304bc6b67ad79e1f893930da0a8ac0bcbd75876b2a5b077c93e5c0f481c389），由冻结NETP_DIAG_V1R2_RAW fresh w.raw派生，本轮未读RAW。第4级残差RMS使用作者新批准的≤0.05mV门限，不要求等于第2/4/6级联合拟合rms_mV；第2/6级与第4级最大差<0.2mV，实测值见QA。面板(b)独立取B表全部floating_at_event=True的六条记录：t_pHL为15480、15486、15500，t_pLH为15591、15598、15612。圆点间灰色竖线0.4pt，t_pLH分类列横向错开±0.15。Fig2–Fig5保留V1R2字节。门限由作者 V1R3 裁定更正，输入未改。t_pHL三个差值按作者指定值±1e-9精确复现，导数比值与g_obs差≤1e-9；t_pLH三个比值按作者指定值±1e-9精确复现，|ratio−1|≤1e-3。原两道错误门已删除。新Fig6的实际生成与核验结果见QA.json。\n\n## 显示优化另存版\n只将15480的tau_r=66.4ns标注锚点从5.0ns右移到5.15ns，保留5.0ns末端空心圆。SPICE实线显示层按源行索引等间隔选取约2000点/配置，保留首尾；RMS及其他科学核对仍使用全部原始导出记录，不修改冻结CSV、不重新拟合。具体抽稀索引与原值见FIG6A_DISPLAY_RECORDS.csv；显示折线相对完整点列的偏差仅作显示审计，见QA.json。原V1R3交付保留。\n'

def preserve_fig2_to_fig5(a,out,qa):
 if a.baseline_dir is None:a.baseline_dir=Path(__file__).resolve().parent/'baseline_assets'
 if not a.baseline_dir.is_dir():raise GateError('Verified V1R2 baseline assets required')
 records=[];portable=out/'baseline_assets';portable.mkdir();(portable/'grayscale_preview').mkdir();(portable/'logs').mkdir()
 for n in range(2,6):
  for rel in ['Fig'+str(n)+'.pdf','Fig'+str(n)+'.png','grayscale_preview/Fig'+str(n)+'_gray.png']:
   src=a.baseline_dir/rel;expected=V1R2_PRESERVED_HASHES[rel]
   if sha(src)!=expected:raise GateError('V1R2 artifact SHA mismatch '+rel)
   for dst in [out/rel,portable/rel]:shutil.copyfile(src,dst)
   records.append({'file':rel,'V1R2_sha256':expected,'V1R3_sha256':sha(out/rel),'byte_identical':src.read_bytes()==(out/rel).read_bytes(),'new_render':False})
 for p in sorted(a.baseline_dir.glob('*.csv')):
  if not p.name.startswith('FIG6') and p.name!='FIGURE_DIMENSIONS.csv':
   shutil.copyfile(p,out/p.name);shutil.copyfile(p,portable/p.name)
 for n in range(2,6):
  for suffix in ['pdffonts','pdfinfo','pdfimages']:
   rel='logs/Fig'+str(n)+'_'+suffix+'.txt'
   if (a.baseline_dir/rel).is_file():
    shutil.copyfile(a.baseline_dir/rel,out/rel);shutil.copyfile(a.baseline_dir/rel,portable/rel)
 if (a.baseline_dir/'QA.json').is_file():
  prior=json.loads((a.baseline_dir/'QA.json').read_text(encoding='utf8'))
  prior={k:v for k,v in prior.items() if k.startswith(('fig2','fig3','fig4','fig5')) or k=='graphics'}
  prior['graphics']={k:v for k,v in prior['graphics'].items() if k in ['Fig2','Fig3','Fig4','Fig5']}
 else:prior=json.loads((a.baseline_dir/'BASELINE_QA_FIG2_FIG5.json').read_text(encoding='utf8'))
 write_json(portable/'BASELINE_QA_FIG2_FIG5.json',prior)
 for k,v in prior.items():
  if k!='graphics':qa[k]=v
 for n in range(2,6):
  name='Fig'+str(n);qa['graphics'][name]=dict(prior['graphics'][name],status='PRESERVED_V1R2_BYTES',new_render=False,byte_identical_to_V1R2=True,validation_basis='original exact PDF/PNG/grayscale bytes retained; font/layout reports are hash-bound baseline evidence')
 write_json(out/'FIG2_FIG5_BYTE_IDENTITY.json',{'status':'PASS','records':records,'scope':'original V1R2 PDF/PNG/grayscale bytes, never regenerated'})

def r3_population_preflight(a,out,qa,locks,fieldmap):
 folder=a.input_dir/'fig6';identity=json.loads((folder/'INPUT_LOCK.json').read_text(encoding='utf8'))
 for name,h in identity['parameter_sha256'].items():
  if sha(folder/name)!=h:raise GateError('Frozen Fig6 table SHA mismatch '+name)
 A=load_csv('V1R3_frozen_A',folder/'A_RELAXATION_FIT.csv',['','T_ns','t0_ns'],locks)
 B=load_csv('V1R3_frozen_B',folder/'B_INDIRECT_NODE_SENSITIVITY.csv',['ctx','edge','floating_at_event','g_obs','g_pred','tau4_ns','dVN_dxi_1','dVN_dxi_4'],locks)
 amap={r['']:r for r in A};selected=[r for r in B if r['floating_at_event']=='True'];phl=[];plh=[]
 delta_targets={'SCI2-RUN-15480':.012362568,'SCI2-RUN-15486':.039302131,'SCI2-RUN-15500':.036712926}
 ratio_targets={'SCI2-RUN-15591':1.000212916,'SCI2-RUN-15598':1.000030265,'SCI2-RUN-15612':1.000001371}
 check('V1R3_PHL_count_and_contexts',len([r for r in selected if r['edge']=='td_phl'])==3 and {r['ctx'] for r in selected if r['edge']=='td_phl'}==set(delta_targets),[r['ctx'] for r in selected if r['edge']=='td_phl'],sorted(delta_targets),qa)
 check('V1R3_PLH_count_and_contexts',len([r for r in selected if r['edge']=='td_plh'])==3 and {r['ctx'] for r in selected if r['edge']=='td_plh'}==set(ratio_targets),[r['ctx'] for r in selected if r['edge']=='td_plh'],sorted(ratio_targets),qa)
 for r in selected:
  ratio=fnum(r['dVN_dxi_4'])/fnum(r['dVN_dxi_1'])
  if r['edge']=='td_phl':
   p=amap[r['ctx']];lam=(fnum(r['tau4_ns'])+fnum(p['t0_ns']))/fnum(p['T_ns']);model=float(1-lam/np.expm1(lam));obs=fnum(r['g_obs']);pred=fnum(r['g_pred']);difference=pred-obs
   check('V1R3_PHL_exact_difference_'+r['ctx'],abs(difference-delta_targets[r['ctx']])<=1e-9,{'actual':difference,'target':delta_targets[r['ctx']],'abs_reproduction_error':abs(difference-delta_targets[r['ctx']])},'absolute reproduction error<=1e-9',qa)
   check('V1R3_PHL_observed_ratio_'+r['ctx'],abs(ratio-obs)<=1e-9,{'derivative_ratio':ratio,'g_obs':obs,'abs_difference':abs(ratio-obs)},'<=1e-9',qa)
   check('V1R3_PHL_model_prediction_'+r['ctx'],abs(model-pred)<=1e-9,{'lambda':lam,'g_model':model,'g_pred':pred,'abs_difference':abs(model-pred)},'<=1e-9; includes15500 using its own A-table parameters',qa)
   phl.append(dict(r,lambda_value=lam,g_model=model,g_pred_minus_g_obs=difference,author_difference_target=delta_targets[r['ctx']],abs_difference_reproduction_error=abs(difference-delta_targets[r['ctx']]),derivative_response_ratio=ratio,abs_ratio_minus_g_obs=abs(ratio-obs),abs_g_model_minus_g_pred=abs(model-pred)))
  else:
   check('V1R3_PLH_exact_ratio_'+r['ctx'],abs(ratio-ratio_targets[r['ctx']])<=1e-9,{'actual':ratio,'target':ratio_targets[r['ctx']],'abs_reproduction_error':abs(ratio-ratio_targets[r['ctx']])},'absolute reproduction error<=1e-9',qa)
   check('V1R3_PLH_author_corrected_deviation_'+r['ctx'],abs(ratio-1)<=1e-3,abs(ratio-1),'<=1e-3; author V1R3 correction',qa)
   plh.append(dict(r,response_ratio=ratio,author_ratio_target=ratio_targets[r['ctx']],abs_ratio_reproduction_error=abs(ratio-ratio_targets[r['ctx']]),abs_response_ratio_minus_one=abs(ratio-1),required_limit=1e-3))
 for i,r in enumerate(sorted(plh,key=lambda r:r['ctx'])):r['category_x']=.5+(-.15,0,.15)[i]
 write_csv(out/'FIG6B_PHL_PREFLIGHT.csv',phl);write_csv(out/'FIG6B_PLH_PREFLIGHT.csv',plh)
 qa['author_correction_note']='门限由作者 V1R3 裁定更正，输入未改'
 qa['fig6b_preflight']={'status':'PASS','author_correction_note':qa['author_correction_note'],'population':'all floating_at_event=True; independent of panel(a)','PHL_count':3,'PLH_count':3,'PHL_records':phl,'PLH_records':plh,'acceptance':'exact author targets within1e-9; PHL ratio matchesg_obs<=1e-9; PLH deviation<=1e-3; no former interval or1e-4 gate'}
 fieldmap['Fig6b_V1R3']={'filter':'all floating_at_event=True','PHL_lambda':'(tau4_ns+A[ctx].t0_ns)/A[ctx].T_ns','PHL_observed_ratio':'dVN_dxi_4/dVN_dxi_1, matchesg_obs<=1e-9','PHL_exact_delta_targets':delta_targets,'PLH_exact_ratio_targets':ratio_targets,'reproduction_absolute_tolerance':1e-9,'PLH_deviation_limit':1e-3,'PLH_category_positions':{'15591':.35,'15598':.5,'15612':.65},'author_correction_note':qa['author_correction_note']}
 write_json(out/'FIG6B_PREFLIGHT.json',qa['fig6b_preflight'])
 return phl,plh


def fig6_science(a,out,qa,locks,fieldmap):
 folder=a.input_dir/'fig6' if a.input_dir else None
 if folder is None or not (folder/'INPUT_LOCK.json').is_file():raise GateError('Author-approved Fig6 frozen CSV lock is required')
 status=json.loads((folder/'INPUT_LOCK.json').read_text(encoding='utf8'))
 if status['status']!='READY':raise GateError('Fig6 frozen CSV input is not READY')
 shutil.copytree(folder,out/'inputs/fig6')
 for name,h in status['parameter_sha256'].items():
  check('fig6_parameter_SHA_'+name,sha(folder/name)==h,sha(folder/name),h,qa)
 wavefile=folder/status['waveform_csv'];sourcesfile=folder/status['sources_json']
 for p in [wavefile,sourcesfile]:
  if not p.resolve().is_relative_to(folder.resolve()):raise GateError('Unsafe Fig6 source path')
 expected='8a304bc6b67ad79e1f893930da0a8ac0bcbd75876b2a5b077c93e5c0f481c389'
 check('fig6_author_CSV_exact_SHA256',sha(wavefile)==expected,sha(wavefile),expected,qa)
 check('fig6_author_SOURCES_exact_SHA256',sha(sourcesfile)==status['sources_sha256'],sha(sourcesfile),status['sources_sha256'],qa)
 origins=json.loads(sourcesfile.read_text(encoding='utf8'))
 A=load_csv('fig6_A',folder/'A_RELAXATION_FIT.csv',['','Veq_V','u_V','T_ns','t0_ns','rms_mV','float_segment_ns'],locks)
 B=load_csv('fig6_B',folder/'B_INDIRECT_NODE_SENSITIVITY.csv',['ctx','mos','edge','floating_at_event','g_obs','g_pred','tau4_ns','dVN_dxi_1','dVN_dxi_4'],locks)
 raw=load_csv('fig6_author_node_waveforms',wavefile,['ctx','stage','raw_vector','tau_ns','V_N_V','V_N_minus_Veq_mV'],locks)
 locks.append({'logical_source':'fig6_author_lineage_record','absolute_path':str(sourcesfile.resolve()),'bytes':sourcesfile.stat().st_size,'sha256':sha(sourcesfile),'declared_RAW_lineage':origins['sources'],'read_scope':'由冻结 NETP_DIAG_V1R2_RAW fresh w.raw 派生；本轮只读CSV；这里记录的RAW哈希来自作者来源JSON，未在本轮重读RAW核验'})
 contexts=['SCI2-RUN-15612','SCI2-RUN-15486','SCI2-RUN-15480'];amap={r['']:r for r in A}
 check('fig6_three_author_contexts',set(r['ctx'] for r in raw)==set(contexts),sorted(set(r['ctx'] for r in raw)),sorted(contexts),qa)
 groups=collections.defaultdict(list)
 for i,r in enumerate(raw):
  ctx=r['ctx'];stage=int(r['stage'])
  if stage not in (2,4,6) or r['raw_vector']!='v(xg%02d.netp)'%stage:raise GateError('Fig6 stage/vector mismatch '+str((ctx,r['stage'],r['raw_vector'])))
  for k in ['tau_ns','V_N_V','V_N_minus_Veq_mV']:fnum(r[k])
  groups[(ctx,stage)].append((r,i+2))
 check('fig6_stage_groups',set(groups)==set((ctx,s) for ctx in contexts for s in (2,4,6)),len(groups),9,qa)
 audits=[];comparisons=[];waves=[];fit_records=[]
 for ctx in contexts:
  origin=origins['sources'].get(ctx,{})
  check('fig6_fresh_lineage_'+ctx,origin.get('member')=='NETP_DIAG_V1R2_RAW/runs/'+ctx+'__fresh/w.raw',origin.get('member'),'fresh archive member for same context',qa)
  p=amap[ctx];arrays={}
  for stage in (2,4,6):
   rr=groups[(ctx,stage)];t=np.array([fnum(r['tau_ns']) for r,i in rr]);v=np.array([fnum(r['V_N_minus_Veq_mV']) for r,i in rr])
   check('fig6_monotone_tau_'+ctx+'_stage'+str(stage),len(t)>1 and bool(np.all(np.diff(t)>0)),{'rows':len(t),'min_tau_ns':float(t[0]),'max_tau_ns':float(t[-1])},'strictly increasing frozen tau_ns; no resampling for plot',qa)
   arrays[stage]=(t,v)
  t,v=arrays[4];mask=t>=.3;tt=t[mask];observed=v[mask]
  predicted=-1000*fnum(p['u_V'])*np.log(-np.expm1(-(tt+fnum(p['t0_ns']))/fnum(p['T_ns'])))
  residual=observed-predicted;rms=float(np.sqrt(np.mean(residual**2)))
  check('fig6_stage4_RMS_le_0p05_mV_'+ctx,len(tt)>0 and rms<=.05,{'rms_mV':rms,'rows_tau_ge_0p3':len(tt)},'<=0.05 mV; author-approved single-stage gate, not equal to pooled rms_mV',qa)
  audits.append({'ctx':ctx,'stage':4,'n_tau_ge_0p3':len(tt),'single_stage_RMS_mV':rms,'RMS_limit_mV':.05,'pooled_stages246_rms_mV_not_acceptance_target':fnum(p['rms_mV'])})
  for stage in (2,6):
   ts,vs=arrays[stage];low=max(.3,float(t[0]),float(ts[0]));high=min(float(t[-1]),float(ts[-1]));m=(t>=low)&(t<=high);grid=t[m]
   other=np.interp(grid,ts,vs);diff=np.abs(other-v[m]);j=int(np.argmax(diff));maximum=float(diff[j])
   check('fig6_stage'+str(stage)+'_versus4_maxdiff_'+ctx,len(grid)>0 and maximum<.2,{'max_abs_diff_mV':maximum,'common_stage4_rows':len(grid)},'<0.2 mV; linear alignment only on shared tau>=0.3 ns, no extrapolation',qa)
   comparisons.append({'ctx':ctx,'compared_stage':stage,'reference_stage':4,'common_tau_min_ns':float(grid[0]),'common_tau_max_ns':float(grid[-1]),'n_common_stage4_samples':len(grid),'max_abs_difference_mV':maximum,'tau_at_max_ns':float(grid[j]),'limit_mV':.2,'method':'linear interpolation onto actual stage4 tau in shared domain, QA only; no plotted samples altered'})
  for r,i in groups[(ctx,4)]:waves.append(dict(r,source_row=i))
  ft=np.arange(1,int(math.floor(fnum(p['float_segment_ns'])/.5))+1,dtype=float)*.5;fv=-1000*fnum(p['u_V'])*np.log(-np.expm1(-(ft+fnum(p['t0_ns']))/fnum(p['T_ns'])))
  fit_records.extend({'ctx':ctx,'tau_ns':float(x),'V_N_minus_Veq_mV':float(y),'formula':'Eq7 with frozen parameters, no refit'} for x,y in zip(ft,fv))
 selected=[r for r in B if r['floating_at_event']=='True']
 check('fig6_all_six_participating_configurations',len({r['ctx'] for r in selected})==6,len({r['ctx'] for r in selected}),6,qa)
 phl=qa['fig6b_preflight']['PHL_records'];plh=qa['fig6b_preflight']['PLH_records']
 write_csv(out/'FIG6A_RAW_WAVE_RECORDS.csv',waves);write_csv(out/'FIG6A_RMS_REPRODUCTION.csv',audits);write_csv(out/'FIG6A_STAGE_COMPARISON.csv',comparisons);write_csv(out/'FIG6A_FIT_CURVES.csv',fit_records)
 write_csv(out/'FIG6B_PHL_RECORDS.csv',phl);write_csv(out/'FIG6B_PLH_RECORDS.csv',plh)
 fieldmap['fig6']={'waveform':'author FIG7A_NODE_WAVEFORMS.csv, exact SHA256 '+expected,'panel_a_filter':'stage4 full source rows retained for all scientific QA; only display chooses2000 original rows per context, endpoints retained','x':'tau_ns [ns], original floating-time origin from author extraction, no time shift in this run','y':'V_N_minus_Veq_mV [mV], factor1, original field directly plotted','source_lineage':'由冻结 NETP_DIAG_V1R2_RAW fresh w.raw 派生；本轮不读RAW','fit':'Eq7 with frozen A parameters; hollow-circle2.5pt samples at0.5ns multiples up to floating endpoint, no connecting line; RMS still evaluated on original tau>=0.3 samples','RMS_gate':'single-stage4 residual RMS at all CSV tau>=0.3 ns <=0.05mV, explicitly authorized by user; pooled rms_mV is not acceptance target','stage_overlap_gate':'stage2/6 versus4 maxabsolute difference<0.2mV over shared tau>=0.3; linear time-grid alignment for QA only, no extrapolation','B_filter':'all floating_at_event=True, panel(b) independent of panel(a); six source configurations preserved','B_lambda':'(tau4_ns+t0_ns)/T_ns for td_phl only','B_phl':'g_obs filled circles and g_pred hollow circles at same lambda; vertical connectors','B_plh':'dVN_dxi_4/dVN_dxi_1, gray triangle in separate categorical column, no lambda assignment'}
 qa['fig6']={'status':'SCIENTIFIC_PASS','generated':False,'provenance':'由冻结 NETP_DIAG_V1R2_RAW fresh w.raw 派生','this_run_RAW_read':False,'waveform_sha256':expected,'source_total_rows':len(raw),'stage4_plotted_rows':len(waves),'stage4_RMS':audits,'stage_overlap':comparisons,'max_stage_overlap_mV':max(r['max_abs_difference_mV'] for r in comparisons),'original_rms_mV_equality_not_required':'author explicitly replaced pooled-fit equality gate with single-stage RMS<=0.05mV','panel_a_contexts':contexts,'panel_b_contexts':sorted({r['ctx'] for r in selected}),'B_phl_records':len(phl),'B_plh_records':len(plh),'source_nodes_preserved':[{'ctx':r['ctx'],'mos':r['mos'],'edge':r['edge']} for r in selected],'population_definition':'panel(a) three original contexts; panel(b) all six floating contexts, 3PHL+3PLH','width_specification_mm':140}
 print('[PASS] ALL Fig6 SCIENTIFIC GATES; plotting permitted',flush=True)
 return {'A':amap,'waves':waves,'phl':phl,'plh':plh,'contexts':contexts,'fit_records':fit_records}


def figure6(data,qa):
 fig=plt.figure(figsize=(140*MM,55*MM));a=fig.add_axes([.085,.23,.39,.69]);b=fig.add_axes([.605,.23,.29,.69]);col=fig.add_axes([.915,.23,.080,.69],sharey=b)
 panel_label(a,'(a)');panel_label(b,'(b)');colors=[BLUE,RED,'black']
 for ctx,color in zip(data['contexts'],colors):
  rr=[r for r in data['waves'] if r['ctx']==ctx];p=data['A'][ctx]
  indices=np.linspace(0,len(rr)-1,min(2000,len(rr)),dtype=int)
  chosen=[rr[int(i)] for i in indices]
  line=a.plot([fnum(r['tau_ns']) for r in chosen],[fnum(r['V_N_minus_Veq_mV']) for r in chosen],color=color,lw=1)[0]
  check('fig6_display_source_rows_'+ctx,len(line.get_ydata())==len(chosen) and bool(np.array_equal(line.get_ydata(),[fnum(r['V_N_minus_Veq_mV']) for r in chosen])) and indices[0]==0 and indices[-1]==len(rr)-1,len(line.get_ydata()),'2000 equally spaced source-row indices, exact original values; endpoints retained',qa)
  full_t=np.array([fnum(r['tau_ns']) for r in rr]);full_y=np.array([fnum(r['V_N_minus_Veq_mV']) for r in rr])
  error=np.abs(full_y-np.interp(full_t,full_t[indices],full_y[indices]));maximum=float(np.max(error))
  qa['fig6'].setdefault('display_optimization',{'method':'uniform source-row index selection using numpy.linspace, endpoints retained; no interpolation of plotted samples, no smoothing','scope':'display only; all scientific gates/RMS use the complete original CSV','records':[]})['records'].append({'ctx':ctx,'full_stage4_rows':len(rr),'display_rows':len(chosen),'first_local_index':int(indices[0]),'last_local_index':int(indices[-1]),'max_display_polyline_deviation_mV':maximum,'display_deviation_fraction_of_full_y_range':maximum/float(np.ptp(full_y)),'deviation_method':'linear polyline evaluated at original tau for display audit only; no effect on scientific QA'})
  qa['fig6'].setdefault('display_records',[]).extend(dict(row,context_local_index=int(i)) for i,row in zip(indices,chosen))
  tau=np.arange(1,int(math.floor(fnum(p['float_segment_ns'])/.5))+1,dtype=float)*.5;fit=-1000*fnum(p['u_V'])*np.log(-np.expm1(-(tau+fnum(p['t0_ns']))/fnum(p['T_ns'])))
  markers=a.plot(tau,fit,color=color,ls='',marker='o',mfc='none',mec=color,mew=.8,ms=2.5)[0]
  check('fig6_Eq7_marker_style_'+ctx,markers.get_linestyle()=='None' and markers.get_marker()=='o' and markers.get_markersize()==2.5 and markers.get_markerfacecolor()=='none',{'linestyle':markers.get_linestyle(),'marker':markers.get_marker(),'size_pt':markers.get_markersize(),'facecolor':markers.get_markerfacecolor()},'unconnected hollow circles2.5pt',qa)
  qa['fig6'].setdefault('Eq7_marker_records',[]).extend({'ctx':ctx,'tau_ns':float(x),'V_N_minus_Veq_mV':float(y),'marker_pt':2.5,'line':'none'} for x,y in zip(tau,fit))
  a.annotate(r'$\tau_r$ = '+format(fnum(p['T_ns']),'.1f')+' ns',xy=(tau[-1]+(.15 if fnum(p['T_ns'])>60 else 0),fit[-1]),xytext=(3,0) if fnum(p['T_ns'])>60 else (0,1 if fnum(p['T_ns'])<2 else 3),textcoords='offset points',color=color,ha='left' if fnum(p['T_ns'])>60 else 'right',va='center' if fnum(p['T_ns'])>60 else 'bottom',fontsize=6.5)
 a.set_xlim(0,max(fnum(data['A'][ctx]['float_segment_ns']) for ctx in data['contexts']));a.set_xlabel(r'$\tau$ (ns)',labelpad=1);a.set_ylabel(r'$V_N-V_\mathrm{eq}$ (mV)',labelpad=1)
 a.legend(handles=[Line2D([],[],color='black',lw=1,label='SPICE'),Line2D([],[],color='black',ls='',marker='o',mfc='none',mec='black',ms=2.5,mew=.8,label='Eq. (7)')],frameon=False,loc='upper right')
 lam=np.logspace(-2,np.log10(20),400);theory=1-lam/np.expm1(lam);b.plot(lam,theory,color='black',lw=1);logaxis(b,'x');b.set_xlim(.01,20);b.set_ylim(0,1.05)
 qa['fig6']['theory_curve']=[{'lambda':float(x),'g':float(y)} for x,y in zip(lam,theory)]
 for r in data['phl']:
  x=r['lambda_value'];obs=fnum(r['g_obs']);pred=fnum(r['g_pred']);connector=b.plot([x,x],[obs,pred],color=GRAY,lw=.4)[0];check('fig6_connector_'+r['ctx'],connector.get_linewidth()==.4,float(connector.get_linewidth()),.4,qa)
  b.plot(x,obs,'o',color=BLUE,ms=3.5);b.plot(x,pred,'o',mfc='none',mec=BLUE,mew=.8,ms=3.5)
 for offset,r in zip([-.15,0,.15],sorted(data['plh'],key=lambda r:r['ctx'])):
  mark=col.plot(.5+offset,r['response_ratio'],'^',color=GRAY,ms=3.5,mew=.8)[0]
  qa['fig6'].setdefault('PLH_artist_positions',[]).append({'ctx':r['ctx'],'x':float(mark.get_xdata()[0]),'response_ratio':float(mark.get_ydata()[0])})
 col.set_xlim(0,1);col.set_xticks([.5]);col.set_xticklabels([EDGE['td_plh']]);col.tick_params(axis='y',labelleft=False);col.tick_params(axis='x',top=False)
 b.set_xlabel(r'$\lambda$',labelpad=1);b.set_ylabel(r'$\chi(k{=}4)/\chi(k{=}1)$',labelpad=1)
 b.legend(handles=[Line2D([],[],color=BLUE,marker='o',ls='',label='SPICE',ms=3.5),Line2D([],[],mec=BLUE,mfc='none',marker='o',ls='',label='Predicted',ms=3.5)],frameon=False,loc='lower right',fontsize=6.5)
 qa['fig6']['generated']=True
 qa['fig6']['stage4_full_source_rows']=len(data['waves']);qa['fig6']['stage4_plotted_rows']=len(qa['fig6']['display_records'])
 qa['fig6']['label_adjustment']={'ctx':'SCI2-RUN-15480','original_anchor_tau_ns':5.0,'new_anchor_tau_ns':5.15,'shift_ns':.15,'terminal_Eq7_hollow_marker_retained':True,'all_other_labels_unchanged':True}
 return fig



def main():
 p=argparse.ArgumentParser();p.add_argument('--r7',type=Path,default=Path('SCI2_MERGE_ALL_20261028/SCI2_R7_RELEASE'));p.add_argument('--coef',type=Path,default=Path('SCI2_CH3_FIG_V4_20261027/inputs/PERMOS_IS_vs_E1.csv'));p.add_argument('--input-dir',type=Path);p.add_argument('--output-parent',type=Path,default=Path.cwd());p.add_argument('--pdf-tools',type=Path);p.add_argument('--visual-review',type=Path);p.add_argument('--baseline-dir',type=Path);a=p.parse_args()
 out=a.output_parent.resolve()/'ch3_figs_v1r3_display_opt'
 if out.exists():print('STOP: output directory already exists; no files modified: '+str(out),file=sys.stderr);return 3
 out.mkdir(parents=True);(out/'logs').mkdir();(out/'grayscale_preview').mkdir();locks=[];fieldmap={};qa={'version':VERSION,'python_version':sys.version,'scientific_release_status':'NOT_RUN','scientific_gates':[],'graphics':{},'no_SPICE':True,'no_RAW_read':True,'no_refit':True,'no_frozen_input_write':True,'numpy_version':np.__version__,'matplotlib_version':matplotlib.__version__,'random_generator':'numpy.random.RandomState(0), reset per figure','quantile_method':'NumPy percentile default linear, type 7','graphic_release_status':'NOT_RUN'}
 shutil.copyfile(Path(__file__).resolve(),out/'make_ch3_figs.py')
 try:
  preserve_fig2_to_fig5(a,out,qa)
  (out/'MANUSCRIPT_SYNC.md').write_text(SYNC,encoding='utf8')
  r3_population_preflight(a,out,qa,locks,fieldmap)
  data=science(a,out,qa,locks,fieldmap)
  node_data=fig6_science(a,out,qa,locks,fieldmap)
  (out/'MANUSCRIPT_SYNC.md').write_text(SYNC,encoding='utf8')
  (out/'COEF_SOURCE.md').write_text('# 逐管系数来源与复现\n\n使用优先级A冻结PERMOS_IS_vs_E1.csv；实际路径和SHA256见SOURCE_LOCK.json。S_E1、S_IS单位均fs/V；q字段已为逐器件V值，未统一替换为6.76 mV；无需从RESULT重建，也未解析RAW。配置/拓扑/栈位置来自RECORDS_ALL96的唯一配置连接；级号来自mos实例名。4032条逐管—边沿记录，串联子集2688条。全部480个冻结角色—边沿的P0和P_IS1均通过绝对误差≤1e-6 fs复现；逐行结果见PREDICTION_REPRODUCTION_480.csv。\n\n最大复现误差：P0='+repr(qa['coefficient_reproduction']['P0_max_abs_error_fs'])+' fs；P_IS1='+repr(qa['coefficient_reproduction']['P_IS1_max_abs_error_fs'])+' fs。没有使用任何图像反取数据。\n',encoding='utf8')
  style_font(qa,locks)
  # Fig2-Fig5 are exact copies only. They are never rendered in V1R3.
  if node_data is not None:
   export_one(figure6(node_data,qa),6,out,a,qa)
   write_csv(out/'FIG6B_THEORY_CURVE.csv',qa['fig6']['theory_curve'])
   write_csv(out/'FIG6A_EQ7_MARKERS.csv',qa['fig6']['Eq7_marker_records']);write_csv(out/'FIG6B_PLH_ARTIST_POSITIONS.csv',qa['fig6']['PLH_artist_positions'])
   write_csv(out/'FIG6A_DISPLAY_RECORDS.csv',qa['fig6']['display_records'])
  contact,axs=plt.subplots(3,2,figsize=(10,10))
  for ax,n in zip(axs.flat,range(2,7)):
   im=mpimg.imread(out/('Fig'+str(n)+'.png'))[::5,::5];ax.imshow(im);ax.set_axis_off();ax.set_title('Fig'+str(n),fontsize=8)
  axs.flat[-1].set_axis_off()
  contact.subplots_adjust(.01,.01,.99,.96,wspace=.04,hspace=.10);contact.savefig(out/'contact_sheet.png',dpi=150);plt.close(contact)
  for src in locks:
   if src['logical_source'] in FILES or src['logical_source']=='coef':
    if sha(src['absolute_path'])!=src['sha256']:raise GateError('Frozen input changed during build '+src['absolute_path'])
  for rel,h in V1R2_PRESERVED_HASHES.items():
   if sha(out/rel)!=h:raise GateError('Fig2-Fig5 preserved bytes changed during build '+rel)
  write_csv(out/'FIGURE_DIMENSIONS.csv',[{'figure':name,'PDF_width_mm':rec['width_mm'],'PDF_height_mm':rec['height_mm'],'PNG_width_pixels':rec['png_pixels'][0],'PNG_height_pixels':rec['png_pixels'][1],'new_render':name=='Fig6'} for name,rec in qa['graphics'].items()])
  qa['graphic_release_status']='AUTOMATED_PASS_VISUAL_REVIEW_PENDING'
  qa['task_status']='PARTIAL_FIG6_INPUT_BLOCKED' if node_data is None else 'ALL_REQUESTED_FIGURES_GENERATED'
  qa['requested_figures']=['Fig2','Fig3','Fig4','Fig5','Fig6']
  qa['generated_figures']=['Fig6'];qa['preserved_figures']=['Fig2','Fig3','Fig4','Fig5']
  qa['overall_status']='NUMERICAL_PASS_NEW_FIG6_VISUAL_PENDING'
  qa['scientific_release_scope']='All inherited Fig2-Fig5 numeric gates plus explicit author-approved Fig6 CSV/RMS/stage-overlap/response gates; all passed before plotting'
  qa['graphic_release_scope']='only actually generated figures listed in graphics; Fig6 is not certified when missing'
  if a.visual_review:
   review=json.loads(a.visual_review.read_text(encoding='utf8'))
   if review.get('status')!='PASS' or review.get('version')!=VERSION or not review.get('new_Fig6_PDF_PNG_grayscale_actually_viewed'):raise RuntimeError('Visual review certificate is not PASS')
   for rel,h in review['reviewed_file_sha256'].items():
    if sha(out/rel)!=h:raise RuntimeError('Visual review hashes do not match current output '+rel)
   qa['graphic_release_status']='PASS';qa['visual_review']={'actual_review_of_generated_PDF_PNG_and_grayscale':True,'reviewed_bytes_match_current_outputs':True,'record':'VISUAL_REVIEW.json'}
   qa['graphics']['Fig6']['visual_check']='PASS_NEW_V1R3_REVIEWED_BYTES_MATCH';qa['overall_status']='PASS'
   for n in range(2,6):qa['graphics']['Fig'+str(n)]['visual_check']='PRESERVED_EXACT_V1R2_BYTES'
   shutil.copyfile(a.visual_review,out/'VISUAL_REVIEW.json');locks.append({'logical_source':'actual_visual_review_record','absolute_path':str(a.visual_review.resolve()),'bytes':a.visual_review.stat().st_size,'sha256':sha(a.visual_review),'records':len(qa['graphics']),'read_scope':'review metadata for exact generated artifact bytes; not a numeric data source'})
  qa['output_sha256']={x.name:sha(x) for x in sorted(out.iterdir()) if x.is_file() and x.suffix in ['.pdf','.png','.csv']};write_json(out/'QA.json',qa);write_json(out/'SOURCE_LOCK.json',locks);write_json(out/'FIELD_MAP.json',fieldmap)
  files=sorted(x for x in out.rglob('*') if x.is_file() and x.name!='SHA256SUMS.txt');(out/'SHA256SUMS.txt').write_text(''.join(sha(x)+'  '+x.relative_to(out).as_posix()+'\n' for x in files),encoding='utf8')
  archive=out.parent/'SCI2_CH3_FIGURES_V1R3_DISPLAY_OPT.zip'
  if archive.exists():raise RuntimeError('ZIP already exists; no overwrite permitted '+str(archive))
  with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
   z.writestr('MANUSCRIPT_SYNC.md',(out/'MANUSCRIPT_SYNC.md').read_bytes())
   for x in sorted(out.rglob('*')):
    if x.is_file():info=zipfile.ZipInfo('ch3_figs_v1r3_display_opt/'+x.relative_to(out).as_posix(),(2000,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,x.read_bytes())
  (out.parent/'SCI2_CH3_FIGURES_V1R3_DISPLAY_OPT.zip.sha256').write_text(sha(archive)+'  '+archive.name+'\n',encoding='utf8')
  print(json.dumps({'output':str(out),'scientific_release_status':qa['scientific_release_status'],'figures':{n:qa['output_sha256'].get(n) for n in ['Fig2.pdf','Fig3.pdf','Fig4.pdf','Fig5.pdf','Fig6.pdf']},'P0_max_error_fs':qa['coefficient_reproduction']['P0_max_abs_error_fs'],'P_IS1_max_error_fs':qa['coefficient_reproduction']['P_IS1_max_abs_error_fs'],'blocker':node_data is None,'task_status':qa['task_status'],'zip':str(archive),'zip_sha256':sha(archive)},ensure_ascii=False),flush=True);return 0
 except Exception as e:
  if a.input_dir and not (out/'inputs').exists():shutil.copytree(a.input_dir,out/'inputs')
  qa['overall_status']='BLOCKED_SCIENTIFIC_GATE_FAILED';qa['Fig6_new_render']='NOT_RUN';qa['new_Fig6_visual_QA']='NOT_RUN';qa['new_Fig6_rebuild_QA']='NOT_RUN'
  science_failure=isinstance(e,GateError) or qa['scientific_release_status']!='PASS';qa['scientific_release_status']='FAIL' if science_failure else 'PASS';qa['graphic_release_status']='NOT_RUN_DUE_TO_SCIENCE_FAIL' if science_failure else 'FAIL';qa['failure']={'type':type(e).__name__,'message':str(e)}
  (out/'BLOCKERS.md').write_text('# STOP — 发布停止\n\n'+type(e).__name__+': '+str(e)+'\n\n门限由作者 V1R3 裁定更正，输入未改。未运行SPICE、RAW解析或重新拟合。具体失败门见QA.json。\n',encoding='utf8');write_json(out/'QA.json',qa);write_json(out/'SOURCE_LOCK.json',locks);write_json(out/'FIELD_MAP.json',fieldmap);print('[STOP] '+str(e),file=sys.stderr,flush=True);return 2

if __name__=='__main__':sys.exit(main())
