from pathlib import Path
from types import SimpleNamespace
import sys,os,json,shutil,math,zipfile
import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from PIL import Image
from mr_common import *
def build(B,S):
 F=B/'03_FIGURES';D=B/'04_REPRODUCIBILITY/data_processed';A=B/'06_QA/figure_numerics'
 for p in [F,D,A,A/'logs',A/'grayscale_preview']:p.mkdir(parents=True,exist_ok=True)
 mod=load('ch3_numeric',S/'code/approved_ch3_v1r2.py');op=load('ch3_node',S/'code/approved_ch3_display.py')
 args=SimpleNamespace(input_dir=S/'fig_inputs',r7=None,coef=None,pdf_tools=B.parent.parent/'SCI2_CH3_FIGURES_BUILD_20261028/poppler')
 qa={'scientific_gates':[],'graphics':{}};locks=[];fm={}
 data=mod.science(args,A,qa,locks,fm)
 # Fig6 uses the author-corrected V1R3 scientific gates, without invoking any legacy copy routine.
 op.r3_population_preflight(args,A,qa,locks,fm)
 node=op.fig6_science(args,A,qa,locks,fm)
 mod.style_font(qa,locks)
 matplotlib.rcParams.update({'pdf.fonttype':42,'ps.fonttype':42,'svg.hashsalt':'SCI2_MR_FROZEN','path.simplify':False})
 built=[]
 def export(fig,name,source,panels):
  sizes={'FIG1':(190,150),'FIG2':(190,130),'FIG3':(150,90),'FIG4':(130,90),'FIG5':(150,90),'FIG6':(190,90),'FIG_S5_1':(110,80),'FIG_S9_1':(190,100)}
  fig.set_size_inches(*(v/25.4 for v in sizes[name]),forward=True)
  for a in fig.axes:
   for label in list(a.get_xticklabels())+list(a.get_yticklabels()):label.set_fontsize(10)
  for t in fig.findobj(matplotlib.text.Text):
   if t.get_text():t.set_fontsize(max(10,float(t.get_fontsize())))
   if t.get_text()==r'$\leq\theta_\mathrm{S}$':t.set_text('≤ numerical resolution');t.set_fontsize(9.2)
  if name=='FIG2':
   # The enlarged type no longer fits eight categories in a narrow third column.
   # Keep every point/statistic, moving(c) to a full-width second row.
   positions=[(.09,.64,.36,.29),(.09,.58,.36,.04),(.61,.64,.36,.29),(.61,.58,.36,.04),(.09,.22,.88,.27),(.09,.16,.88,.04)]
   for a,pos in zip(fig.axes,positions):
    a.set_position(pos)
    for t in list(a.texts):
     if t.get_text()=='≤ numerical resolution':t.remove()
     elif t.get_text()=='(c)':t.set_position((-.09,1.035))
     elif t.get_text() in ['Stimulus','Window']:t.set_position((t.get_position()[0],-1.05))
   fig.text(.52,.025,'Lower strips: ≤ numerical resolution; × denotes exact zero.',ha='center',va='bottom',fontsize=10)
   qa['graphics']['FIG2_print_layout']={'layout':'a,b upper row; c full-width lower row','scientific_data_or_encodings_changed':False,'reason':'actual enlarged type caused category and low-band annotation overlap in three-column layout; corrected after visual inspection'}
  if name=='FIG4':fig.axes[0].get_legend().get_frame().set_boxstyle('square',pad=.25)

  if name=='FIG4':
   legend=fig.axes[0].get_legend();assert legend is not None
   # Borderless white backing keeps the 5 fs guide from crossing legend glyphs.
   legend.set_frame_on(True);legend.get_frame().set_facecolor('white');legend.get_frame().set_edgecolor('none');legend.get_frame().set_alpha(1)
   qa['graphics']['FIG4_legend_readability']={'change':'Opaque white backing without border; 5 fs guide no longer crosses legend glyphs','data_or_line_styles_changed':False}
  for t in fig.findobj(matplotlib.text.Text):
   t.set_text(t.get_text().replace('Eq. (7)','Eq. (9)').replace(r'\tau_r',r'\tau_\mathrm{r}'))
  fig.canvas.draw()
  fonts=[float(t.get_fontsize()) for t in fig.findobj(matplotlib.text.Text) if t.get_text()]
  # All images are actually rendered at 1000 dpi, including the TIFF; no relabel/upscale.
  meta={'Creator':'SCI2 frozen-data Python reconstruction','CreationDate':mod.FIXED,'ModDate':mod.FIXED}
  fig.savefig(F/(name+'.pdf'),bbox_inches='tight',pad_inches=.01,metadata=meta)
  # EPS cannot encode alpha; preblend translucent patch fills against the white background.
  saved=[]
  for artist in fig.findobj():
   if hasattr(artist,'get_alpha') and hasattr(artist,'get_facecolor') and hasattr(artist,'set_facecolor'):
    alpha=artist.get_alpha()
    if alpha is not None and 0<alpha<1:
     color=np.asarray(artist.get_facecolor())
     if color.shape==(4,):saved.append((artist,alpha,color.copy()));artist.set_facecolor(tuple(alpha*color[:3]+1-alpha)+(1,));artist.set_alpha(1)
  fig.savefig(F/(name+'.eps'),bbox_inches='tight',pad_inches=.01)
  for artist,alpha,color in saved:artist.set_facecolor(color);artist.set_alpha(alpha)
  ep=F/(name+'.eps');eps=ep.read_text(encoding='latin1');eps=__import__('re').sub(r'^%%CreationDate:.*$', '%%CreationDate: deterministic frozen-source build',eps,flags=__import__('re').M);ep.write_text(eps,encoding='latin1',newline='\n')
  fig.savefig(F/(name+'.png'),dpi=1000,bbox_inches='tight',pad_inches=.01)
  fig.savefig(F/(name+'.tif'),dpi=1000,bbox_inches='tight',pad_inches=.01,pil_kwargs={'compression':'tiff_lzw'})
  # Keep the native1000dpi rendered pixels; remove only an entirely opaque alpha channel.
  for suffix in ['.png','.tif']:
   path=F/(name+suffix)
   with Image.open(path) as im:
    if im.mode=='RGBA':assert im.getchannel('A').getextrema()==(255,255)
    rgb=im.convert('RGB');size=im.size
   rgb.save(path,dpi=(1000,1000),**({'compression':'tiff_lzw'} if suffix=='.tif' else {}));assert rgb.size==size;rgb.close()
  fig.savefig(F/(name+'_preview.png'),dpi=200,bbox_inches='tight',pad_inches=.01)
  with Image.open(F/(name+'_preview.png')) as im:im.convert('L').save(F/(name+'_gray.png'))
  from pypdf import PdfReader
  pdf=PdfReader(F/(name+'.pdf'));bb=pdf.pages[0].mediabox
  with Image.open(F/(name+'.png')) as im:pix=im.size
  rec=dict(figure=name,status='REGENERATED_FROM_FROZEN_SOURCE',panels=panels,source=source,width_mm=float(bb.width)*25.4/72,height_mm=float(bb.height)*25.4/72,png_width=pix[0],png_height=pix[1],raster_dpi=1000,min_parent_font_pt=min(fonts),math_subscript_policy='natural scaling; actual glyph sizes audited separately',pdf_sha256=sha(F/(name+'.pdf')),png_sha256=sha(F/(name+'.png')),tif_sha256=sha(F/(name+'.tif')),eps_sha256=sha(F/(name+'.eps')))
  built.append(rec);plt.close(fig)
 f,st,ct=mod.figure2(data[1],data[2],qa);cs(A/'FIG2_STAGE_STATS.csv',st);cs(A/'FIG2_CONTRAST_STATS.csv',ct);export(f,'FIG2','fig_inputs/coef.csv + records.csv + v2b.csv','a;b;c')
 f,st=mod.figure3(data[3],qa);cs(A/'FIG3_GROUP_STATS.csv',st);export(f,'FIG3','fig_inputs/records.csv; signed E_transfer = P0-P_IS1; plot magnitude','single stratified panel')
 export(mod.figure4(data[4],qa),'FIG4','fig_inputs/amp.csv; a=8; six models x80 records','single CDF panel')
 export(mod.figure5(data[5],data[6],qa),'FIG5','fig_inputs/pred.csv; RAW transistor-record CSV, not RAW waveform parsing; 56 records','four configurations')
 cs(A/'FIG5_PLOTTED_RECORDS.csv',qa['fig5']['plotted_offsets']);cs(A/'FIG5_MEDIAN_MARKS.csv',qa['fig5']['median_marks'])
 export(op.figure6(node,qa),'FIG6','fig_inputs/fig6/node_waveforms/FIG7A_NODE_WAVEFORMS.csv; A_RELAXATION_FIT.csv; B_INDIRECT_NODE_SENSITIVITY.csv','a;b with categorical t_pLH column')
 cs(A/'FIG6A_EQ9_MARKERS.csv',qa['fig6']['Eq7_marker_records']);cs(A/'FIG6B_THEORY_CURVE.csv',qa['fig6']['theory_curve'])
 # Netlist-derived circuit schematic. Only .sp text is parsed; no simulator, model evaluation or RAW parser.
 sys.path.insert(0,str(S/'code'));p=load('parser_and_qa',S/'code/parser_and_qa.py');sys.modules['parser_and_qa']=p
 p.ROOT=A;p.source_zip=lambda:S/'netlist/frozen_topology_only.zip';p.csvout=lambda path,rows:cs(A/path,rows);p.js=lambda path,v:js(A/path,v)
 (A/'data').mkdir(exist_ok=True)
 fig1=load('netlist_fig1',S/'code/build_fig1.py');fig1.source_zip=p.source_zip;fig1.csvout=p.csvout;fig1.js=p.js
 fig1.save=lambda f,n:export(f,'FIG1','netlist/frozen_topology_only.zip; 96 seven-stage decks with exact original bytes; netlist-derived schematic','a;b;c;d;e')
 fig1.main()
 # Four C1 native samples, frozen JSON independently checked against the exported electronic CSV.
 r=rd(S/'electronic/Supplementary_Data_S5_F_C1_K1_K4.csv');native=json.loads((S/'evidence/C1_fresh.json').read_text())
 x=np.array([int(z['k']) for z in r]);y=np.array([float(z['v_before_input_rise_V'])*1000 for z in r])
 assert len(r)==4 and all(abs(float(z['v_before_input_rise_V'])-native[f'netp_before_inrise_{z["k"]}_V'])<1e-15 for z in r)
 assert f'{y[0]:.1f}'=='184.4' and all(f'{v:.1f}'=='208.4' for v in y[1:])
 f,ax=plt.subplots(figsize=(90/25.4,65/25.4));ax.plot(x,y,'o-',color=mod.BLUE,lw=1,ms=4);ax.set_xticks(x);ax.set_xlabel('Global input rising-edge index $k$');ax.set_ylabel(r'$V_N$ before input rise (mV)');ax.set_ylim(180,215)
 ax.annotate(r'$\Delta V$ = '+f'{y[1]-y[0]:.1f}'+' mV',xy=(1.6,196),ha='left',fontsize=8)
 for k,v in zip(x,y):ax.annotate(f'{v:.1f}',(k,v),xytext=(-4,5) if k==4 else (0,5),textcoords='offset points',ha='right' if k==4 else 'center',fontsize=7)
 ax.spines[['top','right']].set_visible(False);f.tight_layout();export(f,'FIG_S5_1','electronic/Supplementary_Data_S5_F_C1_K1_K4.csv + evidence/C1_fresh.json','four native samples before global rising edges, not local device turn-on')
 # Uniform drift, recalculated from the full 4032 coefficients (no fitting/resampling).
 e=rd(S/'electronic/Supplementary_Data_S8_D.csv');c=rd(S/'fig_inputs/coef.csv');base=rd(S/'fig_inputs/records.csv');coeff={(z['src'],z['mos'],z['edge'],z['role']):z for z in c};meta={z['src']:z for z in base}
 from collections import defaultdict
 pop=defaultdict(list)
 for z in e:
  k=tuple(z[x] for x in ['src','mos','edge','role']);q=coeff[k];assert abs(float(z['S_E1_paper_fs_per_V'])-float(q['S_E1']))<1e-6
  pop[(z['src'],z['edge'])].append((float(q['S_E1'])-float(q['S_IS']),float(q['S_IS']),z['role']))
 actual=[]
 for (src,edge),zs in pop.items():
  for scenario in ['all_devices','pMOS_only']:
   a=[z for z in zs if scenario=='all_devices' or z[2] in ['p-sw-only','p-tied-only']];ds=math.fsum(v[0] for v in a);si=math.fsum(v[1] for v in a)
   actual.append(dict(src=src,edge=edge,scenario=scenario,rho_pct=100*ds/si if abs(si)>=100 else None,c_u=ds/7000,topology=meta[src]['topology'],position=meta[src]['position']))
 cs(A/'RHO_CU_RECOMPUTED.csv',actual)
 frozen=rd(S/'electronic/Supplementary_Data_S9_per_config_edge.csv');key=lambda z:(z['src'],z['edge'],z['scenario']);fr={key(z):z for z in frozen}
 dif=[]
 for z in actual:
  old=fr[key(z)];dif.append(abs(z['c_u']-float(old['c_u'])))
  if z['rho_pct'] is not None:assert abs(z['rho_pct']-float(old['rho_pct']))<1e-8
 assert max(dif)<1e-8
 groups=[('NOR2','td_phl'),('NOR2','td_plh'),('NAND2','td_phl'),('NAND2','td_plh')];f,axs=plt.subplots(1,2,figsize=(190/25.4,77/25.4));rng=np.random.default_rng(0)
 for j,(scenario,col,label) in enumerate([('all_devices',mod.BLUE,'All devices'),('pMOS_only',mod.RED,'pMOS only')]):
  vals=[[z['rho_pct'] for z in actual if z['scenario']==scenario and z['position']=='POS-B' and z['topology']==top and z['edge']==edge and z['rho_pct'] is not None] for top,edge in groups];pos=np.arange(1,5)+(-.18 if j==0 else .18)
  bp=axs[0].boxplot(vals,positions=pos,widths=.3,whis=(5,95),showfliers=False,patch_artist=True,medianprops={'color':'black'})
  for b in bp['boxes']:b.set(facecolor='white',edgecolor=col)
  for k,v in enumerate(vals):axs[0].scatter(pos[k]+rng.uniform(-.07,.07,len(v)),v,s=7,color=col,label=label if k==0 else None)
 axs[0].set_xticks(range(1,5),[top+'\n'+mod.EDGE[edge] for top,edge in groups]);axs[0].axhline(0,color='gray',lw=.6);axs[0].set_ylabel(r'$\rho$ (%)');axs[0].legend(frameon=False,fontsize=7);axs[0].set_title('(a) Uniform-drift sensitivity bias',loc='left',fontsize=8)
 cu=np.array([z['c_u'] for z in actual if z['scenario']=='all_devices' and z['topology']=='NOR2' and z['position']=='POS-B' and z['edge']=='td_phl']);N=np.geomspace(1,200,200);dv=54.1
 qs={'median':float(np.median(cu)),'P90':float(np.quantile(cu,.9)),'max':float(np.max(cu))}
 for (label,v),color in zip(qs.items(),['#86b6ef',mod.BLUE,'#104281']):axs[1].plot(N,N*v*dv/1000,label=label,color=color)
 for yy in [1,10]:axs[1].axhline(yy,color='gray',ls='--',lw=.6);axs[1].text(1.1,yy*1.07,f'{yy} ps',fontsize=7)
 for label,yy in [('median',1),('median',10),('max',10)]:
  n=yy*1000/(qs[label]*dv);axs[1].plot(n,yy,'o',color=mod.BLUE,ms=3);axs[1].annotate(str(math.ceil(n-1e-9)),(n,yy),xytext=(4,-9),textcoords='offset points',fontsize=7)
 axs[1].set(xscale='log',yscale='log',xlim=(1,200),ylim=(.05,50));axs[1].set_xlabel(r'Effective depth $fN$ (stages)');axs[1].set_ylabel('First-order accumulated bias (ps)');axs[1].set_title('(b) Hypothetical uniform 54.1 mV stress',loc='left',fontsize=8);axs[1].legend(frameon=False,title=r'$c_u$ statistic',fontsize=7,title_fontsize=7)
 for ax in axs:ax.spines[['top','right']].set_visible(False)
 f.subplots_adjust(bottom=.25,wspace=.42);f.text(.5,.02,r'$f=1$: same-type unloaded stages; linear estimate, not measured aging or path slack',ha='center',fontsize=7)
 export(f,'FIG_S9_1','electronic/Supplementary_Data_S8_D.csv + fig_inputs/coef.csv; all4032 coefficients; validated S9 per-config','a;b')
 qa['S9_reproduction']={'rho_max_error_pct':max(abs(z['rho_pct']-float(fr[key(z)]['rho_pct'])) for z in actual if z['rho_pct'] is not None),'cu_max_error':max(dif),'rho_NOR2_POSB_phl_all_median':float(np.median([z['rho_pct'] for z in actual if z['scenario']=='all_devices' and z['position']=='POS-B' and z['topology']=='NOR2' and z['edge']=='td_phl'])),'minimum_stages_at_54p1_mV':math.ceil(1000/(qs['median']*dv))}
 assert qa['S9_reproduction']['minimum_stages_at_54p1_mV']==12
 js(A/'QA.json',qa);js(A/'SOURCE_LOCK.json',locks);js(A/'FIELD_MAP.json',fm);cs(F/'FIGURE_DIMENSIONS.csv',built)
 # Complete panel-level binding to source files and transformations.
 bindings=[]
 for rec in built:
  for panel in rec['panels'].split(';'):bindings.append(dict(figure=rec['figure'],panel=panel,source=rec['source'],source_lock='04_REPRODUCIBILITY/sources/SOURCE_LOCK.json',field_map='06_QA/figure_numerics/FIELD_MAP.json',script='04_REPRODUCIBILITY/build_figures.py',seed=0,quantile='numpy linear, except specified nearest-rank in S2-H (not replotted)',output_sha256=rec['pdf_sha256']))
 cs(F/'FIGURE_SOURCE_MANIFEST.csv',bindings);cs(B/'00_SOURCE_AND_RULES/FIGURE_SOURCE_MANIFEST.csv',bindings)
 cs(B/'06_QA/FIGURE_REBUILD_AUDIT.csv',built)
 return qa,built
