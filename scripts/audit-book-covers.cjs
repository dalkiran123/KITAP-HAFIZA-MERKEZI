#!/usr/bin/env node
// Non-destructive cover audit. Historical books are reported, not rewritten.
const fs=require('node:fs'),vm=require('node:vm');
const sandbox={window:{}};vm.runInNewContext(fs.readFileSync('catalog.js','utf8'),sandbox,{timeout:5000});
const books=Array.from(sandbox.window.KITAP_CATALOG||[]);
const validUrl=v=>typeof v==='string'&&/^https:\/\//i.test(v);
const hasCover=b=>validUrl(b.coverUrl)||validUrl(b.coverImage)||validUrl(b.cover);
const missing=books.filter(b=>!hasCover(b));
const isbn=books.filter(b=>String(b.isbn||'').trim());
const report={total:books.length,withRecordedCover:books.length-missing.length,withoutRecordedCover:missing.length,withIsbn:isbn.length,missing:missing.map(b=>({name:b.name,author:b.author}))};
console.log(JSON.stringify(report,null,2));
if(process.argv.includes('--strict')&&missing.length)process.exitCode=1;
