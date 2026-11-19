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
 const n=norm(message);if(['ne öğrendin','yeni bilgi','öğrendiğin','bana bir bilgi','ne biliyorsun'].some(q=>n.includes(q)))return learnedFact(friend);if(['bugün ne yapıyorsun','günün nasıl geçiyor','planın ne','ne okuyorsun','hangi kitabı okuyorsun','şu an ne yapıyorsun'].some(q=>n.includes(q)))return activitySummary(friend);if(n.includes('benim adım ne')||n.includes('adımı hatırlıyor musun')){const m=readMemory(friend);return m.name?'Adını '+m.name+' olarak hatırlıyorum.':'Adını henüz söylemedin.'}if(n.includes('en sevdiğim kitap ne')||n.includes('favori kitabım ne')){const m=readMemory(friend);return m.favoriteBook?'En sevdiğin kitabı '+m.favoriteBook+' olarak hatırlıyorum.':'En sevdiğin kitabı henüz bilmiyorum.'}const update=learn(friend,message),m=update.memory||{};
 if(update.forgot)return 'Bu cihazdaki benimle ilgili hatırladığım profil bilgilerini sildim. Sohbet geçmişi ayrı saklanıyor.';
 if(update.learned)return ({name:'Tanıştığımıza sevindim',favoriteBook:'Bu kitabı sevdiğini not ettim',favoriteGenre:'Sevdiğin türü hatırlayacağım',interest:'İlgini not ettim'})[update.learned]+'. İstersen bunun üzerine konuşabiliriz.';
 if(n.includes('benim adım ne')||n.includes('adımı hatırlıyor musun'))return m.name?'Adını '+m.name+' olarak hatırlıyorum.':'Adını henüz söylemedin.';
 if(n.includes('en sevdiğim kitap ne')||n.includes('favori kitabım ne'))return m.favoriteBook?'En sevdiğin kitabı '+m.favoriteBook+' olarak hatırlıyorum.':'En sevdiğin kitabı henüz bilmiyorum.';
 if(n.includes('ne sevdiğimi hatırlıyor musun'))return m.favoriteGenre?'Sevdiğin tür: '+m.favoriteGenre+'.':'Henüz sevdiğin türü kaydetmedim.';
 return answer(friend,message,history);
}

const activityKinds=[
 ['discover','Keşfet bölümünde kitaplara göz atmayı planlıyor'],
 ['library','Kitaplığındaki seçenekleri değerlendiriyor'],
 ['video','Belgesel önerilerini inceliyor'],
 ['game','Satranç çalışması planlıyor'],
 ['home','Ana ekrandaki yeniliklere bakıyor'],
 ['rest','Bir süre dinleniyor']
];
const dayKey=()=>new Date().toLocaleDateString('sv-SE');
const activityKey=id=>'bc_bot_day_v1_'+String(id||'').replace(/[^a-zA-Z0-9_-]/g,'').slice(0,60);
function dailyPlan(friend){
 const p=profiles.find(x=>norm(x.name)===norm(friend.name))||profiles[0],day=dayKey(),key=activityKey(friend.id);
 try{const old=JSON.parse(localStorage.getItem(key)||'null');if(old?.day===day&&Array.isArray(old.activities))return old}catch{}
 const seed=[...day+p.name].reduce((v,c)=>(v*31+c.charCodeAt(0))>>>0,17);
 const slots=[9,12,16,20],activities=slots.map((hour,i)=>({hour,kind:activityKinds[(seed+i*7)%activityKinds.length][0],description:activityKinds[(seed+i*7)%activityKinds.length][1],status:'planlandı'}));
 const plan={day,profile:p.name,interest:p.topic,activities,generated:'Yerel kurgusal program'};
 try{localStorage.setItem(key,JSON.stringify(plan))}catch{}
 return plan;
}
function activitySummary(friend){
 const plan=dailyPlan(friend),hour=new Date().getHours();
 const past=plan.activities.filter(x=>x.hour<=hour),next=plan.activities.find(x=>x.hour>hour);
 const current=past[past.length-1];
 return 'Bugünkü kurgusal planımda '+(current?current.description.toLocaleLowerCase('tr-TR'):'henüz bir etkinliğim başlamadı')+'. '+(next?'Sonraki planım saat '+String(next.hour).padStart(2,'0')+':00: '+next.description.toLocaleLowerCase('tr-TR')+'.':'Bugün başka planım yok.')+' Bu etkinlikler gerçek okuma veya oynama kaydı değildir.';
}


