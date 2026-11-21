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
 if(n.includes('beni unut')||n.includes('hafızanı sil')||n.includes('bilgilerimi sil')||n.includes('profil hafızamı temizle')){try{localStorage.removeItem(memoryKey(friend.id))}catch{}return {forgot:true}}
 if(learned){m.updated=new Date().toISOString();try{localStorage.setItem(memoryKey(friend.id),JSON.stringify(m))}catch{}}
 return {learned,memory:m};
}
function respond(friend,message,history=[]){
 const n=norm(message);if(n.includes('beni unut')||n.includes('hafızanı sil')||n.includes('bilgilerimi sil')||n.includes('profil hafızamı temizle')){try{localStorage.removeItem(memoryKey(friend.id))}catch{}return 'Bu cihazdaki benimle ilgili profil hafızasını sildim. Sohbet geçmişi ayrı saklanıyor.';}if(n.includes('hafızamda ne var')||n.includes('benim hakkımda ne biliyorsun')||n.includes('hangi bilgilerimi hatırlıyorsun')){const m=readMemory(friend),fields=[['name','Ad'],['favoriteBook','Favori kitap'],['favoriteGenre','Favori tür'],['interest','İlgi alanı']].filter(([key])=>typeof m[key]==='string'&&m[key].trim());return fields.length?'Bu cihazda benimle paylaştığın profil bilgileri: '+fields.map(([key,label])=>label+': '+m[key]).join('; ')+'. Silmek için "hafızanı sil" yazabilirsin.':'Bu cihazda seninle ilgili kayıtlı profil tercihi bulamadım.';}if(['ne öğrendin','yeni bilgi','öğrendiğin','bana bir bilgi','ne biliyorsun'].some(q=>n.includes(q)))return learnedFact(friend);if(['bugün ne yapıyorsun','günün nasıl geçiyor','planın ne','ne okuyorsun','hangi kitabı okuyorsun','şu an ne yapıyorsun'].some(q=>n.includes(q)))return activitySummary(friend);if(n.includes('benim adım ne')||n.includes('adımı hatırlıyor musun')){const m=readMemory(friend);return m.name?'Adını '+m.name+' olarak hatırlıyorum.':'Adını henüz söylemedin.'}if(n.includes('en sevdiğim tür ne')||n.includes('favori türüm ne')){const m=readMemory(friend);return m.favoriteGenre?'Sevdiğin türü '+m.favoriteGenre+' olarak hatırlıyorum.':'En sevdiğin türü henüz söylemedin.'}if(n.includes('ilgimi hatırlıyor musun')||n.includes('neye ilgi duyuyorum')){const m=readMemory(friend);return m.interest?'İlgilendiğin konu: '+m.interest+'.':'İlgi alanını henüz kaydetmedim.'}if(n.includes('en sevdiğim kitap ne')||n.includes('favori kitabım ne')){const m=readMemory(friend);return m.favoriteBook?'En sevdiğin kitabı '+m.favoriteBook+' olarak hatırlıyorum.':'En sevdiğin kitabı henüz bilmiyorum.'}const update=learn(friend,message),m=update.memory||{};
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
'bilim':['Bir protonun elektrik yükü pozitiftir ve büyüklüğü elektronun yükünün mutlak değerine eşittir.','Atmosferdeki azot gazı, kuru havanın hacimce yaklaşık yüzde 78’ini oluşturur.','Ay ışığı, Güneş ışığının Ay yüzeyinden yansımasıdır.','Ses boşlukta yayılamaz; mekanik bir ortama ihtiyaç duyar.','DNA canlıların kalıtsal bilgisini taşır.','Dünya kendi ekseni çevresinde yaklaşık 24 saatte döner.' ,'Işık, boşlukta yaklaşık saniyede 300 bin kilometre hızla ilerler.','Su, deniz seviyesindeki standart atmosfer basıncında yaklaşık 100 °C\'de kaynar.','Güneş ışığının Dünya\'ya ulaşması yaklaşık sekiz dakika sürer.','Dünya\'nın Güneş çevresindeki bir dolanımı yaklaşık 365,25 gün sürer.','Bir ışık yılı zaman değil, ışığın boşlukta bir yılda aldığı uzaklık birimidir.','Bir tutulma sırasında Ay, Güneş ile Dünya arasına girerse Güneş tutulması gerçekleşebilir.','Gökkuşağı, ışığın su damlacıklarında kırılması, yansıması ve renklerine ayrılmasıyla oluşabilir.'],
'roman':['Analepsis, anlatının mevcut zaman çizgisinden daha önce gerçekleşmiş olaylara dönmesidir.','Serim bölümü, anlatıda kişilerin ve başlangıç koşullarının tanıtılmasına yardımcı olur.','Romanlarda anlatıcı ile yazar aynı kişi olmak zorunda değildir.','Bir romandaki çatışma yalnızca kişiler arasında değil, karakterin kendi içinde de yaşanabilir.','Güvenilmez anlatıcı, okurun aktarılanları sorgulamasını sağlar.' ,'Bir romanın olay örgüsü, olayların neden-sonuç ilişkileriyle düzenlenmesini içerir.','Geriye dönüş tekniği, romanda anlatının şimdiki zamanından önceki olaylara dönülmesini sağlar.','İç monolog tekniği, karakterin düşüncelerini doğrudan aktarmaya yarar.','Öyküleme, olayları zaman içinde gelişen bir anlatı olarak sunma tekniğidir.','Betimleme, anlatıda kişi, mekân veya nesnenin özelliklerini okurun zihninde canlandırmaya yarar.','Olay örgüsünün kronolojik anlatılması zorunlu değildir; yazar zaman sırasını değiştirebilir.','Üçüncü tekil şahıs anlatıcı, olayları karakterlerden biri olmak zorunda kalmadan aktarabilir.'],
'doğa':['Deniz kestaneleri derisi dikenliler grubundadır ve yetişkinlerinde çoğunlukla beşli radyal simetri görülür.','Kurbağalar yaşam döngülerinde genellikle iribaş evresinden geçer.','Mantarlar bitki değil, ayrı bir canlılar âlemidir.','Arılar çiçekli bitkilerin tozlaşmasına katkıda bulunur.','Gelgitlerin başlıca nedenlerinden biri Ayın kütleçekimidir.' ,'Likenler, bir mantar ile fotosentez yapan bir ortağın birlikte oluşturduğu ortak yaşam yapılarıdır.','Kurbağalar yaşam döngülerinde genellikle iribaş evresinden geçerek başkalaşım geçirir.','Fotosentez sırasında bitkiler ışık enerjisini kimyasal enerjiye dönüştürür.','Yapraklardaki stomalar gaz alışverişinde ve su buharı kaybında rol oynar.','Toprak solucanlarının açtığı tüneller toprağın havalanmasına katkı sağlar.','Kelebekler tam başkalaşım geçirir; yumurta, larva, pupa ve ergin evreleri bulunur.','Mercanlar bitki değil, knidliler şubesine ait hayvanlardır.'],
'satranç':['Satrançta iki şah birbirine komşu karelerde bulunamaz.','Satrançta pat, sırası gelen oyuncunun yasal hamlesi yokken şahının tehdit altında olmamasıdır.','Satrançta şah tehdit altındayken rok yapılamaz.','Piyon son sıraya ulaşınca terfi eder.','Pat, hamle sırası gelen tarafın yasal hamlesi yokken şahının tehdit altında olmamasıdır.' ,'Satrançta at taşı L biçiminde hareket eder ve diğer taşların üzerinden atlayabilir.','Satrançta fil yalnızca çapraz doğrultularda hareket eder.','Şah, rakip taşın saldırdığı bir kareye hamle yapamaz.','Satrançta vezir yatay, dikey ve çapraz doğrultularda hareket edebilir.','Satrançta at, diğer taşların üzerinden atlayabilen tek standart taştır.','Satrançta rok, aynı hamlede şah ile kalenin yer değiştirmesini içeren özel bir hamledir.','Geçerken alma, piyonun belirli koşullarda rakip piyonu çapraz almasını sağlayan özel hamledir.'],
'şiir':['Tuyuğ, Türk edebiyatında dört dizeli ve genellikle aruzla yazılan bir nazım biçimidir.','Asonans, bir metinde ünlü seslerin tekrarlanmasıyla oluşan ses uyumudur.','Şiirde ölçü ve uyak zorunlu değildir.','İmge, sözcüklerin çağrışımlarıyla yeni anlamlar kurabilir.','Serbest şiirde düzen yalnızca hece sayısına bağlı değildir.' ,'Aliterasyon, şiirde ünsüz seslerin tekrarlanmasıyla oluşan ses sanatıdır.','Asonans, şiirde ünlü seslerin tekrarıyla oluşan ses uyumudur.','Redif, dizelerin sonunda aynı görev ve anlamla yinelenen ek veya sözcüklerdir.','Enjambman, bir şiir dizesinde başlayan cümlenin sonraki dizeye taşmasıdır.','Aliterasyon, şiirde aynı ünsüz seslerin tekrarlanmasıyla oluşan ses uyumudur.','Haiku, geleneksel Japon şiirinde çoğunlukla üç kısa dizeden oluşan bir biçimdir.','Teşbih, iki varlık veya kavram arasında benzerlik ilişkisi kuran söz sanatıdır.'],
'teknoloji':['HTTP 405 yanıt kodu, istenen HTTP yönteminin ilgili kaynak için izinli olmadığını belirtir.','DNS, alan adlarının IP adresleriyle eşleştirilmesinde kullanılan bir adlandırma sistemidir.','İki aşamalı doğrulama hesap güvenliğini artırabilir.','Açık kaynak yazılımın kodu lisans koşullarıyla incelenebilir.','Yerel depolama tarayıcı verisi silindiğinde kaybolabilir.' ,'HTTPS, tarayıcı ile sunucu arasındaki iletişimin şifrelenmesine yardımcı olur.','DNS, alan adlarını IP adresleriyle ilişkilendiren dağıtık bir adlandırma sistemidir.','Önbellek, sık kullanılan veriye daha hızlı erişmek için geçici kopyalar tutabilir.','HTTP 404 durum kodu, istenen kaynağın bulunamadığını belirtir.','HTTPS, HTTP iletişimini TLS ile şifreleyerek aktarım sırasında koruma sağlar.','UTF-8, Unicode karakterlerini bir ile dört bayt arasında kodlayabilen değişken uzunluklu bir biçimdir.','JSON, veriyi anahtar-değer çiftleri ve diziler gibi yapılarla temsil eden metin tabanlı bir biçimdir.'],
'tarih':['Kodikoloji, el yazması kitapların fiziksel yapısını ve üretimini inceleyen disiplindir.','Kronoloji, olayların zaman sırasına göre düzenlenmesidir.','Tarihsel kaynaklar birincil ve ikincil kaynaklar olarak sınıflandırılabilir.','Takvim sistemleri farklı başlangıç noktaları kullanır.','Arkeoloji maddi kalıntıları inceleyerek geçmişi araştırır.' ,'Tarihte kronoloji, olayların zaman sırasına göre düzenlenmesidir.','Birincil tarihsel kaynak, incelenen dönemle doğrudan ilişkili tanıklık veya belgedir.','Sözlü tarih, geçmişe ilişkin tanıklıkları görüşmeler yoluyla kayıt altına alan bir yöntemdir.','Paleografi, eski yazı biçimlerini inceleyen bilim dalıdır.','Arkeoloji, geçmiş toplumların maddi kalıntılarını inceleyen bilim dalıdır.','Numizmatik, madeni paraları ve para tarihini inceleyen bilim dalıdır.','Karbon-14 tarihlemesi, organik kalıntıların yaşını tahmin etmek için kullanılan bir yöntemdir.'],
'psikoloji':['İşlemsel belleğe örnek olarak bisiklet sürme gibi öğrenilmiş motor beceriler verilebilir.','İleriye ket vurma, önce öğrenilen bilginin sonradan öğrenilecek bilgiyi zorlaştırabilmesidir.','Uyku öğrenme ve belleğin pekiştirilmesinde rol oynar.','Dikkat, sınırlı bir bilişsel kaynaktır.','İnsanlar aynı olayı farklı biçimde hatırlayabilir.' ,'Çalışma belleği, bilgiyi kısa süreli olarak zihinde tutup işlemeyi sağlar.','Seri konum etkisi, bir listedeki ilk ve son öğelerin daha iyi hatırlanabilmesi eğilimidir.','Prospektif bellek, gelecekte yapılması planlanan bir işi hatırlama becerisidir.','Seçici dikkat, bir uyaranı öne çıkarırken diğerlerini geri planda tutma sürecidir.','Çalışma belleği, bilgiyi kısa süreli tutup işlemeyi sağlayan bilişsel sistemdir.','Geri çağırma alıştırması, bilgiyi yalnızca yeniden okumak yerine bellekten hatırlamayı gerektirir.','Aralıklı öğrenme, çalışma oturumlarını zamana yayarak uzun süreli hatırlamayı destekleyebilir.'],
'felsefe':['Ontoloji, varlığın ne olduğunu ve var olanların temel kategorilerini inceleyen felsefe alanıdır.','Tümdengelim, öncüllerden mantıksal olarak sonuç çıkarma biçimidir.','Epistemoloji bilginin doğasını ve sınırlarını inceler.','Etik, doğru ve yanlış davranışları sorgular.','Mantık, akıl yürütmelerin geçerliliğini inceler.' ,'Tümdengelim, genel öncüllerden mantıksal sonuç çıkarma yöntemidir.','Ontoloji, varlığın ne olduğunu ve var olmanın anlamını inceleyen felsefe alanıdır.','Bir önermenin doğru olması, onu desteklemek için sunulan her argümanın geçerli olduğu anlamına gelmez.','Aksiyoloji, değerlerin doğasını inceleyen felsefe alanıdır.','Sofizm, ikna edici görünebilen fakat mantıksal açıdan kusurlu akıl yürütmeleri de kapsayan bir kavramdır.','Karşı örnek, evrensel bir iddiayı çürütmek için tek bir istisna göstermeye yarayabilir.','Etik ile hukuk aynı alan değildir; bir davranış yasal olsa da etik açıdan tartışılabilir.'],
'kişisel gelişim':['Bir görevin bitiş ölçütünü önceden tanımlamak, tamamlanıp tamamlanmadığını nesnel biçimde değerlendirmeyi kolaylaştırır.','Bir kontrol listesi, çok adımlı bir işte tamamlanan aşamaları görünür kılar.','Büyük hedefleri küçük adımlara bölmek takibi kolaylaştırır.','Düzenli tekrar bilgiyi hatırlamaya yardımcı olabilir.','Ölçülebilir hedefler ilerlemeyi değerlendirmeyi kolaylaştırır.' ,'Aralıklı tekrar, öğrenilen bilgiyi zaman içine yayılmış oturumlarla gözden geçirme yöntemidir.','Bir hedefin ilerlemesini ölçmek için başlangıç düzeyi ve izleme ölçütü belirlemek yararlıdır.','Bir alışkanlığı takip etmek, uygulama sıklığını görünür kılar.','Uygulama niyeti, bir hedef için ne zaman ve nerede harekete geçileceğini önceden belirleme yöntemidir.','Bir görev için önceden belirlenen kısa bir başlama saati, işe koyulmayı kolaylaştırabilir.']
};

