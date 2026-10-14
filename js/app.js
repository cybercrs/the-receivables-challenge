/** Render original captured teaching screens using native, guarded browser controls. */
import {DATA} from './content.js?v=20261014-aging';
import {Lesson,frontier,shuffled,decodeState,encodeState,readRawDraft,rawDraftToken,
  scoreSummary,currency,evaluateValuation,parseAmount,MAX_AMOUNT} from './engine.js?v=20261014-aging';

const $=id=>document.getElementById(id);
let lesson,orders=new Map(),saveSequence=0;
const create=(tag,text,cls)=>{const node=document.createElement(tag);if(text!==undefined)node.textContent=text;if(cls)node.className=cls;return node;};
const showMessage=text=>{const node=create('p',text,'notice warning');node.setAttribute('role','alert');$('lesson').prepend(node);};
async function save() {
  const sequence=++saveSequence,state=structuredClone(lesson.state),view=lesson.view,raw=structuredClone(lesson.rawNumbers);
  document.documentElement.dataset.saving='true';
  try {
    const token=await encodeState(state);
    if(sequence!==saveSequence)return;
    const url=new URL(location.href);url.searchParams.set('progress',token);url.searchParams.set('view',String(view));
    if(state.s===4&&Object.keys(raw).length)url.searchParams.set('draft',rawDraftToken(raw));else url.searchParams.delete('draft');
    history.replaceState(null,'',url);$('save-error').hidden=true;
  } catch(error) {
    if(sequence!==saveSequence)return;
    $('save-error').textContent='Your address could not be updated. Keep this tab open; copying or refreshing may not preserve the latest input.';
    $('save-error').hidden=false;console.error(error);
  } finally {if(sequence===saveSequence)document.documentElement.dataset.saving='false';}
}
async function prepareOrders() {
  const entries=DATA.groups.flatMap(group=>group.items.map(item=>[item.id,item.options,`${group.prefix}-answer-order:${item.id}`]));
  entries.push(['benefit',DATA.benefitOptions,'valuation-benefit-order']);
  orders=new Map(await Promise.all(entries.map(async([key,options,salt])=>[key,await shuffled(options,lesson.state.z,salt)])));
}
function move(direction) {if(lesson.move(direction)){render();save();resetScroll();}}
function resetScroll(){window.scrollTo({top:0,left:0,behavior:'instant'});$('lesson').focus({preventScroll:true});}
function radio(node) {
  if(lesson.reviewing)return document.createDocumentFragment();
  const fieldset=create('fieldset'),legend=create('legend',node.label);fieldset.append(legend);
  const benefit=node.key==='widget_valuation_benefit',group=DATA.groups.find(g=>g.stage===lesson.position.stage);
  const item=benefit?null:group.items[lesson.position.index];
  const selected=benefit?lesson.state.d.v.benefit:lesson.state.d[group.draft][item.id];
  const options=orders.get(benefit?'benefit':item.id);
  options.forEach((option,index)=>{
    const label=create('label',undefined,'choice'),input=create('input'),text=create('span',option);
    input.type='radio';input.name=node.key;input.value=option;input.id=`${node.key}_${index}`;input.checked=option===selected;
    input.addEventListener('change',()=>{if(benefit?lesson.draftBenefit(option):lesson.draftChoice(option))save();});
    label.append(input,text);fieldset.append(label);
  });
  return fieldset;
}
function number(node) {
  if(lesson.reviewing)return document.createDocumentFragment();
  const key=node.key.replace('widget_valuation_',''),wrapper=create('div',undefined,'amount'),label=create('label',node.label),row=create('div',undefined,'amount-row');
  label.htmlFor=node.key;const input=create('input');input.id=node.key;input.name=key;input.type='text';input.inputMode='numeric';input.maxLength=64;
  input.value=lesson.rawNumbers[key]??String(lesson.state.d.v[key]??0);
  input.setAttribute('aria-describedby','whole-dollars');
  input.addEventListener('input',()=>{if(lesson.draftNumber(key,input.value)){input.setAttribute('aria-invalid',String(parseAmount(input.value)===null));save();}});
  row.append(input);
  for(const [symbol,direction] of [['−',-1],['+',1]]) {
    const button=create('button',symbol);button.type='button';button.setAttribute('aria-label',`${direction<0?'Decrease':'Increase'} ${node.label} by ${node.step}`);
    button.addEventListener('click',()=>{const old=parseAmount(input.value);if(old===null)return;input.value=String(Math.max(0,Math.min(MAX_AMOUNT,old+direction*node.step)));input.dispatchEvent(new Event('input',{bubbles:true}));});row.append(button);
  }
  wrapper.append(label,row);return wrapper;
}
function csv(rows,columns) {return columns.map(x=>`"${x.replaceAll('"','""')}"`).join(',')+'\r\n'+rows.map(row=>columns.map(key=>`"${String(row[key]).replaceAll('"','""')}"`).join(',')).join('\r\n')+'\r\n';}
function table(node,index) {
  const section=create('section'),wrap=create('div',undefined,'table-wrap'),element=create('table');
  if(node.fixedRows){element.className='aging-schedule';wrap.tabIndex=0;wrap.setAttribute('role','region');wrap.setAttribute('aria-label','Aging schedule: age buckets across the top. Scroll horizontally to view each bucket; the total column stays visible.');}
  const caption=create('caption',lesson.position.stage===3?'Completed aging schedule':'Aging estimates');caption.className='visually-hidden';
  element.append(caption);const columns=Object.keys(node.rows[0]),head=create('thead'),tr=create('tr'),body=create('tbody');
  let rows=[...node.rows],sort=null,descending=false;
  const renderRows=()=>{body.replaceChildren();for(const row of rows){const line=create('tr');columns.forEach((key,i)=>{const cell=create(node.fixedRows&&i===0?'th':'td',String(row[key]));if(node.fixedRows&&i===0)cell.scope='row';line.append(cell);});body.append(line);}};
  columns.forEach(key=>{const cell=create('th');cell.scope='col';
    if(node.fixedRows){cell.textContent=key;tr.append(cell);return;}
    const button=create('button',key);button.type='button';
    button.addEventListener('click',()=>{descending=sort===key?!descending:false;sort=key;
      rows=[...node.rows].sort((a,b)=>String(a[key]).localeCompare(String(b[key]),'en')*(descending?-1:1));
      for(const header of tr.children)header.removeAttribute('aria-sort');cell.setAttribute('aria-sort',descending?'descending':'ascending');renderRows();});
    cell.append(button);tr.append(cell);});
  head.append(tr);element.append(head,body);renderRows();wrap.append(element);section.append(wrap);
  if(node.fixedRows){const hint=create('p','Age buckets run across the top. On a narrow screen, scroll the schedule horizontally to see every age bucket; totals remain visible on the right.','caption table-help');section.append(hint);}
  const tools=create('div',undefined,'table-tools'),download=create('button','Download table as CSV');download.type='button';
  const expand=create('button','Expand table');expand.type='button';
  expand.addEventListener('click',()=>{
    const dialog=create('dialog',undefined,'expanded-table'),title=create('h2',caption.textContent),close=create('button','Close table');
    const placeholder=document.createComment('Table location');wrap.before(placeholder);
    close.type='button';close.addEventListener('click',()=>dialog.close());
    dialog.append(title,close,wrap);document.body.append(dialog);
    dialog.addEventListener('close',()=>{placeholder.replaceWith(wrap);dialog.remove();expand.focus();},{once:true});
    dialog.showModal();
  });
  tools.append(expand);
  download.addEventListener('click',()=>{const blob=new Blob([csv(rows,columns)],{type:'text/csv;charset=utf-8'}),url=URL.createObjectURL(blob),link=create('a');
    link.href=url;link.download=`receivables-${lesson.position.stage===3?'aging':'valuation'}-${index+1}.csv`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
  tools.append(download);section.append(tools);return section;
}
function html(node) {
  const template=document.createElement('template');template.innerHTML=node.text;
  if(lesson.position.stage===4&&lesson.state.vs) {
    const row=template.content.querySelector('.feedback-row');
    if(row) {
      const label=row.querySelector('.feedback-label'),detail=row.querySelector('.feedback-detail');
      const field=DATA.valuationFields.find(([,name])=>label.textContent.startsWith(name+' - '));
      const checked=evaluateValuation(lesson.state.vr,lesson.state.vb),correct=field?checked.fields[field[0]].correct:checked.benefit.correct;
      row.classList.toggle('correct',correct);row.classList.toggle('review',!correct);
      label.textContent=(field?field[1]:'Benefit of aging')+' - '+(correct?'Correct':'Review');
      detail.textContent=field?`Your answer: ${currency(lesson.state.vr[field[0]])}. Use the aging estimate and the existing allowance balance.`:`Your answer: ${lesson.state.vb}`;
    }
  }
  if(lesson.position.stage===7)for(const box of template.content.querySelectorAll('.metric-box')) {
    const label=box.querySelector('span').textContent;
    const group=DATA.groups.find(g=>`${g.prefix[0].toUpperCase()+g.prefix.slice(1)}${g.prefix==='claim'?'s':''} first pass`===label);
    if(group)box.querySelector('strong').textContent=category(group.prefix,group.items.length);
  }
  return template.content;
}
function category(prefix,count) {return `${Object.entries(lesson.state.fp).filter(([key,value])=>key.startsWith(prefix+':')&&value).length}/${count}`;}
function renderNode(node,index) {
  if(node.kind==='html')return html(node);
  if(node.kind==='radio')return radio(node);
  if(node.kind==='number')return number(node);
  if(node.kind==='table')return table(node,index);
  if(node.kind==='button') {
    if(lesson.reviewing)return document.createDocumentFragment();
    const button=create('button',node.label,'primary');button.type='button';
    button.addEventListener('click',()=>{
      let result;
      if(node.label.startsWith('Check')) {
        result=lesson.state.s===4?lesson.submitValuation():lesson.submitChoice();
        if(!result) {
          if(lesson.state.s===4) {
            const invalid=DATA.valuationFields.find(([key])=>parseAmount(lesson.rawNumbers[key]??String(lesson.state.d.v[key]??0))===null);
            showMessage(invalid?'Enter whole-dollar amounts from 0 through 10,000,000. Decimal amounts, incomplete comma groups and negative values cannot be submitted.':'Choose a response about aging before checking the valuation.');
          }else showMessage('Choose a response before checking your reasoning.');
          return;
        }
      }else result=lesson.advance();
      if(result){render();save();if(!node.label.startsWith('Check'))resetScroll();}
    });return button;
  }
  if(node.kind==='progress') {
    const box=create('div',node.text,'case-progress'),bar=create('progress');bar.max=1;bar.value=node.value;bar.setAttribute('aria-label',node.text);box.append(bar);return box;
  }
  if(node.kind==='columns'||node.kind==='column') {
    const column=create('div',undefined,node.kind==='columns'?'columns':null);if(node.kind==='columns')column.style.setProperty('--columns',node.children.length);
    node.children.forEach((child,index)=>column.append(renderNode(child,index)));return column;
  }
  if(node.kind==='metric') {
    const metric=create('div',undefined,'metric');metric.append(create('span',node.label),create('strong',String(node.value)));
    if(node.delta!==undefined)metric.append(create('div',node.delta,'delta'+(String(node.delta).startsWith('-')?' negative':'')));return metric;
  }
  if(node.kind==='details') {
    const details=create('details'),summary=create('summary',node.label);details.append(summary);node.children.forEach((child,index)=>details.append(renderNode(child,index)));return details;
  }
  if(node.kind==='markdown') {
    const fragment=document.createDocumentFragment(),lines=node.text.split('\n').map(x=>x.trim()).filter(Boolean);
    if(lines.every(line=>/^\d+\./.test(line))) {const list=create('ol');for(const line of lines)list.append(create('li',line.replace(/^\d+\.\s*/,'')));fragment.append(list);}
    else for(const line of lines)fragment.append(create('p',line));return fragment;
  }
  let text=node.text;
  if(node.kind==='caption'&&lesson.position.stage===7&&text.startsWith('Valuation first pass:')) {
    const score=scoreSummary(lesson.state);text=`Valuation first pass: ${category('valuation',DATA.valuationFields.length+1)} | All first-pass decisions: ${score.correct} of ${score.total} | Practice revisions used: ${score.revisions} | Final mastery: complete`;
  }
  const heading=node.kind==='header'?'h2':node.kind==='subheader'?'h3':'p';
  const result=create(heading,text,['success','warning','info'].includes(node.kind)?`notice ${node.kind}`:node.kind==='caption'?'caption':null);
  if(['success','warning','info'].includes(node.kind))result.setAttribute('role','status');return result;
}
function render() {
  const position=lesson.position,screen=DATA.screens[lesson.view],group=DATA.groups.find(g=>g.stage===position.stage);
  let variant='unanswered';
  if(position.stage===4)variant=lesson.state.vs?(evaluateValuation(lesson.state.vr,lesson.state.vb).correct?'correct':'wrong'):'unanswered';
  else if(group){const item=group.items[position.index],response=lesson.state[group.responseKey][item.id];variant=response===undefined?'unanswered':response===item.correct?'correct':'wrong';}
  $('hero').replaceChildren(...DATA.hero.map(html));
  $('page-counter').textContent=`Page ${lesson.view+1} of ${DATA.positions.length}`;
  $('back').disabled=lesson.view===0;$('forward').disabled=lesson.view>=frontier(lesson.state);$('reset').disabled=lesson.reviewing;
  $('stages').replaceChildren(...DATA.stages.map((label,stage)=>create('div',label,'stage-pill '+(stage<position.stage?'complete':stage===position.stage?'active':''))));
  $('review-message').replaceChildren();
  if(lesson.reviewing){const info=create('p','Review only. Return to your current page to continue the activity.','notice info');info.setAttribute('role','status');$('review-message').append(info);}
  const nodes=screen.variants[variant].map(renderNode);$('lesson').replaceChildren(...nodes);
  if(position.stage===4&&!lesson.reviewing&&!lesson.valuationLocked()) {
    const helper=create('p','Enter whole dollars from 0 through 10,000,000. Commas and a leading dollar sign are accepted.','caption');helper.id='whole-dollars';$('lesson').append(helper);
  }
  $('lesson').setAttribute('aria-busy','false');document.documentElement.dataset.view=String(lesson.view);
  document.documentElement.dataset.reached=String(frontier(lesson.state));
}
async function initialize() {
  if(!globalThis.CompressionStream||!globalThis.DecompressionStream||!globalThis.crypto?.subtle||!globalThis.structuredClone)throw new Error('Required native browser APIs are unavailable');
  const query=new URL(location.href).searchParams,token=query.get('progress'),state=token?await decodeState(token):null;
  lesson=new Lesson(state??undefined,query.get('view')??undefined,readRawDraft(query.get('draft')));
  await prepareOrders();render();if(token&&!state)showMessage('This saved link could not be restored. A new receivables case has been opened.');
  await save();document.documentElement.dataset.ready='true';performance.mark('receivables-ready');
}
$('back').addEventListener('click',()=>move(-1));$('forward').addEventListener('click',()=>move(1));
$('reset').addEventListener('click',async()=>{if(lesson.reset()){await prepareOrders();render();await save();resetScroll();}});
window.addEventListener('popstate',initialize);
initialize().catch(error=>{
  $('lesson').replaceChildren(create('p','This browser could not open the saved activity. Use a current browser with JavaScript, Web Crypto, BigInt, and Compression Streams enabled.','notice warning'));
  $('lesson').setAttribute('aria-busy','false');console.error(error);
});
