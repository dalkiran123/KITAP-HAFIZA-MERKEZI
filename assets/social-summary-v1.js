(()=>{'use strict';
const el=document.getElementById('bc-social-summary'),detail=document.getElementById('bc-social-detail');if(!el||!detail)return;
function bots(){try{const w=JSON.parse(localStorage.getItem('bookcenter_arena_botworld_v1')||'null');return Array.isArray(w?.bots)?w.bots:[]}catch{return []}}
const css=document.createElement('style');css.textContent=`
#bc-social-detail:not([hidden]){position:fixed!important;inset:50% auto auto 50%!important;transform:translate(-50%,-50%)!important;width:min(350px,calc(100vw - 32px))!important;max-width:calc(100vw - 32px)!important;max-height:70dvh!important;overflow-y:auto!important;box-sizing:border-box!important;z-index:100010!important;border-radius:18px!important;padding:16px!important;background:#fffdf8!important;color:#193052!important;box-shadow:0 0 0 100vmax #0007,0 12px 35px #0005!important}
#bc-social-detail .bc-summary-row{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:8px 2px;border-bottom:1px solid #e1e6ec}
#bc-social-detail button{cursor:pointer;border-radius:9px;padding:7px 10px;border:1px solid #bac9dc;background:#eaf2ff;color:#153458;font-weight:700}
`;document.head.append(css);
function close(){detail.hidden=true;el.setAttribute('aria-expanded','false')}
function render(){const list=bots();el.textContent='👥 '+list.length;el.setAttribute('aria-label',list.length+' sanal arkadaş. Ayrıntıları aç');if(detail.hidden)return;detail.replaceChildren();
const header=document.createElement('div');header.style.cssText='display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:8px';
const title=document.createElement('strong');title.textContent='Sanal arkadaşlar ('+list.length+')';
const x=document.createElement('button');x.textContent='✕';x.setAttribute('aria-label','Kapat');x.onclick=close;header.append(title,x);detail.append(header);
const note=document.createElement('p');note.textContent='Bu liste sanal botları gösterir. Gerçek çevrimiçi kullanıcı sayısı doğrulanmadı.';note.style.cssText='font-size:12px;line-height:1.4;margin:6px 0';detail.append(note);
list.forEach((b,i)=>{const row=document.createElement('div');row.className='bc-summary-row';const name=document.createElement('span');name.textContent=String(b.name||'Bot '+(i+1));const msg=document.createElement('button');msg.textContent='Mesaj';msg.onclick=()=>{close();if(typeof window.BookCenterOpenFriendChat==='function')window.BookCenterOpenFriendChat({id:'local-bot-'+b.id,name:String(b.name||'Bot'),kind:'bot'});else alert('Mesajlaşma henüz yüklenmedi. Ana ekrandan yeniden deneyin.')};row.append(name,msg);detail.append(row)})}
el.addEventListener('click',e=>{e.stopPropagation();detail.hidden=!detail.hidden;el.setAttribute('aria-expanded',String(!detail.hidden));render()});
document.addEventListener('click',e=>{if(!detail.hidden&&!detail.contains(e.target)&&e.target!==el)close()});
document.addEventListener('keydown',e=>{if(e.key==='Escape')close()});render();setInterval(render,30000);
})();