/** Native calculations, lossless Python-compatible URL snapshots, and guarded lesson actions. */
import { DATA } from './content.js?v=20261014-aging';

export const GROUPS = DATA.groups;
export const POSITIONS = DATA.positions;
export const MAX_AMOUNT = 10000000;
const keys = ['v','s','z','d','ci','cr','di','dr','ai','ar','vr','vb','vs','ri','rr','mi','mr','at','fp'];
const own = (object, key) => Object.hasOwn(object, key);
const object = value => value !== null && typeof value === 'object' && !Array.isArray(value) && Object.getPrototypeOf(value) === Object.prototype;
const exactKeys = (value, expected) => object(value) && Object.keys(value).length === expected.length && expected.every(key => own(value,key));
const assert = (condition, message) => { if (!condition) throw new Error(message); };
const int = (value,min,max) => Number.isInteger(value) && value >= min && value <= max;
const numericDraft = value => typeof value==='string'&&value.length<=64&&/^[0-9\s$,.+\-]*$/.test(value);
export const copy = value => structuredClone(value);

export function pyRound(value) {
  const lower = Math.floor(value), fraction = value - lower;
  return fraction === 0.5 ? (lower % 2 === 0 ? lower : lower + 1) : Math.round(value);
}
export function currency(value) {
  const rounded = pyRound(value);
  return `${rounded < 0 ? '-' : ''}$${Math.abs(rounded).toLocaleString('en-US')}`;
}
export function agingTotals() {
  const totals = Object.fromEntries(DATA.buckets.map(bucket => [bucket,0]));
  for (const invoice of DATA.invoices) totals[invoice.correct_bucket] += invoice.balance;
  return totals;
}
export function agingRows() {
  const totals = agingTotals();
  return DATA.buckets.map(bucket => ({'Age category':bucket,'Receivables':totals[bucket],
    'Estimated loss rate':DATA.rates[bucket], 'Estimated uncollectible':pyRound(totals[bucket]*DATA.rates[bucket])}));
}
export const gross = () => DATA.invoices.reduce((sum,invoice) => sum+invoice.balance,0);
export const requiredAllowance = () => agingRows().reduce((sum,row) => sum+row['Estimated uncollectible'],0);
export const percentageEstimate = () => pyRound(gross()*DATA.percentageRate);
export function valuationValues() {
  const required = requiredAllowance(), increase = required-DATA.beginningAllowance;
  return {ending_allowance:required, allowance_increase:increase, bad_debt_increase:increase, net_realizable_value:gross()-required};
}
export function evaluateValuation(values, benefit) {
  const expectedValues=valuationValues();
  const fields = Object.fromEntries(DATA.valuationFields.map(([key]) => { const expected=expectedValues[key]; return [key,{submitted:values[key] ?? 0,expected,correct:(values[key] ?? 0)===expected}]; }));
  return {fields,benefit:{submitted:benefit,expected:DATA.benefitCorrect,correct:benefit===DATA.benefitCorrect},
    correct:Object.values(fields).every(field=>field.correct)&&benefit===DATA.benefitCorrect};
}
export function writeoffComparison(amount=14000) {
  const before=gross(),allowance=requiredAllowance();
  return {gross_before:before,allowance_before:allowance,net_before:before-allowance,
    gross_after:before-amount,allowance_after:allowance-amount,net_after:before-allowance};
}
export function dashboardMetrics() {
  const total=gross(),net=valuationValues().net_realizable_value,average=(DATA.beginningNet+net)/2;
  const turnover=DATA.creditSales/average,totals=agingTotals(),overdue=total-totals.Current;
  return {gross_receivables:total,net_receivables:net,overdue_amount:overdue,overdue_percent:overdue/total,
    over_60_amount:totals['61-90 days past due']+totals['More than 90 days past due'],turnover,collection_period:365/turnover};
}
export function validScoreKeys() {
  return new Set([...GROUPS.flatMap(group=>group.items.map(item=>`${group.prefix}:${item.id}`)),
    ...DATA.valuationFields.map(([key])=>`valuation:${key}`),'valuation:benefit']);
}
export function scoreSummary(state) {
  const valid=validScoreKeys(),first=Object.entries(state.fp).filter(([key])=>valid.has(key)),attempts=Object.entries(state.at).filter(([key])=>valid.has(key));
  return {correct:first.filter(([,value])=>value).length,attempted:first.length,
    total:valid.size,revisions:attempts.reduce((sum,[,value])=>sum+Math.max(0,value-1),0)};
}
export function newState(seed) {
  if (seed===undefined) {
    const words=crypto.getRandomValues(new Uint32Array(2));
    seed=(BigInt(words[0]&0x7fffffff)<<32n)|BigInt(words[1]);
  }
  return {v:3,s:0,z:BigInt(seed),d:{c:{},d:{},a:{},v:{},r:{},m:{}},ci:0,cr:{},di:0,dr:{},ai:0,ar:{},
    vr:{},vb:'',vs:false,ri:0,rr:{},mi:0,mr:{},at:{},fp:{}};
}
export function validateSnapshot(raw) {
  assert(exactKeys(raw,keys)&&(raw.v===3||raw.v===4),'Unsupported snapshot');
  assert(int(raw.s,0,7),'Invalid stage');
  assert(typeof raw.z==='bigint'&&raw.z>=0n&&raw.z<2n**63n,'Invalid shuffle seed');
  assert(exactKeys(raw.d,['c','d','a','v','r','m']),'Invalid drafts');
  const stage=raw.s;
  for (const group of GROUPS) {
    const index=raw[group.indexKey],responses=raw[group.responseKey],draft=raw.d[group.draft];
    assert(int(index,0,group.items.length-1),'Invalid index');
    assert(object(responses)&&object(draft),'Invalid answer group');
    const ids=Object.keys(responses),prefix=group.items.slice(0,ids.length);
    assert(ids.length<=group.items.length&&prefix.every(item=>own(responses,item.id)),'Answers out of order');
    for (const item of prefix) assert(typeof responses[item.id]==='string'&&item.options.includes(responses[item.id]),'Unknown answer');
    for (const [id,value] of Object.entries(draft)) {
      const item=group.items.slice(0,index+1).find(item=>item.id===id);
      assert(item&&typeof value==='string'&&item.options.includes(value),'Invalid draft answer');
    }
    assert(stage>=group.stage||Object.keys(draft).length===0,'Future draft');
    assert(stage>=group.stage||ids.length===0,'Future answer');
    if (stage>group.stage) {
      assert(group.items.every(item=>responses[item.id]===item.correct),'Incomplete prior stage');
      assert(index===group.items.length-1,'Invalid completed index');
    }
    for (const item of group.items.slice(0,index)) assert(responses[item.id]===item.correct,'Unresolved prior answer');
    if (stage===group.stage) assert(ids.length===index||ids.length===index+1,'Inconsistent position');
  }
  const valuationKeys=DATA.legacyValuationFields.map(([key])=>key),assessedKeys=DATA.valuationFields.map(([key])=>key);
  assert(typeof raw.vs==='boolean'&&object(raw.vr),'Invalid valuation');
  assert(Object.keys(raw.vr).every(key=>valuationKeys.includes(key)),'Unknown valuation field');
  if(raw.vs) assert(assessedKeys.every(key=>own(raw.vr,key)),'Incomplete valuation');
  for(const value of Object.values(raw.vr)) assert(int(value,0,MAX_AMOUNT),'Invalid amount');
  assert(typeof raw.vb==='string'&&(raw.vb===''||DATA.benefitOptions.includes(raw.vb)),'Invalid benefit');
  if(raw.vs) assert(DATA.benefitOptions.includes(raw.vb),'Missing benefit');
  assert(object(raw.d.v)&&Object.keys(raw.d.v).every(key=>key==='benefit'||valuationKeys.includes(key)),'Invalid valuation draft');
  for (const [key,value] of Object.entries(raw.d.v)) {
    assert(key==='benefit'?typeof value==='string'&&DATA.benefitOptions.includes(value):int(value,0,MAX_AMOUNT),'Invalid valuation draft value');
  }
  assert(stage>=4||(!Object.keys(raw.vr).length&&!raw.vb&&!raw.vs&&!Object.keys(raw.d.v).length),'Future valuation');
  if(stage>=5) assert(raw.vs&&evaluateValuation(raw.vr,raw.vb).correct,'Unresolved valuation');
  assert(object(raw.at)&&object(raw.fp),'Invalid score history');
  const scores=validScoreKeys();scores.add('valuation:ending_allowance');
  for(const [key,value] of Object.entries(raw.at)) assert(scores.has(key)&&int(value,1,raw.v===3?99:Number.MAX_SAFE_INTEGER),'Invalid attempts');
  for(const [key,value] of Object.entries(raw.fp)) assert(scores.has(key)&&typeof value==='boolean','Invalid first pass');
  const normalized=copy(raw);
  // Retire the duplicate checkpoint without discarding any remaining work, seed or frontier.
  delete normalized.at['valuation:ending_allowance'];delete normalized.fp['valuation:ending_allowance'];
  delete normalized.d.v.ending_allowance;
  if(normalized.vs)normalized.vr.ending_allowance=requiredAllowance();
  return normalized;
}
export function canonicalJSON(value) {
  if(typeof value==='bigint') return value.toString();
  if(Array.isArray(value)) return `[${value.map(canonicalJSON).join(',')}]`;
  if(object(value)) return `{${Object.keys(value).sort().map(key=>`${JSON.stringify(key)}:${canonicalJSON(value[key])}`).join(',')}}`;
  return JSON.stringify(value).replace(/[\u007f-\uffff]/g,c=>`\\u${c.charCodeAt(0).toString(16).padStart(4,'0')}`);
}
export function parseSnapshotJSON(text) {
  // Preserve exactly the original 63-bit integer instead of rounding through a JS Number.
  assert(/"z"\s*:\s*-?\d+(?=\s*[,}])/.test(text),'Seed must be a JSON integer');
  const replaced=text.replace(/("z"\s*:\s*)(-?\d+)(?=\s*[,}])/g,'$1"$2"');
  const raw=JSON.parse(replaced);
  assert(typeof raw.z==='string'&&/^\d{1,19}$/.test(raw.z),'Invalid seed encoding');
  raw.z=BigInt(raw.z);
  return validateSnapshot(raw);
}
function base64url(bytes) {
  let text='';for(const byte of bytes)text+=String.fromCharCode(byte);
  return btoa(text).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/g,'');
}
function from64(text) {
  assert(typeof text==='string'&&text.length>0&&text.length<=16000&&/^[\w-]+$/.test(text),'Invalid token');
  return Uint8Array.from(atob(text.replace(/-/g,'+').replace(/_/g,'/')+'='.repeat((4-text.length%4)%4)),c=>c.charCodeAt(0));
}
async function transform(bytes,stream,max) {
  const reader=new Blob([bytes]).stream().pipeThrough(stream).getReader();
  const chunks=[];let length=0;
  while(true) {
    const {done,value}=await reader.read();if(done)break;
    length+=value.length;
    if(length>max){await reader.cancel();throw new Error('Saved state too large');}
    chunks.push(value);
  }
  const output=new Uint8Array(length);let offset=0;
  for(const chunk of chunks){output.set(chunk,offset);offset+=chunk.length;}
  return output;
}
export async function encodeState(state) {
  const normalized=validateSnapshot(state);
  const bytes=new TextEncoder().encode(canonicalJSON(normalized));
  assert(bytes.length<=32000,'Saved state too large');
  return base64url(await transform(bytes,new CompressionStream('deflate'),12000));
}
export async function decodeState(token) {
  try {
    const bytes=await transform(from64(token),new DecompressionStream('deflate'),32000);
    return parseSnapshotJSON(new TextDecoder('utf-8',{fatal:true}).decode(bytes));
  } catch {return null;}
}
export function parseAmount(raw) {
  if(typeof raw!=='string'||raw.length>64)return null;
  const value=raw.trim().replace(/^\$\s*/, '');
  if(!/^(?:\d+|\d{1,3}(?:,\d{3})+)$/.test(value))return null;
  const number=Number(value.replace(/,/g,''));
  return int(number,0,MAX_AMOUNT)?number:null;
}
export const frontier = state => {
  const group=GROUPS.find(group=>group.stage===state.s);
  return POSITIONS.findIndex(position=>position.stage===state.s&&position.index===(group?state[group.indexKey]:0));
};

