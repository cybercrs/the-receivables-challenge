import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {DATA} from '../content.js';
import * as e from '../engine.js';
const oracle=JSON.parse(fs.readFileSync(new URL('./python-oracles.json',import.meta.url),'utf8'));

test('All calculated balances, aging rows, write-offs and ratios match Python',()=>{
 assert.deepEqual(e.agingTotals(),oracle.calculations.agingTotals);
 assert.deepEqual(e.agingRows(),oracle.calculations.agingRows);
 assert.equal(e.gross(),oracle.calculations.gross);
 assert.equal(e.requiredAllowance(),oracle.calculations.required);
 assert.equal(e.percentageEstimate(),oracle.calculations.percentage);
 assert.deepEqual(e.valuationValues(),oracle.calculations.valuation);
 [0,1,14000,22180,118000].forEach((n,i)=>assert.deepEqual(e.writeoffComparison(n),oracle.calculations.writeoff[i]));
 assert.deepEqual(e.dashboardMetrics(),oracle.calculations.dashboard);
});
test('Whole-dollar formatting preserves Python ties-to-even, including negative halves',()=>{
 for(const [value,display] of oracle.currency)assert.equal(e.currency(value),display);
});
test('Every option shuffle matches Python, including seeds above JS safe integer range',async()=>{
 for(const item of oracle.shuffles)assert.deepEqual(await e.shuffled(item.input,BigInt(item.seed),item.salt),item.output);
});
test('Original URL snapshots decode exactly; native snapshots round-trip losslessly',async()=>{
 for(const fixture of oracle.snapshots){
  const state=await e.decodeState(fixture.token),expected={...fixture.payload,z:BigInt(fixture.payload.z)};
  assert.deepEqual(state,expected);
  assert.deepEqual(await e.decodeState(await e.encodeState(state)),state);
 }
 const state=e.newState(2n**63n-1n);
 assert.equal((await e.decodeState(await e.encodeState(state))).z,2n**63n-1n);
});
test('Malformed, oversized, out-of-sequence, and completed-wrong states cannot unlock pages',async()=>{
 for(const value of [null,'','bad','A'.repeat(16001)])assert.equal(await e.decodeState(value),null);
 const source=e.newState(0n);
 for(const mutate of [s=>s.s=7,s=>s.ci=2,s=>s.d.r.risk_disclosure=DATA.groups[3].items[4].correct,
  s=>s.vr.ending_allowance=22180,s=>s.cr.service_on_account='unknown',s=>s.at.future=1,s=>s.fp['claim:service_on_account']='yes',s=>s.z=2n**63n]){
  const bad=e.copy(source);mutate(bad);assert.throws(()=>e.validateSnapshot(bad));
 }
 const bad=e.copy(oracle.snapshots[5].payload);bad.z=0n;bad.vr.ending_allowance=0;
 assert.throws(()=>e.validateSnapshot(bad));
});
test('Amounts accept whole dollars and correct comma groups without silent rounding',()=>{
 for(const [raw,value] of [['22180',22180],['$22,180',22180],[' 0 ',0],['10,000,000',10000000]])assert.equal(e.parseAmount(raw),value);
 for(const raw of ['','22,18','22,180.5','22180.0','-1','1e3','Infinity','NaN','10000001','0x10','<script>',' '.repeat(65)])assert.equal(e.parseAmount(raw),null);
});
test('Read-only actions cannot edit, submit, reveal, reset or advance; Forward stops at frontier',()=>{
 const lesson=new e.Lesson(e.newState(42n),999);
 assert.equal(lesson.view,0);assert.equal(lesson.move(1),false);
 assert(lesson.advance());assert.equal(lesson.move(1),false);assert.equal(lesson.advance(),false);
 const first=DATA.groups[0].items[0],wrong=first.options.find(x=>x!==first.correct);
 assert(lesson.draftChoice(wrong));assert(lesson.submitChoice());assert(lesson.submitChoice());
 assert.equal(lesson.state.at[`claim:${first.id}`],2);assert.equal(lesson.canAdvance(),false);
 assert(lesson.draftChoice(first.correct));assert(lesson.submitChoice());assert.equal(lesson.move(1),false);
 const saved=e.canonicalJSON(lesson.state);
 assert(lesson.move(-1));
 for(const action of [()=>lesson.draftChoice(wrong),()=>lesson.submitChoice(),()=>lesson.draftNumber('ending_allowance','0'),()=>lesson.draftBenefit(DATA.benefitCorrect),()=>lesson.submitValuation(),()=>lesson.advance(),()=>lesson.reset()])assert.equal(action(),false);
 assert.equal(e.canonicalJSON(lesson.state),saved);assert(lesson.move(1));assert.equal(e.canonicalJSON(lesson.state),saved);
 assert(lesson.advance());assert.equal(lesson.view,2);
});
test('Complete case and unchanged valuation rechecks preserve original scoring semantics',()=>{
 const lesson=new e.Lesson(e.newState(42n));lesson.advance();
 for(const group of DATA.groups){
  if(group.stage===5){
   for(const [key] of DATA.valuationFields)lesson.draftNumber(key,'0');lesson.draftBenefit(DATA.benefitCorrect);
   assert(lesson.submitValuation());const before=e.canonicalJSON(lesson.state.at);
   assert(lesson.submitValuation());assert.equal(e.canonicalJSON(lesson.state.at),before);
   for(const [key,value] of Object.entries(e.valuationValues()))lesson.draftNumber(key,String(value));
   assert(lesson.submitValuation());assert(lesson.advance());
  }
  for(const item of group.items){assert(lesson.draftChoice(item.correct));assert(lesson.submitChoice());assert(lesson.advance());}
 }
 assert.equal(lesson.state.s,7);
 assert.deepEqual(e.scoreSummary(lesson.state),{correct:23,attempted:27,total:27,revisions:4});
 const saved=e.canonicalJSON(lesson.state);
 while(lesson.move(-1))assert.equal(e.canonicalJSON(lesson.state),saved);
 while(lesson.move(1))assert.equal(e.canonicalJSON(lesson.state),saved);
 assert.equal(lesson.view,24);assert(lesson.reset());assert.equal(lesson.view,0);
});
test('Snapshot seed type and original boundaries hold; extended practice retains exact scoring and resume',async()=>{
 const original=e.canonicalJSON(e.newState(42n));
 assert.throws(()=>e.parseSnapshotJSON(original.replace('"z":42','"z":"42"')));
 assert.throws(()=>e.parseSnapshotJSON(original.replace('"z":42','"z":42.5')));
 const state=e.newState(42n);state.extra=true;assert.throws(()=>e.validateSnapshot(state));
 const capped=e.newState(42n);capped.at['claim:service_on_account']=100;assert.throws(()=>e.validateSnapshot(capped));
 const lesson=new e.Lesson(e.newState(42n));lesson.advance();
 const first=DATA.groups[0].items[0],wrong=first.options.find(x=>x!==first.correct);
 lesson.draftChoice(wrong);
 for(let i=0;i<105;i++)lesson.submitChoice();
 assert.equal(lesson.state.at[`claim:${first.id}`],105);
 assert.equal(lesson.state.v,4);
 assert.equal(e.scoreSummary(lesson.state).revisions,104);
 assert.deepEqual(await e.decodeState(await e.encodeState(lesson.state)),lesson.state);
 assert.doesNotThrow(()=>e.validateSnapshot(lesson.state));
 lesson.draftChoice(first.correct);assert(lesson.submitChoice());assert(lesson.advance());
});
test('Only numeric draft text is persisted; names or arbitrary text cannot enter the anonymous saved link',()=>{
 const raw={ending_allowance:'22,',allowance_increase:'Jane Doe',bad_debt_increase:'123.5'};
 const saved=e.readRawDraft(e.rawDraftToken(raw));
 assert.deepEqual(saved,{ending_allowance:'22,',bad_debt_increase:'123.5'});
});
