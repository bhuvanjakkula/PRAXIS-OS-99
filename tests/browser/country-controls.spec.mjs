import {test,expect} from '@playwright/test';

test.beforeEach(async({page})=>{
 await page.goto('/');
 await page.getByRole('button',{name:'+ New decision',exact:true}).click();
 await page.getByRole('button',{name:'Fill example',exact:true}).click();
 await page.getByRole('button',{name:'Create decision model →',exact:true}).click();
 await expect(page.getByText('Orchestrator response',{exact:true})).toBeVisible();
});
test('country leadership fields, visible menus, agreements, economics and save',async({page})=>{
 const errors=[];page.on('pageerror',e=>errors.push(e.message));await page.locator('nav [data-page=nationalpage]').click();
 const f=page.locator('#national-form');await expect(f).toBeVisible();
 await page.locator('#country-data-search').fill('India');await page.locator('[data-country-choice=India]').click();
 async function choose(label,value){await page.getByRole('button',{name:label,exact:true}).click();await page.getByRole('group',{name:label+' choices',exact:true}).getByRole('button',{name:value,exact:true}).click();}
 await choose('Decision area','Economic policy');
 await f.locator('[name=as_of]').fill('2026-10-02');await f.locator('[name=period]').fill('One year');await f.locator('[name=unit]').fill('billion USD');await f.locator('[name=source]').fill('Illustrative browser verification');
 for(const name of ['mandate_reference','affected_groups','partners','assumptions']){await f.locator(`[name=${name}]`).fill('Illustrative test input');await expect(f.locator(`[name=${name}]`)).toHaveValue('Illustrative test input');}
 await page.getByRole('button',{name:'Enable policy appraisal',exact:true}).click();await expect(f.locator('[name=policy_years]')).toBeEnabled();await f.locator('[name=policy_years]').fill('2');await page.getByRole('button',{name:'Disable policy appraisal',exact:true}).click();
 await page.getByRole('button',{name:'Enable GDP and fiscal calculations',exact:true}).click();
 for(const[k,v]of Object.entries({gdp:100,revenue:20,primary_spending:18,debt:50,growth:3,effective_interest_rate:4,adverse_growth:1,adverse_revenue_drop:5,adverse_spending_rise:5}))await f.locator(`[name=${k}]`).fill(String(v));
 await page.getByRole('button',{name:'Add agreement',exact:true}).click();
 await choose('Reported status','Proposed');await choose('Proposed action’s consistency with obligation','Consistent (supplied assessment)');
 const g=f.locator('[data-national-agreement]');for(const[k,v]of Object.entries({title:'Illustrative agreement',partner:'Example partner',reviewed_on:'2026-10-02',obligation:'Review before commitment',reference:'Browser test'}))await g.locator(`[name=${k}]`).fill(v);
 await page.getByRole('button',{name:'Remove unsaved agreement'}).click();await expect(g).toHaveCount(0);
 const saved=page.waitForResponse(r=>r.url().endsWith('/national-support'));await page.getByRole('button',{name:'Analyze & save national plan'}).click();expect((await saved).status()).toBe(201);
 await expect(page.locator('[data-national-country=India]').first()).toContainText('Economic scenarios');
 await choose('Filter saved plans by country','India');await expect(page.locator('[data-national-country=India]').first()).toBeVisible();
 expect(errors).toEqual([]);
});