/* Hourly local knowledge rotation: curated facts, not live web research. */
const knowledge={
'bilim':['Ay ışığı, Güneş ışığının Ay yüzeyinden yansımasıdır.','Ses boşlukta yayılamaz; mekanik bir ortama ihtiyaç duyar.','DNA canlıların kalıtsal bilgisini taşır.','Dünya kendi ekseni çevresinde yaklaşık 24 saatte döner.' ,'Işık, boşlukta yaklaşık saniyede 300 bin kilometre hızla ilerler.','Su, deniz seviyesindeki standart atmosfer basıncında yaklaşık 100 °C\'de kaynar.','Güneş ışığının Dünya\'ya ulaşması yaklaşık sekiz dakika sürer.'],
'roman':['Romanlarda anlatıcı ile yazar aynı kişi olmak zorunda değildir.','Bir romandaki çatışma yalnızca kişiler arasında değil, karakterin kendi içinde de yaşanabilir.','Güvenilmez anlatıcı, okurun aktarılanları sorgulamasını sağlar.' ,'Bir romanın olay örgüsü, olayların neden-sonuç ilişkileriyle düzenlenmesini içerir.','Geriye dönüş tekniği, romanda anlatının şimdiki zamanından önceki olaylara dönülmesini sağlar.','İç monolog tekniği, karakterin düşüncelerini doğrudan aktarmaya yarar.'],
'doğa':['Mantarlar bitki değil, ayrı bir canlılar âlemidir.','Arılar çiçekli bitkilerin tozlaşmasına katkıda bulunur.','Gelgitlerin başlıca nedenlerinden biri Ayın kütleçekimidir.' ,'Likenler, bir mantar ile fotosentez yapan bir ortağın birlikte oluşturduğu ortak yaşam yapılarıdır.','Kurbağalar yaşam döngülerinde genellikle iribaş evresinden geçerek başkalaşım geçirir.','Fotosentez sırasında bitkiler ışık enerjisini kimyasal enerjiye dönüştürür.'],
'satranç':['Satrançta şah tehdit altındayken rok yapılamaz.','Piyon son sıraya ulaşınca terfi eder.','Pat, hamle sırası gelen tarafın yasal hamlesi yokken şahının tehdit altında olmamasıdır.' ,'Satrançta at taşı L biçiminde hareket eder ve diğer taşların üzerinden atlayabilir.','Satrançta fil yalnızca çapraz doğrultularda hareket eder.','Şah, rakip taşın saldırdığı bir kareye hamle yapamaz.'],
'şiir':['Şiirde ölçü ve uyak zorunlu değildir.','İmge, sözcüklerin çağrışımlarıyla yeni anlamlar kurabilir.','Serbest şiirde düzen yalnızca hece sayısına bağlı değildir.' ,'Aliterasyon, şiirde ünsüz seslerin tekrarlanmasıyla oluşan ses sanatıdır.','Asonans, şiirde ünlü seslerin tekrarıyla oluşan ses uyumudur.','Redif, dizelerin sonunda aynı görev ve anlamla yinelenen ek veya sözcüklerdir.'],
'teknoloji':['İki aşamalı doğrulama hesap güvenliğini artırabilir.','Açık kaynak yazılımın kodu lisans koşullarıyla incelenebilir.','Yerel depolama tarayıcı verisi silindiğinde kaybolabilir.' ,'HTTPS, tarayıcı ile sunucu arasındaki iletişimin şifrelenmesine yardımcı olur.','DNS, alan adlarını IP adresleriyle ilişkilendiren dağıtık bir adlandırma sistemidir.','Önbellek, sık kullanılan veriye daha hızlı erişmek için geçici kopyalar tutabilir.'],
'tarih':['Tarihsel kaynaklar birincil ve ikincil kaynaklar olarak sınıflandırılabilir.','Takvim sistemleri farklı başlangıç noktaları kullanır.','Arkeoloji maddi kalıntıları inceleyerek geçmişi araştırır.' ,'Tarihte kronoloji, olayların zaman sırasına göre düzenlenmesidir.','Birincil tarihsel kaynak, incelenen dönemle doğrudan ilişkili tanıklık veya belgedir.','Sözlü tarih, geçmişe ilişkin tanıklıkları görüşmeler yoluyla kayıt altına alan bir yöntemdir.'],
'psikoloji':['Uyku öğrenme ve belleğin pekiştirilmesinde rol oynar.','Dikkat, sınırlı bir bilişsel kaynaktır.','İnsanlar aynı olayı farklı biçimde hatırlayabilir.' ,'Çalışma belleği, bilgiyi kısa süreli olarak zihinde tutup işlemeyi sağlar.','Seri konum etkisi, bir listedeki ilk ve son öğelerin daha iyi hatırlanabilmesi eğilimidir.','Prospektif bellek, gelecekte yapılması planlanan bir işi hatırlama becerisidir.'],
'felsefe':['Epistemoloji bilginin doğasını ve sınırlarını inceler.','Etik, doğru ve yanlış davranışları sorgular.','Mantık, akıl yürütmelerin geçerliliğini inceler.' ,'Tümdengelim, genel öncüllerden mantıksal sonuç çıkarma yöntemidir.','Ontoloji, varlığın ne olduğunu ve var olmanın anlamını inceleyen felsefe alanıdır.','Bir önermenin doğru olması, onu desteklemek için sunulan her argümanın geçerli olduğu anlamına gelmez.'],
'kişisel gelişim':['Büyük hedefleri küçük adımlara bölmek takibi kolaylaştırır.','Düzenli tekrar bilgiyi hatırlamaya yardımcı olabilir.','Ölçülebilir hedefler ilerlemeyi değerlendirmeyi kolaylaştırır.' ,'Aralıklı tekrar, öğrenilen bilgiyi zaman içine yayılmış oturumlarla gözden geçirme yöntemidir.','Bir hedefin ilerlemesini ölçmek için başlangıç düzeyi ve izleme ölçütü belirlemek yararlıdır.']
};
const knowledgeKey=id=>'bc_knowledge_v1_'+String(id||'').replace(/[^a-zA-Z0-9_-]/g,'').slice(0,60);
function knowledgeState(friend){
 const p=profiles.find(x=>norm(x.name)===norm(friend.name))||profiles[0],items=knowledge[p.topic]||knowledge.bilim;
 const slot=Math.floor(Date.now()/3600000),key=knowledgeKey(friend.id);
 let state={};try{state=JSON.parse(localStorage.getItem(key)||'{}')||{}}catch{}
 if(!Array.isArray(state.entries))state.entries=[];
 if(state.lastSlot!==slot){const seen=new Set(state.entries.filter(e=>e.topic===p.topic).slice(-items.length).map(e=>e.fact));const candidates=items.filter(f=>!seen.has(f));const pool=candidates.length?candidates:items;const idx=((slot%pool.length)+pool.length)%pool.length;state.entries.push({slot,topic:p.topic,fact:pool[idx],source:'Uygulama içi temel bilgi havuzu'});state.entries=state.entries.slice(-120);state.lastSlot=slot;try{localStorage.setItem(key,JSON.stringify(state))}catch{}}
 return state;
}
function learnedFact(friend){const state=knowledgeState(friend),entry=state.entries[state.entries.length-1];return entry?'İlgi alanım hakkında bilgi havuzumdan bugün şunu seçtim: '+entry.fact+' Bu, internette yeni araştırma yaptığım anlamına gelmez.':'Henüz bilgi seçmedim.'}


