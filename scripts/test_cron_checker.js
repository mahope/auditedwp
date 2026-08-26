// Extracted core of the page's parser for verification
const MONTHS=['January','February','March','April','May','June','July','August','September','October','November','December'];
const DAYS=['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];
function parseField(f,min,max){
  f=f.trim();
  const names={jan:1,feb:2,mar:3,apr:4,may:5,jun:6,jul:7,aug:8,sep:9,oct:10,nov:11,dec:12,sun:0,mon:1,tue:2,wed:3,thu:4,fri:5,sat:6};
  const vals=new Set();
  for(const part of f.split(',')){
    let[range,step]=part.split('/');
    step=step?parseInt(step,10):1;
    if(!step||step<1)throw new Error('invalid step "/'+part+'"');
    let lo,hi;
    if(range==='*'){lo=min;hi=max;}
    else{
      const bits=range.split('-');
      const norm=t=>{t=t.trim().toLowerCase();if(/^\d+$/.test(t))return parseInt(t,10);
                     if(names[t]!==undefined)return names[t];
                     throw new Error('"'+t+'" is not a valid value');};
      lo=norm(bits[0]);
      hi=bits.length>1?norm(bits[1]):lo;
    }
    if(lo<min||hi>max)throw new Error('value out of range ('+min+'-'+max+') in "'+part+'"');
    if(lo>hi)throw new Error('range start > end in "'+part+'"');
    for(let v=lo;v<=hi;v+=step)vals.add(v);
  }
  return vals;
}
function nextRuns(m,h,dom,mon,dow,count){
  const out=[];
  const d=new Date();
  d.setSeconds(0,0);d.setMinutes(d.getMinutes()+1);
  outer:
  for(let i=0;i<366*24*60;i++){
    if(mon.size&&!mon.has(d.getMonth()+1)){d.setMonth(d.getMonth()+1,1);d.setHours(0,0);d.setMinutes(0);continue;}
    const domOk=dom.has(d.getDate());
    const dowOk=dow.has(d.getDay());
    let dayOk;
    if(dom.size&&dow.size)dayOk=domOk||dowOk;
    else if(dom.size)dayOk=domOk;
    else if(dow.size)dayOk=dowOk;
    else dayOk=true;
    if(!dayOk){d.setDate(d.getDate()+1);d.setHours(0,0);d.setMinutes(0);continue;}
    if(h.size&&!h.has(d.getHours())){d.setHours(d.getHours()+1,0);d.setMinutes(0);continue;}
    if(m.size&&!m.has(d.getMinutes())){d.setMinutes(d.getMinutes()+1);continue;}
    out.push(new Date(d));
    if(out.length>=count)break outer;
    d.setMinutes(d.getMinutes()+1);
  }
  return out;
}
function check(expr,count=5){
  const f=expr.split(/\s+/);
  if(f.length!==5)throw new Error('expected 5 fields, got '+f.length);
  const m=parseField(f[0],0,59),h=parseField(f[1],0,23),
        dom=parseField(f[2],1,31),mon=parseField(f[3],1,12),
        dow=new Set([...parseField(f[4].replace(/7/g,'0'),0,6)].map(v=>v%7));
  return nextRuns(m,h,dom,mon,dow,count).map(d=>d.toISOString().slice(0,16).replace('T',' '));
}
const tests=[
  ['*/15 * * * *',5],
  ['0 3 * * *',2],
  ['30 9 * * 1-5',5],
  ['0 0 1 * *',2],
  ['0 */6 * * 0',2],
  ['0 9-17 * * mon-fri',5],
];
for(const[e,c]of tests){
  console.log(e,'=>');
  check(e,c).forEach(r=>console.log('  ',r));
}
// error cases
for(const bad of['*/15 * * *','61 * * * *','abc * * * *','*/0 * * * *']){
  try{check(bad,1);console.log('BAD ACCEPTED:',bad);}catch(err){console.log('rejected ok:',bad,'—',err.message);}
}
