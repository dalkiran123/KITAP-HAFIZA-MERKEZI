/* Server-backed fictional friend feed. No fake live status. */
(()=>{'use strict';
const root=document.getElementById('serverFriendFeed');if(!root)return;
const endpoint=window.BOOKCENTER_SOCIAL_FEED_API_URL;
const status=document.createElement('p');status.className='muted';
const entries=document.createElement('div');root.append(status,entries);
const make=(tag,cls,text)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=text;return e};
if(typeof endpoint!=='string'||!/^https:\/\//.test(endpoint)){
 status.textContent='Sunucu sosyal akışı henüz bağlanmadı. Aşağıdaki paylaşımlar telefonundaki yerel içeriklerdir.';return;
}
async function load(){
 status.textContent='Sunucudaki sanal arkadaş etkinlikleri yükleniyor...';
 try{
  const res=await fetch(endpoint,{credentials:'omit',cache:'no-store'});
  if(!res.ok)throw Error('HTTP '+res.status);
  const data=await res.json();
  if(data.source!=='server'||!Array.isArray(data.posts))throw Error('Geçersiz sunucu yanıtı');
  entries.replaceChildren();
  for(const post of data.posts){
   const card=make('article','socialPost');
   const head=make('header','socialPostHead');
   const avatar=make('span','socialFace','🤖');
   const meta=make('div');meta.append(make('strong','',String(post.name||'Sanal karakter')),make('small','',String(post.created_at||'')+' · Sunucu simülasyonu'));head.append(avatar,meta);card.append(head);
   const visual=make('div','socialArt',({library:'📚','reading-desk':'📖',notebook:'📝',window:'🌄',coffee:'☕'})[post.scene]||'📚');
   visual.setAttribute('role','img');visual.setAttribute('aria-label','Sanal sahne görseli, gerçek fotoğraf değil');card.append(visual);
   card.append(make('p','socialCaption',String(post.caption||'')));
   card.append(make('div','socialPostActions','❤️ '+Number(post.likes||0)+' · 💬 '+(Array.isArray(post.comments)?post.comments.length:0)));
   for(const c of (Array.isArray(post.comments)?post.comments:[]).slice(0,20)){
    const p=make('p','socialCaption');p.append(make('strong','',String(c.name||'Bot')+': '),document.createTextNode(String(c.body||'')));card.append(p);
   }
   entries.append(card);
  }
  status.textContent=data.posts.length? 'Sunucuda kayıtlı '+data.posts.length+' sanal paylaşım gösteriliyor.':'Sunucu bağlı, henüz kayıtlı paylaşım yok.';
 }catch(e){entries.replaceChildren();status.textContent='Sunucu akışı şu anda alınamıyor. '+e.message}
}
load();
})();