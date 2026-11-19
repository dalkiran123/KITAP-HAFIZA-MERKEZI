/* BOOK CENTER inline friend presence. No simulated activity is presented as real online presence.
   Integration: include this script with defer on the main application page.
   Mark menu/book/video/profile containers with data-presence-type and data-presence-id.
   Endpoint GET /api/presence/visible returns {friends:[{id,name,avatar_url,profile_url,kind,online,location:{type,id},last_seen_at}]}
   Only permission-filtered, authenticated records should be returned by the backend. */
(()=>{'use strict';
const API='/api/presence/visible';
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
const safeUrl=(s)=>{try{const u=new URL(s,location.origin);return u.origin===location.origin&&['http:','https:'].includes(u.protocol)?u.href:null}catch{return null}};
const same=(f,type,id)=>f?.online===true&&f.location?.type===type&&String(f.location?.id)===id;
function render(friends){
 document.querySelectorAll('[data-presence-type][data-presence-id]').forEach(host=>{
  const type=host.dataset.presenceType,id=host.dataset.presenceId;
  let root=host.querySelector(':scope > .bc-friends');
  const matched=friends.filter(f=>same(f,type,id));
  if(!matched.length){root?.remove();return}
  if(!root){root=document.createElement('div');root.className='bc-friends';host.append(root)}
  root.replaceChildren();
  matched.slice(0,3).forEach(friend=>{
   const button=document.createElement('button');button.type='button';button.className='bc-friend';
   button.dataset.kind=friend.kind==='bot'?'bot':'user';
   button.title=friend.name+' • '+(friend.kind==='bot'?'Sanal arkadaş':'Çevrimiçi arkadaş');
   button.setAttribute('aria-label',friend.name+' profilini aç');
   const imgUrl=safeUrl(friend.avatar_url);
   if(imgUrl){const img=document.createElement('img');img.src=imgUrl;img.alt='';img.loading='lazy';button.append(img)}
   else button.textContent=String(friend.name||'?').slice(0,1).toUpperCase();
   button.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();
    const target=safeUrl(friend.profile_url);if(target)location.assign(target);
    else document.dispatchEvent(new CustomEvent('bookcenter:open-friend-profile',{detail:{friendId:friend.id,kind:friend.kind}}));
   });
   root.append(button);
  });
  if(matched.length>3){const more=document.createElement('span');more.className='bc-friend-count';more.textContent='+'+(matched.length-3);root.append(more)}
 });
}
let current=[];
async function refresh(){try{
 const response=await fetch(API,{credentials:'same-origin',cache:'no-store'});
 if(!response.ok)throw Error('Presence unavailable');
 const data=await response.json();if(!Array.isArray(data.friends))throw Error('Invalid presence');
 current=data.friends.filter(f=>f&&f.id!=null&&typeof f.name==='string'&&f.location&&['user','bot'].includes(f.kind));
 render(current);
}catch{current=[];render([])}}
const observer=new MutationObserver(()=>{if(current.length)render(current)});
observer.observe(document.body,{childList:true,subtree:true});
refresh();setInterval(refresh,30000);
document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh()});
window.BookCenterPresence={refresh};
})();
