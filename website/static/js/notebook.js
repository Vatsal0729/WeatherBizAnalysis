(() => {
  const stages = [...document.querySelectorAll('.notebook-stage')];
  const links = [...document.querySelectorAll('.stage-nav a')];
  const prev = document.querySelector('#stagePrev');
  const next = document.querySelector('#stageNext');
  const allButton = document.querySelector('#stageAll');
  const status = document.querySelector('#stageStatus');
  let index = Math.max(0, links.findIndex(a => a.hash === location.hash));
  let showAll = false;
  function render() {
    stages.forEach((stage,i) => stage.hidden = !showAll && i !== index);
    links.forEach((a,i) => i === index ? a.setAttribute('aria-current','step') : a.removeAttribute('aria-current'));
    status.textContent = showAll ? `All ${stages.length} stages` : `Stage ${index+1} of ${stages.length}`;
    prev.disabled = showAll || index === 0; next.disabled = showAll || index === stages.length-1;
    allButton.textContent = showAll ? 'Focus on one stage' : 'Show all stages';
  }
  function select(value) {
    index = Math.max(0, Math.min(value, stages.length-1));
    history.replaceState(null,'',location.pathname+links[index].hash); render(); stages[index].focus();
  }
  prev.addEventListener('click',()=>select(index-1)); next.addEventListener('click',()=>select(index+1));
  allButton.addEventListener('click',()=>{showAll=!showAll;render();});
  links.forEach((a,i)=>a.addEventListener('click',e=>{e.preventDefault();select(i);}));
  render();
})();