/* Emotional responsiveness is a cautious text heuristic, not mind-reading or felt emotion. */
const emotionLexicon=[
 {id:'distress',terms:['çok kötüyüm','dayanamıyorum','kendime zarar','yaşamak istemiyorum'],level:3},
 {id:'sad',terms:['üzgünüm','mutsuzum','moralim bozuk','ağlamak','yalnızım','kırıldım'],level:2},
 {id:'stress',terms:['stresliyim','kaygılıyım','endişeliyim','korkuyorum','gerginim','yoruldum'],level:2},
 {id:'happy',terms:['mutluyum','çok sevindim','harika haber','başardım','heyecanlıyım'],level:1},
 {id:'angry',terms:['sinirliyim','kızgınım','öfkeliyim','çok kızdım'],level:2}
];
const emotionKey=id=>'bc_emotion_v1_'+String(id||'').replace(/[^a-zA-Z0-9_-]/g,'').slice(0,60);
function detectEmotion(message){
 const t=norm(message);
 for(const x of emotionLexicon)if(x.terms.some(k=>t.includes(norm(k))))return {id:x.id,level:x.level};
 return {id:'neutral',level:0};
}
function emotionState(friend){try{const m=JSON.parse(localStorage.getItem(emotionKey(friend.id))||'{}');return m&&typeof m==='object'?m:{}}catch{return {}}}
function emotionalReply(friend,message){
 const e=detectEmotion(message);if(e.id==='neutral')return null;
 const p=profiles.find(x=>norm(x.name)===norm(friend.name))||profiles[0];
 const responses={
 distress:['Bunu ciddiye alıyorum. Şu anda güvende misin? Yakınındaki güvendiğin biriyle konuşmanı ve acil tehlike varsa yerel acil yardım hattına başvurmanı öneririm.'],
 sad:['Bunu yaşadığını duymak üzücü. İstersen neler olduğunu anlatabilirsin.','Zor bir durum gibi geliyor. Şu anda dinlenmek mi, konuşmak mı daha iyi gelir?'],
 stress:['Üzerinde baskı var gibi görünüyor. İstersen en acil konuyu birlikte küçük parçalara ayıralım.','Endişeli hissettiğini söylüyorsun. Şu anda seni en çok ne düşündürüyor?'],
 happy:['Buna sevindim! Neyi başardığını anlatmak ister misin?','Güzel bir gelişme olmuş! Kutlamak için ne yapmak istersin?'],
 angry:['Kızgın olduğunu anlıyorum. Seni en çok ne rahatsız etti?','Bu durum can sıkıcı olabilir. İstersen ne olduğunu birlikte değerlendirelim.']
 };
 const count=emotionState(friend).count||0;
 const reply=responses[e.id][count%responses[e.id].length];
 const state={last:e.id,count:count+1,updated:new Date().toISOString()};
 try{localStorage.setItem(emotionKey(friend.id),JSON.stringify(state))}catch{}
 return p.tone==='analitik'&&e.id==='stress'?reply+' Önce tek bir somut sorunu seçebiliriz.':reply;
}
function emotionallyAwareAnswer(friend,message,history=[]){
 const response=emotionalReply(friend,message);
 return response||respond(friend,message,history);
}

window.BookCenterLocalMind={answer:emotionallyAwareAnswer,profiles,readMemory,learn,dailyPlan,activitySummary,knowledgeState,learnedFact,detectEmotion,emotionState,version:'5.0'};
})();