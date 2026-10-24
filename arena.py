"""Reproducible *algorithmic* agent tournament, not a benchmark of commercial LLMs.

Five staged challenges deliberately map to testable systems properties:
interrupt latency, schema compliance, evidence-based debate, incomplete-information
bargaining, and Bayesian use of verified failure history.

All contestant behavior is Python policy code. No language-model calls or hidden
model thoughts. Virtual ticks are not seconds; wall-clock metrics measure only this
local Python implementation.
"""
from __future__ import annotations
import argparse, csv, json, hashlib, random, statistics, time
from dataclasses import dataclass, asdict
from collections import Counter,defaultdict
from pathlib import Path

@dataclass(frozen=True)
class Agent:
    name: str
    title: str
    interrupt_checks: int  # virtual ticks between cooperative cancel checks
    schema_error: float
    evidence_recall: float
    rebuttal_depth: int
    bargaining_target: int
    bargain_flex: int
    bluff_rate: float
    clue_accuracy: float
    history_trust: float

AGENTS=(
 Agent('Atlas','Balanced planner',1,.025,.83,3,6,3,.08,.73,.95),
 Agent('Blitz','Speed-first reactor',4,.19,.43,1,8,1,.45,.62,.23),
 Agent('Coda','Format specialist',2,.004,.64,2,7,2,.05,.66,.48),
 Agent('Echo','Persuasive debater',3,.11,.91,4,6,2,.28,.65,.52),
 Agent('Mira','Adaptive negotiator',3,.10,.62,2,5,4,.35,.68,.65),
 Agent('Sentinel','Cautious verifier',1,.009,.94,3,5,2,.01,.78,.99),
)
BY_NAME={a.name:a for a in AGENTS}
ROUNDS=[('red_light','Red Light, Green Light'),('dalgona','Dalgona'),('tug_of_war','Tug of War'),('marbles','Marbles'),('glass_bridge','Glass Bridge')]
FACTS=(
 ('A CDN cache can never serve stale data.',False,'cache_invalidation','Stale objects can survive until expiry or invalidation.'),
 ('A selective database index can reduce lookup work.',True,'index_selectivity','An index can avoid scanning every row when selectivity is useful.'),
 ('More concurrent retries always help an overloaded service recover.',False,'retry_storm','Uncoordinated retries can increase load during failure.'),
 ('Parameterized SQL reduces injection risk.',True,'bound_parameters','Separating SQL structure from values reduces injection attacks.'),
 ('TLS alone prevents every web attack.',False,'threat_model','Transport encryption does not prevent authorization failures.'),
 ('Idempotency keys can reduce duplicate payment effects.',True,'idempotency','A server can recognize duplicate requests using a stable key.'),
)

def rng(seed,*keys):
    raw='|'.join(map(str,(seed,)+keys)).encode('utf8')
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:8],'big'))

def timed(fn,*args,**kwargs):
    start=time.perf_counter_ns();res=fn(*args,**kwargs)
    return res,(time.perf_counter_ns()-start)/1000.0  # measured CPU wall usec, not LLM time


def red_light(a,seed):
    trace=[]; score=0
    for i in range(18):
        g=rng(seed,'signal',i)
        deadline=g.choice([1,2,2,3,3,4,5])
        # Controller samples stop signal after up to interval-1 virtual ticks.
        phase=rng(seed,'phase',a.name,i).randrange(a.interrupt_checks)
        # Reaction includes mandatory one-tick acknowledgment.
        latency=phase+1
        stopped=latency<=deadline
        score+=int(stopped)
        trace.append({'step':i+1,'light':'RED','deadline_virtual_ticks':deadline,
             'poll_interval_ticks':a.interrupt_checks,'phase_ticks':phase,
             'reaction_virtual_ticks':latency,'stopped_before_deadline':stopped,
             'action':'CANCELLED' if stopped else 'MISSED_DEADLINE',
             'explanation':f'Polled every {a.interrupt_checks} virtual tick(s); interruption observed after {latency} tick(s).',
             'candidate_checks':a.interrupt_checks})
    return {'score':score,'passes':score,'total':18,'mean_reaction_ticks':round(statistics.mean(t['reaction_virtual_ticks'] for t in trace),3),'events':trace}


