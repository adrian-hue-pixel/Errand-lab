// Let the native form submit normally. Only display progress for a valid route comparison.
const planner = document.querySelector('.planner');
if (planner) {
  const progress = document.querySelector('#progress');
  let timer;
  function reset() {
    clearTimeout(timer);
    progress.hidden = true;
    planner.removeAttribute('aria-busy');
  }
  planner.addEventListener('submit', event => {
    if (event.submitter && event.submitter.value !== 'run') return;
    planner.setAttribute('aria-busy', 'true');
    timer = setTimeout(() => { progress.hidden = false; }, 120);
  });
  window.addEventListener('pageshow', reset);
}

// Mirror edits in each disclosure so the collapsed stop stays recognizable.
if (planner) {
  planner.addEventListener('input', event => {
    const editor = event.target.closest('.stopeditor');
    if (!editor) return;
    const read = prefix => editor.querySelector('input[name^="' + prefix + '"]').value;
    editor.querySelector('summary strong').textContent = read('name') || 'Add stop details';
    editor.querySelector('summary small').textContent = read('open') + '–' + read('close');
  });
  planner.addEventListener('invalid', event => {
    const editor = event.target.closest('.stopeditor');
    if (editor) editor.open = true;
  }, true);
}

// The SVG drives the route trace and marker on the same clock.
if (!matchMedia('(prefers-reduced-motion: reduce)').matches) {
  document.querySelectorAll('.route-player').forEach(player => {
    const button = player.querySelector('button');
    const label = player.querySelector('[data-play-label]');
    const status = player.querySelector('[data-play-status]');
    const animations = [...player.querySelectorAll('[data-replay-start]')];
    const first = animations[0];
    if (!first || typeof first.beginElement !== 'function') return;
    button.hidden = false;
    button.addEventListener('click', () => {
      label.textContent = 'Restart route';
      status.textContent = 'Playing route.';
      animations.forEach(animation => animation.beginElement());
    });
    first.addEventListener('endEvent', () => {
      label.textContent = 'Replay route';
      status.textContent = 'Route replay complete.';
    });
  });
}
