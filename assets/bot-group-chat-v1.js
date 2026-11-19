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
const clean=s=>String(s||'').toLocaleLowerCase('tr-TR').replace(/[^a-zçğıöşü0-9 ]/g,' ').replace(/\\s+/g,' ').trim();
function distinctAnswer(name,message,history){
 const t=clean(message),style=styles[name]||{};
 if(/^(selam|merhaba|hey|günaydın|iyi akşamlar)( arkadaşlar| herkese| ekip)?$/.test(t))return style.hello||'Merhaba!';
 if(/aynı cevab|aynı yanıt|farklı cevap|farklı yanıt|hep aynı/.test(t))return style.repeat||name+' olarak kendi bakış açımdan yanıt vermeye çalışacağım.';
 const friend={id:name.toLowerCase(),name,kind:'bot'};
 let reply=window.BookCenterLocalMind?.answer(friend,message,history)||'Biraz daha ayrıntı paylaşır mısın?';
 const recent=history.filter(m=>m.role==='bot'&&m.text).slice(-8).map(m=>clean(m.text));
 if(recent.includes(clean(reply))){
   const subject=window.BookCenterLocalMind?.knowledgeState?.(friend)?.entries?.slice(-1)[0]?.fact;
   reply=subject?name+' olarak başka bir açı ekleyeyim: '+subject:(style.hello||name+' olarak farklı bir örnek üzerinden konuşalım mı?');
 }
 return reply;
}

function addressedBots(text,members){
 const normalized=clean(text);
 return members.filter(name=>new RegExp('(^| )'+clean(name)+'( |$)').test(normalized));
}
function chooseResponders(text,members){
 const mentioned=addressedBots(text,members);
 const first=clean(text).split(' ')[0];
 if(mentioned.length>1&&/(ne dedi|ne söyle|anladın|katılıyor musun|fikri|görüşü)/.test(clean(text))){
   const recipient=mentioned.find(n=>clean(n)===first);
   if(recipient)return [recipient];
 }
 if(mentioned.length)return mentioned;
 return members.slice(0,3);
}
function previousBotMessage(history,name){
 return [...history].reverse().find(m=>m.role==='bot'&&m.name===name&&typeof m.text==='string');
}
function contextAnswer(name,message,history,members){
 const t=clean(message),mentioned=addressedBots(message,members),other=mentioned.filter(n=>n!==name);
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
 const overlay=document.createElement('div');overlay.id='bc-group-modal';overlay.style.cssText='position:fixed;inset:0;z-index:110100;background:#000a;display:flex;align-items:center;justify-content:center;padding:10px';
 const panel=document.createElement('section');panel.style.cssText='width:min(680px,100%);height:min(780px,92dvh);background:#f8fafc;color:#142942;border-radius:18px;display:flex;flex-direction:column;overflow:hidden';
 const header=document.createElement('div');header.style.cssText='padding:13px;background:#17365a;color:white;display:flex;justify-content:space-between;align-items:center;gap:8px';
 const title=document.createElement('strong');title.textContent='💬 BOOK CENTER · Ortak Chat';
 const close=document.createElement('button');close.textContent='✕';close.style.cssText='background:transparent;color:white;border:0;font-size:22px';close.onclick=()=>overlay.remove();header.append(title,close);panel.append(header);
 const note=document.createElement('div');note.textContent='Sanal bot sohbeti. Harici yapay zekâ kullanılmaz. Mesajlar bu cihazda saklanır.';note.style.cssText='padding:8px 12px;font-size:12px;color:#536477';panel.append(note);
 const memberBox=document.createElement('div');memberBox.style.cssText='display:flex;gap:5px;flex-wrap:wrap;padding:7px 12px;border-bottom:1px solid #d7e0e8';
 const log=document.createElement('div');log.style.cssText='flex:1;overflow:auto;padding:12px;display:flex;flex-direction:column;gap:8px';
 const render=()=>{memberBox.replaceChildren();defaults.forEach(name=>{const b=document.createElement('button');const active=state.members.includes(name);b.textContent=(active?'✓ ':'+ ')+name;b.style.cssText='border:1px solid #adc2d5;border-radius:15px;padding:6px 9px;background:'+(active?'#cde7da':'#fff')+';color:#193b55';b.onclick=()=>{state.members=active?state.members.filter(n=>n!==name):[...state.members,name];save(state);render()};memberBox.append(b)});
 log.replaceChildren();state.messages.forEach(m=>{const item=document.createElement('div');item.style.cssText='align-self:'+(m.role==='user'?'flex-end':'flex-start')+';background:'+(m.role==='user'?'#d5eaff':'#fff')+';border-radius:12px;padding:9px 12px;max-width:88%;overflow-wrap:anywhere';const who=document.createElement('strong');who.textContent=m.role==='user'?'Sen':m.name;const body=document.createElement('div');body.textContent=m.text;if(m.replyTo&&m.replyTo!=='user'){const replyTag=document.createElement('small');replyTag.textContent='↳ '+m.replyTo+' adlı bota yanıt';replyTag.style.cssText='display:block;color:#5d7081;margin:3px 0';item.append(replyTag)}item.append(who,body);log.append(item)});log.scrollTop=log.scrollHeight};
 panel.append(memberBox,log);
 const form=document.createElement('form');form.style.cssText='display:flex;gap:7px;padding:10px;border-top:1px solid #d7e0e8';
 const input=document.createElement('input');input.placeholder='Gruba mesaj yaz...';input.maxLength=1000;input.style.cssText='flex:1;min-width:0;border:1px solid #aab9c9;border-radius:10px;padding:12px;font-size:16px';
 const send=document.createElement('button');send.type='submit';send.textContent='Gönder';send.style.cssText='background:#17365a;color:white;border:0;border-radius:10px;padding:10px';
 form.append(input,send);panel.append(form);
 let busy=false;
 form.onsubmit=e=>{e.preventDefault();const value=input.value.trim();if(!value||busy)return;input.value='';state.messages.push({role:'user',text:value,at:new Date().toISOString()});updateRelations(state.members);save(state);render();
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
 const tools=document.createElement('div');tools.style.cssText='display:flex;gap:8px;padding:6px 12px';
 const exportBtn=document.createElement('button');exportBtn.textContent='Sohbeti dışa aktar';exportBtn.onclick=()=>{const blob=new Blob([JSON.stringify(state,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='book-center-ortak-chat.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};
 const clearBtn=document.createElement('button');clearBtn.textContent='Sohbeti sil';clearBtn.onclick=()=>{if(!confirm('Ortak sohbet geçmişi silinsin mi?'))return;state.messages=[];save(state);render()};
 const relationBtn=document.createElement('button');relationBtn.textContent='🤝 Arkadaşlıklar';relationBtn.onclick=()=>{const pairs=Object.entries(getRelations()).sort((a,b)=>b[1]-a[1]).slice(0,10);alert(pairs.length?pairs.map(([names,count])=>names.replace('|',' & ')+': '+count+' ortak sohbet').join('\\n'):'Henüz ortak sohbet kaydı yok. Bu puanlar yalnızca birlikte sohbet etme sıklığını gösterir.')};tools.append(exportBtn,clearBtn,relationBtn);panel.insertBefore(tools,form);
 overlay.append(panel);overlay.onclick=e=>{if(e.target===overlay)overlay.remove()};document.body.append(overlay);render();input.focus();
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount);else mount();
})();