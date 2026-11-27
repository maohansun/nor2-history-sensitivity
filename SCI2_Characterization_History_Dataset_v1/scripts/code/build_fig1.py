from parser_and_qa import *
from collections import Counter
COLOR='#337F82'
def load_decks():
 decks=[];rows=[];members=[]
 with zipfile.ZipFile(source_zip()) as z:
  sums={l.split(None,1)[1].strip():l.split()[0] for l in z.read('SHA256SUMS.txt').decode().splitlines() if l.strip()}
  for n in sorted(z.namelist()):
   if not n.endswith('.sp'):continue
   deck_bytes=z.read(n);assert digest(deck_bytes)==sums[n];d=parse_deck(deck_bytes,str(source_zip())+'!'+n);rr=d['rows']
   assert len(d['instances'])==7 and len(rr)==28
   for k in range(1,8):
    r=[x for x in rr if x['stage']==k];assert len(r)==4
    top=d['meta']['topology'];pos=d['meta']['position'];fix='0' if top=='NOR2' else 'vdd'
    assert all(x['fixed']==fix and x['switching']==('in' if k==1 else rr[(k-2)*4]['output']) for x in r)
    for x in r:
     assert x['b']==('vdd' if x['model']=='pmos' else '0')
     assert abs(x['W_m']/x['L_m']-(8 if x['model']=='pmos' else 2))<1e-10
     assert abs(x['L_m']-{'PTM45':45e-9,'PTM65':65e-9}[x['technology']])<1e-20
    roles={x['role']:x for x in r};a,b=(roles['PTop'],roles['PBottom']) if top=='NOR2' else (roles['NTop'],roles['NBottom'])
    assert a['local_d']==b['local_s'] and a['local_s']=='vdd' and b['local_d']=='y' if top=='NOR2' else a['local_s']==b['local_d'] and a['local_d']=='y' and b['local_s']=='vss'
    inner='netp' if top=='NOR2' else 'netn';assert inner in [a['local_d'],a['local_s']]
    outs=b if top=='NOR2' else a;rail=a if top=='NOR2' else b
    assert outs['local_g']==('sw' if pos=='POS-A' else 'fix') and rail['local_g']==('fix' if pos=='POS-A' else 'sw')
    parallel=[x for x in r if x not in [a,b]]
    assert len(parallel)==2 and {x['local_g'] for x in parallel}=={'sw','fix'}
    assert all(x['local_d']=='y' and x['local_s']==('vss' if top=='NOR2' else 'vdd') for x in parallel)
   assert not any(t[0].lower().startswith(('r','c')) for t in d['top'])
   decks.append(d);rows+=rr;members.append({'member':n,'sha256':digest(deck_bytes),'context':d['meta']['run_id']})
 groups=Counter(tuple(d['meta'][k] for k in ['technology','topology','position']) for d in decks)
 assert len(decks)==96 and len(groups)==8 and set(groups.values())=={12}
 signatures={}
 for d in decks:
  key=tuple(d['meta'][k] for k in ['technology','topology','position'])
  sig=[tuple(r[k] for k in ['stage','role','model','d','g','s','b','W_m','L_m']) for r in d['rows']]
  if key in signatures:assert signatures[key]==sig
  signatures[key]=sig
 csvout('data/FIG1_NETLIST_CONNECTIVITY.csv',rows)
 return decks,{'status':'PASS','contexts_checked':96,'devices':len(rows),'groups':{'/'.join(k):v for k,v in groups.items()},'parent_zip':str(source_zip()),'parent_sha256':sha(source_zip()),'members':members,'checks':['seven stages','4 MOS/stage','D/G/S/B exact','true parallel branches','internal series node','POS mappings','fixed input','L and W/L','body rail','no explicit R/C load','12-context full topology equality']}
