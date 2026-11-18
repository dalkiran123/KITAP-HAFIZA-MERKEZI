/* BOOK CENTER: non-invasive friends presence overlay, preview only. */
(()=>{'use strict';
const friends=[['Luna','👩🏻‍🦰','Sefiller'],['Atlas','🧑🏽‍💻','Dönüşüm'],['Mira','👩🏽','İlyada'],['Deniz','🧑🏻','Doğa belgeseli'],['Ada','👩🏼','Küçük Prens']];
const css=document.createElement('style');css.textContent=`
#bcFriendsToggle{position:fixed;right:12px;bottom:16px;z-index:950;background:linear-gradient(120deg,#25395f,#64447c);color:white;border:1px solid #e5bc79;border-radius:50px;padding:10px 14px;box-shadow:0 7px 22px #0007;font:700 13px system-ui;max-width:190px}
#bcFriendsOverlay{position:fixed;right:10px;bottom:66px;z-index:951;width:min(310px,calc(100vw - 20px));background:#1c2541f5;color:white;border:1px solid #e5bc79;border-radius:19px;padding:12px;box-shadow:0 14px 35px #0008;font:13px system-ui;max-height:55vh;overflow:auto}
#bcFriendsOverlay[hidden]{display:none!important}.bcFriendRow{display:flex;gap:10px;align-items:center;background:#ffffff0c;border:1px solid #ffffff22;border-radius:12px;padding:8px;margin-top:7px;width:100%;color:white;text-align:left;font:inherit}.bcFriendRow .bcFace{font-size:28px}.bcFriendRow small{display:block;color:#d5dcf1;font-size:11px;margin-top:2px}.bcFriendHead{display:flex;align-items:center;justify-content:space-between;gap:8px}.bcFriendHead button{background:#3c4c70;color:white;border:0;border-radius:9px;padding:6px 9px}.bcFriendNote{font-size:11px;color:#ffd7a1;margin:8px 0}.bcFriendMore{display:block;text-align:center;color:#ffdfa5;padding:10px}
`;document.head.append(css);
const toggle=document.createElement('button');toggle.id='bcFriendsToggle';toggle.type='button';toggle.textContent='👥 Arkadaşlar · Önizleme';
const overlay=document.createElement('aside');overlay.id='bcFriendsOverlay';overlay.hidden=true;overlay.setAttribute('aria-label','Arkadaşlar ortak ekran önizlemesi');
const head=document.createElement('div');head.className='bcFriendHead';const title=document.createElement('strong');title.textContent='👥 Yanındaki arkadaşlar';const close=document.createElement('button');close.type='button';close.textContent='✕';head.append(title,close);overlay.append(head);
const note=document.createElement('p');note.className='bcFriendNote';note.textContent='Örnek karakterler. Gerçek çevrimiçi durum veya kitap okuma kaydı değildir.';overlay.append(note);
const list=document.createElement('div');overlay.append(list);
const link=document.createElement('a');link.className='bcFriendMore';link.href='./birlikte/index.html';link.textContent='Ortak ekranı aç';overlay.append(link);
let mode='book';
function detectRoom(label){const s=String(label||'').toLocaleLowerCase('tr');if(/video|belgesel|izle/.test(s))return 'video';if(/arena|yarış|oyun/.test(s))return 'arena';return 'book'}
function draw(){list.replaceChildren();for(let i=0;i<3;i++){const f=friends[(i+(mode==='video'?2:mode==='arena'?1:0))%friends.length];const row=document.createElement('button');row.type='button';row.className='bcFriendRow';const face=document.createElement('span');face.className='bcFace';face.textContent=f[1];const txt=document.createElement('span');const b=document.createElement('b');b.textContent=f[0];const small=document.createElement('small');small.textContent=mode==='video'?'Örnek: '+(i===0?'Doğa belgeseli':i===1?'Uzay belgeseli':'Tarih belgeseli')+' izliyor':mode==='arena'?'Örnek: bilgi yarışmasına katılıyor':'Örnek: '+f[2]+' okuyor';txt.append(b,small);row.append(face,txt);row.onclick=()=>{const msg=document.createElement('div');msg.className='bcFriendNote';msg.textContent=f[0]+' · Sanal karakter. Profilini ortak ekranda inceleyebilirsin.';const old=overlay.querySelector('.bcSelected');if(old)old.remove();msg.classList.add('bcSelected');overlay.insertBefore(msg,link)};list.append(row)}}
function open(){draw();overlay.hidden=false;toggle.setAttribute('aria-expanded','true')}
function hide(){overlay.hidden=true;toggle.setAttribute('aria-expanded','false')}
toggle.onclick=()=>overlay.hidden?open():hide();close.onclick=hide;
document.addEventListener('click',e=>{const target=e.target;if(!(target instanceof Element))return;const el=target.closest('button,a,[role=button]');if(!el||el===toggle||overlay.contains(el))return;const label=(el.textContent||'').trim();if(/video|belgesel|izle|arena|yarış|oyun|oku|kitap/i.test(label)){mode=detectRoom(label);if(!overlay.hidden)draw()}},true);
document.addEventListener('keydown',e=>{if(e.key==='Escape')hide()});
document.body.append(toggle,overlay);draw();
})();