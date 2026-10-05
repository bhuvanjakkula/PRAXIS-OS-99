import {test,expect} from '@playwright/test';
test.beforeEach(async({page})=>{
 await page.goto('/');await page.getByRole('button',{name:'+ New decision',exact:true}).click();await page.getByRole('button',{name:'Fill example',exact:true}).click();await page.getByRole('button',{name:'Create decision model →',exact:true}).click();await expect(page.getByText('Orchestrator response',{exact:true})).toBeVisible();
});
async function handoff(root){
 await root.locator('[data-integration-objective]').fill('Review a synthetic cross-team learning exercise');await root.locator('[data-integration-escalation]').fill('Integration lead');await root.getByRole('button',{name:'Add cross-functional handoff',exact:true}).click();
 const h=root.locator('[data-integration-handoff]');for(const[k,v]of Object.entries({title:'Synthetic handoff',sending_team:'Research',receiving_team:'Operations',owner:'Operations lead',due_on:'2026-10-02',source:'Synthetic report',interpretation:'Testable observation',acceptance:'Meeting record',experiment:'Bounded training exercise',result:'Inconclusive',reviewer:'Review lead'}))await h.locator(`[name=${k}]`).fill(v);
 await h.locator('[name=stage]').selectOption('reviewed');
}
test('CTO current and proposed network, knowledge handoff, reload and mobile',async({page})=>{
 const errors=[];page.on('pageerror',e=>errors.push(e.message));await page.locator('nav [data-page=ctopage]').click();await page.locator('#executive-sector').selectOption('Technology');const f=page.locator('#executive-form');
 for(const[k,v]of Object.entries({organization:'Network test',unit:'Synthetic units',period:'Synthetic period',source:'Recorded synthetic input'}))await f.locator(`[name=${k}]`).fill(v);
 await page.getByRole('button',{name:'Enable CTO execution review',exact:true}).click();
 for(const[k,v]of Object.entries({as_of:'2026-10-03',review_on:'2026-10-10',budget:'100',capacity_hours:'10'}))await f.locator(`[name=lr_${k}]`).fill(v);
 for(const check of await f.locator('[data-leadership-check]').all())await check.locator('[name=review_on]').fill('2026-10-10');
 await page.getByRole('button',{name:'Enable collaboration network review',exact:true}).click();await page.getByRole('button',{name:'Fill synthetic network example',exact:true}).click();await handoff(f.locator('.network-editor'));
 const pending=page.waitForResponse(r=>r.url().endsWith('/executive-support')&&r.request().method()==='POST');await page.getByRole('button',{name:'Analyze & save CTO plan',exact:true}).click();const response=await pending;expect(response.status(),await response.text()).toBe(201);
 const a=(await response.json()).analysis.technology_strategy.network_review;expect(a.current.units[1].betweenness).toBe(1);expect(a.with_proposals.units[1].betweenness).toBe(0);expect(a.integration.overdue_count).toBe(1);
 await expect(page.locator('.network-results')).toContainText('Integration lead');await page.reload();await page.locator('nav [data-page=ctopage]').click();
 await expect(page.locator('.network-results')).toContainText('Engineering');await page.getByText('Compare hypothetical proposed connections',{exact:true}).click();await expect(page.locator('.network-results svg')).toHaveCount(2);
 await page.locator('.network-results').scrollIntoViewIfNeeded();await page.screenshot({path:'../../.test-tmp/cto-network-review.png'});
 await page.setViewportSize({width:390,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);expect(errors).toEqual([]);
});
test('aviation organizational checks and incomplete closure persist without clearance',async({page})=>{
 const errors=[];page.on('pageerror',e=>errors.push(e.message));await page.locator('nav [data-page=aircrewpage]').click();const f=page.locator('#operations-form');
 for(const[k,v]of Object.entries({platform_type:'Synthetic training aircraft',identifier:'Training-only',phase:'Ground exercise',situation:'Review handoff coordination',observations:'Synthetic observation'}))await f.locator(`[name=${k}]`).fill(v);
 await page.getByRole('button',{name:'Enable aviation coordination review',exact:true}).click();await f.locator('[name=ac_as_of]').fill('2026-10-03');
 for(const check of await f.locator('[data-aviation-check]').all())await check.locator('[name=review_on]').fill('2026-10-02');
 await handoff(f.locator('.aviation-coordination'));
 const pending=page.waitForResponse(r=>r.url().endsWith('/operations-incidents')&&r.request().method()==='POST');await page.getByRole('button',{name:'Save incident assessment',exact:true}).click();const response=await pending;expect(response.status(),await response.text()).toBe(201);const a=(await response.json()).analysis.coordination;
 expect(a.flight_clearance).toBe(false);expect(a.fitness_assessment).toBe(false);expect(a.actions).toHaveLength(7);expect(a.integration.overdue_count).toBe(1);
 await page.reload();await page.locator('nav [data-page=aircrewpage]').click();await expect(page.locator('.aviation-coordination-results')).toContainText('Integration lead');
 const downloaded=page.waitForEvent('download');await page.getByRole('button',{name:'Download incident handover',exact:true}).click();expect((await downloaded).suggestedFilename()).toContain('aviation-handover');
 await page.locator('.aviation-coordination-results').scrollIntoViewIfNeeded();await page.screenshot({path:'../../.test-tmp/aviation-coordination-review.png'});
 await page.setViewportSize({width:390,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);expect(errors).toEqual([]);
});
