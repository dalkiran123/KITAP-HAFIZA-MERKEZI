// Read-only regression checks for the single-page application.
import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import vm from 'node:vm';
const html=readFileSync('index.html','utf8');
const scripts=[...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/gi)].map(m=>m[1]).filter(Boolean);
assert.ok(scripts.length>0,'Inline scripts should exist');
for(const [i,code] of scripts.entries())new vm.Script(code,{filename:'index.html:inline-'+i});
const videoHtml=readFileSync('documentaries.html','utf8');
const videoScripts=[...videoHtml.matchAll(/<script(?:\\s[^>]*)?>([\\s\\S]*?)<\\/script>/gi)].map(m=>m[1]).filter(Boolean);
assert.ok(videoScripts.length>0,'Video page inline script should exist');
for(const [i,code] of videoScripts.entries())new vm.Script(code,{filename:'documentaries.html:inline-'+i});
for(const file of ['catalog.js','catalog-queue.js'])new vm.Script(readFileSync(file,'utf8'),{filename:file});
assert.match(html,/catalog-added/,'Catalog addition timestamp missing');
assert.match(html,/catalog\.slice\(\)\.sort/,'Ready-first sorting missing');
assert.match(html,/kitap-hafiza-current-reading-v1/,'Recommendation rotation missing');
assert.match(html,/localStorage\.getItem\(key\)/,'Existing local book data key must be retained');
console.log('PASS: JS syntax and catalog/recommendation regression checks');
