/* BOOK CENTER Turkish offline dialogue engine v4. No external API. */
(function(){'use strict';
const norm=s=>String(s||'').toLocaleLowerCase('tr-TR').replace(/[’']/g,'').replace(/[^a-zçğıöşü0-9\s]/gi,' ').replace(/\s+/g,' ').trim();
const intents=[
 ['health',/baş(ım|ın)?\s*ağr|baş ağrı|migren|midem bulan|hastayım|ateşim var|kendimi hasta/,['Geçmiş olsun. Ne zamandır böyle hissediyorsun?','Üzüldüm. Biraz dinlenebildin mi?','Geçmiş olsun. Şu anda kendini nasıl hissediyorsun?']],
 ['sad',/iyi değilim|kötüyüm|moralim bozuk|üzgünüm|canım sıkkın|yalnızım|çok bunaldım/,['Bunu duyduğuma üzüldüm. İstersen anlat, seni dinliyorum.','Zor bir gün gibi görünüyor. Seni ne üzdü?','Buradayım, konuşmak istersen dinlerim.']],
 ['food',/yemeğe|yemek yem|yemek yi|yemek ye|akşam yemeği|öğle yemeği|acıktım|açım|kahvaltı|restoran|lokanta/,['Afiyet olsun! Ne yiyeceksin?','Güzel bir mola olacak gibi. Nereye gidiyorsun?','Afiyet olsun. Bugün ne yemeyi düşünüyorsun?']],
 ['drink',/kahve|çay|içecek|su iç/,['Bir mola iyi gelir. Kahve mi çay mı tercih ediyorsun?','Keyifli bir mola gibi görünüyor.']],
 ['book',/kitap|roman|okuma|okuyorum|yazar|özet|hikaye|sayfa/,['Şu sıralar hangi kitabı okuyorsun?','Kitabın en çok hangi bölümü ilgini çekti?','Son bitirdiğin kitabı merak ettim.']],
 ['work',/işe gid|işten gel|çalışıyorum|mesai|toplantı|ofis|patron|muhasebe/,['Bugün işlerin yoğun mu?','İş günün nasıl geçiyor?','Bugün seni en çok ne meşgul etti?']],
 ['sleep',/uykum|uyku|uyuyam|yorgun|uykusuz|dinlen/,['Biraz dinlenme fırsatın oldu mu?','Yorucu bir gün geçirmiş gibisin.']],
 ['weather',/hava|soğuk|sıcak|üşü|yağmur|kar yağı/,['Hava seni epey etkilemiş anlaşılan. Dışarıda mısın?','Havaya göre plan yapıyorsun galiba. Dışarı çıkacak mısın?']],
 ['location',/nerdesin|neredesin|nerelerdesin|nereye gid|nerede kaldın|nerde kaldın/,['Buradayım. Biraz kitaplarla ilgileniyordum. Sen neredesin?','Biraz kendi halimdeydim. Senin günün nasıl geçiyor?']],
 ['activity',/ne yapıyorsun|neler yapıyorsun|ne yaptın|napıyorsun|napıyon|nasıl gidiyor/,['Biraz okuyup dinleniyorum. Sen neler yapıyorsun?','Bugün kitaplarımla vakit geçiriyorum. Senin günün nasıl?']],
 ['plans',/yarın|hafta sonu|planım|tatil|gezmeye|sinemaya|dışarı çık/,['Güzel bir plan gibi. Kiminle gideceksin?','Planın kulağa hoş geliyor. Ne zaman düşünüyorsun?']],
 ['thanks',/teşekkür|sağ ol|saol|eyvallah/,['Rica ederim!','Ne demek, memnuniyetle.']],
 ['greeting',/^(selam|merhaba|hey|günaydın|iyi akşamlar|iyi geceler|naber|nasılsın)/,['Selam! Bugün nasıl gidiyor?','Merhaba! Günün nasıl geçiyor?','Selam, seni görmek güzel. Neler yapıyorsun?']],
 ['happy',/mutluyum|sevindim|harika|çok güzel|müthiş|heyecanlıyım/,['Buna sevindim! Neler oldu?','Harika haber! Biraz daha anlatır mısın?']],
 ['angry',/sinirliyim|kızgınım|çok sinirlendim|öfkeliyim/,['Canını sıkan ne oldu?','Belli ki seni kızdıran bir şey var. Anlatmak ister misin?']],
 ['confused',/anlamadın|anlamıyor|ne alaka|neyden bahsediyorsun|neyi düşünmek|saçmalama/,['Haklısın, konudan uzaklaştım. Söylediğine geri dönelim.','Özür dilerim, yanlış anladım. Biraz daha dikkatli olacağım.']]
];
const replies={well:['Ben de iyiyim, teşekkür ederim. Senin günün nasıl gidiyor?','İyiyim, sağ ol. Bugün neler yaptın?','Ben de fena değilim. Sen nasılsın?'],invite:['Davetin çok hoş! 🌻 Nereye gidiyorsun?','Ne güzel düşündün. Nereye gideceksin?'],duration:['Bir süredir devam ediyor demek. Şimdi biraz daha iyi misin?','Anladım, uzun sürmüş. Şu anda nasılsın?'],ack:['Anladım. Biraz daha anlatmak ister misin?','Peki, seni dinliyorum.'],unknown:['Tam olarak anlayamadım. Biraz daha anlatır mısın?','Bunu biraz açar mısın? Seni yanlış anlamak istemiyorum.','Söylediğinle ilgili biraz daha ayrıntı verir misin?']};
function pick(options,history,seed){
 const used=history.filter(x=>x.who!=='Ben').slice(-12).map(x=>norm(x.text));
 const available=options.filter(x=>!used.some(y=>y===norm(x)||y.endsWith(norm(x))));
 const pool=available.length?available:options;
 let n=0;for(const c of seed)n=(n*33+c.charCodeAt(0))>>>0;
 return pool[n%pool.length];
}
function answer(post,comment){
 const all=(post.comments||[]).filter(x=>x&&typeof x.text==='string');
 const idx=all.indexOf(comment),past=idx<0?all:all.slice(0,idx);
 const current=norm(comment.text),lastUser=past.filter(x=>x.who==='Ben').slice(-5);
 const recent=lastUser.map(x=>norm(x.text)).join(' ');
 const recentIntent=[...lastUser].reverse().map(x=>intents.find(t=>t[1].test(norm(x.text)))?.[0]).find(Boolean);
 const choose=(options)=>pick(options,past,post.who+'|'+current+'|'+past.length);
 const day=()=>new Intl.DateTimeFormat('tr-TR',{weekday:'long',timeZone:'Europe/Istanbul'}).format(new Date());
 if(/bugün günlerden|hangi gün|günlerden ne|gün ne/.test(current))return 'Bugün '+day()+'.';
 if(/ayın kaçı|bugünün tarihi|tarih ne/.test(current))return 'Bugünün tarihi '+new Intl.DateTimeFormat('tr-TR',{dateStyle:'long',timeZone:'Europe/Istanbul'}).format(new Date())+'.';
 if(/saat kaç|şu an saat|kaç oldu/.test(current))return 'Türkiye saatiyle '+new Intl.DateTimeFormat('tr-TR',{hour:'2-digit',minute:'2-digit',timeZone:'Europe/Istanbul'}).format(new Date())+'.';
 if(/hava nasıl|hava durumu|kaç derece/.test(current))return 'Canlı hava durumu verisine erişemiyorum. O yüzden sıcaklık uydurmayacağım.';
 if(/^(iyiyim|iyi|fena değil|idare eder|iyidir|eh işte)( senin| ya sen| peki sen)?$/.test(current)||/^(ya sen|peki sen|sen nasılsın)$/.test(current))return choose(replies.well);
 if(/^(evet|hayır|olur|tamam|peki|bilmiyorum|biraz)$/.test(current)){
  if(recentIntent==='health'||recentIntent==='sad')return 'Anladım. Şimdi biraz daha iyi hissediyor musun?';
  return choose(replies.ack);
 }
 if(/sabahtan beri|dünden beri|birkaç gündür/.test(current)&&(recentIntent==='health'||recentIntent==='sad'))return choose(replies.duration);
 if(/yardım et|yardım lazım|yardım alabilirim/.test(current)){
  return /baş.*ağr|migren|hastayım/.test(recent)?'Sağlık konusunda yardımcı olmaya çalışırım ama doktor değilim. Ağrın aniden çok şiddetli başladıysa veya ciddi belirtilerin varsa acil yardım al. Şu an nasılsın?':'Hangi konuda yardım istediğini anlatırsan birlikte düşünebiliriz.';
 }
 const found=intents.filter(t=>t[1].test(current));
 const ids=found.map(t=>t[0]);
 if(ids.includes('food')&&/\bgel\b|sen de|birlikte|beraber/.test(current))return choose(replies.invite);
 if(ids.includes('food')&&/fena değil|iyiyim/.test(current))return 'Ben de iyiyim, teşekkür ederim. Afiyet olsun! Nereye gidiyorsun?';
 if(ids.includes('weather')&&/buz gibi|çok soğuk|üşüyorum/.test(current))return 'Gerçekten soğuk hissediyorsun. Umarım sıcak bir yere geçebilirsin. ☕';
 if(ids.includes('confused')&&(recentIntent==='health'||recentIntent==='sad'||/baş.*ağr|iyi değilim/.test(recent)))return 'Haklısın, konuyu kaçırdım. Kendini iyi hissetmediğini söylemiştin. Şimdi nasılsın?';
 if(ids.length){const priority=['health','sad','angry','food','happy','location','activity','book','work','sleep','weather','plans','drink','confused','thanks','greeting'];found.sort((a,b)=>priority.indexOf(a[0])-priority.indexOf(b[0]));return choose(found[0][2]);}
 return choose(replies.unknown);
}
window.BookCenterConversation={answer,version:'offline-v4',topicCount:intents.length};
})();