/* Verified offline Turkish knowledge additions. No user data or external requests. */
knowledge["bilim"].push("Ay, Dünya çevresindeki dolanımını yaklaşık 27,3 günde tamamlar.");
knowledge["roman"].push("Geriye dönüş tekniği, anlatının şimdiki zamanından geçmişteki olaylara geçilmesidir.");
knowledge["doğa"].push("Likenler, bir mantar ile fotosentez yapan bir ortak arasında kurulan simbiyotik birlikteliklerdir.");
knowledge["satranç"].push("Satrançta piyon ilk hamlesinde, önündeki kareler boşsa iki kare ilerleyebilir.");
knowledge["şiir"].push("Serbest ölçüde dizelerin belirli bir hece veya aruz kalıbına uyması zorunlu değildir.");
knowledge["teknoloji"].push("HTTP 301 durum kodu, kaynağın kalıcı olarak başka bir adrese taşındığını belirtir.");
knowledge["tarih"].push("Epigrafi, taş ve metal gibi yüzeylere yazılmış tarihî yazıtları inceler.");
knowledge["psikoloji"].push("İşlemsel bellekte bilgi, yapılan işlemler sırasında geçici olarak tutulup işlenir.");
knowledge["felsefe"].push("Epistemoloji, bilginin kaynağını, kapsamını ve gerekçelendirilmesini inceler.");
knowledge["kişisel gelişim"].push("Geriye dönük değerlendirme, tamamlanan bir çalışmada neyin iyi gittiğini ve neyin geliştirilebileceğini incelemektir.");

