const {chromium}=require('playwright');const assert=require('node:assert/strict');
(async()=>{const browser=await chromium.launch({channel:'msedge',headless:true});try{
 const page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 const base=process.env.PRAXIS_BROWSER_URL||'http://127.0.0.1:8884';
 const decision=await (await page.request.post(base+'/v1/decision-models',{data:{title:'Demand shift foresight',problem:'Deploy software when demand changes',objective:'Reliable service',constraints:['Budget'],options:[{name:'Launch'},{name:'Pilot'}]}})).json();
 await page.goto(base+'/#foresight');await page.locator('#foresight-form').waitFor();
 if(await page.locator('#active-decision').inputValue()!==decision.decision_id){await page.locator('#active-decision').selectOption(decision.decision_id);await page.waitForFunction(id=>state.workspace?.revision.decision_id===id,decision.decision_id);}
 const form=page.locator('#foresight-form');await form.locator('[name=new_situation]').fill('Demand doubled after a launch');await form.locator('[name=unknowns]').fill('Peak capacity');
 await page.locator('#enable-series').check();
 for(const [key,value]of Object.entries({metric:'Demand',unit:'requests',interval:'week',source:'Observed weekly logs',values:'10,20,30,40,50,60,70,80',horizon:'3',target:'100'}))await form.locator(`[name=${key}]`).fill(value);
 await page.locator('#enable-worlds').check();await form.locator('[name=payoff_unit]').fill('USD over 12 months');
 for(const [i,value]of ['0.6','0.3','0.1'].entries())await page.locator(`[data-world-prob="${i}"]`).fill(value);
 for(const [i,values]of [[100,-100,200],[50,0,80]].entries())for(const [j,value]of values.entries())await page.locator(`[data-payoff-option="${i}"][data-payoff-world="${j}"]`).fill(String(value));
 for(const i of [0,1])await page.locator(`[data-constraint-option="${i}"][data-constraint-index="0"]`).selectOption('pass');
 const response=page.waitForResponse(r=>r.url().endsWith('/foresight')&&r.request().method()==='POST');await page.getByRole('button',{name:'Explore & save foresight',exact:true}).click();assert.equal((await response).status(),201);
 await page.getByRole('heading',{name:'Candidate solutions to test',exact:true}).waitFor();assert.equal(await page.locator('svg.foresight-chart').count(),1);
 await page.getByText('Selected model:',{exact:false}).waitFor();await page.getByText('Test a limited version of Launch, with explicit expansion gates.',{exact:true}).click();
 await page.locator('#toast').evaluate(e=>e.hidden=true);
 await page.screenshot({path:'.test-tmp/foresight-desktop.png',fullPage:true});await page.setViewportSize({width:390,height:844});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);await page.screenshot({path:'.test-tmp/foresight-mobile.png',fullPage:true});
 const observation=page.locator('#forecast-observation-form');await observation.locator('[name=actual]').fill('95');await observation.locator('[name=source]').fill('Week 9 measured requests');await observation.locator('[name=learning]').fill('Demand exceeded the projected trend');
 await page.getByRole('button',{name:'Record observed outcome',exact:true}).click();await page.getByText('Demand exceeded the projected trend',{exact:true}).waitFor();
 await page.getByRole('button',{name:'Open human review',exact:true}).click();const advice=await page.locator('[name=advice_id] option').filter({hasText:'Foresight and candidate solutions'}).last().getAttribute('value');await page.locator('[name=advice_id]').selectOption(advice);await page.locator('[name=disposition]').selectOption('defer');await page.locator('[name=reviewer]').fill('Human');await page.locator('[name=rationale]').fill('Wait for additional measurements');await page.getByRole('button',{name:'Save human review',exact:true}).click();await page.getByText('Wait for additional measurements',{exact:true}).waitFor();
 await page.reload();await page.locator('#foresight-form').waitFor();if(await page.locator('#active-decision').inputValue()!==decision.decision_id){await page.locator('#active-decision').selectOption(decision.decision_id);await page.waitForFunction(id=>state.workspace?.revision.decision_id===id,decision.decision_id);}
 await page.getByText('Demand exceeded the projected trend',{exact:true}).waitFor();await page.getByRole('button',{name:'Reuse these inputs',exact:true}).first().click();assert.equal(await page.locator('#foresight-form [name=values]').inputValue(),'10, 20, 30, 40, 50, 60, 70, 80');assert.equal(await page.locator('[data-world-prob="0"]').inputValue(),'0.6');assert.deepEqual(errors,[]);console.log('PASS: forecast chart, scenario matrix, candidate hypotheses, observed error, human review, restart persistence, mobile overflow and page errors');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
