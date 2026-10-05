const {chromium}=require('playwright');const assert=require('node:assert/strict');
(async()=>{const b=await chromium.launch({channel:'msedge',headless:true});try{
 const p=await b.newPage({viewport:{width:1440,height:1000}}),errors=[];p.on('pageerror',e=>errors.push(e.message));
 await p.goto('http://127.0.0.1:8895/');await p.getByRole('button',{name:'+ New decision',exact:true}).click();await p.getByRole('button',{name:'Fill example',exact:true}).click();await p.getByRole('button',{name:'Create decision model →',exact:true}).click();await p.getByText('Orchestrator response',{exact:true}).waitFor();
 for(const role of ['ceo','cfo','cto']){
  await p.locator(`nav [data-page=${role}page]`).click();const f=p.locator(`#executive-form[data-role=${role}]`);await f.waitFor();
  await f.locator('#executive-sector').selectOption(role==='cfo'?'Real estate':role==='cto'?'Technology':'Financial services');await f.locator('#executive-sector-context h3').waitFor();
  await f.locator('#executive-area').selectOption(role==='cfo'?'Residential property':role==='cto'?'Software and SaaS':'Banking');await f.locator('#executive-area-context h3').waitFor();
  for(const [key,value] of Object.entries({organization:'Demo organization',unit:'INR',period:'October 2026',source:'Example measurements for browser testing',assumptions:'Validate demand',industry_requirements:'Internal review policy'}))await f.locator(`[name=${key}]`).fill(value);
  assert.deepEqual(await f.locator('input:invalid,textarea:invalid').evaluateAll(es=>es.map(e=>({name:e.name,value:e.value,reason:e.validationMessage}))),[]);
  const saved=p.waitForResponse(r=>r.url().endsWith('/executive-support'),{timeout:5000});await f.getByRole('button',{name:`Analyze & save ${role.toUpperCase()} plan`}).click();let response;try{response=await saved;}catch(error){console.error(role,errors,await p.locator('#toast').textContent());throw error;}assert.equal(response.status(),201);await p.getByRole('heading',{name:'Suggested next steps',exact:true}).waitFor();
  await p.reload();await p.locator(`nav [data-page=${role}page]`).click();await p.getByRole('heading',{name:'Suggested next steps',exact:true}).waitFor();await p.locator('#executive-sector-filter').selectOption(role==='cfo'?'Real estate':role==='cto'?'Technology':'Financial services');assert.match(await p.locator('#executive-sector-count').innerText(),/1 saved plans shown/);
  await p.getByRole('heading',{name:'Specific professional area',exact:true}).waitFor();
 }
 await p.screenshot({path:'.test-tmp/executive-desktop.png'});
 await p.getByRole('button',{name:'Compare alternatives in Decision compute',exact:true}).click();await p.locator('#compute-criteria').waitFor();assert.match(await p.locator('#compute-criteria').inputValue(),/Reliability benefit/);
 await p.setViewportSize({width:390,height:844});for(const role of ['ceo','cfo','cto']){await p.locator(`nav [data-page=${role}page]`).click();assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);}
 assert.deepEqual(errors,[]);console.log('Separate executive workspaces, calculations, persistence, decision engine handoff and mobile passed');
}finally{await b.close();}})().catch(e=>{console.error(e);process.exit(1)});