/* Distinct curated facts for all ten fictional bot interests. */
knowledge["bilim"].push("Venüs, Güneş Sistemi'ndeki gezegenler arasında yüzey sıcaklığı en yüksek olanıdır.");
knowledge["roman"].push("Çerçeve anlatı, başka bir hikâyeyi içine alan üst anlatı yapısıdır.");
knowledge["doğa"].push("Ahtapotların üç kalbi vardır.");
knowledge["satranç"].push("Satrançta piyonlar geriye doğru hareket edemez.");
knowledge["şiir"].push("Epifora, art arda gelen söz veya dizelerin sonunda aynı ifadenin yinelenmesidir.");
knowledge["teknoloji"].push("HTTP 503 durum kodu, sunucunun isteği geçici olarak karşılayamadığını belirtir.");
knowledge["tarih"].push("Dendrokronoloji, ağaçların yıllık büyüme halkalarından yararlanarak tarihleme yapar.");
knowledge["psikoloji"].push("İleriye dönük bellek, gelecekte yapılması planlanan bir eylemi hatırlamayı sağlar.");
knowledge["felsefe"].push("Bir argümanın geçerli olması, öncülleri doğruysa sonucunun yanlış olamaması demektir.");
knowledge["kişisel gelişim"].push("Pomodoro tekniğinde çalışma, kısa odaklanma aralıkları ve molalar halinde düzenlenir.");
/* Curated offline knowledge expansion. */
knowledge["bilim"].push("Jüpiter, Güneş Sistemi'nin en büyük gezegenidir.");
knowledge["roman"].push("Leitmotif, bir anlatıda tekrarlanarak anlam kazanan motif veya izlek öğesidir.");
knowledge["doğa"].push("Yarasalarda aktif uçuş, ön üyelerin kanada dönüşmesiyle gerçekleşir.");
knowledge["satranç"].push("Satrançta şah mat olduğunda oyun sona erer; mat edilen taraf kaybeder.");
knowledge["şiir"].push("Akrostişte dizelerin ilk harfleri bir sözcük veya ifade oluşturabilir.");
knowledge["teknoloji"].push("HTTP 429 durum kodu, istemcinin belirli bir sürede çok fazla istek gönderdiğini belirtir.");
knowledge["tarih"].push("Herodot, Antik Yunan tarih yazıcılığının önemli isimlerinden biridir.");
knowledge["psikoloji"].push("Klasik koşullanma, başlangıçta nötr bir uyaranın başka bir uyaranla eşleşerek öğrenilmiş tepki oluşturabilmesidir.");
knowledge["felsefe"].push("Bir argümanda öncüller, sonucu desteklemek için sunulan önermelerdir.");
knowledge["kişisel gelişim"].push("SMART hedef yaklaşımında hedeflerin belirli, ölçülebilir, ulaşılabilir, ilgili ve zamana bağlı olması amaçlanır.");
/* Offline facts, 2026-11-20. Fictional bot interests; no personal data. */
knowledge["bilim"].push("Satürn'ün ortalama yoğunluğu sudan düşüktür; bu, gezegenin dev bir su kütlesinde gerçekten yüzebileceği anlamına gelmez.");
knowledge["roman"].push("Epistolary roman, olayları mektup veya benzeri yazışma belgeleri üzerinden anlatan roman türüdür.");
knowledge["doğa"].push("Deniz yıldızlarının çoğu türünde merkezi bir beyin yerine sinir halkası ve kollara uzanan sinirler bulunur.");
knowledge["satranç"].push("Satrançta fil, oyuna başladığı karenin rengindeki karelerde kalır.");
knowledge["şiir"].push("Kinaye, bir sözün hem gerçek hem mecaz anlamını düşündürerek mecaz anlamını öne çıkaran anlatım yoludur.");
knowledge["teknoloji"].push("HTTP 204 yanıtı, isteğin başarıyla işlendiğini ancak yanıtta içerik gövdesi bulunmadığını belirtir.");
knowledge["tarih"].push("Stratigrafi, arkeolojik tabakaların sırasını ve birbirleriyle ilişkilerini incelemeye yardımcı olur.");
knowledge["psikoloji"].push("Bilişsel çarpıtma, olayların değerlendirilmesinde sistematik ve yanıltıcı düşünce kalıplarını ifade eder.");
knowledge["felsefe"].push("Tümevarımda tekil gözlemlerden daha genel bir sonuca ulaşılır; sonuç mantıksal olarak zorunlu değildir.");
knowledge["kişisel gelişim"].push("Kanban panosu, işleri yapılacak, sürüyor ve tamamlandı gibi aşamalarda görselleştirmeye yarar.");

/* Offline curated facts. No conversation data or external APIs. */
knowledge["bilim"].push("Mars'ın bir günü yaklaşık 24 saat 39 dakika sürer.");
knowledge["roman"].push("Bilinç akışı tekniği, karakterin zihninden geçen düşünce ve çağrışımları kesintili biçimde yansıtabilir.");
knowledge["doğa"].push("Penguenler kuştur; kanatlarını uçmak yerine suda yüzmek için kullanırlar.");
knowledge["satranç"].push("Satrançta üç kez aynı konumun oluşması, kurallar uyarınca beraberlik talebine olanak sağlayabilir.");
knowledge["şiir"].push("Hece ölçüsü, dizelerdeki hece sayılarının belirli bir düzende kullanılmasına dayanır.");
knowledge["teknoloji"].push("HTTP 201 durum kodu, isteğin sonucunda yeni bir kaynağın oluşturulduğunu belirtir.");
knowledge["tarih"].push("Tarihsel belgelerin özgünlüğünü ve güvenilirliğini sorgulama sürecine kaynak eleştirisi denir.");
knowledge["psikoloji"].push("Hatırlama sırasında bağlam ipuçları, öğrenilmiş bilginin geri çağrılmasını kolaylaştırabilir.");
knowledge["felsefe"].push("Bir önermenin değili, önerme doğruyken yanlış; yanlışken doğrudur.");
knowledge["kişisel gelişim"].push("Bir görevin tamamlanma ölçütünü önceden belirlemek, ilerlemenin değerlendirilmesini kolaylaştırır.");

