/* Friends V6 private chat UI. Requires authenticated server API configuration. */
(()=>{'use strict';
const root=document.getElementById('friendsChat');if(!root)return;
const names=()=>{try{return window.arenaBotWorld?.names()?.slice(0,10)||[]}catch{return []}};
const fallback=['Atlas','Mira','Deniz','Arda','Luna','Nova','Orion','Ada','Bilge','Zirve'];
const api=()=>{const value=window.BOOKCENTER_CHAT_API_URL;return typeof value==='string'&&/^https:\/\//.test(value)?value:null};
const make=(tag,text)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;return e};
const select=make('select'),log=make('div'),input=make('textarea'),send=make('button','Gönder'),status=make('p');
select.setAttribute('aria-label','Sanal arkadaş seç');log.className='friendsChatLog';log.setAttribute('aria-live','polite');
input.placeholder='Arkadaşına mesaj yaz...';input.rows=2;input.maxLength=1000;send.type='button';status.className='muted';
root.append(select,log,input,send,status);
function populate(){const prior=select.value;select.replaceChildren();(names().length===10?names():fallback).forEach((name,i)=>{const o=make('option',name);o.value=String(i+1);select.append(o)});if(prior)select.value=prior}
function render(messages){log.replaceChildren();for(const m of messages){const line=make('div',m.body);line.className='friendsChatBubble '+(m.sender==='user'?'mine':'theirs');log.append(line)}log.scrollTop=log.scrollHeight}
async function load(){const url=api();send.disabled=!url;input.disabled=!url;if(!url){status.textContent='Mesajlaşma sunucusu henüz bağlanmadı. Bu ekran hazırlık aşamasında.';render([]);return}status.textContent='Konuşma yükleniyor...';try{const res=await fetch(url+'?person_id='+encodeURIComponent(select.value),{credentials:'include',cache:'no-store'});if(res.status===401){status.textContent='Mesajlaşmak için sunucu oturumu açılmalı.';return}if(!res.ok)throw Error('Sunucu yanıtı: '+res.status);const data=await res.json();render(Array.isArray(data.messages)?data.messages:[]);status.textContent='Sanal karakterle özel sohbet';}catch(e){status.textContent='Sohbet yüklenemedi: '+e.message}}
send.onclick=async()=>{const url=api(),message=input.value.trim();if(!url||!message)return;send.disabled=true;status.textContent='Yanıt bekleniyor...';try{const res=await fetch(url,{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({person_id:Number(select.value),message})});if(!res.ok)throw Error('Sunucu yanıtı: '+res.status);input.value='';await load()}catch(e){status.textContent='Mesaj gönderilemedi: '+e.message}finally{send.disabled=!api()?true:false}};
select.onchange=load;populate();load();window.addEventListener('arena-botnames-updated',()=>{populate();load()});
})();