def dalgona(a,seed):
    trace=[];score=0
    for i in range(18):
        x=3+i; y=4+2*i
        wanted='{"status":"OK","value":'+str(x+y)+'}'
        er=rng(seed,'cookie',a.name,i)
        error=er.random()<a.schema_error
        kind=er.choice(['extra_space','suffix','wrong_value','wrong_case','newline']) if error else 'none'
        output=wanted
        if kind=='extra_space': output=output.replace(',"value"',', "value"')
        elif kind=='suffix':output+='.'
        elif kind=='wrong_value':output=output.replace(str(x+y),str(x+y+1),1)
        elif kind=='wrong_case':output=output.replace('OK','Ok')
        elif kind=='newline':output+='\n'
        syntactically_valid=False
        try:
            parsed=json.loads(output)
            syntactically_valid=(list(parsed.keys())==['status','value'] and type(parsed['value']) is int and parsed['status']=='OK')
        except (ValueError,TypeError):pass
        exact=(output==wanted)
        score+=int(exact)
        trace.append({'step':i+1,'expected':wanted,'actual':output,'error':kind,
             'valid_json_schema':syntactically_valid,'exact_contract':exact,
             'action':'ACCEPTED' if exact else 'BROKEN_COOKIE',
             'explanation':'Exact bytes and correct value required; syntactic JSON alone is insufficient.',
             'candidate_checks':2})
    return {'score':score,'exact_matches':score,'total':18,'events':trace}


def make_argument(a,question,seed,turn):
    text,truth,eid,evidence=FACTS[question]
    local=rng(seed,'debate',a.name,question,turn)
    has_evidence=(local.random()<a.evidence_recall)
    correct=has_evidence or local.random()<(.12+.06*a.rebuttal_depth)
    stance=truth if correct else not truth
    # A simple grounded referee: sourced+correct evidence beats rhetorical certainty.
    score=(6 if stance==truth else 0)+(3 if has_evidence else 0)
    words=(f'Claim={stance}. Evidence[{eid}]: {evidence}' if has_evidence else
         f'Claim={stance}. I cannot produce a checked source for this assertion.')
    return {'claim':text,'stance':stance,'ground_truth':truth,'evidence_id':eid if has_evidence else None,
            'evidence_text':evidence if has_evidence else None,'speech':words,'score':score,
            'candidate_checks':a.rebuttal_depth+1}


def tug_of_war(a,alive,seed):
    trace=[];score=0
    for other in alive:
        if other.name==a.name:continue
        for q in range(4):
            my=make_argument(a,q,seed,1);their=make_argument(other,q,seed,1)
            # Inspect an opponent's evidence; a rebuttal is effective only on a false stance.
            correction=(their['stance']!=FACTS[q][1] and my['evidence_id'] is not None)
            points=my['score']+(2 if correction else 0)
            score+=points
            trace.append({'opponent':other.name,'question':FACTS[q][0],
                'own_argument':my['speech'],'opponent_argument':their['speech'],
                'judge_score':points,'opponent_base_score':their['score'],
                'rebuttal':'Corrected unsupported opponent conclusion using '+FACTS[q][2] if correction else 'No checked correction supplied',
                'action':'ARGUED','candidate_checks':my['candidate_checks']+their['candidate_checks']})
    return {'score':score,'debates':len(trace),'evidence_hits':sum('Evidence[' in e['own_argument'] for e in trace),'events':trace}


