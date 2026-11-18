/* BOOK CENTER offline conversation engine v1. No external API. */
(function(){'use strict';
const topics=[
 {id:'day',re:/bugün günlerden ne|bugün hangi gün|günlerden ne|hangi gündeyiz|hangi gün|gün ne/i,replies:[]},
 {id:'time',re:/saat kaç|şu an saat|kaç oldu saat/i,replies:[]},
 {id:'weather',re:/hava nasıl|hava buz gibi|hava soğuk|hava sıcak|üşüyorum|yağmur yağıyor/i,replies:[]},
 {id:'help',re:/sen yardım et|yardım et|nereden yardım alabilirim|yardım lazım/i,replies:[]},

 {id:'headache',re:/baş(ım|ın|ı)?\s*(çok\s*)?(ağrı|ağrıyor)|migren|baş ağrısı/i,replies:['Geçmiş olsun. Ne zamandır başın ağrıyor?','Üzüldüm. Biraz dinlenme fırsatın oldu mu?','Baş ağrısı yorucu olabilir. Ağrın hafif mi, şiddetli mi?']},
 {id:'unwell',re:/iyi değilim|kötüyüm|kendimi kötü|moralim bozuk|üzgünüm|canım sıkkın/i,replies:['Bunu duyduğuma üzüldüm. İstersen neler olduğunu anlatabilirsin.','Yanındayım, seni dinliyorum. Seni üzen bir şey mi oldu?','Zor bir gün geçiriyor gibisin. Konuşmak ister misin?']},
 {id:'duration',re:/sabahtan beri|dünden beri|kaç saattir|birkaç gündür|uzun zamandır/i,replies:['Anladım, bir süredir devam ediyor. Şu anda biraz daha iyi misin?','Bu kadar sürmesi yorucu olmalı. Dinlenebildin mi?']},
 {id:'confusion',re:/beni anlamıyor|anlamadın|neyden bahsediyorsun|neyi düşünmek|ne alaka|saçmalama/i,replies:['Haklısın, söylediklerini yanlış yorumladım. Konumuza geri dönelim.','Özür dilerim, cevabım söylediklerinle uyuşmadı. Seni daha dikkatli dinleyeceğim.']},
 {id:'books',re:/kitap|roman|okuyorum|yazar|özet|sayfa/i,replies:['Ne güzel, hangi kitabı okuyorsun?','Bu kitapta seni en çok etkileyen şey ne oldu?','Okumayı seviyorum. Son bitirdiğin kitabı merak ettim.']},
 {id:'location',re:/nerelerdesin|neredesin|nerdesin|nereye gidiyorsun|nerede kaldın/i,replies:['Buradayım, biraz kendi halimde vakit geçiriyordum. Sen neler yapıyorsun?','Kitaplarımla ilgileniyordum. Senin günün nasıl geçiyor?']},
 {id:'greeting',re:/^(merhaba|selam|günaydın|iyi akşamlar|hey)\b/i,replies:['Merhaba! Günün nasıl geçiyor?','Selam! Bugün neler yaptın?']},
 {id:'thanks',re:/teşekkür|sağ ol|eyvallah/i,replies:['Rica ederim, ne zaman istersen konuşabiliriz.','Ne demek, memnun oldum.']},
 {id:'positive',re:/çok iyiyim|mutluyum|harika|sevindim|güzel haber/i,replies:['Buna sevindim! Ne oldu, anlatır mısın?','Harika! Bu güzel haberin devamını duymak isterim.']},
 {id:'sleep',re:/uyku|uyuyamıyorum|yorgunum|uykusuz/i,replies:['Yorgun hissetmek zor olmalı. Bugün yoğun bir gün müydü?','Biraz dinlenebilmeni umuyorum. Seni uykusuz bırakan bir şey mi var?']},
 {id:'work',re:/iş|ofis|toplantı|mesai|çalışıyorum/i,replies:['İşlerin nasıl gidiyor? Bugün yoğun muydu?','Anladım. Günün en zor kısmı neydi?']},
 {id:'food',re:/kahve|çay|yemek|acıktım|kahvaltı/i,replies:['Güzel bir mola gibi! Yanında kitap da var mı?','Afiyet olsun! Bugün kendine vakit ayırabildin mi?']}
];
const personalities={Mira:{prefix:'🌻 ',warm:true},Deniz:{prefix:'',analytical:true},Atlas:{prefix:'',brief:true},Luna:{prefix:'🌙 '},Ada:{prefix:'✨ '}};
const normalize=x=>String(x||'').toLocaleLowerCase('tr-TR').trim();
function pick(list,seed){let h=0;for(const c of seed)h=(h*31+c.charCodeAt(0))>>>0;return list[h%list.length]}
function answer(post,comment){
 const history=(post.comments||[]).filter(c=>c&&typeof c.text==='string');
 const index=history.indexOf(comment);
 const earlier=index<0?history:history.slice(0,index);
 const userEarlier=earlier.filter(c=>c.who==='Ben').slice(-6);
 const current=normalize(comment.text);
 if(/yemeğe gid|yemek yemeye gid|akşam yemeği|öğle yemeği/i.test(current)){
   return /\bgel\b|birlikte|sen de/i.test(current)?'Afiyet olsun! 🌻 Davetin çok hoş. Nereye gidiyorsun?':'Afiyet olsun! 🌻 Nereye gidiyorsun, ne yiyeceksin?';
 }
 if(/fena değil|idare eder|iyiyim|iyi senin|iyi ya sen/i.test(current)&&!/yemeğe gid|yemek yemeye gid/i.test(current)){
   return 'Ben de iyiyim, teşekkür ederim. 🌻 Bugün neler yapıyorsun?';
 }

 const recentBot=earlier.filter(c=>c.who===post.who).slice(-6).map(c=>normalize(c.text));
 if(/^(iyi(yim)?|iyidir|fena değil|idare eder)([, ]+sen(in)?|[, ]+ya sen)?[?.!]*$/.test(current)){
   const options=['Ben de iyiyim, teşekkür ederim. Bugün neler yaptın?','İyiyim, sağ ol! Bugün nasıl geçti?','Ben de fena değilim. Senin gününde güzel bir şey oldu mu?'];
   return pick(options.filter(x=>!recentBot.includes(normalize(x))),post.who+earlier.length);
 }
 if(/^(sen nasılsın|ya sen|peki sen|senin nasıl)[?.!]*$/.test(current))return 'Ben de iyiyim, teşekkür ederim. Bugün neler yaptın?';

 if(/bugün günlerden ne|bugün hangi gün|günlerden ne|hangi gündeyiz|hangi gün|gün ne/i.test(current)){const day=new Intl.DateTimeFormat('tr-TR',{weekday:'long',timeZone:'Europe/Istanbul'}).format(new Date());return 'Bugün '+day+'. 🌻';}
 if(/bugün ayın kaçı|ayın kaçı|bugünün tarihi|tarih ne/i.test(current))return 'Bugünün tarihi '+new Intl.DateTimeFormat('tr-TR',{day:'numeric',month:'long',year:'numeric',timeZone:'Europe/Istanbul'}).format(new Date())+'.';
 if(/saat kaç|şu an saat|kaç oldu saat/i.test(current))return 'Türkiye saatiyle '+new Intl.DateTimeFormat('tr-TR',{hour:'2-digit',minute:'2-digit',timeZone:'Europe/Istanbul'}).format(new Date())+'.';
 if(/hava nasıl/i.test(current))return 'Güncel hava durumuna erişimim yok. Hangi şehirde olduğunu söylersen sohbet edebiliriz ama sıcaklık uydurmak istemem.';
 if(/hava buz gibi|hava soğuk|üşüyorum/i.test(current))return 'Çok soğuk hissediyorsun anlaşılan. Umarım sıcak bir yere geçebilirsin. ☕';
 if(/hava sıcak|çok sıcak/i.test(current))return 'Sıcak bunaltıcı olabiliyor. Serinleyebildin mi?';
 if(/sen yardım et|yardım et|nereden yardım alabilirim|yardım lazım/i.test(current))return /baş.*ağr|migren|iyi değilim/.test(userEarlier.map(x=>normalize(x.text)).join(' '))?'Başın ağrıdığı için yardım istiyorsun, anladım. Şiddetli veya ani başlayan bir ağrıysa ya da başka ciddi belirtiler varsa acil tıbbi yardım al. Nasıl hissettiğini biraz daha anlatabilir misin?':'Elimden geldiğince yardımcı olayım. Hangi konuda yardıma ihtiyacın var?';

 let match=topics.find(t=>t.re.test(current));
 const previousTopics=userEarlier.map(c=>topics.find(t=>t.re.test(normalize(c.text)))?.id).filter(Boolean);
 const lastTopic=previousTopics[previousTopics.length-1];
 if(match?.id==='duration'&&lastTopic==='headache')return 'Sabahtan beri başının ağrıdığını anladım. Geçmiş olsun. Şu anda ağrın hafifledi mi?';
 if(match?.id==='confusion'&&previousTopics.some(t=>t==='headache'||t==='unwell'))return 'Haklısın, konuyu kaçırdım. Kendini iyi hissetmediğini söyledin. Seni dinliyorum, şimdi nasılsın?';
 if(!match&&lastTopic==='headache'&&/evet|hayır|biraz|çok|hala|hâlâ|geçmedi|azaldı/i.test(current))return 'Anladım. Umarım kısa zamanda rahatlarsın. Biraz dinlenme fırsatın var mı?';
 if(!match&&lastTopic==='unwell'&&/evet|hayır|bilmiyorum|biraz/i.test(current))return 'Anlıyorum. İstersen seni neyin yorduğunu konuşabiliriz.';
 if(!match)return 'Tam olarak ne demek istediğini anlayamadım. Biraz daha anlatır mısın?';
 const choices=match.replies.filter(x=>!recentBot.includes(normalize(x))&&!recentBot.some(y=>y.endsWith(normalize(x))));
 const base=pick(choices.length?choices:match.replies,post.who+'|'+match.id+'|'+earlier.length);
 const persona=personalities[post.who]||{};
 return (persona.prefix||'')+base;
}
window.BookCenterConversation={answer,version:'offline-v3',topicCount:topics.length};
})();