import assert from "node:assert/strict"; import test from "node:test";
import { selectNarrative, normalizeEvent, narrativeCopy, archiveStory, EVENT_PRIORITY } from "../src/public/scripts/narrative.js";
test("prioritizes contradiction and deduplicates",()=>{ const d=selectNarrative([{id:"a",type:"decayed"},{id:"b",type:"contradiction"},{id:"b",type:"contradiction"}],new Set()); assert.equal(d.featured.type,"contradiction"); assert.equal(d.events.filter(e=>e.featured).length,1); assert.equal(d.events.length,2); });
test("unknown event settles quietly",()=>{ const e=normalizeEvent({id:"x",type:"mystery"}); assert.equal(e.phase,"settled"); assert.equal(narrativeCopy({event:e},{}).eyebrow,"Settled"); });
test("maps phases and handles null bursts",()=>{ assert.equal(EVENT_PRIORITY.contradiction,60); assert.equal(normalizeEvent({type:"new_belief"}).phase,"arrival"); assert.equal(normalizeEvent(null).type,"unknown"); assert.equal(selectNarrative(null,null).events.length,0); assert.equal(selectNarrative([{id:"a",type:"decayed"},{id:"b",type:"pruned"}]).featured.id,"b"); });
test('archive storyteller follows selection, hover, event, then overview priority deterministically', () => {
  const memories=[{id:'a',statement:'Prefers quiet motion',category:'preference',vitality:.9},{id:'b',statement:'Uses Docker',category:'system_state',vitality:.6}];
  const base={memories,relationships:[{source:'a',target:'b'}],events:[]};
  const overview=archiveStory(base); assert.match(overview.body,/2 memories/); assert.deepEqual(overview,archiveStory(base));
  assert.match(archiveStory({...base,events:[{id:'e',type:'new_belief'}]}).eyebrow,/Arrival/i);
  assert.match(archiveStory({...base,hoveredMemory:memories[1]}).title,/Uses Docker/);
  assert.match(archiveStory({...base,hoveredMemory:memories[1],selectedMemory:memories[0]}).title,/Prefers quiet motion/);
});
test("normalizes lifecycle events into human-readable statements",()=>{ const event=normalizeEvent({id:1,event_type:"new_belief",entity_source:"phoenix",entity_target:"Phoenix",detail:{relation:"codename"}}); assert.equal(event.displayStatement,"Stored · phoenix codename Phoenix"); });