def bargain_pair(a,b,seed):
    g=rng(seed,'bargain',*sorted((a.name,b.name)))
    turn_a=g.random()<.5
    proposer,receiver=(a,b) if turn_a else (b,a)
    # Each player has a private minimum; reports may be inflated by a bluff.
    claim={}
    for p in (a,b):
        claim[p.name]=p.bargaining_target+(2 if rng(seed,'bluff',a.name,b.name,p.name).random()<p.bluff_rate else 0)
    transcript=[]
    for turn in range(1,5):
        flexibility=proposer.bargain_flex*(turn-1)//3
        offer=max(0,min(12,proposer.bargaining_target-1+flexibility))
        # Some negotiators inspect the opponent's stated floor; it can be a bluff.
        if proposer.bargain_flex>=3:offer=max(offer,min(12,claim[receiver.name]))
        accepted=offer>=receiver.bargaining_target
        transcript.append({'turn':turn,'speaker':proposer.name,'opponent':receiver.name,
                 'claim_floor':claim[receiver.name], 'true_receiver_floor':receiver.bargaining_target,
                 'offer_marbles':offer,'reply':'ACCEPT' if accepted else 'REJECT',
                 'candidate_checks':2+proposer.bargain_flex})
        if accepted:
            value={proposer.name:12-offer,receiver.name:offer}
            return value,transcript,True
        proposer,receiver=receiver,proposer
    return {a.name:0,b.name:0},transcript,False


def marbles(a,alive,seed):
    score=0;trace=[];deals=0
    for b in alive:
        if b.name==a.name:continue
        ordered=sorted((a,b),key=lambda z:z.name)
        values,talk,deal=bargain_pair(*ordered,seed)
        score+=values[a.name];deals+=int(deal)
        trace.append({'opponent':b.name,'marbles_received':values[a.name],
                     'deal':deal,'dialogue':talk,'candidate_checks':sum(t['candidate_checks'] for t in talk)})
    return {'score':score,'deals':deals,'matches':len(trace),'events':trace}


def bridge_world(seed,n=20):
    return [{'step':i+1,'safe':rng(seed,'bridgeworld',i).choice(('L','R'))} for i in range(n)]


def bridge(a,b,seed,memory=True):
    """Same hidden safe tile for both; order alternates; second sees first's failure only.
    Each agent chooses once for each position, even if it chose a broken tile before;
    'death' only changes scoring, not whether further observations exist.
    This is a repeated-decision benchmark, not literal Squid Game survival.
    """
    scored={a.name:0,b.name:0};traces={a.name:[],b.name:[]}
    for panel in bridge_world(seed):
        step=panel['step'];safe=panel['safe']
        order=(a,b) if step%2==1 else (b,a)
        failed=None
        for p in order:
            local=rng(seed,'bridge_decision',p.name,step)
            # Noisy sensor has calibrated accuracy according to fixed policy parameter.
            sensor_correct=local.random()<p.clue_accuracy
            clue=safe if sensor_correct else ('L' if safe=='R' else 'R')
            had_verified_history=bool(memory and failed is not None)
            used_history=had_verified_history and local.random()<p.history_trust
            choice=('R' if failed=='L' else 'L') if used_history else clue
            correct=(choice==safe)
            scored[p.name]+=int(correct)
            traces[p.name].append({'step':step,'turn':'first' if p==order[0] else 'second',
                'signal':clue,'verified_failed_tile':failed,'used_failure_memory':bool(used_history),
                'action':choice,'safe_tile':safe,'correct':bool(correct),
                'explanation':('Avoided verified failed '+str(failed) if used_history else 'Followed noisy local signal '+clue),
                'candidate_checks':3 if used_history else 2})
            if not correct:failed=choice
    return {a.name:{'score':scored[a.name],'correct':scored[a.name],'total':20,'events':traces[a.name]},
            b.name:{'score':scored[b.name],'correct':scored[b.name],'total':20,'events':traces[b.name]}}