def main():
 style()
 import matplotlib.pyplot as plt
 from matplotlib.patches import Circle,Rectangle,FancyArrowPatch
 decks,proof=load_decks();trace=[];symbol_styles=[]
 fig=plt.figure(figsize=(7.1,5.0));gs=fig.add_gridspec(3,2,height_ratios=[1.4,2.4,2.4],hspace=.18,wspace=.12)
 ax=fig.add_subplot(gs[0,:]);ax.axis('off');ax.set(xlim=(-.8,14.9),ylim=(-3.2,1.5));ax.set_title('(a) Seven-stage NAND2/NOR2 chain',loc='left',fontweight='bold',pad=3)
 rr=decks[0]['rows']
 for k in range(7):
  q=rr[k*4];x=k*2
  ax.add_patch(Rectangle((x,0),1.3,.65,fill=False,lw=1));ax.text(x+.65,.33,f'G{k+1}',ha='center',va='center')
  ax.plot([x-.6,x],[.43,.43],color='black');ax.plot([x+.42,x+.42],[-.5,0],color='black');ax.text(x+.42,-.83,'fix',ha='center')
  ax.plot([x+1.3,x+2 if k<6 else x+1.85],[.43,.43],color='black')
  ax.plot(x+1.65,.43,'o',ms=2.6,color='black')
  ax.text(x+1.65,.9,'out ($V_{out}$)' if k==6 else q['output'],ha='right' if k==6 else 'center',fontsize=12 if k==6 else 8)
  trace.append({'panel':'a','stage':k+1,'switching':q['switching'],'fixed':q['fixed'],'output':q['output'],'source_sha256':q['source_sha256']})
 ax.plot(-.6,.43,'o',ms=3,color='black');ax.text(-.6,.9,'in ($V_{in}$)',ha='left',fontsize=12)
 ax.text(6.6,-1.8,'fix = 0 (NOR2); fix = VDD (NAND2)',ha='center')
 ax.text(6.6,-2.9,r'Chain delay measured between $V_{in}$ and $V_{out}$',ha='center',fontsize=12)
 for row,top in enumerate(['NOR2','NAND2'],1):
  for col,pos in enumerate(['POS-A','POS-B']):
   label=['b','c','d','e'][(row-1)*2+col];ax=fig.add_subplot(gs[row,col]);ax.axis('off');ax.set(xlim=(-4.7,5.4),ylim=(-.8,11.6))
   ax.set_title(f'({label}) {top} {pos}',loc='left',fontweight='bold',pad=3)
   d=next(d for d in decks if d['meta']['topology']==top and d['meta']['position']==pos);r=d['rows'][:4];pins={};devs={}
   def wire(net,points,devices=(),color='black',lw=1):
    # Any named device terminal included in a wire must have this parsed net.
    for device,terminal in devices:assert devs[device]['local_'+terminal]==net
    bulk=any(t[1]=='b' for t in devices)
    ls=(0,(3,2)) if bulk else '-'
    ax.plot([p[0] for p in points],[p[1] for p in points],color=color,lw=lw,ls=ls,solid_capstyle='round')
    trace.append({'panel':label,'net':net,'points':points,'terminals':devices,'bulk_return':bulk,'linestyle':'dashed' if bulk else 'solid','source_sha256':r[0]['source_sha256']})
   for q in r:
    role=q['role'];series=role in ['PTop','PBottom','NTop','NBottom'];pm=q['model']=='pmos'
    if top=='NOR2':x=0 if series else (-2.5 if q['local_g']=='sw' else 2.4);y=(8.4 if role=='PTop' else 5.8) if series else 1.6
    else:x=0 if series else (-2.5 if q['local_g']=='sw' else 2.4);y=(4.7 if role=='NTop' else 2.1) if series else 8.4
    emph=pos=='POS-B' and role==('PTop' if top=='NOR2' else 'NBottom');color=COLOR if emph else 'black'
    # Four-terminal MOS glyph: isolated gate, channel, D/S branches,
    # separate bulk plate and bulk arrow. Bulk is wired to the parsed rail.
    for ya,yb in [(-.4,-.18),(-.10,.10),(.18,.4)]:ax.plot([x,x],[y+ya,y+yb],color=color,lw=1.8 if emph else 1.2)
    ax.plot([x-.22,x-.22],[y-.4,y+.4],color=color,lw=1.4 if emph else 1)
    for sign in [-1,1]:ax.plot([x,x+.4,x+.4],[y+sign*.4,y+sign*.4,y+sign*.85],color=color,lw=1.4 if emph else 1)
    ax.plot([x+.19,x+.19],[y-.16,y+.16],color=color,lw=1)
    if pm:ax.plot([x+.2,x+.65],[y,y],lw=1,color=color)
    else:ax.add_patch(FancyArrowPatch((x+.65,y),(x+.2,y),arrowstyle='-|>',mutation_scale=5.5,lw=.8,color=color))
    symbol_styles.append({'panel':label,'device':q['device'],'model':q['model'],'gate_circle':pm,'bulk_arrow':not pm,'bulk_terminal_and_wire_retained':True})
    ax.plot([x+.65,x+.85],[y,y],color=color,lw=1)
    gateend=x-.43 if pm else x-.22
    ax.plot([x-.88,gateend],[y,y],color=color,lw=1)
    if pm:ax.add_patch(Circle((x-.33,y),.10,fill=False,lw=1,edgecolor=color,facecolor='white'))
    ax.text(x-.98,y,q['local_g'],ha='right',va='center',fontsize=8,color=color)
    ax.text(x+1.4,y+.55,role,fontsize=8,color=color,fontweight='bold' if emph else 'normal')
    ax.text(x+1.25,y-.9,'B',fontsize=8,color='.25')
    # pMOS upper terminal is actual source; nMOS upper is actual drain.
    pins[role]={'s':(x+.4,y+(.85 if pm else -.85)),'d':(x+.4,y+(-.85 if pm else .85)),'b':(x+.85,y),'g':(x-.88,y)};devs[role]=q
    trace.append({'panel':label,'device':q['device'],'role':role,'model':q['model'],'nodes':{t:q['local_'+t] for t in ['d','g','s','b']},'terminal_positions':pins[role],'highlight':emph,'source_sha256':q['source_sha256']})
   vdd_y=10.2;gnd_y=.15
   # Actual body wires: a direct S tie only when B equals parsed S;
   # otherwise route an external rail wire without shorting the internal node.
   for role,q in devs.items():
    bpin=pins[role]['b'];spin=pins[role]['s'];net=q['local_b']
    if net==q['local_s']:
     wire(net,[bpin,(bpin[0]+.25,bpin[1]),(bpin[0]+.25,spin[1]),spin],[(role,'b'),(role,'s')],color='.35',lw=.8)
    else:
     target_y=vdd_y if net=='vdd' else gnd_y
     wire(net,[bpin,(4.65,bpin[1]),(4.65,target_y),(.4,target_y)],[(role,'b')],color='.35',lw=.8)
   if top=='NOR2':
    wire('vdd',[pins['PTop']['s'],(.4,vdd_y)], [('PTop','s')])
    wire('netp',[pins['PTop']['d'],pins['PBottom']['s']],[('PTop','d'),('PBottom','s')])
    wire('y',[pins['PBottom']['d'],(.4,4.0)], [('PBottom','d')])
    parallel=['NSw','NFix']
    for role in parallel:wire('y',[pins[role]['d'],(pins[role]['d'][0],4)],[(role,'d')]);wire('vss',[pins[role]['s'],(pins[role]['s'][0],gnd_y)],[(role,'s')])
    wire('y',[(-2.1,4),(3.8,4)]);wire('vss',[(-2.1,gnd_y),(.4,gnd_y),(2.8,gnd_y)])
    internal_y=7.1;internal='netp'
   else:
    parallel=['PSw','PFix']
    for role in parallel:wire('vdd',[pins[role]['s'],(pins[role]['s'][0],vdd_y)],[(role,'s')]);wire('y',[pins[role]['d'],(pins[role]['d'][0],6.8)],[(role,'d')])
    wire('vdd',[(-2.1,vdd_y),(.4,vdd_y),(2.8,vdd_y)]);wire('y',[(-2.1,6.8),(3.8,6.8)])
    wire('y',[pins['NTop']['d'],(.4,6.8)],[('NTop','d')]);wire('netn',[pins['NTop']['s'],pins['NBottom']['d']],[('NTop','s'),('NBottom','d')]);wire('vss',[pins['NBottom']['s'],(.4,gnd_y)],[('NBottom','s')])
    internal_y=3.4;internal='netn'
   out_y=4 if top=='NOR2' else 6.8
   ax.plot([-.0,.8],[vdd_y+.45,vdd_y+.45],color='black',lw=1);ax.plot([.4,.4],[vdd_y,vdd_y+.45],color='black',lw=1);ax.text(.4,vdd_y+.7,'VDD',ha='center',fontsize=8)
   ax.plot([.4,.4],[gnd_y,gnd_y-.25],color='black',lw=1)
   for dy,width in [(0,.7),(-.13,.45),(-.26,.18)]:ax.plot([.4-width/2,.4+width/2],[gnd_y-.25+dy]*2,color='black',lw=.9)
   ax.text(4.0,out_y,'y',va='center',fontsize=8)
   for x,y in [(.4,vdd_y),(.4,gnd_y),(.4,out_y)]:ax.plot(x,y,'o',ms=2.8,color='black')
   if pos=='POS-B':ax.plot(.4,internal_y,marker='D',ms=4.8,mfc=COLOR,mec='black',mew=.8)
   else:ax.plot(.4,internal_y,'o',ms=3,color='black')
   ax.text(-.0,internal_y,'N ('+internal+')' if pos=='POS-B' else internal,ha='right',va='center',fontsize=8,color=COLOR if pos=='POS-B' else 'black')
   assert all(q['local_b'] in ['vdd','vss'] for q in r)
   proof.setdefault('highlight_mapping',[]).append({'panel':label,'context':r[0]['context'],'device':('PTop' if top=='NOR2' else 'NBottom') if pos=='POS-B' else None,'node':internal if pos=='POS-B' else None})
 fig.subplots_adjust(left=.055,right=.98,top=.93,bottom=.10)
 fig.text(.5,.045,'Teal/bold device and diamond N: POS-B rail-side switching condition.',ha='center',fontsize=8,color='black')
 fig.text(.5,.015,'Dashed gray: bulk (B) ties. Solid: source/drain wiring.',ha='center',fontsize=8,color='black')
 proof.update({'panel_labels':['a','b','c','d','e'],'drawn_body_wires':16,'terminal_trace':'FIG1_DRAWING_TRACE.json'})
 js('data/FIG1_TOPOLOGY_PROOF.json',proof);js('data/FIG1_DRAWING_TRACE.json',trace);js('data/FIG1_SYMBOL_STYLE_QA.json',symbol_styles)
 save(fig,'SCI2_FIG1_CMOS_SCHEMATICS');plt.close(fig)
if __name__=='__main__':main()