// CPython's integer-seeded MT19937 and _randbelow: imported bookmarks keep their exact option order.
class PythonRandom {
  constructor(seed) {
    const words=[];do{words.push(Number(seed&0xffffffffn));seed>>=32n;}while(seed);
    this.mt=new Uint32Array(624);this.mt[0]=19650218;
    for(let i=1;i<624;i++)this.mt[i]=(Math.imul(1812433253,this.mt[i-1]^(this.mt[i-1]>>>30))+i)>>>0;
    let i=1,j=0;
    for(let k=Math.max(624,words.length);k>0;k--) {
      this.mt[i]=((this.mt[i]^Math.imul(this.mt[i-1]^(this.mt[i-1]>>>30),1664525))+words[j]+j)>>>0;
      if(++i>=624){this.mt[0]=this.mt[623];i=1;}if(++j>=words.length)j=0;
    }
    for(let k=623;k>0;k--) {
      this.mt[i]=((this.mt[i]^Math.imul(this.mt[i-1]^(this.mt[i-1]>>>30),1566083941))-i)>>>0;
      if(++i>=624){this.mt[0]=this.mt[623];i=1;}
    }
    this.mt[0]=0x80000000;this.index=624;
  }
  next() {
    if(this.index>=624) {
      for(let i=0;i<624;i++) {
        const value=(this.mt[i]&0x80000000)|(this.mt[(i+1)%624]&0x7fffffff);
        this.mt[i]=(this.mt[(i+397)%624]^(value>>>1)^((value&1)?0x9908b0df:0))>>>0;
      }
      this.index=0;
    }
    let value=this.mt[this.index++];value^=value>>>11;value^=(value<<7)&0x9d2c5680;value^=(value<<15)&0xefc60000;value^=value>>>18;
    return value>>>0;
  }
  below(n) {const bits=n.toString(2).length;let value;do{value=this.next()>>>(32-bits);}while(value>=n);return value;}
}
export async function shuffled(input,seed,salt) {
  const bytes=new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(`${seed}:${salt}`)));
  let number=0n;for(const byte of bytes.slice(0,8))number=(number<<8n)|BigInt(byte);
  const random=new PythonRandom(number),result=[...input];
  for(let i=result.length-1;i>0;i--){const j=random.below(i+1);[result[i],result[j]]=[result[j],result[i]];}
  if(result.length>1&&result.every((value,index)=>value===input[index]))return [...result.slice(1),result[0]];
  return result;
}