/* Offline curated knowledge. 2026-11-20. */
knowledge["bilim"].push("Güneş sistemindeki en büyük uydu, Jüpiter'in Ganymede uydusudur.");
knowledge["roman"].push("Epistolar roman, öyküsünü mektup veya benzeri yazılı belgeler üzerinden kurabilir.");
knowledge["doğa"].push("Deniz kaplumbağaları akciğerleriyle solunum yapar ve nefes almak için su yüzeyine çıkar.");
knowledge["satranç"].push("Satrançta şahlar birbirine bitişik karelerde bulunamaz.");
knowledge["şiir"].push("Dize, şiirin satırlarından her biridir.");
knowledge["teknoloji"].push("HTTP 403 durum kodu, sunucunun isteği anladığı ancak erişime izin vermediği anlamına gelir.");
knowledge["tarih"].push("Tarih yazımında anakronizm, bir olayın veya kavramın ait olmadığı döneme yerleştirilmesidir.");
knowledge["psikoloji"].push("İşlemsel koşullanma, davranışın sonuçlarının gelecekteki görülme sıklığını etkileyebildiği öğrenme biçimidir.");
knowledge["felsefe"].push("Bir argümanın geçerli olması, öncüllerinin mutlaka doğru olduğu anlamına gelmez.");
knowledge["kişisel gelişim"].push("Bir görevin bitiş koşulunu önceden yazmak, tamamlanıp tamamlanmadığını değerlendirmeyi kolaylaştırır.");

/* Curated offline facts; no user data. */
knowledge["bilim"].push("Merkür'ün Güneş çevresindeki bir dolanımı yaklaşık 88 Dünya günü sürer.");
knowledge["roman"].push("Önseme, anlatıda ileride yaşanacak olaylara ilişkin ipuçları verilmesidir.");
knowledge["doğa"].push("Denizatlarında çoğu türde yumurtaları erkek bireyin kuluçka kesesi taşır.");
knowledge["satranç"].push("Satrançta vezir başlangıçta kendi rengindeki kareye yerleştirilir.");
knowledge["şiir"].push("Enjambman, bir dizede başlayan söz diziminin sonraki dizede sürmesidir.");
knowledge["teknoloji"].push("HTTP 304 yanıtı, koşullu istekte kaynağın değişmediğini ve önbellekteki sürümün kullanılabileceğini belirtir.");
knowledge["tarih"].push("Rosetta Taşı üzerindeki farklı yazılar, Mısır hiyerogliflerinin çözülmesinde önemli rol oynamıştır.");
knowledge["psikoloji"].push("Seri konum etkisi, bir listedeki ilk ve son öğelerin ortadakilere göre daha kolay hatırlanabilmesini ifade eder.");
knowledge["felsefe"].push("Bir argümanın sağlam olması, hem geçerli olması hem de öncüllerinin doğru olması demektir.");
knowledge["kişisel gelişim"].push("Eisenhower matrisi, görevleri önem ve aciliyet düzeylerine göre dört gruba ayırır.");
/* 2026-11-20 verified offline knowledge expansion. */
knowledge["bilim"].push("Neptün, Güneş çevresindeki bir turunu yaklaşık 165 Dünya yılında tamamlar.");
knowledge["roman"].push("Çoklu bakış açısı, aynı olayın farklı karakterlerin anlatımlarıyla sunulmasını sağlar.");
knowledge["doğa"].push("Yunuslar balıktır değil, akciğerleriyle solunum yapan memelilerdir.");
knowledge["satranç"].push("Satrançta at, bulunduğu karenin rengini her hamlede değiştirir.");
knowledge["şiir"].push("Redif, dizelerin sonunda aynı anlam ve görevle tekrarlanan ek ya da sözcüklerdir.");
knowledge["teknoloji"].push("HTTP 418 durum kodu, bir Nisan Şakası geleneğinden doğan mizahi bir yanıttır.");
knowledge["tarih"].push("Çivi yazısı, Mezopotamya'da kil tabletler üzerine işaretler basılarak kullanılmıştır.");
knowledge["psikoloji"].push("Yanlış anı, kişinin yaşanmamış veya farklı yaşanmış bir olayı olmuş gibi hatırlamasıdır.");
knowledge["felsefe"].push("Bir önermenin karşıtı ile çelişiği mantıkta aynı ilişkiyi ifade etmez.");
knowledge["kişisel gelişim"].push("Zaman kutulama, bir işe önceden belirlenmiş sınırlı bir zaman aralığı ayırma yöntemidir.");

/* 2026-11-20: offline curated facts; no personal data or external API. */
knowledge["bilim"].push("Uranüs'ün dönme ekseni yörünge düzlemine göre yaklaşık 98 derece eğiktir.");
knowledge["roman"].push("Metinlerarasılık, bir edebî eserin başka metinlerle açık veya örtük ilişkiler kurmasıdır.");
knowledge["doğa"].push("Ornitorenk, yumurtlayan memelilerden biridir.");
knowledge["satranç"].push("Satrançta bir oyuncu şahını tehdit altında bırakacak hamleyi yasal olarak yapamaz.");
knowledge["şiir"].push("İstiare, benzetmenin iki temel unsurundan yalnızca biriyle kurulan söz sanatıdır.");
knowledge["teknoloji"].push("HTTP 206 durum kodu, istenen kaynağın yalnızca bir bölümünün başarıyla gönderildiğini belirtir.");
knowledge["tarih"].push("Paleolitik Çağ, tarih öncesi dönemlerin Eski Taş Çağı olarak da adlandırılan bölümüdür.");
knowledge["psikoloji"].push("İleriye dönük bellek, gelecekte yapılması planlanan bir eylemi uygun zamanda hatırlamayı ifade eder.");
knowledge["felsefe"].push("Geçerli bir tümdengelimde öncüller doğruysa sonucun yanlış olması mümkün değildir.");
knowledge["kişisel gelişim"].push("Bir hedef için belirlenen ölçüt, ilerlemenin gözleme dayalı değerlendirilmesini kolaylaştırır.");
/* 2026-11-20: curated offline facts. No user conversations or remote APIs. */
knowledge["bilim"].push("Bir parsek, yaklaşık 3,26 ışık yılına eşit bir uzaklık birimidir.");
knowledge["roman"].push("Odaklanma, anlatıda olayların hangi karakterin algısı veya bilgisi üzerinden sunulduğunu ifade eder.");
knowledge["doğa"].push("Mangrov ağaçları, tuzlu veya acı su bulunan kıyı ekosistemlerinde yaşayabilen bitkilerdir.");
knowledge["satranç"].push("Satrançta rok yapabilmek için şah ile ilgili kale daha önce hareket etmemiş olmalıdır.");
knowledge["şiir"].push("Tunç uyakta, bir sözcük diğerinin sonunda bütünüyle yer alır.");
knowledge["teknoloji"].push("HTTP 202 durum kodu, isteğin işlenmek üzere kabul edildiğini ancak işlemenin tamamlanmadığını belirtir.");
knowledge["tarih"].push("Epigrafi, taş veya metal gibi dayanıklı yüzeylerdeki yazıtları inceleyen bilim dalıdır.");
knowledge["psikoloji"].push("Aralıklı tekrar, öğrenilen bilginin farklı zaman aralıklarında yeniden çalışılmasına dayanır.");
knowledge["felsefe"].push("Bir çıkarımın geçerliliği, öncüllerle sonuç arasındaki mantıksal ilişkiye bağlıdır; öncüllerin fiilen doğru olmasını gerektirmez.");
knowledge["kişisel gelişim"].push("Geri bildirim, yapılan işin sonuçları hakkında bilgi sağlayarak sonraki adımların düzenlenmesine yardımcı olur.");
const knowledgeKey=id=>'bc_knowledge_v1_'+String(id||'').replace(/[^a-zA-Z0-9_-]/g,'').slice(0,60);
function knowledgeState(friend){
 const p=profiles.find(x=>norm(x.name)===norm(friend.name))||profiles[0],rawItems=knowledge[p.topic]||knowledge.bilim;
 const seenFacts=new Set();const items=rawItems.filter(f=>{const key=norm(f);if(seenFacts.has(key))return false;seenFacts.add(key);return true});
 const slot=Math.floor(Date.now()/3600000),key=knowledgeKey(friend.id);
 let state={};try{state=JSON.parse(localStorage.getItem(key)||'{}')||{}}catch{}
 if(!Array.isArray(state.entries))state.entries=[];
 if(state.lastSlot!==slot){const seen=new Set(state.entries.filter(e=>e.topic===p.topic).slice(-items.length).map(e=>e.fact));const candidates=items.filter(f=>!seen.has(f));const lastFact=state.entries.filter(e=>e.topic===p.topic).slice(-1)[0]?.fact;const pool=candidates.length?candidates:(items.length>1?items.filter(f=>f!==lastFact):items);const idx=((slot%pool.length)+pool.length)%pool.length;state.entries.push({slot,topic:p.topic,fact:pool[idx],source:'Uygulama içi temel bilgi havuzu'});state.entries=state.entries.slice(-120);state.lastSlot=slot;try{localStorage.setItem(key,JSON.stringify(state))}catch{}}
 return state;
}

