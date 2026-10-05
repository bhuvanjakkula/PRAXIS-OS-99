const {chromium}=require('playwright');const assert=require('node:assert/strict');
(async()=>{const browser=await chromium.launch({channel:'msedge',headless:true});try{
 const page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:8894/');
 await page.getByRole('button',{name:'+ New decision',exact:true}).click();
 await page.getByRole('button',{name:'Fill example',exact:true}).click();
 await page.getByRole('button',{name:'Create decision model →',exact:true}).click();
 await page.getByText('Orchestrator response',{exact:true}).waitFor();
 await page.locator('nav [data-page=inquirypage]').click();
 const f=page.locator('#inquiry-form');
 for(const [name,value] of Object.entries({metric:'Latency',unit:'ms',baseline:'200',target:'100',measurement_source:'Monitoring log',budget:'100',cost_unit:'USD'}))await f.locator(`[name=${name}]`).fill(value);
 const candidates=f.locator('[data-candidate]');
 for(let i=0;i<await candidates.count();i++){const c=candidates.nth(i);for(const [name,value] of Object.entries({action:'Bounded load test',predicted:String(80+i*10),cost:String(20+i*10),assumptions:'Stable workload',stop_condition:'Stop if critical traffic fails'}))await c.locator(`[name=${name}]`).fill(value);await c.locator('[name=reversible]').selectOption('true');for(const check of await c.locator('[data-check]').all())await check.selectOption('pass');}
 const saved=page.waitForResponse(r=>r.url().endsWith('/inquiry')&&r.request().method()==='POST');await page.getByRole('button',{name:'Compare & save inquiry',exact:true}).click();assert.equal((await saved).status(),201);
 const observation=page.locator('[data-inquiry-observation]').first();await observation.waitFor();
 for(const [name,value]of Object.entries({actual:'90',actual_cost:'25',source:'Measured test log',lesson:'Latency improved'}))await observation.locator(`[name=${name}]`).fill(value);
 for(const check of await observation.locator('[data-check]').all())await check.selectOption('pass');
 const result=page.waitForResponse(r=>r.url().endsWith('/inquiry-observations'));await observation.getByRole('button',{name:'Save outcome & learn'}).click();assert.equal((await result).status(),201);await page.getByRole('heading',{name:'Target met in reported test',exact:true}).waitFor();
 await page.reload();await page.locator('nav [data-page=inquirypage]').click();await page.getByRole('heading',{name:'Target met in reported test',exact:true}).waitFor();
 await page.setViewportSize({width:390,height:844});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);assert.deepEqual(errors,[]);assert(!/geometer|\bdewey\b|\bblake\b|\bnewton\b/i.test(await page.locator('body').innerText()));
 console.log('Inquiry comparison, measured outcome, reload, branding and mobile layout passed');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exit(1)});
