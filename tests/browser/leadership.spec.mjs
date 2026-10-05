import {test,expect} from '@playwright/test';
test.beforeEach(async({page})=>{
 await page.goto('/');await page.getByRole('button',{name:'+ New decision',exact:true}).click();
 await page.getByRole('button',{name:'Fill example',exact:true}).click();await page.getByRole('button',{name:'Create decision model →',exact:true}).click();
 await expect(page.getByText('Orchestrator response',{exact:true})).toBeVisible();
});
async function review(page,role){
 await page.getByRole('button',{name:`Enable ${role.toUpperCase()} execution review`,exact:true}).click();
 const root=page.locator('.leadership-editor');
 for(const[k,v]of Object.entries({as_of:'2026-10-03',review_on:'2026-10-10',budget:'100',capacity_hours:'10',basis:'Synthetic one-year incremental values; common unit; no overlap'}))await root.locator(`[name=lr_${k}]`).fill(v);
 if(role==='cmo')await root.locator('[name=lr_protected_brand_budget]').fill('30');
 for(const row of await root.locator('[data-leadership-check]').all()){
  await row.locator('[name=status]').selectOption('gap');await row.locator('[name=owner]').fill('Review owner');
  await row.locator('[name=evidence]').fill('Synthetic evidence');await row.locator('[name=review_on]').fill('2026-10-10');
 }
 return root;
}
async function project(page,role,name){
 await page.getByRole('button',{name:`Add ${role==='cto'?'technology':'marketing'} initiative`,exact:true}).click();
 const row=page.locator('[data-leadership-project]').last();
 for(const[k,v]of Object.entries({name,owner:'Accountable owner',evidence:'Synthetic test',cost:'30',hours:'4',adverse_value:'60'}))await row.locator(`[name=${k}]`).fill(v);
 if(role==='cto'){
  await row.locator('[name=outcome]').fill('Acceptance measurement');await row.locator('[name=rollback]').fill('Restore prior configuration');
  await row.locator('[name=security]').selectOption('pass');await row.locator('[name=ip]').selectOption('pass');
 }else{await row.locator('[name=approved]').selectOption('true');await row.locator('[name=brand]').selectOption('true');}
 return row;
}
test('CTO dependency-aware portfolio, save, reload, export and mobile',async({page})=>{
 const errors=[];page.on('pageerror',e=>errors.push(e.message));await page.locator('nav [data-page=ctopage]').click();
 await page.locator('#executive-sector').selectOption('Technology');
 const form=page.locator('#executive-form');
 for(const[k,v]of Object.entries({organization:'Synthetic CTO review',unit:'Test units',period:'One-year portfolio; measured monthly operations',source:'Synthetic measurements'}))await form.locator(`[name=${k}]`).fill(v);
 await review(page,'cto');await project(page,'cto','Foundation');const second=await project(page,'cto','Launch');
 await second.locator('[name=depends_on]').fill('Foundation');await second.locator('[name=required]').selectOption('true');
 const pending=page.waitForResponse(r=>r.url().endsWith('/executive-support')&&r.request().method()==='POST');
 await page.getByRole('button',{name:'Analyze & save CTO plan',exact:true}).click();const response=await pending;
 expect(response.status(),await response.text()).toBe(201);const result=(await response.json()).analysis.technology_strategy;
 expect(result.delivery_sequence.map(r=>r.name)).toEqual(['Foundation','Launch']);expect(result.feasible_count).toBe(1);
 await page.reload();await page.locator('nav [data-page=ctopage]').click();await expect(page.locator('.leadership-results')).toContainText('Foundation');
 const download=page.waitForEvent('download');await page.getByRole('button',{name:'Export professional plan',exact:true}).click();expect((await download).suggestedFilename()).toContain('praxis-cto');
 await page.locator('.leadership-results').scrollIntoViewIfNeeded();await page.screenshot({path:'../../.test-tmp/cto-execution-results.png'});
 await page.setViewportSize({width:390,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);expect(errors).toEqual([]);
});
test('CMO shared KPIs, brand floor and leadership continuity persist',async({page})=>{
 const errors=[];page.on('pageerror',e=>errors.push(e.message));await page.locator('nav [data-page=cmopage]').click();
 await page.getByRole('button',{name:'Fill illustrative example',exact:true}).click();await review(page,'cmo');await project(page,'cmo','Brand pilot');
 await page.getByRole('button',{name:'Add shared metric',exact:true}).click();const metric=page.locator('[data-leadership-metric]');
 for(const[k,v]of Object.entries({name:'Qualified pipeline',unit:'accounts',owner:'Sales',source:'Synthetic CRM',observed_on:'2026-10-01',actual:'90',target:'100',max_age_days:'3'}))await metric.locator(`[name=${k}]`).fill(v);
 await metric.locator('[name=category]').selectOption('pipeline');
 await page.getByRole('button',{name:'Add leadership event',exact:true}).click();await page.locator('[data-leadership-event] [name=occurred_on]').fill('2026-10-02');
 const pending=page.waitForResponse(r=>r.url().endsWith('/marketing-support')&&r.request().method()==='POST');
 await page.getByRole('button',{name:'Analyze & save CMO plan',exact:true}).click();const response=await pending;
 expect(response.status(),await response.text()).toBe(201);const result=(await response.json()).analysis.execution_review;
 expect(result.metrics[0].status).toBe('off_target');expect(result.top_portfolios[0].brand_spend).toBe(30);expect(result.leadership_continuity[0].status).toBe('continuity_review_needed');
 await page.reload();await page.locator('nav [data-page=cmopage]').click();await expect(page.locator('.leadership-results')).toContainText('Qualified pipeline');
 await page.setViewportSize({width:390,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);expect(errors).toEqual([]);
});
