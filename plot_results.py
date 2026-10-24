"""Generate figures only from actual simulation CSVs. No fabricated figures or concept diagrams."""
from pathlib import Path
import csv,json,argparse,collections,statistics,math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

ap=argparse.ArgumentParser();ap.add_argument('--results',default='results');ap.add_argument('--out',default='../article_assets')
a=ap.parse_args();root=Path(a.results);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
read=lambda name:list(csv.DictReader((root/name).open()))
t=read('tournaments.csv'); rounds=read('rounds.csv'); abr=read('bridge_ablation.csv')
N=len(t); colors={'Atlas':'#2E5A88','Blitz':'#D36B5C','Coda':'#6B8DA3','Echo':'#76679B','Mira':'#539287','Sentinel':'#A89C6D'}
order=['Atlas','Sentinel','Coda','Echo','Mira','Blitz'];bg='#FFFFFF';fg='#202020';muted='#666666'
plt.rcParams.update({'figure.facecolor':bg,'axes.facecolor':bg,'savefig.facecolor':bg,'text.color':fg,'axes.labelcolor':fg,'xtick.color':muted,'ytick.color':muted,'font.family':'DejaVu Sans','font.size':13,'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#888888'})
def save(name):plt.savefig(out/name,dpi=170,facecolor=bg,bbox_inches='tight',pad_inches=.25);plt.close()

counts=collections.Counter(x['winner'] for x in t)
fig,ax=plt.subplots(figsize=(12.5,5.8));bars=ax.barh(order[::-1],[counts[n] for n in order[::-1]],color=[colors[n] for n in order[::-1]],height=.57)
for b,n in zip(bars,order[::-1]):ax.text(b.get_width()+2,b.get_y()+b.get_height()/2,f'{counts[n]}/{N}  ({counts[n]/N:.1%})',va='center',color=fg,fontsize=13)
ax.set_xlim(0,max(counts.values())*1.3);ax.set_xlabel('Tournament victories');ax.set_title(f'Who won?  {N} seeded runs of six Python agent policies',loc='left',fontsize=18,pad=22);ax.grid(axis='x',color='#D6D6D6',alpha=.35);ax.set_axisbelow(True);save('fig_wins.png')

stages=['red_light','dalgona','tug_of_war','marbles','glass_bridge'];stage_names=['Interrupt','Exact format','Debate','Negotiate','Bridge']
elims=collections.Counter((x['round'],x['agent']) for x in rounds if int(x['eliminated']))
fig,ax=plt.subplots(figsize=(12.5,5.3));bottom=[0]*5
for n in order:
 v=[elims[(s,n)] for s in stages]
 ax.bar(range(5),v,bottom=bottom,label=n,color=colors[n],width=.59)
 bottom=[b+j for b,j in zip(bottom,v)]
ax.set_xticks(range(5),stage_names);ax.set_ylabel('Number of elimination events');ax.set_title('Which challenge removes which strategy?',loc='left',fontsize=18,pad=22);ax.legend(ncol=3,frameon=False,loc='upper right',fontsize=10);ax.grid(axis='y',color='#D6D6D6',alpha=.4);ax.set_axisbelow(True);save('fig_elimination.png')

by=collections.defaultdict(list)
for x in abr:by[x['agent']].append(int(x['difference']))
fig,ax=plt.subplots(figsize=(12.5,5.5)); names=['Atlas','Sentinel','Coda','Blitz'];means=[statistics.mean(by[n]) for n in names]
ax.bar(names,means,color=[colors[n] for n in names],width=.55)
for i,n in enumerate(names):ax.text(i,means[i]+.065,f'+{means[i]:.2f}',ha='center',fontsize=13)
ax.axhline(0,color=fg,lw=.7,alpha=.5);ax.set_ylim(-.2,max(means)+.4);ax.set_ylabel('Mean extra correct panels out of 20');ax.set_title('Paired test: verified failure history ON vs OFF',loc='left',fontsize=18,pad=22);ax.text(0,-.15,'Same world and decision RNG in each pair • 250 seeds per pair',color=muted,fontsize=10);save('fig_bridge_memory.png')

# per-agent median virtual ticks from FEATURED trace (not clock seconds)
f=json.loads((root/'featured.json').read_text());red=f['rounds'][0]['details']
fig,ax=plt.subplots(figsize=(12.5,5.4));v=[red[n]['mean_reaction_ticks'] for n in order];bars=ax.bar(order,v,color=[colors[n] for n in order],width=.55)
for b,val in zip(bars,v):ax.text(b.get_x()+b.get_width()/2,val+.035,f'{val:.2f}',ha='center',fontsize=12)
ax.set_ylim(0,max(v)+.65);ax.set_ylabel('Mean virtual reaction ticks (lower is faster)');ax.set_title('Stop compliance measures polling delay—not LLM thought time',loc='left',fontsize=17,pad=22);ax.text(0,-.17,'Seed 42 • 18 stop events per policy • virtual ticks have no seconds conversion',color=muted,fontsize=10);save('fig_interrupt_ticks.png')

# measured wall-clock microseconds can be volatile; show medians by agent
by_us=collections.defaultdict(list)
for x in rounds:by_us[x['agent']].append(float(x['measured_policy_us']))
fig,ax=plt.subplots(figsize=(12.5,5.4));u=[statistics.median(by_us[n]) for n in order]
ax.bar(order,u,color=[colors[n] for n in order],width=.55)
for i,z in enumerate(u):ax.text(i,z+5,f'{z:.0f} µs',ha='center',fontsize=11)
ax.set_ylabel('Measured Python execution per agent/round (µs)');ax.set_ylim(0,max(u)*1.24)
ax.set_title('Local policy runtime (not model inference latency)',loc='left',fontsize=18,pad=22)
save('fig_python_runtime.png')
print('Made figures in',out)
