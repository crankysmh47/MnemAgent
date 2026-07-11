export const ARCHIVE_FILTERS = Object.freeze({
  categories: [{value:'all',label:'All forms'},{value:'preference',label:'Preferences'},{value:'persona',label:'Persona'},{value:'system_state',label:'System state'}],
  lifecycles: [{value:'all',label:'All vitality'},{value:'vivid',label:'Vivid'},{value:'rooted',label:'Rooted'},{value:'stable',label:'Stable'},{value:'new',label:'New'},{value:'fading',label:'Fading'},{value:'dormant',label:'Dormant'}],
});

function populateFilters(root, options, current, onSelect) { if(!root) return; root.querySelectorAll('button[data-filter]').forEach(node=>node.remove()); for(const item of options){ const button=document.createElement('button'); button.type='button'; button.dataset.filter=item.value; button.textContent=item.label; button.setAttribute('aria-pressed',String(item.value===current)); button.addEventListener('click',()=>{ root.querySelectorAll('button[data-filter]').forEach(node=>node.setAttribute('aria-pressed','false')); button.setAttribute('aria-pressed','true'); onSelect(item.value); }); root.append(button); } }

export function createArchiveMenu(dialog, store, callbacks = {}) {
  const button = document.querySelector('#archiveMenuButton');
  const setOpen = open => { if (open) dialog?.showModal?.(); else dialog?.close?.(); button?.setAttribute('aria-expanded', String(open)); };
  button?.addEventListener('click', () => setOpen(true));
  dialog?.addEventListener('close', () => button?.setAttribute('aria-expanded', 'false'));
  document.querySelector('#motionToggle')?.addEventListener('click', event => { const enabled = event.currentTarget.getAttribute('aria-pressed') !== 'true'; event.currentTarget.setAttribute('aria-pressed', String(enabled)); store?.dispatch({ type: 'SET_MOTION', motion: enabled }); });
  document.querySelector('#replayOpening')?.addEventListener('click', () => callbacks.onReplayOpening?.());
  document.querySelector('#resetArchiveView')?.addEventListener('click', () => callbacks.onReset?.());
  document.querySelector('#exportArchive')?.addEventListener('click', () => callbacks.onExport?.());
  document.querySelector('#retryArchive')?.addEventListener('click', () => callbacks.onRetry?.());
  const userInput=document.querySelector('#userId'); if(userInput){ userInput.value=callbacks.userId||''; userInput.addEventListener('change',()=>callbacks.onUserChange?.(userInput.value.trim())); userInput.addEventListener('keydown',event=>{ if(event.key==='Enter'){ event.preventDefault(); callbacks.onUserChange?.(userInput.value.trim()); } }); }
  populateFilters(document.querySelector('#categoryFilters'),ARCHIVE_FILTERS.categories,store?.getState?.().filters?.category||'all',value=>store?.dispatch({type:'SET_FILTERS',filters:{category:value}}));
  populateFilters(document.querySelector('#lifecycleFilters'),ARCHIVE_FILTERS.lifecycles,store?.getState?.().filters?.lifecycle||'all',value=>store?.dispatch({type:'SET_FILTERS',filters:{lifecycle:value}}));
  return { open: () => setOpen(true), close: () => setOpen(false), destroy() {} };
}
