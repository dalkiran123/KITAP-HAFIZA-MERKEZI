#!/usr/bin/env node
// Validate addedAt for new catalog entries without rewriting historical entries.
const fs=require('fs'),cp=require('child_process'),vm=require('vm');
function parse(source){const sandbox={window:{}};vm.runInNewContext(source,sandbox,{timeout:3000});return Array.from(sandbox.window.KITAP_CATALOG||[])}
const now=parse(fs.readFileSync('catalog.js','utf8'));
let before=[];try{before=parse(cp.execFileSync('git',['show','HEAD^:catalog.js'],{encoding:'utf8'}))}catch(e){console.log('No previous catalog revision; checking only entries that already have addedAt.');before=now}
const key=b=>String(b.name||'').trim().toLocaleLowerCase('tr-TR')+'|'+String(b.author||'').trim().toLocaleLowerCase('tr-TR');
const old=new Set(before.map(key)),seen=new Set(),errors=[];
for(const b of now){const k=key(b);if(seen.has(k))errors.push('Duplicate catalog entry: '+b.name);seen.add(k);if(old.has(k))continue;
 if(typeof b.addedAt!=='string'||!/\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?(?:Z|[+-]\d\d:\d\d)$/.test(b.addedAt)||!Number.isFinite(Date.parse(b.addedAt)))errors.push('New entry missing valid timezone-aware addedAt: '+b.name);
}
if(errors.length){console.error(errors.join('\n'));process.exit(1)}
console.log('addedAt validation passed. New entries: '+now.filter(b=>!old.has(key(b))).length);
