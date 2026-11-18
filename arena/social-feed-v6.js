(()=>{'use strict';
const KEY='bookcenter_social_v6_posts',FACES=['📚','🌻','🧠','🎨','🌙','✨','🚀','🦋','📝','🏅'],DEFAULT=['Atlas','Mira','Deniz','Arda','Luna','Nova','Orion','Ada','Bilge','Zirve'];
const SCENES=[['📖','Bugün kitaplarla dolu bir gün. Yeni bir hikâyeye başladım.','#513c91','#ba6f9d'],['🌄','Biraz doğa, biraz kitap. Siz bugün ne okuyorsunuz?','#246a8a','#d7a36e'],['☕','Kahve molasında okuma notlarımı düzenliyorum.','#8b4b59','#e1a565'],['🌌','Bu akşam yeni fikirler keşfetmek için harika.','#263b83','#7953ac'],['🌿','Okuduğum satırlar üzerine düşünmek iyi geliyor.','#227b69','#8bbf86']];
const $=id=>document.getElementById(id);const names=()=>{try{return window.arenaBotWorld?.names()?.slice(0,10)||DEFAULT}catch{return DEFAULT}};
const load=()=>{try{const v=JSON.parse(localStorage.getItem(KEY));return Array.isArray(v)?v.filter(x=>x&&typeof x.id==='string').slice(0,80):[]}catch{return []}};
let posts=load();
const REPLY_DELAY=12000;
function replyFor(post,c){
 const msg=c.text.toLocaleLowerCase('tr-TR');
 if(/nerede|nerelerdesin|nereye/.test(msg))return post.who==='Mira'?'Buradayım 🌻 Biraz doğayla baş başa kaldım, sonra kitabıma döneceğim. Sen neler yapıyorsun?':'Şu an kitaplarımla ilgileniyorum 📚 Sen neredesin?';
 if(/ne oku|hangi kitap|kitap öner/.test(msg))return 'Bugün yeni bir kitap keşfetmeye çalışıyorum 📖 Senin son okuduğun kitap hangisi?';
 if(/merhaba|selam|nasılsın/.test(msg))return 'Merhaba! 😊 İyiyim, biraz okuma molasındayım. Sen nasılsın?';
 if(/teşekkür|sağ ol/.test(msg))return 'Ne demek, her zaman! ✨';
 const choices=['Güzel bir noktaya değindin. Biraz daha anlatır mısın? 📚','Bunu düşünmek hoşuma gitti. Senin fikrini merak ediyorum. 🌿','Ben de bu konu üzerine düşünüyorum. Sence nasıl ilerlemeli? 💬'];
 return choices[(c.text.length+post.who.length)%choices.length];
}
function settleReplies(){
 let changed=false;const now=Date.now();
 posts.forEach(post=>{if(!post.sim||!Array.isArray(post.comments))return;
 const pending=post.comments.filter(c=>c.who==='Ben'&&!c.replied&&c.replyAt&&now>=c.replyAt);
 pending.forEach(c=>{post.comments.push({who:post.who,text:replyFor(post,c),at:new Date().toISOString(),simulated:true});c.replied=true;changed=true;});
 });
 if(changed){save();render();}
}

function save(){try{localStorage.setItem(KEY,JSON.stringify(posts.slice(0,80)));return true}catch{alert('Telefon depolama alanı dolu. Fotoğrafı küçültüp tekrar deneyin.');return false}}
function node(tag,cls,txt){const e=document.createElement(tag);if(cls)e.className=cls;if(txt!==undefined)e.textContent=txt;return e}
function seed(){if(posts.length)return;const n=names();posts=SCENES.map((s,i)=>({id:'demo-'+i,who:n[i],avatar:FACES[i],text:s[1],emoji:s[0],colors:[s[2],s[3]],time:new Date(Date.now()-(i+1)*3600000).toISOString(),likes:[],comments:[],sim:true}));save()}
function render(){const strip=$('socialFriendStrip'),feed=$('socialFeedItems');if(!strip||!feed)return;strip.replaceChildren();feed.replaceChildren();names().forEach((name,i)=>{const b=node('button','socialAvatar');b.type='button';const face=node('i','',FACES[i]);const label=node('span','',name);b.append(face,label);b.onclick=()=>{const target=$('botWorld');target?.scrollIntoView({behavior:'smooth'})};strip.append(b)});
const composer=node('section','socialComposer');composer.append(node('strong','', '✍️ Paylaşım oluştur'));const ta=node('textarea');ta.placeholder='Bugün neler okuyorsun, neler düşünüyorsun?';ta.maxLength=700;ta.rows=2;const file=node('input');file.type='file';file.accept='image/*';file.setAttribute('aria-label','Fotoğraf seç');const publish=node('button','socialPublish','📸 Fotoğraf / Yazı Paylaş');composer.append(ta,file,publish);feed.append(composer);
publish.onclick=()=>{const text=ta.value.trim();const f=file.files?.[0];if(!text&&!f){alert('Yazı veya fotoğraf ekleyin.');return}if(f&&(!f.type.startsWith('image/')||f.size>8000000)){alert('8 MB altı bir görsel seçin.');return}
const add=(photo)=>{posts.unshift({id:'user-'+Date.now(),who:'Ben',avatar:'🙂',text,photo,time:new Date().toISOString(),likes:[],comments:[],sim:false});if(save())render()};
if(!f){add(null);return}const img=new Image(),reader=new FileReader();reader.onload=()=>{img.onload=()=>{const c=document.createElement('canvas');const scale=Math.min(1,900/img.width,900/img.height);c.width=Math.max(1,Math.round(img.width*scale));c.height=Math.max(1,Math.round(img.height*scale));c.getContext('2d').drawImage(img,0,0,c.width,c.height);add(c.toDataURL('image/jpeg',.65))};img.onerror=()=>alert('Fotoğraf okunamadı.');img.src=reader.result};reader.readAsDataURL(f)};
posts.forEach(post=>{const card=node('article','socialPost');const head=node('header','socialPostHead');head.append(node('span','socialFace',post.avatar||'🤖'));const meta=node('div');meta.append(node('strong','',post.who));meta.append(node('small','',new Date(post.time).toLocaleString('tr-TR')+(post.sim?' · Sanal paylaşım':'')));head.append(meta);card.append(head);
if(post.photo){const image=node('img','socialPhoto');image.src=post.photo;image.alt='Paylaşılan fotoğraf';image.loading='lazy';card.append(image)}else if(post.emoji){const art=node('div','socialArt',post.emoji);art.style.background='linear-gradient(135deg,'+(post.colors||['#51417b','#9d658c']).join(',')+')';art.setAttribute('role','img');art.setAttribute('aria-label','Sanal paylaşım görseli');card.append(art)}
if(post.text)card.append(node('p','socialCaption',post.text));
const actions=node('div','socialPostActions');const like=node('button','', (post.likes?.includes('me')?'❤️':'🤍')+' '+(post.likes?.length||0)+' Beğen');like.onclick=()=>{post.likes=post.likes||[];post.likes=post.likes.includes('me')?post.likes.filter(x=>x!=='me'):[...post.likes,'me'];save();render()};actions.append(like,node('span','', '💬 '+(post.comments?.length||0)+' yorum'));card.append(actions);
const comments=node('div','socialComments');(post.comments||[]).forEach(c=>{const line=node('p');line.append(node('strong','',c.who+': '),document.createTextNode(c.text));comments.append(line)});const input=node('input');input.placeholder='Yorum yaz...';input.maxLength=300;const send=node('button','','Gönder');send.onclick=()=>{const t=input.value.trim();if(!t)return;post.comments=post.comments||[];post.comments.push({who:'Ben',text:t,at:new Date().toISOString(),replyAt:post.sim?Date.now()+REPLY_DELAY:null});save();render()};const form=node('div','socialCommentForm');form.append(input,send);comments.append(form);card.append(comments);feed.append(card)});
const foot=node('p','socialStatus','Bot yanıtları bu cihazda üretilen örnek simülasyonlardır. Gerçek yapay zekâ sohbeti ve cihazlar arası senkronizasyon için sunucu entegrasyonu gerekir.');feed.append(foot)}
seed();settleReplies();render();window.setInterval(settleReplies,2000);document.addEventListener('visibilitychange',()=>{if(!document.hidden)settleReplies()});window.addEventListener('arena-botnames-updated',()=>{posts.forEach(p=>{if(p.id.startsWith('demo-'))p.who=names()[Number(p.id.slice(5))]||p.who});save();render()});
})();