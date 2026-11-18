/* BOOK CENTER profile visitor indicator. Display only authenticated, server-recorded visits. */
(()=>{'use strict';
const endpoint=window.BOOKCENTER_PROFILE_VISITORS_API_URL;
if(typeof endpoint!=='string'||!/^https:\/\//.test(endpoint))return;
const card=document.createElement('aside');card.id='bookcenterProfileVisitors';card.style.cssText='position:fixed;right:10px;bottom:85px;z-index:80;max-width:170px;border:1px solid #e5b56d;border-radius:17px;background:#27213fe8;color:#fff;padding:9px 11px;box-shadow:0 9px 25px #0005;font:12px system-ui';
card.setAttribute('aria-label','Profil ziyaretçileri');
const title=document.createElement('div');title.textContent='👀 Profilini ziyaret edenler';title.style.cssText='font-weight:800;margin-bottom:5px';
const list=document.createElement('div');card.append(title,list);
function row(visit){const el=document.createElement('button');el.type='button';el.style.cssText='display:flex;align-items:center;gap:6px;background:transparent;border:0;color:white;padding:5px 0;text-align:left;width:100%;font:inherit';
const icon=document.createElement('span');icon.textContent='👤';icon.style.cssText='font-size:20px';
const name=document.createElement('span');name.textContent=String(visit.display_name||'Ziyaretçi').slice(0,45);el.append(icon,name);
const when=visit.visited_at?new Date(visit.visited_at):null;
const stamp=when&&!Number.isNaN(when.getTime())?when.toLocaleString('tr-TR',{dateStyle:'short',timeStyle:'short'}):'Zaman bilgisi yok';
el.title=stamp+' tarihinde profilini ziyaret etti';
el.onclick=()=>{const old=el.querySelector('small');if(old){old.remove();return}const hint=document.createElement('small');hint.textContent='Ziyaret: '+stamp;hint.style.cssText='display:block;color:#ffdda5';el.append(hint)};
return el}
async function load(){try{const res=await fetch(endpoint,{credentials:'include',cache:'no-store'});if(!res.ok)return;const data=await res.json();if(!Array.isArray(data.visitors))return;const visits=data.visitors.filter(v=>v&&typeof v.display_name==='string'&&v.visited_at).slice(0,3);if(!visits.length){card.remove();return}list.replaceChildren(...visits.map(row));if(!card.isConnected)document.body.append(card)}catch{card.remove()}}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',load,{once:true});else load();
document.addEventListener('visibilitychange',()=>{if(!document.hidden)load()});
})();