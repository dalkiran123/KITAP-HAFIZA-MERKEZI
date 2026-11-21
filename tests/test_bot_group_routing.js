/* Run: node tests/test_bot_group_routing.js */
'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('assets/bot-group-chat-v1.js','utf8');
const start=source.indexOf('const clean='),end=source.indexOf('function previousBotMessage(');
assert(start>=0&&end>start,'routing source exists');
const snippet=source.slice(start,end);
const context=vm.createContext({});
vm.runInContext(snippet+';globalThis.route=chooseResponders;',context);
const members=['Atlas','Mira','Arda'];
const cases=[
 ['Selam Atlas',['Atlas']],
 ['Arda, Mira\'yı tanıyor musun?',['Arda']],
 ['Atlas ve Arda konuşsun',['Atlas','Arda']],
 ['Arda ve Atlas konuşsun',['Atlas','Arda']],
 ['Mira ile Arda konuşsun',['Mira','Arda']],
 ['Mira, Atlas ne dedi?',['Mira']],
 ['Selam arkadaşlar',['Atlas','Mira','Arda']]
];
for(const [message,expected] of cases){
 assert.deepEqual(Array.from(context.route(message,members)),expected,message);
}
console.log('PASS: '+cases.length+' bot routing cases');
