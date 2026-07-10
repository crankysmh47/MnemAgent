import assert from "node:assert/strict"; import test from "node:test";
import { selectNarrative, normalizeEvent, narrativeCopy } from "../src/public/scripts/narrative.js";
test("prioritizes contradiction and deduplicates",()=>{ const d=selectNarrative([{id:"a",type:"decayed"},{id:"b",type:"contradiction"},{id:"b",type:"contradiction"}],new Set()); assert.equal(d.featured.type,"contradiction"); assert.equal(d.events.filter(e=>e.featured).length,1); assert.equal(d.events.length,2); });
test("unknown event settles quietly",()=>{ const e=normalizeEvent({id:"x",type:"mystery"}); assert.equal(e.phase,"settled"); assert.equal(narrativeCopy({event:e},{}).eyebrow,"Settled"); });
