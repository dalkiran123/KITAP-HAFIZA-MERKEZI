/* BOOK CENTER group chat: offline fictional bots, persistent on-device history. */
(()=>{'use strict';
const KEY='bc_group_chat_v1',MAX=500;
const defaults=['Atlas','Mira','Deniz','Arda','Luna','Nova','Orion','Ada','Bilge','Zirve'];
const load=()=>{try{const x=JSON.parse(localStorage.getItem(KEY)||'null');return x&&Array.isArray(x.messages)?x:null}catch{return null}};
const save=x=>{try{localStorage.setItem(KEY,JSON.stringify({...x,messages:x.messages.slice(-MAX)}))}catch{}};
function mount(){
 if(document.getElementById('bc-group-open'))return;
 const btn=document.createElement('button');btn.id='bc-group-open';btn.type='button';btn.textContent='💬 Ortak Chat';btn.setAttribute('aria-label','Sanal arkadaşlar ortak sohbet');
 btn.style.cssText='position:fixed;right:12px;bottom:76px;z-index:89999;border:0;border-radius:22px;background:#183a60;color:white;padding:12px 16px;box-shadow:0 4px 18px #0005;font-weight:800;cursor:pointer';
 btn.onclick=open;document.body.append(btn);
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
 log.replaceChildren();state.messages.forEach(m=>{const item=document.createElement('div');item.style.cssText='align-self:'+(m.role==='user'?'flex-end':'flex-start')+';background:'+(m.role==='user'?'#d5eaff':'#fff')+';border-radius:12px;padding:9px 12px;max-width:88%;overflow-wrap:anywhere';const who=document.createElement('strong');who.textContent=m.role==='user'?'Sen':m.name;const body=document.createElement('div');body.textContent=m.text;item.append(who,body);log.append(item)});log.scrollTop=log.scrollHeight};
 panel.append(memberBox,log);
 const form=document.createElement('form');form.style.cssText='display:flex;gap:7px;padding:10px;border-top:1px solid #d7e0e8';
 const input=document.createElement('input');input.placeholder='Gruba mesaj yaz...';input.maxLength=1000;input.style.cssText='flex:1;min-width:0;border:1px solid #aab9c9;border-radius:10px;padding:12px;font-size:16px';
 const send=document.createElement('button');send.type='submit';send.textContent='Gönder';send.style.cssText='background:#17365a;color:white;border:0;border-radius:10px;padding:10px';
 form.append(input,send);panel.append(form);
 let busy=false;
 form.onsubmit=e=>{e.preventDefault();const value=input.value.trim();if(!value||busy)return;input.value='';state.messages.push({role:'user',text:value,at:new Date().toISOString()});save(state);render();
 const members=state.members.slice();if(!members.length)return;
 busy=true;send.disabled=true;
 // Reply from up to three participants, sequentially; every turn uses the shared conversation context.
 const chosen=members.slice(0,3);let index=0;
 const next=()=>{if(!overlay.isConnected){busy=false;return}if(index>=chosen.length){busy=false;send.disabled=false;return}
 const name=chosen[index++],friend={id:name.toLowerCase(),name,kind:'bot'};
 const answer=window.BookCenterLocalMind?.answer(friend,value,state.messages)||'Bu konuyu biraz daha açabilir misin?';
 const typing=document.createElement('div');typing.textContent=name+' yazıyor…';typing.style.cssText='padding:9px;color:#596e84';log.append(typing);log.scrollTop=log.scrollHeight;
 setTimeout(()=>{if(!overlay.isConnected)return;typing.remove();state.messages.push({role:'bot',name,text:answer,at:new Date().toISOString()});save(state);render();next()},Math.min(1600,450+answer.length*12))};
 next()};
 const tools=document.createElement('div');tools.style.cssText='display:flex;gap:8px;padding:6px 12px';
 const exportBtn=document.createElement('button');exportBtn.textContent='Sohbeti dışa aktar';exportBtn.onclick=()=>{const blob=new Blob([JSON.stringify(state,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='book-center-ortak-chat.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};
 const clearBtn=document.createElement('button');clearBtn.textContent='Sohbeti sil';clearBtn.onclick=()=>{if(!confirm('Ortak sohbet geçmişi silinsin mi?'))return;state.messages=[];save(state);render()};
 tools.append(exportBtn,clearBtn);panel.insertBefore(tools,form);
 overlay.append(panel);overlay.onclick=e=>{if(e.target===overlay)overlay.remove()};document.body.append(overlay);render();input.focus();
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount);else mount();
})();