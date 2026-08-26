// Minimal DOM stub for Node: esc() uses textContent->innerHTML round-trip
const _els={};
function mkEl(){return {value:'',className:'',innerHTML:'',_listeners:{},addEventListener(k,f){this._listeners[k]=f;}};}
global.document={
  getElementById:id=>_els[id]||(_els[id]=mkEl()),
  createElement:()=>({
    _t:'',
    set textContent(v){this._t=v;},
    get innerHTML(){return String(this._t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
  })
};


function setEx(btn){
  document.getElementById('cexpr').value=btn.textContent;
  doCheck();
}
const MONTHS=['January','February','March','April','May','June','July','August','September','October','November','December'];
const DAYS=['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
function parseField(f,min,max,stepOk){
  f=f.trim();
  const names={jan:1,feb:2,mar:3,apr:4,may:5,jun:6,jul:7,aug:8,sep:9,oct:10,nov:11,dec:12,
               sun:0,mon:1,tue:2,wed:3,thu:4,fri:5,sat:6};
  const vals=new Set();
  for(const part of f.split(',')){
    let[range,step]=part.split('/');
    step=step?parseInt(step,10):1;
    if(!step||step<1)throw new Error('invalid step in "'+part+'"');
    let lo,hi;
    if(range==='*'){lo=min;hi=max;}
    else{
      const bits=range.split('-');
      const norm=t=>{t=t.trim().toLowerCase();if(/^\d+$/.test(t))return parseInt(t,10);
                     if(names[t]!==undefined)return names[t];
                     throw new Error('"'+t+'" is not a valid value');};
      lo=norm(bits[0]);
      hi=bits.length>1?norm(bits[1]):(step>1&&stepOk?max:lo);
    }
    if(lo<min||hi>max)throw new Error('value out of range ('+min+'-'+max+') in "'+part+'"');
    for(let v=lo;v<=hi;v+=step)vals.add(v);
  }
  return vals;
}
function describe(f,label){
  if(f==='*')return 'every '+label;
  if(f.startsWith('*/'))return 'every '+f.slice(2)+' '+label+'s';
  return f.replace(/\b([a-z]{3})\b/gi,w=>{
    const k=w.toLowerCase();
    if(MONTHS.some((m,i)=>m.toLowerCase().slice(0,3)===k&&label==='month'))return MONTHS[['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'].indexOf(k)];
    if(DAYS.some(d=>d.toLowerCase().slice(0,3)===k)&&label==='weekday')return DAYS[['sun','mon','tue','wed','thu','fri','sat'].indexOf(k)];
    return w;
  })+(label==='minute'||label==='hour'?'th '+label:'');
}
function nextRuns(m,h,domRestricted,dom,mon,dow,count){
  const out=[];
  const d=new Date();
  d.setUTCSeconds(0,0);d.setUTCMinutes(d.getUTCMinutes()+1);
  for(let i=0;i<366*24*60&&out.length<count;i++){
    if(mon.size&&!mon.has(d.getUTCMonth()+1)){d.setUTCMonth(d.getUTCMonth()+1,1);d.setUTCHours(0,0,0,0);continue;}
    const domOk=dom.has(d.getUTCDate());
    const dowOk=dow.has(d.getUTCDay());
    let dayOk;
    if(domRestricted&&dow.size)dayOk=domOk||dowOk;      // both restricted: either matches (standard cron)
    else if(domRestricted)dayOk=domOk;
    else if(dow.size)dayOk=dowOk;
    else dayOk=true;
    if(!dayOk){d.setUTCDate(d.getUTCDate()+1);d.setUTCHours(0,0,0,0);continue;}
    if(h.size&&!h.has(d.getUTCHours())){d.setUTCHours(d.getUTCHours()+1,0,0,0);continue;}
    if(m.size&&!m.has(d.getUTCMinutes())){d.setUTCMinutes(d.getUTCMinutes()+1);continue;}
    out.push(new Date(d));
    d.setUTCMinutes(d.getUTCMinutes()+1);
  }
  return out;
}
function pad(n){return String(n).padStart(2,'0');}
function fmtUTC(d){return d.getUTCFullYear()+'-'+pad(d.getUTCMonth()+1)+'-'+pad(d.getUTCDate())+' '+pad(d.getUTCHours())+':'+pad(d.getUTCMinutes());}
function doCheck(){
  const raw=document.getElementById('cexpr').value.trim();
  const box=document.getElementById('result');
  if(!raw){box.className='bad';box.textContent='Enter a cron expression first.';return;}
  const fields=raw.split(/\s+/);
  if(fields.length!==5){box.className='bad';box.textContent='Expected 5 fields (minute hour day month weekday) — got '+fields.length+'.';return;}
  try{
    const m=parseField(fields[0],0,59,true);
    const h=parseField(fields[1],0,23,true);
    const domRaw=fields[2];
    const dom=parseField(domRaw,1,31,false);
    const mon=parseField(fields[3],1,12,false);
    // normalize dow: accept 0-7 with 7==Sunday; leave empty when field is '*'
    const dowSet=new Set();
    if(fields[4]!=='*'){
      for(const part of fields[4].split(',')){
        const vals=[...parseField(part,0,7,false)];
        for(const v of vals)dowSet.add(v%7);
      }
    }
    const domRestricted=domRaw!=='*';
    const dowRestricted=fields[4]!=='*';
    const human=[
      describe(fields[0],'minute'),
      describe(fields[1],'hour'),
      domRestricted?'day of month: '+fields[2]:'every day',
      fields[3]!=='*'?'month: '+fields[3]:'every month',
      dowRestricted?[...dowSet].sort().map(v=>DAYS[v]).join(', '):'any weekday'
    ];
    const runs=nextRuns(m,h,domRestricted,dom,mon,dowSet,5);
    box.className='ok';
    box.innerHTML='<dl>'+
      '<dt>Minute</dt><dd>'+esc(human[0])+'</dd>'+
      '<dt>Hour</dt><dd>'+esc(human[1])+'</dd>'+
      '<dt>Day of month</dt><dd>'+esc(human[2])+'</dd>'+
      '<dt>Month</dt><dd>'+esc(human[3])+'</dd>'+
      '<dt>Weekday</dt><dd>'+esc(human[4])+'</dd>'+
      '</dl><p style="margin-top:10px;font-weight:600">Next runs in UTC:</p><ol>'+
      runs.map(r=>'<li>'+fmtUTC(r)+' UTC</li>').join('')+'</ol>';
  }catch(e){
    box.className='bad';box.textContent='Could not parse expression: '+e.message;
  }
}
function esc(s){const d=document.createElement('div');d.textContent=s;return d.innerHTML;}
document.getElementById('cexpr').addEventListener('keydown',e=>{if(e.key==='Enter')doCheck();});

function run(expr){
  document.getElementById('cexpr').value=expr;
  doCheck();
  const el=document.getElementById('result');
  return {cls:el.className,text:el.innerHTML.replace(/<[^>]+>/g,' '),html:el.innerHTML};
}
let fails=0;
function expect(expr,check,name){
  const r=run(expr);
  if(!check(r)){fails++;console.log('FAIL:',name||expr,'=>',r.cls,'|',r.text.slice(0,160));}
  else console.log('ok:',name||expr);
}
expect('*/15 * * * *',r=>r.cls==='ok'&&r.text.includes('every 15 minutes'),'*/15 ok');
expect('0 3 * * *',r=>{const m=r.html.match(/<li>([^<]+)<\/li>/);return m&&m[1].endsWith('03:00 UTC');},'daily 3am UTC');
expect('30 9 * * 1-5',r=>{const lis=[...r.html.matchAll(/<li>([^<]+)<\/li>/g)].map(m=>m[1]);
  return r.text.includes('Monday, Tuesday, Wednesday, Thursday, Friday')&&lis.every(t=>{const d=new Date(t.replace(' UTC','')+'Z');return d.getUTCHours()===9&&d.getUTCMinutes()===30;});},'weekdays 9:30 named');
expect('0 0 1 * *',r=>{const m=r.html.match(/<li>([^<]+)<\/li>/);return m&&m[1].slice(8,10)==='01'&&m[1].endsWith('00:00 UTC');},'first of month midnight');
expect('0 */6 * * 0',r=>{const lis=[...r.html.matchAll(/<li>([^<]+)<\/li>/g)].map(m=>m[1]);
  return r.text.includes('Sunday')&&lis.every(t=>{const d=new Date(t.replace(' UTC','')+'Z');return d.getUTCDay()===0&&d.getUTCHours()%6===0;});},'sundays every 6h');
expect('0 9-17 * * mon-fri',r=>{const lis=[...r.html.matchAll(/<li>([^<]+)<\/li>/g)].map(m=>m[1]);
  return r.cls==='ok'&&r.text.includes('Monday')&&lis.every(t=>{const d=new Date(t.replace(' UTC','')+'Z');return d.getUTCHours()>=9&&d.getUTCHours()<=17&&d.getUTCDay()>=1&&d.getUTCDay()<=5;});},'mon-fri 9-17');
expect('15,45 */2 * * *',r=>{const lis=[...r.html.matchAll(/<li>([^<]+)<\/li>/g)].map(m=>m[1]);
  return r.cls==='ok'&&lis.every(t=>{const d=new Date(t.replace(' UTC','')+'Z');return (d.getUTCMinutes()===15||d.getUTCMinutes()===45)&&d.getUTCHours()%2===0;});},'15,45 every 2h');
expect('* * 31 12 *',r=>{const lis=[...r.html.matchAll(/<li>([^<]+)<\/li>/g)].map(m=>m[1]);
  return r.cls==='ok'&&lis.every(t=>t.startsWith('2026-12-31'));},'december 31 only');
expect('* * * * 7',r=>{const lis=[...r.html.matchAll(/<li>([^<]+)<\/li>/g)].map(m=>m[1]);
  return r.text.includes('Sunday')&&lis.every(t=>new Date(t.replace(' UTC','')+'Z').getUTCDay()===0);},'dow 7 = sunday');
expect('* * * * 0',r=>r.text.includes('Sunday'),'dow 0 = sunday');
expect('0 12 13 * 5',r=>{const lis=[...r.html.matchAll(/<li>([^<]+)<\/li>/g)].map(m=>m[1]);
  return lis.length===5&&lis.every(t=>{const d=new Date(t.replace(' UTC','')+'Z');return d.getUTCDate()===13||d.getUTCDay()===5;})&&lis.some(t=>new Date(t.replace(' UTC','')+'Z').getUTCDate()!==13);},'dom OR dow semantics');
expect('*/15 * * *',r=>r.cls==='bad','4 fields rejected');
expect('61 * * * *',r=>r.cls==='bad','minute 61 rejected');
expect('abc * * * *',r=>r.cls==='bad','abc rejected');
expect('*/0 * * * *',r=>r.cls==='bad','step 0 rejected');
expect('',r=>r.cls==='bad','empty rejected');
console.log(fails===0?'ALL PASS':'FAILURES: '+fails);
process.exit(fails?1:0);
