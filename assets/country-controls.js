// Use page-rendered menus: embedded browsers may not display native select popups.
function enhanceCountryControls(){
 if(state.page!=='nationalpage')return;
 for(const checkbox of document.querySelectorAll('#policy-appraisal-enabled,#national-form [name="economics"]')){
  if(checkbox.dataset.sectionButton)continue;
  checkbox.dataset.sectionButton='true';
  const button=document.createElement('button');button.type='button';button.className='secondary country-section-toggle';
  const title=checkbox.id==='policy-appraisal-enabled'?'policy appraisal':'GDP and fiscal calculations';
  const update=()=>{button.textContent=(checkbox.checked?'Disable ':'Enable ')+title;button.setAttribute('aria-pressed',String(checkbox.checked));};
  button.onclick=()=>{checkbox.checked=!checkbox.checked;checkbox.dispatchEvent(new Event('change',{bubbles:true}));update();};
  checkbox.addEventListener('change',update);checkbox.closest('label').after(button);update();
 }
 for(const input of document.querySelectorAll('#main input[type="date"]')){input.type='text';input.pattern='[0-9]{4}-[0-9]{2}-[0-9]{2}';input.placeholder='YYYY-MM-DD';input.title='Enter a date as YYYY-MM-DD';}
 for(const select of document.querySelectorAll('#main select')){
  if(select.dataset.pageMenu){const menu=select.nextElementSibling;menu.querySelector('.country-menu-trigger').disabled=select.disabled;for(const b of menu.querySelectorAll('[data-value]'))b.disabled=select.disabled||[...select.options].some(o=>o.value===b.dataset.value&&o.disabled);continue;}
  select.dataset.pageMenu='true';
  const label=select.closest('label'),title=select.getAttribute('aria-label')||label?.firstChild?.textContent?.trim()||'Choose an option';
  const wrapper=document.createElement('div');wrapper.className='country-menu';
  const trigger=document.createElement('button');trigger.type='button';trigger.className='secondary country-menu-trigger';trigger.setAttribute('aria-label',title);trigger.setAttribute('aria-expanded','false');
  const options=document.createElement('div');options.className='country-menu-options';options.hidden=true;options.setAttribute('role','group');options.setAttribute('aria-label',title+' choices');
  const update=()=>{trigger.textContent=(select.selectedOptions[0]?.textContent||'Choose an option')+' ▾';for(const b of options.children)b.setAttribute('aria-pressed',String(b.dataset.value===select.value));};
  for(const option of select.options){const b=document.createElement('button');b.type='button';b.className='secondary';b.textContent=option.textContent;b.dataset.value=option.value;b.disabled=option.disabled;b.onclick=()=>{select.value=option.value;select.dispatchEvent(new Event('change',{bubbles:true}));update();options.hidden=true;trigger.setAttribute('aria-expanded','false');trigger.focus();};options.appendChild(b);}
  trigger.onclick=()=>{options.hidden=!options.hidden;trigger.setAttribute('aria-expanded',String(!options.hidden));};
  trigger.onkeydown=e=>{if(e.key==='Escape'){options.hidden=true;trigger.setAttribute('aria-expanded','false');}};
  select.addEventListener('change',update);select.addEventListener('invalid',()=>{options.hidden=false;trigger.setAttribute('aria-expanded','true');});
  select.classList.add('country-native-select');select.tabIndex=-1;
  wrapper.append(trigger,options);select.after(wrapper);update();
 }
}
const renderBeforeCountryControls=render;
render=function(){renderBeforeCountryControls();enhanceCountryControls();};
document.addEventListener('DOMContentLoaded',()=>{const main=document.querySelector('#main');new MutationObserver(enhanceCountryControls).observe(main,{childList:true,subtree:true});main.addEventListener('change',enhanceCountryControls);enhanceCountryControls();});
