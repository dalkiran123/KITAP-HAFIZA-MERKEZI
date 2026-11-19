/* BOOK CENTER inline friend presence. No simulated activity is presented as real online presence.
   Integration: include this script with defer on the main application page.
   Mark menu/book/video/profile containers with data-presence-type and data-presence-id.
   Endpoint GET /api/presence/visible returns {friends:[{id,name,avatar_url,profile_url,kind,online,location:{type,id},last_seen_at}]}
   Only permission-filtered, authenticated records should be returned by the backend. */
(()=>{'use strict';
const API=window.BOOKCENTER_PRESENCE_API_URL||null;
const SIMULATION_LABEL='Sanal etkinlik';
// Cache-independent asset release: no local reading record implies live section presence.
const style=document.createElement('style');
style.textContent=`
[data-presence-type][data-presence-id]{position:relative}
.bc-friends{position:absolute;left:5px;right:auto;top:5px;z-index:20;display:flex;align-items:center;gap:2px;max-width:calc(100% - 10px);isolation:isolate;filter:none!important;animation:none!important}
.bc-friend{flex:0 0 25px;width:25px;height:25px;border-radius:50%;border:2px solid #fff;background:#20345a;color:white;padding:0;display:grid;place-items:center;overflow:hidden;box-shadow:0 2px 8px #0004;cursor:pointer}
.bc-friend img{width:100%;height:100%;object-fit:cover}
.bc-friend-person{display:flex;flex-direction:column;align-items:center;gap:2px;flex:0 0 auto;max-width:76px;cursor:pointer}
.bc-friend-name{display:block;max-width:76px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;background:#fff9e8!important;color:#142544!important;-webkit-text-fill-color:#142544!important;border:1px solid #b58a46;border-radius:6px;padding:1px 4px;font:700 10px/1.3 system-ui!important;text-shadow:none!important;filter:none!important;opacity:1!important;animation:none!important;box-shadow:0 1px 4px #0003}
.bc-friends-menu{gap:4px!important;align-items:flex-start!important;max-width:calc(100vw - 12px)!important}
.bc-friends-menu .bc-friend-person{max-width:62px}
.bc-friends-menu .bc-friend-name{max-width:62px}
.bc-friends:not(.bc-friends-menu) .bc-friend-person{max-width:68px}

.bc-friend[data-kind=bot]{border-color:#d9a65d}
.bc-friend:focus-visible{outline:3px solid #2085ff}
.bc-friends-menu{pointer-events:auto;white-space:nowrap;z-index:10050!important}
.bc-floating-presence{position:fixed!important;z-index:10050!important;pointer-events:auto!important;max-width:calc(100vw - 12px)!important}
nav.v2nav,nav.nav{overflow:visible!important}
nav.v2nav button,nav.nav button{position:relative}
nav.v2nav button[data-bc-active-friends="1"],nav.nav button[data-bc-active-friends="1"]{position:relative!important}
nav.v2nav button:has(> .bc-friends-menu) .bc-friends-menu,nav.nav button:has(> .bc-friends-menu) .bc-friends-menu{top:5px!important;left:5px!important;transform:none!important;filter:none!important;animation:none!important}
nav.v2nav button:has(> .bc-friends-menu) .bc-friends-menu *,nav.nav button:has(> .bc-friends-menu) .bc-friends-menu *{animation:none!important;filter:none!important}
.bc-friends-menu .bc-friend{background:#162b51!important;color:#fff!important;-webkit-text-fill-color:#fff!important;font-size:12px!important;font-weight:800!important;line-height:1!important;text-shadow:none!important;opacity:1!important;transform:none!important;animation:none!important;box-shadow:0 1px 5px #0008!important}
.bc-friends-menu .bc-friend-count{background:#172a4b!important;color:#fff!important;-webkit-text-fill-color:#fff!important;opacity:1!important;animation:none!important;white-space:nowrap}
.bc-friends-menu .bc-friend-count{font-size:10px;padding:2px 5px;border:1px solid #d9a65d;box-shadow:0 1px 4px #0005}
.bc-book-activity{position:relative;margin:6px 0 0;display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;background:#172a4be8;color:#fff;border:1px solid #d9a65d;border-radius:9px;padding:3px 6px;font:11px system-ui;pointer-events:none}
.bc-friend-count{background:#172a4b;color:white;border-radius:12px;padding:3px 5px;font-size:11px}
`;
style.textContent+=`
.bc-floating-presence,.bc-friends{overflow:visible!important}
.bc-presence-trigger{appearance:none!important;border:1px solid #f3d18a!important;border-radius:16px!important;background:#193558!important;color:#fff!important;-webkit-text-fill-color:#fff!important;font:700 11px/1.2 system-ui!important;padding:5px 8px!important;min-height:28px!important;white-space:nowrap!important;box-shadow:0 2px 6px #0005!important;cursor:pointer!important;animation:none!important}
.bc-presence-panel{position:absolute!important;left:0!important;top:32px!important;z-index:10090!important;width:min(290px,calc(100vw - 24px))!important;max-height:280px!important;overflow-y:auto!important;padding:9px!important;border:1px solid #a4aab9!important;border-radius:12px!important;background:#fffdf7!important;color:#152c4d!important;box-shadow:0 8px 22px #0005!important;animation:none!important;text-align:left!important}
.bc-presence-panel[hidden]{display:none!important}
.bc-presence-heading{font:700 13px system-ui!important;margin:2px 0 8px!important}
.bc-presence-line{display:flex!important;align-items:center!important;justify-content:space-between!important;gap:6px!important;margin:5px 0!important}
.bc-presence-person,.bc-presence-message{appearance:none!important;background:#edf3ff!important;color:#142c4b!important;-webkit-text-fill-color:#142c4b!important;border:1px solid #b5c5db!important;border-radius:9px!important;padding:5px!important;font:600 12px system-ui!important;min-height:34px!important;cursor:pointer!important;animation:none!important}
.bc-presence-person{display:flex!important;align-items:center!important;gap:7px!important;min-width:0!important;flex:1!important;text-align:left!important}
.bc-presence-person img,.bc-presence-initial{width:24px!important;height:24px!important;border-radius:50%!important;object-fit:cover!important;background:#1e365c!important;color:white!important;display:grid!important;place-items:center!important;flex:none!important}
`;
document.head.appendChild(style);
document.addEventListener('click',e=>{if(!e.target.closest('.bc-friends'))document.querySelectorAll('.bc-presence-panel').forEach(p=>p.hidden=true)});
const safeUrl=(s)=>{if(typeof s!=='string'||!s.trim())return null;try{const u=new URL(s,location.origin);return u.origin===location.origin&&['http:','https:'].includes(u.protocol)?u.href:null}catch{return null}};
const normalizeBook=s=>String(s||'').normalize('NFKC').toLocaleLowerCase('tr-TR').replace(/\s+/g,' ').trim();
const same=(f,type,id)=>{if(!(f?.online===true||f?.kind==='bot'&&f?.localSimulation===true))return false;return f.location?.type===type&&(type==='book'?normalizeBook(f.location?.id)===normalizeBook(id):String(f.location?.id)===id)};
function render(friends){
 document.querySelectorAll('[data-presence-type][data-presence-id]').forEach(host=>{
  const type=host.dataset.presenceType,id=host.dataset.presenceId;
  const menu=host.matches('nav.v2nav button, nav.nav button');
  let root=menu?document.querySelector('.bc-floating-presence[data-host-key="'+(host.dataset.bcPresenceKey||'')+'"]'):host.querySelector(':scope > .bc-friends');
  const matched=friends.filter(f=>same(f,type,id));
  if(!matched.length){if(menu)delete host.dataset.bcActiveFriends;root?.remove();host.querySelector(':scope > .bc-book-activity')?.remove();return}
  if(menu)host.dataset.bcActiveFriends='1';
  if(!root){root=document.createElement('div');root.className='bc-friends';if(menu){host.dataset.bcPresenceKey=host.dataset.bcPresenceKey||('bc-'+Math.random().toString(36).slice(2));root.dataset.hostKey=host.dataset.bcPresenceKey;root.classList.add('bc-floating-presence');document.body.append(root)}else host.append(root)}
  if(menu){const rect=host.getBoundingClientRect();root.style.left=Math.max(2,rect.left+4)+'px';root.style.top=Math.max(2,rect.top-18)+'px';root.style.display=rect.bottom>0&&rect.top<innerHeight&&rect.top>40?'flex':'none'}
  root.classList.toggle('bc-friends-menu',menu);
  const signature=(menu?'menu|':'card|')+matched.map(f=>String(f.id)+'|'+String(f.last_seen_at||'')+'|'+String(f.name)+'|'+String(f.avatar_url||'')).join(';');
  if(root.dataset.signature===signature)return;
  root.dataset.signature=signature;
  root.replaceChildren();
  const oldActivity=host.querySelector(':scope > .bc-book-activity');
  if(type==='book'){
   const bots=matched.filter(f=>f.localSimulation);
   if(bots.length){
    const activity=oldActivity||document.createElement('span');
    activity.className='bc-book-activity';
    activity.textContent='🤖 '+bots.slice(0,2).map(f=>f.name).join(', ')+(bots.length>2?' +'+(bots.length-2):'')+' · sanal okuma';
    activity.title=bots.map(f=>f.name+' · '+new Date(f.last_seen_at).toLocaleString('tr-TR')).join(' | ');
    if(!oldActivity)host.append(activity);
   }else oldActivity?.remove();
  }else oldActivity?.remove();
  const trigger=document.createElement('button');
  trigger.type='button';trigger.className='bc-presence-trigger';
  trigger.textContent='👥 '+matched.length;
  trigger.setAttribute('aria-label',matched.length+' arkadaş. Listeyi aç');
  trigger.title=matched.filter(f=>f.kind==='bot').length+' sanal arkadaş; simülasyon gerçek çevrimiçi durumu değildir';
  root.append(trigger);
  const panel=document.createElement('div');panel.className='bc-presence-panel';panel.hidden=true;
  const heading=document.createElement('div');heading.className='bc-presence-heading';
  heading.textContent='Bu alandaki arkadaşlar ('+matched.length+')';
  panel.append(heading);
  matched.forEach(friend=>{
   const line=document.createElement('div');line.className='bc-presence-line';
   const name=document.createElement('button');name.type='button';name.className='bc-presence-person';
   const url=safeUrl(friend.avatar_url);
   if(url){const img=document.createElement('img');img.src=url;img.alt='';name.append(img)}
   else {const initials=document.createElement('span');initials.className='bc-presence-initial';initials.textContent=String(friend.name||'?').slice(0,1).toUpperCase();name.append(initials)}
   const label=document.createElement('span');label.textContent=String(friend.name||'Arkadaş')+(friend.kind==='bot'?' · Sanal':' · Çevrimiçi');name.append(label);
   name.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();const target=safeUrl(friend.profile_url);if(target)location.assign(target);else document.dispatchEvent(new CustomEvent('bookcenter:open-friend-profile',{detail:{friendId:friend.id,kind:friend.kind}}))});
   const message=document.createElement('button');message.type='button';message.className='bc-presence-message';message.textContent='Mesaj';
   message.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();document.dispatchEvent(new CustomEvent('bookcenter:message-friend',{detail:{friendId:friend.id,kind:friend.kind,name:friend.name}}));panel.hidden=true});
   line.append(name,message);panel.append(line);
  });
  root.append(panel);
  trigger.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();document.querySelectorAll('.bc-presence-panel').forEach(p=>{if(p!==panel)p.hidden=true});panel.hidden=!panel.hidden;trigger.setAttribute('aria-expanded',String(!panel.hidden))});
  trigger.setAttribute('aria-expanded','false');
 });
}
let current=[];
function localBotRecords(){
 try{
  const world=JSON.parse(localStorage.getItem('bookcenter_arena_botworld_v1')||'null');
  if(!Array.isArray(world?.bots))return [];
  return world.bots.flatMap((bot,i)=>{
   if(!bot||!Number.isInteger(bot.id)||bot.id<0||bot.id>9)return [];
   const reading=Array.isArray(bot.reading)?bot.reading[0]:null;
   if(!reading||typeof reading.title!=='string'||!reading.title.trim())return [];
   const stamp=Date.parse(reading.at||'');
   if(!Number.isFinite(stamp)||Date.now()-stamp>86400000||stamp>Date.now()+60000)return [];
   return [{id:'local-bot-'+bot.id,name:String(bot.name||'Bot '+(bot.id+1)),kind:'bot',simulated:true,localSimulation:true,online:false,
    location:{type:'book',id:reading.title.trim()},last_seen_at:reading.at}];
  });
 }catch{return []}
}
function simulatedBotSections(){
 try{
  const world=JSON.parse(localStorage.getItem('bookcenter_arena_botworld_v1')||'null');
  if(!Array.isArray(world?.bots))return [];
  const sections=['home','video','discover','news','youtube','linkedin','library'];
  const slot=Math.floor(Date.now()/90000);
  return world.bots.filter(b=>b&&Number.isInteger(b.id)&&b.id>=0&&b.id<10).map(bot=>{
   const index=(bot.id*3+slot)%sections.length;
   return {id:'local-bot-'+bot.id,name:String(bot.name||'Bot '+(bot.id+1)),kind:'bot',
    simulated:true,simulatedSection:true,localSimulation:true,online:false,
    location:{type:'section',id:sections[index]},last_seen_at:new Date(slot*90000).toISOString()};
  });
 }catch{return []}
}
function draw(){annotate();render([...current,...localBotRecords(),...simulatedBotSections()])}
async function refresh(){try{
 if(!API){current=[];draw();return}
 const parsed=new URL(API,location.href);
 if(parsed.protocol!=='https:'&&parsed.hostname!=='localhost')throw Error('Presence requires HTTPS');
 const response=await fetch(API,{credentials:'include',cache:'no-store'});
 if(!response.ok)throw Error('Presence unavailable');
 const data=await response.json();if(!Array.isArray(data.friends))throw Error('Invalid presence');
 current=data.friends.filter(f=>f&&f.id!=null&&typeof f.name==='string'&&f.name.length<=80&&f.location&&['user','bot'].includes(f.kind)&&f.online===true&&['section','book','video'].includes(f.location.type)&&typeof f.location.id==='string'&&f.location.id.length<=180).slice(0,100).map(f=>({...f,localSimulation:false}));
 draw();
}catch{current=[];draw()}}
function annotate(){
 document.querySelectorAll('nav.v2nav button, nav.nav button').forEach(button=>{
  const label=(button.textContent||'').toLocaleLowerCase('tr-TR');
  const type=/video|belgesel/.test(label)?'video':/arena|yarış/.test(label)?'arena':/keşfet/.test(label)?'discover':/kitaplığım/.test(label)?'library':/profil|kariyer/.test(label)?'profile':/ana menü/.test(label)?'home':/yedek/.test(label)?'backup':/yenile/.test(label)?'refresh':/haber/.test(label)?'news':/youtube/.test(label)?'youtube':/linkedin/.test(label)?'linkedin':/zaman/.test(label)?'time':null;
  if(type){button.dataset.presenceType='section';button.dataset.presenceId=type}
 });
 document.querySelectorAll('#catalogshelf .tile, #discover .catalog-card, #discover .tile, [data-book-id], [data-book-name], #page-home .book-card, #page-home [class*=book-card]').forEach(card=>{
  const name=card.dataset.bookId||card.dataset.bookName||card.querySelector('strong,h3,h4')?.textContent?.trim();
  if(name){card.dataset.presenceType='book';card.dataset.presenceId=name}
 });
 document.querySelectorAll('[data-video-id]').forEach(card=>{card.dataset.presenceType='video';card.dataset.presenceId=card.dataset.videoId});
}
annotate();
setInterval(draw,5000);
window.addEventListener('scroll',draw,{passive:true});window.addEventListener('resize',draw,{passive:true});
window.addEventListener('arena-world-updated',()=>{annotate();draw()});
window.addEventListener('storage',event=>{if(event.key==='bookcenter_arena_botworld_v1'){annotate();draw()}});
refresh();setInterval(refresh,30000);
document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh()});
document.addEventListener('bookcenter:open-friend-profile',event=>{
 const id=String(event.detail?.friendId||'');
 if(event.detail?.kind!=='bot'||!/^local-bot-[0-9]+$/.test(id))return;
 const botId=Number(id.slice('local-bot-'.length));
 if(!Number.isInteger(botId)||botId<0||botId>9)return;
 let bot;
 try{bot=JSON.parse(localStorage.getItem('bookcenter_arena_botworld_v1')||'null')?.bots?.find(b=>b?.id===botId)}catch{}
 if(!bot)return;
 document.getElementById('bcInlineBotProfile')?.remove();
 const dialog=document.createElement('section');dialog.id='bcInlineBotProfile';
 dialog.setAttribute('role','dialog');dialog.setAttribute('aria-modal','true');dialog.setAttribute('aria-label','Sanal arkadaş profili');
 dialog.style.cssText='position:fixed;z-index:1200;inset:auto 12px 12px;max-width:440px;margin:auto;background:#1d2947;color:#fff;border:1px solid #d9a65d;border-radius:18px;padding:18px;box-shadow:0 12px 38px #0008;font:14px system-ui';
 const title=document.createElement('h3');title.textContent='🤖 '+String(bot.name||'Sanal arkadaş');title.style.margin='0 0 9px';
 const desc=document.createElement('p');desc.textContent='Sanal karakter · '+(Number(bot.books)||0)+' kitap etkinliği · '+(Number(bot.points)||0)+' puan';
 const last=document.createElement('p');const recent=Array.isArray(bot.reading)?bot.reading[0]:null;
 last.textContent=recent?'Son simüle okuma: '+String(recent.title||'')+' · '+(Number.isFinite(Date.parse(recent.at))?new Date(recent.at).toLocaleString('tr-TR'):'Tarih bilinmiyor'):'Henüz okuma kaydı yok';
 const note=document.createElement('small');note.textContent='Bu bilgiler yerel simülasyondur. Gerçek zamanlı kullanıcı etkinliği değildir.';
 const close=document.createElement('button');close.type='button';close.textContent='Kapat';close.style.cssText='display:block;margin-top:12px;background:#e5bc79;color:#17233c';
 close.onclick=()=>{dialog.remove();document.removeEventListener('keydown',escape)};
 dialog.append(title,desc,last,note,close);document.body.append(dialog);close.focus();
 const escape=event=>{if(event.key==='Escape'){dialog.remove();document.removeEventListener('keydown',escape)}};
 document.addEventListener('keydown',escape);
 dialog.addEventListener('click',event=>{if(event.target===dialog){dialog.remove();document.removeEventListener('keydown',escape)}});
});
window.BookCenterPresence={refresh,diagnostics:()=>({apiConfigured:!!API,remoteCount:current.length,localBotCount:localBotRecords().length,simulatedBotCount:simulatedBotSections().length,annotated:document.querySelectorAll('[data-presence-type][data-presence-id]').length})};
})();