/* Curated offline facts. No personal or chat data. */
knowledge["bilim"].push("Bir astronomik birim, Dünya ile Güneş arasındaki ortalama uzaklığa yakın olan tam 149.597.870.700 metredir.");
knowledge["roman"].push("Anlatıda zaman atlaması, olaylar arasındaki bir dönemin ayrıntılı anlatılmadan geçilmesidir.");
knowledge["doğa"].push("Kutup ayılarının derisi siyaha yakın renktedir; kürk kılları ise pigment bakımından büyük ölçüde saydamdır.");
knowledge["satranç"].push("Satrançta bir oyuncunun şahı tehdit altındaysa bu duruma şah çekilmesi denir; oyuncu tehdidi gidermek zorundadır.");
knowledge["şiir"].push("Pastoral şiir, doğa ve kır yaşamını konu alan şiir türüdür.");
knowledge["teknoloji"].push("HTTP 410 durum kodu, istenen kaynağın artık mevcut olmadığını ve bu durumun kalıcı olmasının beklendiğini belirtir.");
knowledge["tarih"].push("Diplomatik, tarihî belgelerin biçimini, özgünlüğünü ve düzenleniş özelliklerini inceleyen yardımcı tarih bilimidir.");
knowledge["psikoloji"].push("İleriye ket vurma, önceden öğrenilen bilginin yeni bilginin öğrenilmesini zorlaştırabilmesidir.");
knowledge["felsefe"].push("Modus ponens, 'P ise Q' ve 'P' öncüllerinden 'Q' sonucunu çıkaran geçerli akıl yürütme biçimidir.");
knowledge["kişisel gelişim"].push("Uygulama niyeti, bir hedef için 'Eğer X olursa Y yapacağım' biçiminde somut bir eylem planı kurmaktır.");
/* 2026-11-20: ten curated offline facts. */
knowledge["bilim"].push("Bir tam Güneş tutulması, Ay'ın Güneş diskini Dünya'daki belirli bir gözlemci için tamamen örtmesiyle gerçekleşir.");
knowledge["roman"].push("İç monolog, bir anlatı kişisinin düşüncelerinin doğrudan aktarılmasına dayanan anlatım tekniğidir.");
knowledge["doğa"].push("Mercanlar, Knidliler şubesine ait hayvanlardır; mercan resifleri çok sayıda polipin oluşturduğu yapılardır.");
knowledge["satranç"].push("Satrançta geçerken alma, rakip piyon başlangıç karesinden iki kare ilerledikten hemen sonraki hamlede yapılabilen özel bir piyon alışıdır.");
knowledge["şiir"].push("Aliterasyon, bir şiir veya düzyazıda ünsüz seslerin yinelenmesiyle oluşan ses sanatıdır.");
knowledge["teknoloji"].push("HTTP 511 durum kodu, ağ erişimi için kimlik doğrulaması gerektiğini bildirir.");
knowledge["tarih"].push("Paleografi, eski yazı biçimlerini ve tarihsel el yazılarını inceleyen bilim dalıdır.");
knowledge["psikoloji"].push("Örtük bellek, bilgilerin bilinçli olarak hatırlanmasına gerek kalmadan davranışı etkileyebilen bellek türüdür.");
knowledge["felsefe"].push("Modus tollens, 'Eğer P ise Q; Q değil; öyleyse P değil' biçimindeki geçerli çıkarım kuralıdır.");
knowledge["kişisel gelişim"].push("Pomodoro tekniği, çalışmayı kısa odaklanma dönemleri ve aralarla düzenleyen bir zaman yönetimi yöntemidir.");
/* 2026-11-20: ten distinct curated Turkish facts; offline only. */
knowledge["bilim"].push("Jüpiter'in en büyük uydusu Ganymede, Merkür gezegeninden daha büyük bir çapa sahiptir.");
knowledge["roman"].push("Leitmotif, bir anlatıda belirli bir düşünceyi veya karakteri çağrıştırmak üzere yinelenen motiftir.");
knowledge["doğa"].push("Denizanası olarak bilinen hayvanların çoğunda merkezi bir beyin yerine sinir ağı bulunur.");
knowledge["satranç"].push("Satrançta bir piyon son yataya ulaştığında vezir, kale, fil veya ata terfi edebilir.");
knowledge["şiir"].push("Cinaslı uyak, yazılışı veya söylenişi aynı olup anlamı farklı sözcüklerle kurulan uyaktır.");
knowledge["teknoloji"].push("HTTP 429 durum kodu, istemcinin belirli bir süre içinde çok fazla istek gönderdiğini belirtir.");
knowledge["tarih"].push("Stratigrafi, arkeolojik tabakaların sıralanmasını ve birbirleriyle ilişkilerini incelemede kullanılır.");
knowledge["psikoloji"].push("Geriye ket vurma, sonradan öğrenilen bilginin daha önce öğrenilen bilgiyi hatırlamayı zorlaştırabilmesidir.");
knowledge["felsefe"].push("Yanlış ikilem, seçenekler ikiden fazla olabilecekken yalnızca iki seçenek varmış gibi sunan akıl yürütme hatasıdır.");
knowledge["kişisel gelişim"].push("SMART hedef yaklaşımında hedefin belirli, ölçülebilir, ulaşılabilir, ilgili ve zamana bağlı olması amaçlanır.");
/* 2026-11-20: ten offline educational facts; no personal data. */
knowledge["bilim"].push("Venüs, Güneş Sistemi'nde kendi ekseni çevresinde çoğu gezegenin ters yönünde döner.");
knowledge["roman"].push("Çerçeve anlatı, bir öykünün başka bir öykünün içinde anlatıldığı kurgu tekniğidir.");
knowledge["doğa"].push("Ahtapotların üç kalbi vardır; ikisi solungaçlara, biri vücudun geri kalanına kan pompalar.");
knowledge["satranç"].push("Satrançta pat, hamle sırası gelen oyuncunun şahı tehdit altında değilken hiçbir yasal hamlesinin bulunmamasıdır ve oyun berabere biter.");
knowledge["şiir"].push("Asonans, şiirde ünlü seslerin yinelenmesiyle oluşan ses uyumudur.");
knowledge["teknoloji"].push("HTTP 415 yanıt kodu, sunucunun istekteki içerik biçimini desteklemediğini belirtir.");
knowledge["tarih"].push("Kronoloji, olayları zaman sırasına göre düzenleme ve tarihlendirme çalışmasıdır.");
knowledge["psikoloji"].push("Çalışma belleği, bilgiyi kısa süreli olarak tutarken aynı zamanda işlemeyi sağlayan bilişsel sistemdir.");
knowledge["felsefe"].push("Epistemoloji, bilginin doğasını, kaynaklarını ve sınırlarını inceleyen felsefe dalıdır.");
knowledge["kişisel gelişim"].push("Kanban yöntemi, işlerin durumunu görselleştirmek için yapılacak, sürüyor ve tamamlandı gibi sütunlar kullanabilir.");

