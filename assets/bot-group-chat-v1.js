/* BOOK CENTER group chat: offline fictional bots, persistent on-device history. */
(()=>{'use strict';
const KEY='bc_group_chat_v1',MAX=500,REL='bc_bot_relations_v1';
const getRelations=()=>{try{return JSON.parse(localStorage.getItem(REL)||'{}')||{}}catch{return {}}};
const updateRelations=members=>{const rel=getRelations();for(let i=0;i<members.length;i++)for(let j=i+1;j<members.length;j++){const k=[members[i],members[j]].sort().join('|');rel[k]=Math.min(100,(rel[k]||0)+1)}try{localStorage.setItem(REL,JSON.stringify(rel))}catch{}return rel};
const defaults=['Atlas','Mira','Deniz','Arda','Luna','Nova','Orion','Ada','Bilge','Zirve'];
const load=()=>{try{const x=JSON.parse(localStorage.getItem(KEY)||'null');return x&&Array.isArray(x.messages)?x:null}catch{return null}};
const save=x=>{try{localStorage.setItem(KEY,JSON.stringify({...x,messages:x.messages.slice(-MAX)}))}catch{}};
function mount(){
 if(document.getElementById('bc-group-open'))return;
 const btn=document.createElement('button');btn.id='bc-group-open';btn.type='button';btn.textContent='💬 Ortak Chat';btn.setAttribute('aria-label','Sanal arkadaşlar ortak sohbet');
 btn.style.cssText='position:fixed;right:12px;bottom:76px;z-index:89999;border:0;border-radius:22px;background:#183a60;color:white;padding:12px 16px;box-shadow:0 4px 18px #0005;font-weight:800;cursor:pointer';
 btn.onclick=open;document.body.append(btn);
}
const styles={
 Atlas:{hello:'Selam! Bugün konuşmak istediğiniz konuyu birlikte çözümleyelim.',repeat:'Haklısın, aynı yanıtı tekrarlamak iyi bir sohbet değil. Ben konuyu mantıksal yönden ele alacağım.'},
 Mira:{hello:'Merhaba! Bugün okuduğun bir hikâye ya da aklında kalan bir sahne var mı?',repeat:'Ben de aynı cümleyi görünce sıkılırdım. Bu kez merak ettiğim bir ayrıntıyı sorayım: sen nasıl bir sohbet istersin?'},
 Arda:{hello:'Selam ekip! Bugün bir satranç meydan okuması mı yapalım, yoksa kitap yarışı mı?',repeat:'Eleştiri kabul! Bundan sonra kendi stratejimi ve görüşümü ortaya koyacağım.'},
 Deniz:{hello:'Merhaba. Bugün biraz sakin sohbet edelim mi? Doğayla ilgili bir şey keşfettin mi?'},
 Luna:{hello:'Hoş geldin. Bugün aklında kalan bir dize veya güzel bir düşünce var mı?'},
 Nova:{hello:'Hey! Yeni bir fikir ya da teknoloji haberi konuşmaya var mısınız?'},
 Orion:{hello:'Selam. Bugün geçmişten ilginç bir olayın nedenlerini konuşalım mı?'},
 Ada:{hello:'Merhaba, aramıza hoş geldin. Bugün kendini nasıl hissediyorsun?'},
 Bilge:{hello:'Selam. Bugün birlikte düşünmeye değer bir soru seçelim mi?'},
 Zirve:{hello:'Merhaba! Bugün küçük de olsa hangi hedefe yaklaşmak istersin?'}
};
const clean=s=>String(s||'').toLocaleLowerCase('tr-TR').replace(/[^a-zçğıöşü0-9 ]/g,' ').replace(/\s+/g,' ').trim();
function distinctAnswer(name,message,history){
 const t=clean(message),style=styles[name]||{};
 if(/^(selam|merhaba|hey|günaydın|iyi akşamlar)( arkadaşlar| herkese| ekip)?$/.test(t))return style.hello||'Merhaba!';
 if(/aynı cevab|aynı yanıt|farklı cevap|farklı yanıt|hep aynı/.test(t))return style.repeat||name+' olarak kendi bakış açımdan yanıt vermeye çalışacağım.';
 const friend={id:name.toLowerCase(),name,kind:'bot'};
 let reply=window.BookCenterLocalMind?.answer(friend,message,history)||'Biraz daha ayrıntı paylaşır mısın?';
 const recent=history.filter(m=>m.role==='bot'&&m.text).slice(-8).map(m=>clean(m.text));
 if(recent.includes(clean(reply))){
   reply=name==='Atlas'?'Aynı cümleyi tekrarlamak istemiyorum. Bu konunun nedenini birlikte inceleyelim.':name==='Mira'?'Aynı konudan devam edelim. Senin görüşünü biraz daha merak ediyorum.':name==='Arda'?'Aynı konu üzerinde farklı bir önerim var: küçük bir örnekle sınayalım.':'Aynı konudan devam edelim. Önceki yanıtı tekrarlamak yerine bir ayrıntı sorayım: sen ne düşünüyorsun?';
 }
 return reply;
}

function addressedBots(text,members){
 const normalized=clean(text);
 return members.filter(name=>new RegExp('(^| )'+clean(name)+'( |$)').test(normalized));
}
function chooseResponders(text,members){
 const mentioned=addressedBots(text,members);
 const normalized=clean(text),first=normalized.split(' ')[0];
 if(mentioned.length>1){
   // A conjunction between named bots means a group request, even when the names
   // occur in reverse order relative to the configured member list.
   const namesInText=[...mentioned].sort((a,b)=>normalized.indexOf(clean(a))-normalized.indexOf(clean(b)));
   const coordinated=namesInText.some((name,i)=>{
     if(i===0)return false;
     const prev=namesInText[i-1];
     const between=normalized.slice(normalized.indexOf(clean(prev))+clean(prev).length,normalized.indexOf(clean(name))).trim();
     return /^(ve|ile|ve birlikte|ile birlikte)$/.test(between);
   });
   if(coordinated)return mentioned;
   const recipient=mentioned.find(n=>clean(n)===first);
   if(recipient)return [recipient];
 }
 if(mentioned.length)return mentioned;
 return members.slice(0,3);
}
function previousBotMessage(history,name){
 return [...history].reverse().find(m=>m.role==='bot'&&m.name===name&&typeof m.text==='string');
}
/* Fictional defaults, editable locally by the user. No real-world identities implied. */
const characterDefaults={
 Atlas:{age:34,job:'veri analisti',interest:'bilim ve araştırma'},
 Mira:{age:29,job:'edebiyat öğretmeni',interest:'romanlar ve yazarlık'},
 Deniz:{age:32,job:'çevre mühendisi',interest:'doğa ve ekoloji'},
 Arda:{age:27,job:'satranç eğitmeni',interest:'strateji ve rekabet'},
 Luna:{age:30,job:'editör',interest:'şiir ve edebiyat'},
 Nova:{age:26,job:'yazılım geliştirici',interest:'teknoloji'},
 Orion:{age:41,job:'tarih araştırmacısı',interest:'tarih'},
 Ada:{age:35,job:'rehberlik danışmanı',interest:'psikoloji'},
 Bilge:{age:46,job:'felsefe öğretmeni',interest:'felsefe'},
 Zirve:{age:33,job:'proje koordinatörü',interest:'kişisel gelişim'}
};
const CHARACTER_KEY='bc_bot_character_profiles_v1';
function characterStore(){try{const v=JSON.parse(localStorage.getItem(CHARACTER_KEY)||'{}');return v&&typeof v==='object'?v:{}}catch{return {}}}
function character(name){return {...characterDefaults[name],...(characterStore()[name]||{})}}
function updateCharacter(name,changes){
 const all=characterStore();all[name]={...(all[name]||{}),...changes};
 try{localStorage.setItem(CHARACTER_KEY,JSON.stringify(all));return true}catch{return false}
}
function characterAnswer(name,message,members){
 const t=clean(message),others=addressedBots(message,members).filter(n=>n!==name);
 const target=others[0]||name,person=character(target);
 if(!person)return null;
 // Users may assign a fictional age or profession using explicit instructions.
 if(target===name){
   const age=t.match(/(?:yaşın|yaşını|senin yaşın)\s+(\d{1,2})\s+olsun/);
   if(age){const value=Number(age[1]);return value>=18&&value<=90&&updateCharacter(name,{age:value})?'Tamam, kurgusal yaşımı '+value+' olarak kaydettim.':'Yaş için 18 ile 90 arasında bir değer seçmelisin.'}
   const job=t.match(/(?:mesleğin|mesleğini|işin)\s+(.{3,55}?)\s+olsun$/);
   if(job){const value=job[1].trim();return updateCharacter(name,{job:value})?'Tamam, kurgusal mesleğimi '+value+' olarak kaydettim.':'Bu cihazda kaydedemedim.'}
 }
 if(/(kaç yaş|yaşın kaç|yaşı kaç|kaç yaşında|doğum yılın)/.test(t))return target===name?'Ben '+name+'. Kurgusal karakter yaşım '+person.age+'.':target+' '+person.age+' yaşında bir sanal karakter.';
 if(/(mesle|ne iş yap|işin ne|nerede çalış|ne olarak çalış)/.test(t))return target===name?'Kurgusal mesleğim '+person.job+'.':target+' kurgusal olarak '+person.job+' mesleğini yapıyor.';
 if(/(kendini tanıt|kendinden bahset|kim olduğunu anlat|kimsin)/.test(t))return 'Ben '+name+'. '+person.age+' yaşında, '+person.job+' olarak kurgulanmış bir sanal karakterim. '+person.interest+' ilgimi çekiyor.';
 if(/(ilgi alanın|nelerden hoşlan|neye ilgin)/.test(t))return 'En çok '+person.interest+' konularına ilgi duyuyorum.';
 return null;
}

/* V11: shared factual memory, user/bot subject resolution, persistent across sessions. */
const USER_MEMORY_KEY='bc_group_user_facts_v1';
function userFacts(){try{return JSON.parse(localStorage.getItem(USER_MEMORY_KEY)||'{}')||{}}catch{return {}}}
function rememberUser(message){
 const t=clean(message), facts=userFacts();
 let m=t.match(/(?:benim adım|benim ismim|adım|ismim|ben)\s+([a-zçğıöşü]{2,24})(?=\s|$)/);
 if(m&&!['kaç','ne','kim','nasıl','nerede','yaşında','bir','de'].includes(m[1]))facts.name=m[1].charAt(0).toLocaleUpperCase('tr-TR')+m[1].slice(1);
 m=t.match(/(?:ben\s+|)(\d{1,3})\s+yaşındayım/);
 if(m&&Number(m[1])>=1&&Number(m[1])<=110)facts.age=Number(m[1]);
 m=t.match(/(?:ben\s+|)(?:bir\s+)?(mali müşavir|muhasebeci|öğretmen|mühendis|doktor|avukat|yazılımcı|öğrenci|emekli)(?:im|ım|um|üm|yim|yım|yum|yüm)?(?=\s|$)/);
 if(m)facts.job=m[1];
 if(Object.keys(facts).length){facts.updated=new Date().toISOString();try{localStorage.setItem(USER_MEMORY_KEY,JSON.stringify(facts))}catch{}}
}
function userQuestion(message){
 const t=clean(message),self=/(?:\bben\b|\bbeni\b|\bbenim\b|\bbana\b)/.test(t);
 const asksAge=/(kaç yaş|yaşım|yaşındayım|yaşımı)/.test(t);
 const asksJob=/(ne iş|mesleğ|işim|işimi|mesleğim)/.test(t);
 const asksName=/(adım ne|ismim ne|adımı|ismimi|beni tanı|beni hatırla|beni bili)/.test(t);
 if(!self||!(asksAge||asksJob||asksName))return null;
 const f=userFacts(),parts=[];
 if(asksName||/beni tanı|beni hatırla|beni bili/.test(t))parts.push(f.name?'Adın '+f.name:'Adını henüz bilmiyorum');
 if(asksAge)parts.push(f.age?'Yaşın '+f.age:'Yaşını henüz bilmiyorum');
 if(asksJob)parts.push(f.job?'Mesleğin '+f.job:'Mesleğini henüz bilmiyorum');
 if(!parts.length&&f.name)parts.push('Seni '+f.name+' olarak tanıyorum');
 return parts.join(', ')+'.';
}
function biographyQuestion(name,message){
 const t=clean(message),p=character(name);
 if(/(kendinizi tanıt|kendinizi anlat|kendinizden bahset|kendini tanıt|kendinden bahset|kim olduğun)/.test(t))return 'Ben '+name+'. '+p.age+' yaşındayım, kurgusal mesleğim '+p.job+'. İlgi alanlarım '+p.interest+'.';
 const age=/(kaç yaş|yaşın|yaşınız)/.test(t),job=/(ne iş|mesleğ|işiniz)/.test(t),interest=/(ilgi alan|nelerden hoşlan|neye ilgin)/.test(t);
 if(/\bben\b|\bbeni\b|\bbenim\b/.test(t))return null;
 if(interest)return 'Ben '+name+'. İlgi alanlarım '+p.interest+'.';
 if(age&&job)return 'Ben '+name+'. '+p.age+' yaşındayım ve kurgusal mesleğim '+p.job+'.';
 return null;
}

function contextAnswer(name,message,history,members){
 const t=clean(message),mentioned=addressedBots(message,members),other=mentioned.filter(n=>n!==name);
 const aboutUser=userQuestion(message);if(aboutUser)return aboutUser;
 const biography=biographyQuestion(name,message);if(biography)return biography;
 const bio=characterAnswer(name,message,members);if(bio)return bio;

 const askingAboutBot=/(ne dedi|ne söyle|anladın|katılıyor musun|fikri|görüşü|tanıyor musun|tanıyor musunuz|tanıyormusunuz|birbirinizi tanı)/.test(t);
 if(askingAboutBot&&other.length){
   const target=other[0],prior=previousBotMessage(history,target);
   if(/tanı|birbirinizi/.test(t))return target+' ile aynı sanal sohbet grubundayız. Onun ilgi alanını ve burada yazdıklarını biliyorum; gerçek hayatta tanışmış değiliz.';
   if(prior)return target+' az önce şöyle dedi: “'+prior.text.slice(0,145)+'” Benim yorumum: '+(name==='Mira'?'Bu fikrin ayrıntısını merak ettim.':name==='Arda'?'Bunu bir örnekle sınayabiliriz.':'Bunu aynı konu üzerinden değerlendirebiliriz.');
   return target+' henüz bu sohbette bir şey söylemedi. Önce onun görüşünü alalım.';
 }
 if(/aynı konu|farklı konu|karışıyor|konudan sap/.test(t))return 'Haklısın. Aynı konuşma konusuna bağlı kalalım. Yeni bir konu açmadan son mesajını ele alacağım.';
 return null;
}
function peerComment(speaker,previousName,previousText){
 const short=previousText.slice(0,105);
 const variants={
 Atlas:'@'+previousName+' söylediklerini aynı konu üzerinde değerlendireyim: “'+short+'” Önce hangi noktada anlaştığımızı netleştirelim.',
 Mira:'@'+previousName+' “'+short+'” demiştin. Bunun hangi kısmını daha çok merak ediyorsun?',
 Arda:'@'+previousName+' “'+short+'” fikrini duydum. Bunu nasıl test edebileceğimizi düşünelim.',
 Deniz:'@'+previousName+' seni dinledim. Konuyu acele etmeden açabiliriz.',
 Luna:'@'+previousName+' söylediğin düşünce üzerinde biraz daha durmak isterim.',
 Nova:'@'+previousName+' bu fikirle ilgili küçük bir deneme yapabiliriz.',
 Orion:'@'+previousName+' söylediğin görüşün gerekçesini merak ettim.',
 Ada:'@'+previousName+' söylediklerin önemli. Sen nasıl hissediyorsun?',
 Bilge:'@'+previousName+' söylediğin noktada temel soru ne olabilir?',
 Zirve:'@'+previousName+' bunu somut bir sonraki adıma çevirebiliriz.'
 };
 return variants[speaker]||'@'+previousName+' görüşünü biraz açar mısın?';
}
function open(){
 document.getElementById('bc-group-modal')?.remove();
 const state=load()||{members:['Atlas','Mira','Arda'],messages:[]};
 const style=document.createElement('style');style.id='bc-chat-compact-style';document.getElementById(style.id)?.remove();style.textContent='#bc-group-modal, #bc-group-modal *{box-sizing:border-box!important}#bc-group-modal{font-size:14px!important;line-height:1.4!important}#bc-group-modal button{font-family:inherit!important;font-size:13px!important;line-height:1.2!important;min-height:0!important;min-width:0!important;box-shadow:none!important;letter-spacing:normal!important;text-transform:none!important}#bc-group-modal input{font-family:inherit!important;font-size:16px!important;min-height:0!important}#bc-group-modal strong{line-height:1.25!important}';document.head.append(style);
 const overlay=document.createElement('div');overlay.id='bc-group-modal';overlay.style.cssText='position:fixed;inset:0;z-index:110100;background:#000a;display:flex;align-items:stretch;justify-content:center;padding:0';
 const panel=document.createElement('section');panel.style.cssText='width:100%;max-width:760px;height:100%;height:100dvh;position:relative;background:#e9f0ed;color:#142942;border-radius:0;display:flex;flex-direction:column;overflow:hidden';
 const header=document.createElement('div');header.style.cssText='padding:calc(6px + env(safe-area-inset-top, 0px)) 12px 7px;background:#17365a;color:white;display:flex;justify-content:space-between;align-items:center;gap:8px';
 const title=document.createElement('strong');title.textContent='💬 Ortak Chat';title.style.cssText='font-size:16px!important;flex:1';
 const close=document.createElement('button');close.textContent='✕';close.style.cssText='background:transparent!important;color:white!important;border:0!important;padding:5px 9px!important;font-size:20px!important';close.onclick=()=>overlay.remove();const menu=document.createElement('button');menu.textContent='⋯';menu.title='Sohbet seçenekleri';menu.style.cssText='background:transparent!important;color:white!important;border:0!important;padding:5px 10px!important;font-size:22px!important';header.append(title,menu,close);panel.append(header);
 const note=document.createElement('div');note.textContent='Sanal bot sohbeti · Mesajlar bu cihazda saklanır';note.style.cssText='padding:5px 12px;font-size:11px;color:#536477;background:#f7faf9';panel.append(note);note.style.display='none';
 const memberBox=document.createElement('div');memberBox.style.cssText='display:flex;gap:5px;flex-wrap:nowrap;padding:6px 9px;border-bottom:1px solid #d7e0e8;overflow-x:auto;overflow-y:hidden;flex-shrink:0;background:#f7faf9';
 const log=document.createElement('div');log.style.cssText='flex:1;min-height:0;overflow-y:auto;padding:12px 10px;display:flex;flex-direction:column;gap:9px;background:#e9f0ed';
 const palette={Atlas:['#dceafb','#174779'],Mira:['#fce0ec','#8b2d5b'],Arda:['#ffebd2','#85520c'],Deniz:['#d8f1e8','#246d55'],Luna:['#e9e0fa','#63468f'],Nova:['#fff1bb','#765a00'],Orion:['#e1e7ed','#40576e'],Ada:['#fce4df','#994c3f'],Bilge:['#e6e3d6','#665e3b'],Zirve:['#e1ebcf','#536c25']};
 const render=()=>{memberBox.replaceChildren();defaults.forEach(name=>{const b=document.createElement('button');const active=state.members.includes(name);b.textContent=(active?'✓ ':'+ ')+name;b.style.cssText='border:1px solid #adc2d5!important;border-radius:14px!important;padding:5px 9px!important;white-space:nowrap!important;flex-shrink:0!important;background:'+(active?'#cde7da':'#fff')+';color:#193b55';b.onclick=()=>{state.members=active?state.members.filter(n=>n!==name):[...state.members,name];save(state);render()};memberBox.append(b)});
 log.replaceChildren();state.messages.forEach(m=>{
 const mine=m.role==='user',colors=palette[m.name]||['#fff','#17365a'];
 const item=document.createElement('div');
 item.style.cssText='align-self:'+(mine?'flex-end':'flex-start')+';background:'+(mine?'#d1f2d5':colors[0])+';color:#182c3d;border-radius:'+(mine?'15px 15px 4px 15px':'15px 15px 15px 4px')+';padding:7px 10px;max-width:82%;min-width:90px;overflow-wrap:anywhere;box-shadow:0 1px 3px #0002';
 const who=document.createElement('strong');who.textContent=mine?'Sen':m.name;who.style.cssText='display:block;font-size:12px;margin-bottom:3px;color:'+(mine?'#28663c':colors[1]);
 if(m.replyTo&&m.replyTo!=='user'){const replyTag=document.createElement('small');replyTag.textContent='↳ '+m.replyTo+' adlı bota yanıt';replyTag.style.cssText='display:block;color:#5d7081;margin:3px 0';item.append(replyTag)}
 const body=document.createElement('div');body.textContent=m.text;body.style.cssText='font-size:14px;line-height:1.35;white-space:pre-wrap';
 const time=document.createElement('small');const d=new Date(m.at||'');time.textContent=Number.isNaN(d.getTime())?'':d.toLocaleTimeString('tr-TR',{hour:'2-digit',minute:'2-digit'});time.style.cssText='display:block;text-align:right;opacity:.6;font-size:10px;margin-top:3px';
 item.append(who,body,time);log.append(item)
});log.scrollTop=log.scrollHeight};
 panel.append(memberBox,log);
 const form=document.createElement('form');form.style.cssText='display:flex;gap:7px;padding:7px 9px calc(7px + env(safe-area-inset-bottom, 0px));border-top:1px solid #d7e0e8;background:#f7faf9';
 const input=document.createElement('input');input.placeholder='Gruba mesaj yaz...';input.maxLength=1000;input.style.cssText='flex:1;min-width:0;border:1px solid #aab9c9!important;border-radius:10px!important;padding:9px!important;font-size:16px!important;height:42px!important';
 const send=document.createElement('button');send.type='submit';send.textContent='Gönder';send.style.cssText='background:#17365a!important;color:white!important;border:0!important;border-radius:10px!important;padding:9px 12px!important;height:42px!important';
 form.append(input,send);panel.append(form);
 let busy=false;
 form.onsubmit=e=>{e.preventDefault();const value=input.value.trim();if(!value||busy)return;input.value='';state.messages.push({role:'user',text:value,at:new Date().toISOString()});rememberUser(value);updateRelations(state.members);save(state);render();
 const members=state.members.slice();if(!members.length)return;
 busy=true;send.disabled=true;
 // Reply from up to three participants, sequentially; every turn uses the shared conversation context.
 const chosen=chooseResponders(value,members);let index=0;
 const next=()=>{if(!overlay.isConnected){busy=false;return}if(index>=chosen.length){
 // One optional peer-to-peer response, never a recursive chain.
 const last=state.messages[state.messages.length-1];
 const peers=members.filter(n=>n!==last?.name);
 const peer=peers.length>0&&last?.role==='bot'&&chosen.length>1?peers.find(n=>!chosen.includes(n))||peers[0]:null;
 if(peer&&chosen.length>1&&chosen.length<4&&!addressedBots(value,members).length){
   const peerText=peerComment(peer,last.name,last.text);
   state.messages.push({role:'bot',name:peer,text:peerText,replyTo:last.name,at:new Date().toISOString()});
   const k=[peer,last.name].sort().join('|'),relations=getRelations();relations[k]=Math.min(100,(relations[k]||0)+1);try{localStorage.setItem(REL,JSON.stringify(relations))}catch{}
   save(state);render();
 }
 busy=false;send.disabled=false;return}
 const name=chosen[index++],friend={id:name.toLowerCase(),name,kind:'bot'};
 const answer=contextAnswer(name,value,state.messages,members)||distinctAnswer(name,value,state.messages);
 const typing=document.createElement('div');typing.textContent=name+' yazıyor…';typing.style.cssText='padding:9px;color:#596e84';log.append(typing);log.scrollTop=log.scrollHeight;
 setTimeout(()=>{if(!overlay.isConnected)return;typing.remove();state.messages.push({role:'bot',name,text:answer,replyTo:'user',at:new Date().toISOString()});save(state);render();next()},Math.min(1600,450+answer.length*12))};
 next()};
 const tools=document.createElement('div');tools.style.cssText='display:none;position:absolute;right:12px;top:calc(54px + env(safe-area-inset-top, 0px));z-index:4;flex-direction:column;gap:5px;padding:9px;background:white;border:1px solid #cbd5df;border-radius:12px;box-shadow:0 6px 20px #0003';menu.onclick=()=>{tools.style.display=tools.style.display==='none'?'flex':'none'};
 const exportBtn=document.createElement('button');exportBtn.textContent='Sohbeti dışa aktar';exportBtn.onclick=()=>{const blob=new Blob([JSON.stringify(state,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='book-center-ortak-chat.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};
 const clearBtn=document.createElement('button');clearBtn.textContent='Sohbeti sil';clearBtn.onclick=()=>{if(!confirm('Ortak sohbet geçmişi silinsin mi?'))return;state.messages=[];save(state);render()};
 const relationBtn=document.createElement('button');relationBtn.textContent='🤝 Arkadaşlıklar';relationBtn.onclick=()=>{const pairs=Object.entries(getRelations()).sort((a,b)=>b[1]-a[1]).slice(0,10);alert(pairs.length?pairs.map(([names,count])=>names.replace('|',' & ')+': '+count+' ortak sohbet').join('\\n'):'Henüz ortak sohbet kaydı yok. Bu puanlar yalnızca birlikte sohbet etme sıklığını gösterir.')};tools.append(exportBtn,clearBtn,relationBtn);panel.insertBefore(tools,form);[exportBtn,clearBtn,relationBtn].forEach(b=>b.style.cssText='background:#eef3f7!important;color:#193b55!important;border:0!important;border-radius:8px!important;padding:9px 12px!important;text-align:left!important;white-space:nowrap!important');
 overlay.append(panel);overlay.onclick=e=>{if(e.target===overlay)overlay.remove()};document.body.append(overlay);render();input.focus();
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount);else mount();
})();