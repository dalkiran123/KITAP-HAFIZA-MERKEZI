/* BOOK CENTER inline friend presence. No simulated activity is presented as real online presence.
   Integration: include this script with defer on the main application page.
   Mark menu/book/video/profile containers with data-presence-type and data-presence-id.
   Endpoint GET /api/presence/visible returns {friends:[{id,name,avatar_url,profile_url,kind,online,location:{type,id},last_seen_at}]}
   Only permission-filtered, authenticated records should be returned by the backend. */
(()=>{'use strict';
const API=window.BOOKCENTER_PRESENCE_API_URL||null;
const style=document.createElement('style');
style.textContent=`
[data-presence-type][data-presence-id]{position:relative}
.bc-friends{position:absolute;right:5px;top:5px;z-index:5;display:flex;align-items:center;gap:2px;max-width:110px}
.bc-friend{width:29px;height:29px;border-radius:50%;border:2px solid #fff;background:#20345a;color:white;padding:0;display:grid;place-items:center;overflow:hidden;box-shadow:0 2px 8px #0004;cursor:pointer}
.bc-friend img{width:100%;height:100%;object-fit:cover}
.bc-friend[data-kind=bot]{border-color:#d9a65d}
.bc-friend:focus-visible{outline:3px solid #2085ff}
.bc-friend-count{background:#172a4b;color:white;border-radius:12px;padding:3px 5px;font-size:11px}
`;
document.head.appendChild(style);
const safeUrl=(s)=>{if(typeof s!=='string'||!s.trim())return null;try{const u=new URL(s,location.origin);return u.origin===location.origin&&['http:','https:'].includes(u.protocol)?u.href:null}catch{return null}};
const normalizeBook=s=>String(s||'').normalize('NFKC').toLocaleLowerCase('tr-TR').replace(/\s+/g,' ').trim();
const same=(f,type,id)=>{if(!(f?.online===true||f?.kind==='bot'&&f?.simulated===true))return false;if(type==='section'&&id==='discover'&&f.kind==='bot'&&f.simulated===true&&f.location?.type==='book')return true;return f.location?.type===type&&(type==='book'?normalizeBook(f.location?.id)===normalizeBook(id):String(f.location?.id)===id)};
function render(friends){
 document.querySelectorAll('[data-presence-type][data-presence-id]').forEach(host=>{
  const type=host.dataset.presenceType,id=host.dataset.presenceId;
  let root=host.querySelector(':scope > .bc-friends');
  const matched=friends.filter(f=>same(f,type,id));
  if(!matched.length){root?.remove();return}
  if(!root){root=document.createElement('div');root.className='bc-friends';host.append(root)}
  const signature=matched.map(f=>String(f.id)+'|'+String(f.last_seen_at||'')+'|'+String(f.name)).join(';');
  if(root.dataset.signature===signature)return;
  root.dataset.signature=signature;
  root.replaceChildren();
  matched.slice(0,3).forEach(friend=>{
   const button=document.createElement('span');button.className='bc-friend';button.setAttribute('role','button');button.tabIndex=0;
   button.dataset.kind=friend.kind==='bot'?'bot':'user';
   const lastTime=Date.parse(friend.last_seen_at||'');
   button.title=friend.name+' • '+(friend.kind==='bot'?'Sanal okuma kaydı (canlı değil)':'Çevrimiçi arkadaş')+(Number.isFinite(lastTime)?' · '+new Date(lastTime).toLocaleString('tr-TR'):'');
   button.setAttribute('aria-label',friend.name+' profilini aç');
   const imgUrl=safeUrl(friend.avatar_url);
   if(imgUrl){const img=document.createElement('img');img.src=imgUrl;img.alt='';img.loading='lazy';button.append(img)}
   else button.textContent=String(friend.name||'?').slice(0,1).toUpperCase();
   const openProfile=event=>{event.preventDefault();event.stopPropagation();
    const target=safeUrl(friend.profile_url);if(target)location.assign(target);
    else document.dispatchEvent(new CustomEvent('bookcenter:open-friend-profile',{detail:{friendId:friend.id,kind:friend.kind}}));
   };
   button.addEventListener('click',openProfile);
   button.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){openProfile(event)}});
   root.append(button);
  });
  if(matched.length>3){const more=document.createElement('span');more.className='bc-friend-count';more.textContent='+'+(matched.length-3);root.append(more)}
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
   return [{id:'local-bot-'+bot.id,name:String(bot.name||'Bot '+(bot.id+1)),kind:'bot',simulated:true,online:false,
    location:{type:'book',id:reading.title.trim()},last_seen_at:reading.at}];
  });
 }catch{return []}
}
function draw(){render([...current,...localBotRecords()])}
async function refresh(){try{
 if(!API){current=[];draw();return}
 const parsed=new URL(API,location.href);
 if(parsed.protocol!=='https:'&&parsed.hostname!=='localhost')throw Error('Presence requires HTTPS');
 const response=await fetch(API,{credentials:'include',cache:'no-store'});
 if(!response.ok)throw Error('Presence unavailable');
 const data=await response.json();if(!Array.isArray(data.friends))throw Error('Invalid presence');
 current=data.friends.filter(f=>f&&f.id!=null&&typeof f.name==='string'&&f.location&&['user','bot'].includes(f.kind));
 draw();
}catch{current=[];draw()}}
function annotate(){
 document.querySelectorAll('nav.v2nav button, nav.nav button').forEach(button=>{
  const label=(button.textContent||'').toLocaleLowerCase('tr-TR');
  const type=/video|belgesel/.test(label)?'video':/arena|yarış/.test(label)?'arena':/keşfet/.test(label)?'discover':/kitaplığım/.test(label)?'library':/profil|kariyer/.test(label)?'profile':null;
  if(type){button.dataset.presenceType='section';button.dataset.presenceId=type}
 });
 document.querySelectorAll('#catalogshelf .tile, #discover .catalog-card, #discover .tile').forEach(card=>{
  const name=card.dataset.bookId||card.dataset.bookName||card.querySelector('strong,h3,h4')?.textContent?.trim();
  if(name){card.dataset.presenceType='book';card.dataset.presenceId=name}
 });
 document.querySelectorAll('[data-video-id]').forEach(card=>{card.dataset.presenceType='video';card.dataset.presenceId=card.dataset.videoId});
}
annotate();
setInterval(()=>{annotate();draw()},5000);
window.addEventListener('arena-world-updated',()=>{annotate();draw()});
window.addEventListener('storage',event=>{if(event.key==='bookcenter_arena_botworld_v1'){annotate();draw()}});
refresh();setInterval(refresh,30000);
document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh()});
document.addEventListener('bookcenter:open-friend-profile',event=>{
 const id=String(event.detail?.friendId||'');
 if(!id.startsWith('local-bot-'))return;
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
 close.onclick=()=>dialog.remove();
 dialog.append(title,desc,last,note,close);document.body.append(dialog);close.focus();
});
window.BookCenterPresence={refresh};
})();
