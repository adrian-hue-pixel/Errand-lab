(() => {
  try {
    const root = document.documentElement;
    root.dataset.theme = localStorage.getItem('errand:theme') || (matchMedia('(prefers-color-scheme:light)').matches ? 'light' : 'dark');
    root.dataset.motion = localStorage.getItem('errand:motion') || 'Subtle';
  } catch { /* CSS supplies the dark default when storage is unavailable. */ }
})();