export class Lesson {
  constructor(state=newState(),view,rawNumbers={}) {
    this.state=validateSnapshot(state);
    const reached=frontier(state),number=typeof view==='string'&&/^-?\d+$/.test(view)?Number(view):view;
    this.view=int(number,0,reached)?number:reached;
    this.rawNumbers={};
    if(state.s===4&&object(rawNumbers))for(const [key,value] of Object.entries(rawNumbers))
      if(DATA.valuationFields.some(([field])=>field===key)&&numericDraft(value))this.rawNumbers[key]=value;
  }
  get reviewing(){return this.view<frontier(this.state);}
  get position(){return POSITIONS[this.view];}
  move(direction) {
    if(direction!==-1&&direction!==1)return false;
    const target=this.view+direction;if(!int(target,0,frontier(this.state)))return false;
    this.view=target;return true;
  }
  canAdvance() {
    if(this.reviewing||this.state.s===7)return false;
    if(this.state.s===0)return true;
    if(this.state.s===4)return this.state.vs&&evaluateValuation(this.state.vr,this.state.vb).correct;
    const group=GROUPS.find(group=>group.stage===this.state.s),item=group.items[this.state[group.indexKey]];
    return this.state[group.responseKey][item.id]===item.correct;
  }
  advance() {
    if(!this.canAdvance())return false;
    const next=POSITIONS[this.view+1],group=GROUPS.find(group=>group.stage===next.stage);
    this.state.s=next.stage;if(group)this.state[group.indexKey]=next.index;
    this.view++;this.rawNumbers={};validateSnapshot(this.state);return true;
  }
  choiceContext() {
    const group=GROUPS.find(group=>group.stage===this.state.s);
    if(!group)return null;
    const item=group.items[this.state[group.indexKey]];
    return {group,item,correct:this.state[group.responseKey][item.id]===item.correct};
  }
  draftChoice(value) {
    const context=this.choiceContext();
    if(this.reviewing||!context||context.correct||!context.item.options.includes(value))return false;
    this.state.d[context.group.draft][context.item.id]=value;return true;
  }
  recordAttempt(key,correct) {
    // Original v3 links cap saved counters at 99. Upgrade only on overflow so
    // repeated practice retains its full original score instead of losing resume.
    const attempts=(this.state.at[key]??0)+1;
    if(attempts>99)this.state.v=4;
    this.state.at[key]=attempts;
    if(!own(this.state.fp,key))this.state.fp[key]=Boolean(correct);
  }
  submitChoice() {
    const context=this.choiceContext();if(this.reviewing||!context||context.correct)return false;
    const selected=this.state.d[context.group.draft][context.item.id];
    if(!context.item.options.includes(selected))return false;
    this.state[context.group.responseKey][context.item.id]=selected;
    this.recordAttempt(`${context.group.prefix}:${context.item.id}`,selected===context.item.correct);return true;
  }
  valuationLocked(){return this.state.vs&&evaluateValuation(this.state.vr,this.state.vb).correct;}
  draftNumber(key,raw) {
    if(this.reviewing||this.state.s!==4||this.valuationLocked()||!DATA.valuationFields.some(([field])=>field===key)||typeof raw!=='string'||raw.length>64)return false;
    this.rawNumbers[key]=raw;const amount=parseAmount(raw);if(amount!==null)this.state.d.v[key]=amount;return true;
  }
  draftBenefit(value) {
    if(this.reviewing||this.state.s!==4||this.valuationLocked()||!DATA.benefitOptions.includes(value))return false;
    this.state.d.v.benefit=value;return true;
  }
  submitValuation() {
    if(this.reviewing||this.state.s!==4||this.valuationLocked())return false;
    const values={};
    for(const [key] of DATA.valuationFields) {
      const raw=this.rawNumbers[key]??String(this.state.d.v[key]??0),value=parseAmount(raw);
      if(value===null)return false;values[key]=value;
    }
    const benefit=this.state.d.v.benefit;if(!DATA.benefitOptions.includes(benefit))return false;
    const result=evaluateValuation(values,benefit);
    for(const [key] of DATA.valuationFields) {
      const scoreKey=`valuation:${key}`;
      if(!own(this.state.fp,scoreKey)||this.state.vr[key]!==values[key])this.recordAttempt(scoreKey,result.fields[key].correct);
    }
    if(!own(this.state.fp,'valuation:benefit')||this.state.vb!==benefit)this.recordAttempt('valuation:benefit',result.benefit.correct);
    // Carry the given allowance total as an unscored legacy wire field for old URL compatibility.
    this.state.vr={ending_allowance:requiredAllowance(),...values};this.state.vb=benefit;this.state.vs=true;this.state.d.v={...values,benefit};return true;
  }
  reset() {
    if(this.reviewing)return false;this.state=newState();this.view=0;this.rawNumbers={};return true;
  }
}
export function rawDraftToken(rawNumbers) {
  const numeric=Object.fromEntries(Object.entries(rawNumbers).filter(([,value])=>numericDraft(value)));
  return base64url(new TextEncoder().encode(JSON.stringify(numeric)));
}
export function readRawDraft(token) {
  try{if(!token||token.length>1000)return {};return JSON.parse(new TextDecoder().decode(from64(token)));}catch{return {};}
}
