"""Plain white-background matplotlib charts using recorded stress-test CSV only."""
from pathlib import Path
import csv, argparse, statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=argparse.ArgumentParser();p.add_argument('--input',default='results/poisoned_memory.csv');p.add_argument('--output',default='../article_assets/fig_memory_poisoning_white.png');a=p.parse_args()
rows=list(csv.DictReader(open(a.input)))
xs=[0,.1,.25,.5,.75,1.0]
ys=[statistics.mean(float(r['delta']) for r in rows if float(r['log_corruption'])==x) for x in xs]
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'figure.facecolor':'white','axes.facecolor':'white','savefig.facecolor':'white','axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(figsize=(10,5.1));ax.plot([x*100 for x in xs],ys,color='#244e76',linewidth=2,marker='o',markersize=7)
ax.axhline(0,color='#5f5f5f',linestyle='--',linewidth=1)
for x,y in zip(xs,ys):ax.annotate(f'{y:+.2f}',(x*100,y),xytext=(0,11 if y>=0 else -19),textcoords='offset points',ha='center',fontsize=10)
ax.set_xlabel('Corrupted public failure reports (%)');ax.set_ylabel('Average extra correct bridge panels (out of 20)')
ax.set_title('When borrowed experience becomes misinformation',loc='left',fontsize=15,pad=15)
ax.grid(axis='y',alpha=.22);fig.subplots_adjust(bottom=.25);fig.text(.12,.02,'500 paired worlds · two fixed agent pairings · 2,000 agent outcomes per condition · scripted policy simulation',fontsize=9,color='#555555')
Path(a.output).parent.mkdir(parents=True,exist_ok=True);fig.savefig(a.output,dpi=180,bbox_inches='tight');plt.close(fig)
print(a.output)
