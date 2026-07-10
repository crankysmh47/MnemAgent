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
  return { open: () => setOpen(true), close: () => setOpen(false), destroy() {} };
}
