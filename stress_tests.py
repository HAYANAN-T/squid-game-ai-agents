"""Sensitivity tests on the same policy simulator; no LLM models or imagined results.
A controlled adversarial log ablation asks when memory is worse than no memory.
"""
import argparse,csv,random,statistics,json
from pathlib import Path
from arena import BY_NAME,bridge_world,rng

# Same safe tile sequence and per-agent noisy clue for every paired intervention.
# The second mover can observe the first's failed tile, but its log entry is
# corrupted at a specified rate (independently of the agent's other randomness).
def simulate_pair(seed, a, b, corruption, use_memory):
    scored={a.name:0,b.name:0}
    for item in bridge_world(seed):
        step,safe=item['step'],item['safe']
        order=(a,b) if step%2 else (b,a)
        failed=None
        for p in order:
            local=rng(seed,'bridge_decision',p.name,step)
            clue=safe if local.random()<p.clue_accuracy else ('L' if safe=='R' else 'R')
            trust_draw=local.random()
            # Corruption happens in the public *feedback channel*, not in a model's perception.
            if use_memory and failed is not None and trust_draw<p.history_trust:
                flipped=rng(seed,'poisoned_log',step).random()<corruption
                reported_failed=('R' if failed=='L' else 'L') if flipped else failed
                choice=('R' if reported_failed=='L' else 'L')
            else:
                choice=clue
            scored[p.name]+=int(choice==safe)
            if choice!=safe: failed=choice
    return scored

def run(seed_start=45000,seeds=500):
    rows=[]
    for seed in range(seed_start,seed_start+seeds):
        for a,b in [(BY_NAME['Atlas'],BY_NAME['Echo']),(BY_NAME['Sentinel'],BY_NAME['Coda'])]:
            baseline=simulate_pair(seed,a,b,0,False)
            for noise in [0,.1,.25,.5,.75,1.0]:
                experiment=simulate_pair(seed,a,b,noise,True)
                for p in (a,b):
                    rows.append(dict(seed=seed,agent=p.name,opponent=b.name if p==a else a.name,
                                     log_corruption=noise, memory_correct=experiment[p.name],
                                     no_memory_correct=baseline[p.name],delta=experiment[p.name]-baseline[p.name]))
    return rows

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='results');ap.add_argument('--seeds',type=int,default=500);args=ap.parse_args()
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True);rows=run(seeds=args.seeds)
    with (out/'poisoned_memory.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    summary={str(r):round(statistics.mean(x['delta'] for x in rows if x['log_corruption']==r),4) for r in [0,.1,.25,.5,.75,1.0]}
    (out/'memory_noise_summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))
