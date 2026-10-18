/* Progressive enhancement: all chapters remain available without JavaScript. */
(() => {
  const nav = document.querySelector('[aria-label="EDA chapters"]');
  const links = [...nav.querySelectorAll('a')];
  const chapters = links.map(a => document.querySelector(a.hash));
  const form = document.querySelector('.eda-select');
  const toolbar = document.createElement('div');
  toolbar.className = 'eda-toolbar';
  const status = document.createElement('span');
  status.setAttribute('role', 'status');
  const button = (label, action) => {
    const b = document.createElement('button'); b.type = 'button';
    b.className = 'eda-button'; b.textContent = label;
    b.addEventListener('click', action); return b;
  };
  let index = Math.max(0, links.findIndex(a => a.hash === location.hash));
  let all = false;
  const previous = button('← Previous', () => select(index - 1, true));
  const next = button('Next →', () => select(index + 1, true));
  const toggle = button('Show all chapters', () => { all = !all; render(); });
  const print = button('Print / save PDF', () => window.print());
  toolbar.append(previous, status, next, toggle, print);
  form.after(toolbar);
  nav.classList.add('chapter-tabs');
  document.body.classList.add('eda-guided');
  const hints = [
    'Start here: explain what one row represents and where the data come from.',
    'Explain which observations were excluded—and what the audit cannot yet tell us.',
    'Compare the mean with the median. Then inspect skew and unusual values.',
    'Compare rain groups, but watch for differences in seasons and weekdays.',
    'Look for calendar patterns before attributing changes to weather.',
    'Separate observed findings from possible explanations and limitations.',
    'Read the association table first. Expand the calculations when you need the math.'
  ];
  chapters.forEach((section, i) => {
    section.tabIndex = -1;
    const hint = document.createElement('p'); hint.className = 'chapter-hint';
    hint.textContent = hints[i]; section.querySelector('h2').after(hint);
    section.querySelectorAll('.table-wrap').forEach(w => {
      w.tabIndex = 0; w.setAttribute('role', 'region');
      w.setAttribute('aria-label', 'Data table; scroll horizontally for more columns');
      const note = document.createElement('p'); note.className = 'table-help';
      note.textContent = 'More columns? Scroll the table sideways.'; w.before(note);
    });
  });
  // Keep the summary and scatterplot visible; collapse the longer derivations.
  [...document.querySelectorAll('#correlation-math > article')].slice(2).forEach(article => {
    const title = article.querySelector('h3');
    const details = document.createElement('details'); details.className = 'panel math-details';
    const summary = document.createElement('summary'); summary.textContent = title.textContent;
    title.remove(); details.append(summary);
    while (article.firstChild) details.append(article.firstChild);
    article.replaceWith(details);
  });
  function render() {
    chapters.forEach((section, i) => section.hidden = !all && i !== index);
    links.forEach((a, i) => i === index ? a.setAttribute('aria-current','step') : a.removeAttribute('aria-current'));
    status.textContent = all ? 'All 7 chapters' : `Chapter ${index + 1} of 7`;
    previous.disabled = all || index === 0;
    next.disabled = all || index === chapters.length - 1;
    toggle.textContent = all ? 'Focus on one chapter' : 'Show all chapters';
    form.action = '/eda' + links[index].hash;
  }
  function select(i, focus) {
    index = Math.max(0, Math.min(i, chapters.length - 1));
    history.replaceState(null, '', location.pathname + location.search + links[index].hash);
    render();
    if (focus) chapters[index].focus();
  }
  links.forEach((a,i) => a.addEventListener('click', e => { e.preventDefault(); select(i,true); }));
  window.addEventListener('hashchange', () => {
    const i = links.findIndex(a => a.hash === location.hash);
    if (i >= 0) { index = i; render(); }
  });
  const seriesSelect = form.querySelector('#series');
  if (seriesSelect) {
    seriesSelect.addEventListener('change', () => {
      const yearSelect = form.querySelector('select[name="year"]');
      const seasonSelect = form.querySelector('select[name="season"]');
      const dayTypeSelect = form.querySelector('select[name="day_type"]');
      if (yearSelect) yearSelect.value = 'all';
      if (seasonSelect) seasonSelect.value = 'all';
      if (dayTypeSelect) dayTypeSelect.value = 'all';
    });
  }
  form.querySelectorAll('select').forEach(select => select.addEventListener('change', () => form.requestSubmit()));
  form.querySelector('button').textContent = 'Refresh data';
  let openBeforePrint = [];
  window.addEventListener('beforeprint', () => {
    openBeforePrint = [...document.querySelectorAll('details')].filter(d => !d.open);
    openBeforePrint.forEach(d => d.open = true);
  });
  window.addEventListener('afterprint', () => openBeforePrint.forEach(d => d.open = false));
  render();
})();