/* Offline curated knowledge. Fictional bot interests; no personal data. */
knowledge["bilim"].push("Bir nötron elektriksel olarak yüksüzdür ve atom çekirdeğinde protonlarla birlikte bulunabilir.");
knowledge["roman"].push("Diyalog, anlatıdaki karakterlerin konuşmalarının doğrudan aktarılmasıdır.");
knowledge["doğa"].push("Ağaçların kökleri su ve mineral alımına yardımcı olurken bitkinin toprağa tutunmasını da sağlar.");
knowledge["satranç"].push("Satrançta başlangıç konumunda her oyuncunun sekiz piyonu bulunur.");
knowledge["şiir"].push("Bent, şiirde birden fazla dizenin oluşturduğu bölümdür.");
knowledge["teknoloji"].push("HTTP 503 durum kodu, sunucunun isteği geçici olarak işleyemediğini bildirir.");
knowledge["tarih"].push("Nümizmatik, sikke ve madalyaları tarihsel bağlamlarıyla inceleyen alandır.");
knowledge["psikoloji"].push("Bölünmüş dikkat, dikkatin aynı anda birden fazla göreve yöneltilmesini ifade eder.");
knowledge["felsefe"].push("Etik ile hukuk aynı şey değildir; bir davranış yasal olsa da etik açıdan tartışılabilir.");
knowledge["kişisel gelişim"].push("Bir kontrol listesi, tekrarlanan görevlerde unutulan adımları azaltmaya yardımcı olabilir.");
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
 const n=norm(message);if(n.includes('beni unut')||n.includes('hafızanı sil')||n.includes('bilgilerimi sil')||n.includes('profil hafızamı temizle'))return respond(friend,message,history);
 const response=emotionalReply(friend,message);
 return response||respond(friend,message,history);
}

knowledge["bilim"].push("Satürn'ün ortalama yoğunluğu sudan düşüktür; yaklaşık 0,69 gram/santimetreküptür.");
knowledge["roman"].push("Güvenilmez anlatıcı, olayları aktardığı hâlde anlatımının doğruluğuna bütünüyle güvenilemeyen anlatıcıdır.");
knowledge["doğa"].push("Arılar çiçeklerden nektar toplarken polen taşıyarak birçok bitkinin tozlaşmasına katkıda bulunur.");
knowledge["satranç"].push("Satrançta fil, önünde taş bulunmadığı sürece çapraz doğrultuda istediği kadar kare ilerleyebilir.");
knowledge["şiir"].push("Akrostişte dizelerin ilk harfleri bir sözcük veya ifadeyi oluşturabilir.");
knowledge["teknoloji"].push("HTTP 204 durum kodu, isteğin başarıyla işlendiğini ancak yanıt gövdesi gönderilmediğini belirtir.");
knowledge["tarih"].push("Karbon-14 tarihlemesi, uygun organik kalıntıların yaşını belirlemek için radyoaktif karbonun bozunmasından yararlanır.");
knowledge["psikoloji"].push("Seçici dikkat, birden fazla uyaran arasından belirli bilgilere odaklanma sürecidir.");
knowledge["felsefe"].push("Tümevarım, tekil gözlemlerden daha genel sonuçlara ulaşmaya çalışan akıl yürütmedir.");
knowledge["kişisel gelişim"].push("Önceliklendirme, görevleri önem ve aciliyet gibi ölçütlere göre sıralamayı sağlar.");
/* 2026-11-20: curated offline knowledge, no private data. */
knowledge["bilim"].push("Merkür, Güneş çevresindeki bir dolanımını yaklaşık 88 Dünya gününde tamamlar.");
knowledge["roman"].push("Epistolary roman, anlatının mektuplar veya benzeri yazılı belgeler üzerinden kurulduğu roman türüdür.");
knowledge["doğa"].push("Yarasalar, gerçek anlamda aktif uçuş yapabilen tek memeli grubudur.");
knowledge["satranç"].push("Satrançta üç kez aynı konumun oluşması, koşulları sağlandığında oyuncuya beraberlik talep etme hakkı verir.");
knowledge["şiir"].push("Rubai, geleneksel olarak dört dizeden oluşan ve kendine özgü aruz kalıpları bulunan nazım biçimidir.");
knowledge["teknoloji"].push("HTTP 304 durum kodu, koşullu istekte kaynağın değişmediğini ve önbellekteki kopyanın kullanılabileceğini belirtir.");
knowledge["tarih"].push("Rosetta Taşı, aynı kararnamenin farklı yazı sistemleriyle yazılmış metinlerini içerdiği için Mısır hiyerogliflerinin çözülmesine katkı sağlamıştır.");
knowledge["psikoloji"].push("İleriye dönük bellek, gelecekte belirli bir işi yapmayı hatırlama becerisidir.");
knowledge["felsefe"].push("Safsata, ikna edici görünebilse de mantıksal açıdan sorunlu bir akıl yürütmedir.");
knowledge["kişisel gelişim"].push("Eisenhower matrisi, görevleri önem ve aciliyet boyutlarına göre dört gruba ayıran önceliklendirme aracıdır.");
/* 2026-11-20: offline verified knowledge additions; no user data. */
knowledge["bilim"].push("Işık yılı bir zaman değil, ışığın boşlukta bir yılda aldığı yaklaşık 9,46 trilyon kilometrelik uzaklıktır.");
knowledge["roman"].push("Öyküleme, olayların bir zaman akışı içinde anlatılmasıdır; betimleme ise kişi, yer veya nesnenin özelliklerini görünür kılar.");
knowledge["doğa"].push("Mantarlar fotosentez yapmaz; besinlerini çevrelerindeki organik maddelerden elde eder.");
knowledge["satranç"].push("Satrançta at, iki kare bir yönde ve bir kare ona dik yönde ilerler; diğer taşların üzerinden atlayabilir.");
knowledge["şiir"].push("Hece ölçüsü, şiir dizelerindeki hece sayılarının düzenine dayanır.");
knowledge["teknoloji"].push("HTTP 201 durum kodu, isteğin başarıyla sonuçlanıp yeni bir kaynak oluşturulduğunu bildirir.");
knowledge["tarih"].push("Miladi takvimde artık yıl kuralı, 4'e bölünebilen yılları kapsar; 100'e bölünen yıllar ancak 400'e de bölünüyorsa artık yıldır.");
knowledge["psikoloji"].push("Seri konum etkisi, bir listedeki ilk ve son öğelerin orta öğelere göre daha iyi hatırlanabilmesi eğilimidir.");
knowledge["felsefe"].push("Bir önermenin karşıt örneği, genel bir iddianın yanlış olduğunu göstermek için yeterli olabilir.");
knowledge["kişisel gelişim"].push("Zaman bloklama, takvimde belirli görevler için önceden ayrılmış çalışma aralıkları oluşturma yöntemidir.");

