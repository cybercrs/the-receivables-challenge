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
test('Original URL snapshots migrate only the retired checkpoint; native snapshots round-trip losslessly',async()=>{
 for(const fixture of oracle.snapshots){
  const state=await e.decodeState(fixture.token),expected={...fixture.payload,z:BigInt(fixture.payload.z)};
  if(expected.vs)expected.vr.ending_allowance=e.requiredAllowance();
  delete expected.d.v.ending_allowance;delete expected.at['valuation:ending_allowance'];delete expected.fp['valuation:ending_allowance'];
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
 const bad=e.copy(oracle.snapshots[5].payload);bad.z=0n;bad.vr.allowance_increase=0;
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
 assert.deepEqual(e.scoreSummary(lesson.state),{correct:23,attempted:26,total:26,revisions:3});
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
const legacyBookmarks=JSON.parse(fs.readFileSync(new URL('./legacy-native-bookmarks.json',import.meta.url),'utf8'));
test('Old native v3/v4 bookmarks keep remaining work, large seeds, view/frontier, and corrected 26-point scoring',async()=>{
 for(const record of legacyBookmarks.records){
  const decoded=await e.decodeState(record.token);assert(decoded,record.name);
  const lesson=new e.Lesson(decoded,record.view,record.rawNumbers);
  assert.equal(lesson.state.z,2n**63n-1n);assert.equal(lesson.view,record.view);
  assert(!Object.hasOwn(lesson.state.at,'valuation:ending_allowance'));
  assert(!Object.hasOwn(lesson.state.fp,'valuation:ending_allowance'));
  assert.equal(e.scoreSummary(lesson.state).total,26);
  assert.deepEqual(await e.decodeState(await e.encodeState(lesson.state)),lesson.state);
  if(record.name==='unfinished-legacy-drafts'){
   assert.equal(lesson.rawNumbers.allowance_increase,'18,');assert(!Object.hasOwn(lesson.rawNumbers,'ending_allowance'));assert(!lesson.canAdvance());
  } else if(record.name==='perfect-old-completion-review'){
   assert.equal(lesson.state.s,7);assert.equal(e.scoreSummary(lesson.state).correct,26);assert(lesson.reviewing);assert(!lesson.advance());
  } else {
   assert.equal(lesson.state.s,4);assert(lesson.canAdvance());assert(!lesson.move(1));
   assert.equal(lesson.state.vr.ending_allowance,22180);assert(lesson.advance());assert.equal(lesson.state.s,5);
  }
 }
});
test('Native-only schedules and final discussion implement the revised learning sequence',()=>{
 assert.equal(DATA.valuationFields.length,3);assert(!DATA.valuationFields.some(([key])=>key==='ending_allowance'));
 assert.equal(e.validScoreKeys().size,26);
 for(const screen of DATA.screens.filter(s=>[3,4].includes(s.stage)))for(const nodes of Object.values(screen.variants)){
  const table=nodes.find(n=>n.kind==='table');assert(table.fixedRows);assert.equal(table.rows.length,3);
  assert.deepEqual(Object.keys(table.rows[0]),['Measure',...DATA.buckets,'Total']);
  assert.equal(table.rows[0].Total,'$118,000');assert.equal(table.rows[2].Total,'[4] $22,180');
  if(screen.stage===4){assert(!nodes.some(n=>n.key==='widget_valuation_ending_allowance'));
   assert(!nodes.some(n=>n.kind==='caption'&&n.text.includes('Method comparison')));
   assert(!JSON.stringify(nodes).includes('$9,440'));
  }
 }
 const discussion=DATA.screens.at(-1).variants.correct.find(n=>n.kind==='details'&&n.label.includes('single flat'));
 assert(discussion);const text=discussion.children.map(n=>n.text).join(' ');
 assert(text.includes('As an illustration, 8% of $118,000 gives a $9,440'));
 assert(text.includes('well supported by collection evidence'));assert(text.includes('Neither approach guarantees accuracy'));
});
test('Aging cell directions and explanations follow the transposed native axes',()=>{
 const text=JSON.stringify(DATA.screens.filter(s=>s.stage===3));
 for(const old of ['Current row under Receivables','past due row under Estimated','total of the Estimated uncollectible column','The receivables column groups'])assert(!text.includes(old));
 assert(text.includes('Current column on the Accounts receivable row'));
 assert(text.includes('61-90 days past due column on the Estimated loss rate row'));
 assert(text.includes('More than 90 days past due column on the Estimated uncollectible row'));
 assert(text.includes('total on the Estimated uncollectible row'));
});
