<script lang="ts">
  let { value, min, max, onresize, onreset }: {
    value: number; min: number; max: number;
    onresize: (width: number) => void; onreset: () => void;
  } = $props();
  let drag = $state<{ pointerId: number; x: number; width: number } | null>(null);
  const clamp = (width: number) => Math.round(Math.max(min, Math.min(max, width)));

  function begin(event: PointerEvent) {
    if (event.button !== 0) return;
    const handle = event.currentTarget as HTMLElement;
    handle.focus();
    handle.setPointerCapture(event.pointerId);
    drag = { pointerId: event.pointerId, x: event.clientX, width: value };
    event.preventDefault();
  }
  function move(event: PointerEvent) {
    if (drag?.pointerId === event.pointerId) onresize(clamp(drag.width + drag.x - event.clientX));
  }
  function end(event: PointerEvent) {
    const handle = event.currentTarget as HTMLElement;
    if (handle.hasPointerCapture(event.pointerId)) handle.releasePointerCapture(event.pointerId);
    drag = null;
  }
  function keyboard(event: KeyboardEvent) {
    const step = event.shiftKey ? 40 : 16;
    if (event.key === 'ArrowLeft') onresize(clamp(value + step));
    else if (event.key === 'ArrowRight') onresize(clamp(value - step));
    else if (event.key === 'Home') onresize(min);
    else if (event.key === 'End') onresize(max);
    else if (event.key === 'Enter') onreset();
    else return;
    event.preventDefault();
  }
</script>

<!-- A focusable separator is the interactive window-splitter variant; Svelte's role classifier treats all separators as static. -->
<!-- svelte-ignore a11y_no_noninteractive_tabindex, a11y_no_noninteractive_element_interactions -->
<div
  class="panel-divider" class:dragging={!!drag}
  role="separator" tabindex="0" aria-label="Resize request panel"
  aria-orientation="vertical" aria-controls="request-inspector"
  aria-valuemin={min} aria-valuemax={max} aria-valuenow={value}
  aria-valuetext={`${value} pixels wide`}
  title="Drag to resize · ← wider / → narrower · double-click or Enter to reset"
  onpointerdown={begin} onpointermove={move} onpointerup={end}
  onpointercancel={end} onlostpointercapture={() => drag = null}
  onkeydown={keyboard} ondblclick={onreset}
><span aria-hidden="true"></span></div>

<style>
  .panel-divider { position: relative; z-index: 8; width: 8px; min-height: 0; align-self: stretch; background: #e6edf1; cursor: col-resize; touch-action: none; user-select: none; outline-offset: -2px; }
  .panel-divider::before { content: ''; position: absolute; inset: 0 -3px; }
  .panel-divider span { position: absolute; top: 45%; left: 2px; width: 4px; height: 34px; border-left: 1px solid #8aa9ad; border-right: 1px solid #8aa9ad; border-radius: 3px; }
  .panel-divider:hover, .panel-divider:focus-visible, .panel-divider.dragging { background: #bfd9d4; outline: 2px solid #267d79; }
  @media (max-width: 900px) { .panel-divider { display: none; } }
</style>