/* 2026-11-21: 10 curated offline facts; no user conversation data. */
knowledge["bilim"].push("Jüpiter, Güneş Sistemi'ndeki en büyük gezegendir.");
knowledge["roman"].push("Bir romanın anlatıcısı ile romanın yazarı aynı kişi olmak zorunda değildir.");
knowledge["doğa"].push("Likenler, mantar ile fotosentez yapan bir ortak arasında kurulan simbiyotik birlikteliklerdir.");
knowledge["satranç"].push("Satrançta vezir, önünde taş yoksa yatay, dikey ve çapraz doğrultuda ilerleyebilir.");
knowledge["şiir"].push("Serbest nazımda dizeler belirli bir hece veya aruz ölçüsüne bağlı olmak zorunda değildir.");
knowledge["teknoloji"].push("HTTP 404 durum kodu, sunucunun istenen kaynağı bulamadığını belirtir.");
knowledge["tarih"].push("Çivi yazısı ilk olarak Mezopotamya'da geliştirilmiştir.");
knowledge["psikoloji"].push("Aralıklı tekrar, öğrenilen bilgiyi zaman içinde farklı aralıklarla yeniden gözden geçirme yöntemidir.");
knowledge["felsefe"].push("Tümdengelimde, geçerli bir çıkarımda öncüller doğruysa sonuç yanlış olamaz.");
knowledge["kişisel gelişim"].push("Bir hedefin ölçülebilir olması, ilerlemenin somut göstergelerle izlenmesini sağlar.");

/* Curated offline facts 2026-11-21. */
knowledge["bilim"].push("Neptün, Güneş Sistemi'nde Güneş'e en uzak gezegendir.");
knowledge["roman"].push("Öyküde olay örgüsü, anlatılan olayların neden-sonuç ve zaman ilişkileriyle düzenlenmesidir.");
knowledge["doğa"].push("Yunuslar balık değil, akciğerleriyle solunum yapan memelilerdir.");
knowledge["satranç"].push("Satrançta rok hamlesi, şah ile aynı renkteki kalenin birlikte yer değiştirdiği özel hamledir.");
knowledge["şiir"].push("Redif, dizelerin sonunda aynı görev ve anlamla tekrarlanan ek ya da sözcüklerdir.");
knowledge["teknoloji"].push("HTTP 206 durum kodu, sunucunun istenen içeriğin yalnızca belirli bir bölümünü döndürdüğünü belirtir.");
knowledge["tarih"].push("Tarih öncesi dönemlerin sınırları, yazının farklı bölgelerde farklı zamanlarda kullanılmaya başlanması nedeniyle bölgeden bölgeye değişebilir.");
knowledge["psikoloji"].push("Hatırlama, bellekteki bilgiyi ipucu olmadan geri getirmeyi; tanıma ise sunulan bilgiyi önceden öğrenilmiş olarak ayırt etmeyi içerir.");
knowledge["felsefe"].push("Bir önermenin karşıtının yanlış olması, tek başına o önermenin doğruluğunu kanıtlamaz.");
knowledge["kişisel gelişim"].push("Bir alışkanlığı takip etmek için her uygulandığı günü takvimde işaretlemek, davranışın sıklığını görünür kılar.");

/* 2026-11-21: 10 verified, non-personal offline facts. */
knowledge["bilim"].push("Mars'ın iki doğal uydusu Phobos ve Deimos olarak adlandırılır.");
knowledge["roman"].push("Metinlerarasılık, bir edebî metnin başka metinlerle kurduğu açık veya örtük ilişkileri ifade eder.");
knowledge["doğa"].push("Denizyıldızlarının çoğunda su damar sistemi hareket etmeye ve beslenmeye yardımcı olur.");
knowledge["satranç"].push("Satrançta at, kendi taşlarının ve rakip taşların üzerinden atlayabilen tek standart taştır.");
knowledge["şiir"].push("Enjambman, bir şiir dizesinde başlayan söz diziminin sonraki dizede sürmesidir.");
knowledge["teknoloji"].push("HTTP 418 durum kodu, 1998 tarihli mizahi HTCPCP protokolünde 'I'm a teapot' yanıtı olarak tanımlanmıştır.");
knowledge["tarih"].push("Hiyeroglif yazısı yalnızca resimlerden oluşmaz; ses değerleri taşıyan işaretler de içerir.");
knowledge["psikoloji"].push("Prospektif bellek, gelecekte belirli bir zamanda veya durumda yapılması planlanan işi hatırlama yetisidir.");
knowledge["felsefe"].push("Ockham'ın usturası, eşit açıklama gücündeki varsayımlar arasında gereksiz çoğaltmadan kaçınmayı öğütler.");
knowledge["kişisel gelişim"].push("Uygulama niyeti, bir hedefi 'Eğer X olursa Y yapacağım' biçiminde somut bir koşula bağlar.");

/* 2026-11-21: 10 distinct offline knowledge additions; no user data. */
knowledge["bilim"].push("Ay'ın Dünya çevresindeki dolanımı nedeniyle Dünya'dan görülen aydınlık yüzeyinin şekli evreler hâlinde değişir.");
knowledge["roman"].push("İç çözümleme, anlatıcının bir karakterin duygu ve düşüncelerini doğrudan aktardığı anlatım tekniğidir.");
knowledge["doğa"].push("Kelebekler tam başkalaşım geçirir; yaşam döngülerinde yumurta, larva, pupa ve ergin evreleri bulunur.");
knowledge["satranç"].push("Satrançta bir piyon son yataya ulaştığında aynı renkten vezir, kale, fil veya ata terfi eder.");
knowledge["şiir"].push("Ölçü, şiirde dizelerin ritmik düzenini belirleyen hece sayısı veya aruz kalıbı gibi yapılardır.");
knowledge["teknoloji"].push("HTTP 301 yanıtı, bir kaynağın kalıcı olarak başka bir adrese taşındığını bildirir.");
knowledge["tarih"].push("Tarih araştırmalarında birincil kaynaklar, incelenen dönemde üretilmiş belge veya nesneleri kapsar.");
knowledge["psikoloji"].push("Çapa etkisi, ilk sunulan sayısal bilginin sonraki tahmin ve değerlendirmeleri etkileme eğilimidir.");
knowledge["felsefe"].push("Geçerli bir argüman, öncülleri doğru olduğunda sonucunun yanlış olamayacağı çıkarım biçimidir.");
knowledge["kişisel gelişim"].push("Bir işi küçük ve somut adımlara bölmek, ilerlemeyi izlemeyi ve ilk adımı atmayı kolaylaştırabilir.");

/* 2026-11-21: ten curated offline facts, no personal data. */
knowledge["bilim"].push("Güneş'in enerjisi çekirdeğinde hidrojenin helyuma dönüşmesini sağlayan nükleer füzyondan kaynaklanır.");
knowledge["roman"].push("Leitmotif, bir anlatıda yinelenerek belirli bir karakteri, düşünceyi veya temayı çağrıştıran motiftir.");
knowledge["doğa"].push("Yusufçukların erginleri ve sucul nimfleri avcıdır; nimfler çoğunlukla suda yaşar.");
knowledge["satranç"].push("Satrançta şah çekilmişken oyuncu tehdidi ortadan kaldıran yasal bir hamle yapmak zorundadır.");
knowledge["şiir"].push("Kafiye, dizelerin sonlarında rediften önce görülen ses benzerliğidir.");
knowledge["teknoloji"].push("HTTP 422 durum kodu, sunucunun isteğin içeriğini anladığı ancak içerdiği talimatları işleyemediği durumu belirtir.");
knowledge["tarih"].push("Dendrokronoloji, ağaçların yıllık büyüme halkalarını inceleyerek tarihleme yapmaya yardımcı olur.");
knowledge["psikoloji"].push("Geriye ket vurma, yeni öğrenilen bilginin daha önce öğrenilmiş bilgiyi hatırlamayı zorlaştırabilmesidir.");
knowledge["felsefe"].push("Yanlış ikilem safsatası, başka seçenekler de mümkünken yalnızca iki seçenek varmış gibi sunulmasıdır.");
knowledge["kişisel gelişim"].push("Pomodoro tekniği, odaklı çalışma aralıklarını kısa molalarla dönüşümlü kullanmaya dayanır.");

