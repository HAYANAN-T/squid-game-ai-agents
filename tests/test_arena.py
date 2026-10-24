"""Unit checks for tournament invariants and causal paired bridge setup."""
import unittest
from arena import AGENTS,BY_NAME,red_light,dalgona,make_argument,bargain_pair,bridge,bridge_world,run_tournament,ablation

class TournamentTests(unittest.TestCase):
 def test_five_rounds_one_survivor(self):
  t=run_tournament(42)
  self.assertEqual(len(t['rounds']),5)
  self.assertEqual([len(r['contestants']) for r in t['rounds']],[6,5,4,3,2])
  self.assertEqual(t['winner'],t['rounds'][-1]['remaining'][0])
  self.assertEqual(set(r['eliminated'] for r in t['rounds'])|{t['winner']},set(a.name for a in AGENTS))
 def test_reproducibility_excluding_wall_clocks(self):
  a,b=run_tournament(117),run_tournament(117)
  self.assertEqual(a['winner'],b['winner'])
  for x,y in zip(a['rounds'],b['rounds']):
   self.assertEqual(x['details'],y['details']);self.assertEqual(x['ranking'],y['ranking'])
 def test_interrupt_deadlines(self):
  x=red_light(BY_NAME['Atlas'],18)
  self.assertTrue(all(z['stopped_before_deadline']==(z['reaction_virtual_ticks']<=z['deadline_virtual_ticks']) for z in x['events']))
  self.assertEqual(len(x['events']),18)
 def test_exact_format_and_semantic_validation(self):
  v=dalgona(BY_NAME['Coda'],18)
  self.assertTrue(all(e['exact_contract']==(e['expected']==e['actual']) for e in v['events']))
  self.assertEqual(len(v['events']),18)
 def test_debate_evidence_ids(self):
  d=make_argument(BY_NAME['Echo'],0,42,1)
  self.assertEqual(d['claim'],'A CDN cache can never serve stale data.')
  self.assertIn(d['score'],(0,6,9))
 def test_marble_values_are_valid(self):
  u,transcript,deal=bargain_pair(BY_NAME['Atlas'],BY_NAME['Mira'],42)
  self.assertLessEqual(len(transcript),4)
  self.assertEqual(sum(u.values()),12 if deal else 0)
 def test_no_omniscient_agent(self):
  x=bridge(BY_NAME['Atlas'],BY_NAME['Echo'],42)
  self.assertEqual(len(x['Atlas']['events']),20)
  self.assertTrue(all(e['action'] in ('L','R') for e in x['Atlas']['events']))
  self.assertEqual(sum(e['correct'] for e in x['Atlas']['events']),x['Atlas']['score'])
 def test_memory_ablation_paired_improvement_nonnegative(self):
  rows=ablation(30)
  self.assertEqual(len(rows),120)
  self.assertTrue(all(r['difference']>=0 for r in rows))
 def test_public_failure_is_real(self):
  res=bridge(BY_NAME['Atlas'],BY_NAME['Echo'],17)
  for p in res.values():
   for e in p['events']:
    if e['used_failure_memory']:
     self.assertIsNotNone(e['verified_failed_tile'])
     self.assertNotEqual(e['action'],e['verified_failed_tile'])
 def test_tie_break_changes_only_order(self):
  x=run_tournament(42)
  for r in x['rounds']:self.assertEqual(set(r['scores']),set(r['ranking']))

if __name__=='__main__':unittest.main()
