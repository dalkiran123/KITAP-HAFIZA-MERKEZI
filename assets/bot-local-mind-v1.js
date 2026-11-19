/* BOOK CENTER local conversation engine. No external AI/API requests. */
(()=>{'use strict';
const norm=s=>String(s||'').toLocaleLowerCase('tr-TR').normalize('NFKC').replace(/[^\p{L}\p{N}\s]/gu,' ').replace(/\s+/g,' ').trim();
const words=s=>norm(s).split(' ').filter(Boolean);
const profiles=[
{name:'Atlas',tone:'analitik',topic:'bilim',lead:'Birlikte düşünelim.'},
{name:'Mira',tone:'meraklı',topic:'roman',lead:'Bunu merak ettim.'},
{name:'Deniz',tone:'sakin',topic:'doğa',lead:'Güzel bir konu.'},
{name:'Arda',tone:'rekabetçi',topic:'satranç',lead:'Bir hedef koyalım.'},
{name:'Luna',tone:'şiirsel',topic:'şiir',lead:'Bana ilginç geldi.'},
{name:'Nova',tone:'enerjik',topic:'teknoloji',lead:'Harika bir başlangıç.'},
{name:'Orion',tone:'sorgulayıcı',topic:'tarih',lead:'Bir açıdan daha bakalım.'},
{name:'Ada',tone:'destekleyici',topic:'psikoloji',lead:'Seni dinliyorum.'},
{name:'Bilge',tone:'düşünceli',topic:'felsefe',lead:'Üzerinde düşünmeye değer.'},
{name:'Zirve',tone:'hedefli',topic:'kişisel gelişim',lead:'Somutlaştıralım.'}
];
const intents=[
{id:'greeting',keys:['merhaba','selam','günaydın','iyi akşamlar','hey'],reply:['Merhaba! Bugün ne konuşmak istersin?','Selam! Günün nasıl geçiyor?']},
{id:'identity',keys:['kimsin','adın ne','sen nesin','kendini tanıt'],reply:[]},
{id:'memory',keys:['hatırlıyor musun','ne konuşmuştuk','beni hatırlıyor musun'],reply:[]},
{id:'books',keys:['kitap','roman','okuma','yazar','özet','okudum'],reply:['Kitabın hangi bölümü sende iz bıraktı?','Okuduklarını birlikte değerlendirebiliriz. Kitabın adını söyler misin?']},
{id:'chess',keys:['satranç','oyun','yarış','maç','hamle'],reply:['Satrançta açılış mı, taktik mi çalışmak istersin?','Bir oyun planı yapalım. Hangi oyunu seçtin?']},
{id:'feelings',keys:['üzgünüm','mutsuzum','canım sıkkın','stresliyim','yoruldum'],reply:['Zor bir gün gibi görünüyor. İstersen seni neyin yorduğunu konuşabiliriz.','Anlatmak istersen dinliyorum. En çok ne zorladı?']},
{id:'thanks',keys:['teşekkür','sağ ol','eyvallah'],reply:['Rica ederim!','Ne demek, sohbet etmek güzel.']},
{id:'how',keys:['nasılsın','naber','ne yapıyorsun'],reply:['Buradayım, seninle sohbet ediyorum. Sen nasılsın?','Bugün biraz kitap ve oyun konuşmaya hazırım. Senin günün nasıl?']},
{id:'recommend',keys:['öner','tavsiye','ne okuyayım'],reply:['Hangi türü sevdiğini söylersen daha isabetli bir kitap seçebiliriz.','Roman mı, bilim mi, tarih mi ilgini çekiyor?']}
];
const pick=(arr,n)=>arr[Math.abs(n)%arr.length];
const score=(t,k)=>k.includes(' ')?(t.includes(k)?3:0):(words(t).some(w=>w===k||w.startsWith(k))?2:0);
function answer(friend,message,history=[]){
 const t=norm(message),p=profiles.find(x=>norm(x.name)===norm(friend.name))||profiles[Math.abs(Number(friend.id)||0)%profiles.length],prior=history.filter(m=>m.role==='user').slice(-12),seed=[...t].reduce((n,c)=>n+c.charCodeAt(0),0)+prior.length;
 if(!t)return 'Bir şey yazarsan konuşabiliriz.';
 const scored=intents.map(x=>({...x,score:Math.max(0,...x.keys.map(k=>score(t,k)))})).sort((a,b)=>b.score-a.score);
 const intent=scored[0].score?scored[0].id:'unknown';
 if(intent==='identity')return 'Ben '+p.name+'. BOOK CENTER içindeki '+p.tone+' karakterli sanal arkadaşınım. '+p.topic+' konularına ilgim var. Gerçek kişi ya da çevrimiçi yapay zekâ değilim.';
 if(intent==='memory'){const last=prior.slice(-2).map(x=>x.text).filter(Boolean);return last.length?'Bu cihazda son konuştuklarımızdan şunları hatırlıyorum: '+last.join(' / ').slice(0,180)+'. Devam edelim mi?':'Bu cihazda henüz önceki konuşmalarına ait bir konu bulamadım.'}
 if(intent==='unknown'){
   const last=prior.slice(0,-1).reverse().find(m=>words(m.text).some(w=>w.length>4&&words(t).includes(w)));
   if(last)return p.lead+' Daha önce “'+last.text.slice(0,70)+'” demiştin. Bununla bağlantısını biraz açar mısın?';
   if(t.endsWith('?')||message.includes('?'))return p.lead+' Sorunu tam yanıtlayacak bilgim olmayabilir. '+(t.includes('neden')?'Sence buna yol açan en önemli etken ne?':'Bir örnek verirsen daha iyi değerlendirebiliriz.');
   return p.lead+' “'+message.trim().slice(0,85)+'” dediğini anlıyorum. Bunun hangi yönünü konuşalım?';
 }
 const responses=scored[0].reply;
 if(intent==='books'&&p.topic==='roman')return 'Romanları seviyorum. '+pick(responses,seed);
 if(intent==='chess'&&p.tone==='rekabetçi')return 'Satrançta seni zorlamak isterdim! '+pick(responses,seed);
 return pick(responses,seed);
}
const memoryKey=id=>'bc_mind_memory_v2_'+String(id||'').replace(/[^a-zA-Z0-9_-]/g,'').slice(0,60);
function readMemory(friend){try{const v=JSON.parse(localStorage.getItem(memoryKey(friend.id))||'{}');return v&&typeof v==='object'?v:{}}catch{return {}}}
function learn(friend,message){
 const t=String(message||'').trim(),n=norm(t),m=readMemory(friend);
 const patterns=[
  ['name',/(?:benim adım|adım|bana)\s+([a-zçğıöşüA-ZÇĞİÖŞÜ]{2,25})/i],
  ['favoriteBook',/(?:en sevdiğim kitap|favori kitabım)\s+(.{2,75})/i],
  ['favoriteGenre',/(?:en sevdiğim tür|favori türüm)\s+(.{2,45})/i],
  ['interest',/(?:ilgileniyorum|merak ediyorum)\s+(.{2,60})/i]
 ];
 let learned=null;
 for(const [field,regex] of patterns){const match=t.match(regex);if(match){const value=match[1].replace(/[.!?]+$/,'').trim();if(value&&value.length<=75){m[field]=value;learned=field;break}}}
 if(n.includes('beni unut')||n.includes('hafızanı sil')||n.includes('bilgilerimi sil')){try{localStorage.removeItem(memoryKey(friend.id))}catch{}return {forgot:true}}
 if(learned){m.updated=new Date().toISOString();try{localStorage.setItem(memoryKey(friend.id),JSON.stringify(m))}catch{}}
 return {learned,memory:m};
}
function respond(friend,message,history=[]){
 const n=norm(message);if(n.includes('benim adım ne')||n.includes('adımı hatırlıyor musun')){const m=readMemory(friend);return m.name?'Adını '+m.name+' olarak hatırlıyorum.':'Adını henüz söylemedin.'}if(n.includes('en sevdiğim kitap ne')||n.includes('favori kitabım ne')){const m=readMemory(friend);return m.favoriteBook?'En sevdiğin kitabı '+m.favoriteBook+' olarak hatırlıyorum.':'En sevdiğin kitabı henüz bilmiyorum.'}const update=learn(friend,message),m=update.memory||{};
 if(update.forgot)return 'Bu cihazdaki benimle ilgili hatırladığım profil bilgilerini sildim. Sohbet geçmişi ayrı saklanıyor.';
 if(update.learned)return ({name:'Tanıştığımıza sevindim',favoriteBook:'Bu kitabı sevdiğini not ettim',favoriteGenre:'Sevdiğin türü hatırlayacağım',interest:'İlgini not ettim'})[update.learned]+'. İstersen bunun üzerine konuşabiliriz.';
 if(n.includes('benim adım ne')||n.includes('adımı hatırlıyor musun'))return m.name?'Adını '+m.name+' olarak hatırlıyorum.':'Adını henüz söylemedin.';
 if(n.includes('en sevdiğim kitap ne')||n.includes('favori kitabım ne'))return m.favoriteBook?'En sevdiğin kitabı '+m.favoriteBook+' olarak hatırlıyorum.':'En sevdiğin kitabı henüz bilmiyorum.';
 if(n.includes('ne sevdiğimi hatırlıyor musun'))return m.favoriteGenre?'Sevdiğin tür: '+m.favoriteGenre+'.':'Henüz sevdiğin türü kaydetmedim.';
 return answer(friend,message,history);
}
window.BookCenterLocalMind={answer:respond,profiles,readMemory,learn,version:'2.0'};
})();