export function createArchiveNavigation(svg, world, store) {
  const d3 = globalThis.d3;
  if (!d3 || !svg || !world) return { reset() {}, focusBounds() {}, destroy() {} };
  const selection = d3.select(svg);
  const behavior = d3.zoom().scaleExtent([0.7, 3.2]).on('zoom', event => { d3.select(world).attr('transform', event.transform); store?.dispatch({ type: 'SET_ZOOM', zoom: event.transform }); });
  selection.call(behavior);
  return { reset() { selection.transition().duration(180).call(behavior.transform, d3.zoomIdentity); }, focusBounds(bounds) { if (!bounds) return; const scale = Math.min(svg.clientWidth / bounds.width, svg.clientHeight / bounds.height); selection.call(behavior.transform, d3.zoomIdentity.scale(Math.max(.7, Math.min(3.2, scale)))); }, destroy() { selection.on('.zoom', null); } };
}