/* 2026-11-21: new curated facts; fictional bots, no user data. */
knowledge["bilim"].push("Uranüs'ün dönme ekseni yörünge düzlemine neredeyse paraleldir; bu nedenle gezegen yan yatmış gibi döner.");
knowledge["roman"].push("Prolepsis, anlatıda henüz gerçekleşmemiş gelecekteki olaylara önceden geçilmesidir.");
knowledge["doğa"].push("Ornitorenk, yumurtlayan memeliler grubuna ait bir hayvandır.");
knowledge["satranç"].push("Satrançta elli hamle kuralı, her iki tarafın son ellişer hamlesinde piyon sürülmemiş ve taş alınmamışsa beraberlik talebine olanak verir.");
knowledge["şiir"].push("Mazmun, özellikle divan şiirinde gelenekleşmiş mecaz ve çağrışım kalıplarıdır.");
knowledge["teknoloji"].push("HTTP 410 durum kodu, istenen kaynağın sunucuda artık bulunmadığını ve bu durumun kalıcı olmasının beklendiğini belirtir.");
knowledge["tarih"].push("Termolüminesans tarihleme, uygun koşullarda ısıtılmış arkeolojik seramiklerin son ısıtılma zamanını tahmin etmek için kullanılabilir.");
knowledge["psikoloji"].push("Zeigarnik etkisi, tamamlanmamış görevlerin bazı koşullarda tamamlanmış görevlere göre daha kolay hatırlanabilmesi eğilimidir.");
knowledge["felsefe"].push("Modus ponens, 'P ise Q; P; öyleyse Q' biçimindeki geçerli çıkarım kuralıdır.");
knowledge["kişisel gelişim"].push("WOOP yöntemi, dilek, sonuç, engel ve plan adımlarını kullanarak hedefe yönelik eylemi somutlaştırır.");
/* 2026-11-21: curated offline facts, no user data. */
knowledge["bilim"].push("Satürn'ün halkaları büyük ölçüde buz parçacıklarından ve daha az miktarda kayaç malzemeden oluşur.");
knowledge["roman"].push("Çerçeve anlatı, bir veya birden fazla hikâyenin başka bir anlatının içinde sunulduğu yapıdır.");
knowledge["doğa"].push("Penguenler kuş olmalarına rağmen uçamaz; yüzmeye uyum sağlamış kanatları vardır.");
knowledge["satranç"].push("Satrançta açmaz, bir taşın hareket etmesi hâlinde arkasındaki daha değerli taşın veya şahın saldırıya açık kalması durumudur.");
knowledge["şiir"].push("Epifora, art arda gelen dizelerin veya cümlelerin sonunda aynı sözcüğün ya da ifadenin tekrarlanmasıdır.");
knowledge["teknoloji"].push("HTTP 431 durum kodu, sunucunun istek başlık alanları çok büyük olduğu için isteği işlemeyi reddettiğini belirtir.");
knowledge["tarih"].push("Paleolitik Çağ, taş aletlerin kullanıldığı tarih öncesi dönemin en eski ve en uzun bölümüdür.");
knowledge["psikoloji"].push("Kodlama özgüllüğü ilkesi, hatırlamanın öğrenme sırasında bulunan ipuçlarıyla desteklenebileceğini açıklar.");
knowledge["felsefe"].push("Modus tollens, 'P ise Q; Q değil; öyleyse P değil' biçimindeki geçerli çıkarım kuralıdır.");
knowledge["kişisel gelişim"].push("SMART hedef yaklaşımı, hedefleri belirli, ölçülebilir, ulaşılabilir, ilgili ve zamana bağlı biçimde tanımlamayı önerir.");

/* 2026-11-21: curated offline knowledge; no user data. */
knowledge["bilim"].push("Ganymede, Jüpiter'in en büyük uydusu ve Güneş Sistemi'nin en büyük doğal uydusudur.");
knowledge["roman"].push("Bilinç akışı tekniği, karakterin zihninden geçen düşünceleri çağrışımlı ve kesintili biçimde yansıtabilir.");
knowledge["doğa"].push("Deniz kaplumbağaları akciğerleriyle solunum yapar ve yumurtlamak için karaya çıkar.");
knowledge["satranç"].push("Satrançta zugzwang, hamle sırası kendisinde olan oyuncunun her yasal hamlesinin konumunu kötüleştirdiği durumdur.");
knowledge["şiir"].push("Asonans, şiirde aynı veya benzer ünlü seslerin yinelenmesiyle oluşan ses uyumudur.");
knowledge["teknoloji"].push("HTTP 202 durum kodu, isteğin işlenmek üzere kabul edildiğini fakat işlemin henüz tamamlanmamış olabileceğini belirtir.");
knowledge["tarih"].push("Rosetta Taşı üzerinde aynı kararname üç farklı yazı sistemiyle kaydedilmiştir.");
knowledge["psikoloji"].push("Stroop etkisi, bir kelimenin yazıldığı rengi söylerken kelimenin anlamının tepkiyi zorlaştırabilmesidir.");
knowledge["felsefe"].push("Döngüsel akıl yürütmede sonuç, onu desteklemek için sunulan öncüllerde zaten varsayılır.");
knowledge["kişisel gelişim"].push("Geriye doğru planlama, hedefin tamamlanma tarihinden başlayıp gerekli adımları geriye doğru sıralama yöntemidir.");
/* 2026-11-21: ten offline facts, no user data. */
knowledge["bilim"].push("Venüs, Güneş Sistemi'ndeki gezegenler arasında en uzun kendi ekseni dönüş süresine sahiptir.");
knowledge["roman"].push("Epigraf, bir eserin veya bölümün başına yerleştirilen kısa alıntı ya da özdeyiştir.");
knowledge["doğa"].push("Ahtapotların üç kalbi vardır; ikisi solungaçlara, biri vücuda kan pompalar.");
knowledge["satranç"].push("Satrançta en passant alma hakkı, rakip piyonun iki kare ilerlediği hamlenin hemen ardından kullanılabilir.");
knowledge["şiir"].push("Pastoral şiir, kır yaşamını ve doğayı konu edinen şiir türüdür.");
knowledge["teknoloji"].push("HTTP 204 durum kodu, isteğin başarılı olduğunu ve yanıtta içerik gövdesi bulunmadığını belirtir.");
knowledge["tarih"].push("Epigrafi, taş veya metal gibi kalıcı yüzeyler üzerindeki yazıtları inceler.");
knowledge["psikoloji"].push("Duruma bağlı bellek, öğrenme ve hatırlama sırasında benzer fizyolojik koşulların geri çağırmayı kolaylaştırabilmesidir.");
knowledge["felsefe"].push("Tümevarım, tekil gözlemlerden genel bir sonuca ulaşmaya çalışan akıl yürütmedir; sonucu zorunlu kılmaz.");
knowledge["kişisel gelişim"].push("Kanban yöntemi, işleri yapılacak, sürüyor ve tamamlandı gibi aşamalarda görselleştirerek akışı izlemeye yardımcı olur.");
window.BookCenterLocalMind={answer:emotionallyAwareAnswer,profiles,readMemory,learn,dailyPlan,activitySummary,knowledgeState,learnedFact,detectEmotion,emotionState,version:'5.0'};
})();