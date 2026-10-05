const {chromium}=require('playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1000}}), errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  const base=process.env.PRAXIS_BROWSER_URL||'http://127.0.0.1:8883';
  const source=await (await page.request.post(base+'/v2/resources/source',{data:{name:'Browser pilot log',domain:'technology',uri:'internal:browser-pilot',source_type:'report'}})).json();
  await page.request.post(base+'/v2/resources/document',{data:{source_id:source.id,content:'Software pilot latency = 120 milliseconds.'}});
  const decision=await (await page.request.post(base+'/v1/decision-models',{data:{title:'Research browser test',problem:'Should we deploy software?',objective:'Reduce latency',options:[{name:'Pilot'},{name:'Wait'}]}})).json();
  await page.goto(base);
  await page.getByRole('button',{name:/Search & decide$/}).click();
  const current=await page.locator('#active-decision').inputValue();
  if(current!==decision.decision_id){const loaded=page.waitForResponse(r=>r.url().endsWith('/'+decision.decision_id+'/workspace'));await page.locator('#active-decision').selectOption(decision.decision_id);await loaded;await page.waitForFunction(id=>state.workspace?.revision.decision_id===id,decision.decision_id);}
  await page.locator('[name=query]').fill('software latency');
  await page.getByRole('button',{name:'Search sources',exact:true}).click();
  await page.locator('#research-results').getByText('Software pilot latency = 120 milliseconds.',{exact:true}).first().waitFor();
  await page.getByRole('button',{name:'Build & save decision memo',exact:true}).click();
  await page.locator('details.record > summary').filter({hasText:'software latency'}).first().waitFor();
  await page.locator('details.record > summary').filter({hasText:'software latency'}).first().click();
  await page.getByText('No forecast supplied. No numerical ranking generated.',{exact:true}).waitFor();
  await page.screenshot({path:'.test-tmp/research-desktop.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  await page.screenshot({path:'.test-tmp/research-mobile.png',fullPage:true});
  await page.getByRole('button',{name:'Open human review',exact:true}).click();
  const choice=await page.locator('[name=advice_id] option').filter({hasText:'Search and decision memo'}).last().getAttribute('value');
  await page.locator('[name=advice_id]').selectOption(choice);
  await page.locator('[name=disposition]').selectOption('reject');
  await page.locator('[name=reviewer]').fill('Research reviewer');
  await page.locator('[name=rationale]').fill('Gather independent trial evidence');
  await page.getByRole('button',{name:'Save human review',exact:true}).click();
  await page.getByText('Gather independent trial evidence',{exact:true}).waitFor();
  await page.reload();
  await page.getByRole('button',{name:/Search & decide$/}).click();
  if(await page.locator('#active-decision').inputValue()!==decision.decision_id){const loaded=page.waitForResponse(r=>r.url().endsWith('/'+decision.decision_id+'/workspace'));await page.locator('#active-decision').selectOption(decision.decision_id);await loaded;}
  await page.locator('details.record > summary').filter({hasText:'software latency'}).first().waitFor();
  assert.deepEqual(errors,[]);
  console.log('PASS: ranked sources, saved memo, human rejection, reload history, desktop/mobile, no page errors');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