def run_tournament(seed, memory=True, include_trace=True):
    alive=list(AGENTS);rounds=[];all_events=[]
    for key,label in ROUNDS:
        sc={};wall={}
        if key=='glass_bridge':
            res,elapsed=timed(bridge,alive[0],alive[1],seed,memory)
            for a in alive: sc[a.name]=res[a.name];wall[a.name]=elapsed/2
        else:
            for a in alive:
                fn={'red_light':red_light,'dalgona':dalgona,'tug_of_war':tug_of_war,'marbles':marbles}[key]
                args=(a,seed) if key in ('red_light','dalgona') else (a,alive,seed)
                sc[a.name],wall[a.name]=timed(fn,*args)
        ranking=sorted((a.name for a in alive),key=lambda n:(-sc[n]['score'],rng(seed,'tie',key,n).random()))
        loser=ranking[-1]
        round_summary={'key':key,'label':label,'seed':seed,'contestants':[a.name for a in alive],
          'ranking':ranking,'eliminated':loser,'scores':{n:sc[n]['score'] for n in ranking},
          'measured_policy_us':{n:round(wall[n],2) for n in ranking},
          'candidate_checks':{n:sum(ev.get('candidate_checks',0) for ev in sc[n]['events']) for n in ranking},
          'remaining':[n for n in ranking if n!=loser]}
        if include_trace:round_summary['details']=sc
        rounds.append(round_summary)
        alive=[a for a in alive if a.name!=loser]
    return {'seed':seed,'winner':alive[0].name,'rounds':rounds,'model_type':'algorithmic_policy_simulation',
            'reality_check':'No LLM inference, no hidden chain of thought, no human participants.'}


def ablation(n,seed_start=20000):
    """Paired finalist bridge comparisons with identical world and stochastic draws."""
    rows=[]
    for seed in range(seed_start,seed_start+n):
        for a,b in ((BY_NAME['Atlas'],BY_NAME['Blitz']),(BY_NAME['Sentinel'],BY_NAME['Coda'])):
            yes=bridge(a,b,seed,True);no=bridge(a,b,seed,False)
            for p in (a,b):
                rows.append({'seed':seed,'agent':p.name,'opponent':(b if p==a else a).name,
                             'with_memory':yes[p.name]['score'],'without_memory':no[p.name]['score'],
                             'difference':yes[p.name]['score']-no[p.name]['score'],
                             'verified_failures_used':sum(v['used_failure_memory'] for v in yes[p.name]['events'])})
    return rows


def save_csv(path,rows):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--tournaments',type=int,default=250)
    ap.add_argument('--seed',type=int,default=42)
    ap.add_argument('--output',default='results')
    o=ap.parse_args();output=Path(o.output);output.mkdir(parents=True,exist_ok=True)
    featured=run_tournament(o.seed)
    (output/'featured.json').write_text(json.dumps(featured,indent=2))
    tournaments=[];round_rows=[];wins=Counter();timing=[]
    for seed in range(o.seed,o.seed+o.tournaments):
        result=run_tournament(seed,include_trace=False)
        wins[result['winner']]+=1
        tournaments.append({'seed':seed,'winner':result['winner']})
        for rd in result['rounds']:
            for n in rd['contestants']:
                round_rows.append({'seed':seed,'round':rd['key'],'agent':n,'score':rd['scores'][n],
                       'eliminated':int(rd['eliminated']==n),'measured_policy_us':rd['measured_policy_us'][n],
                       'candidate_checks':rd['candidate_checks'][n]})
    save_csv(output/'tournaments.csv',tournaments)
    save_csv(output/'rounds.csv',round_rows)
    abl=ablation(250)
    save_csv(output/'bridge_ablation.csv',abl)
    median_by_agent={n:round(statistics.median(x['measured_policy_us'] for x in round_rows if x['agent']==n),2) for n in BY_NAME}
    totals=Counter(x['round'] for x in round_rows)
    summary={'kind':'algorithmic_policy_simulation','tournaments':o.tournaments,'featured_seed':o.seed,
       'featured_winner':featured['winner'],'wins':dict(sorted(wins.items())),
       'median_policy_microseconds_by_agent':median_by_agent,
       'round_observations':dict(totals),
       'bridge_memory_mean_delta':round(statistics.mean(r['difference'] for r in abl),4),
       'bridge_memory_mean_delta_by_agent':{n:round(statistics.mean(r['difference'] for r in abl if r['agent']==n),4) for n in set(r['agent'] for r in abl)},
       'notes':['Virtual stop ticks are a logical clock, not measured seconds.',
        'Measured microseconds are local Python policy execution, not LLM thinking time.',
        'Round rank elimination makes tournament results sensitive to scoring and policy design.',
        'No commercial model was queried; no causal generalization to LLMs.']}
    (output/'summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
