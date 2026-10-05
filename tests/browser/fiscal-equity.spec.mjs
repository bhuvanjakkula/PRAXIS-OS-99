import {test,expect} from '@playwright/test';

test.beforeEach(async({page})=>{
 await page.goto('/');
 await page.getByRole('button',{name:'+ New decision',exact:true}).click();
 await page.getByRole('button',{name:'Fill example',exact:true}).click();
 await page.getByRole('button',{name:'Create decision model →',exact:true}).click();
 await expect(page.getByText('Orchestrator response',{exact:true})).toBeVisible();
});
test('fiscal and equity assumptions compute, save and survive reload',async({page})=>{
 const errors=[];page.on('pageerror',e=>errors.push(e.message));await page.locator('nav [data-page=nationalpage]').click();
 await page.locator('#country-data-search').fill('India');await page.locator('[data-country-choice=India]').click();
 const f=page.locator('#national-form');
 for(const[k,v]of Object.entries({as_of:'2026-10-03',period:'Two years',unit:'Synthetic units',source:'Synthetic browser test',problem:'Compare fiscal paths',objective:'Assess distribution'}))await f.locator(`[name=${k}]`).fill(v);
 await page.getByRole('button',{name:'Enable multi-year fiscal design',exact:true}).click();
 const fiscal={years:2,opening_gdp:1000,opening_debt:100,opening_reserve:15,nominal_growth:0,adverse_nominal_growth:-10,tax_base_share:50,effective_tax_rate:20,collection_efficiency:100,adverse_collection_drop:20,non_tax_revenue:0,capital_spending:30,service_spending:60,social_spending:20,spending_growth:0,interest_rate:10,adverse_interest_increase:5,evidence:'Synthetic fiscal assumptions'};
 for(const[k,v]of Object.entries(fiscal))await f.locator(`[name=fd_${k}]`).fill(String(v));
 await page.getByRole('button',{name:'Enable transfer equity analysis',exact:true}).click();
 for(const[k,v]of Object.entries({leakage:'25',poverty_line:'20',groups:'Lower | 100 | 10 | 0 | 20 | 50\nHigher | 100 | 30 | 5 | 0 | 0',evidence:'Synthetic population groups'}))await f.locator(`[name=te_${k}]`).fill(v);
 const response=page.waitForResponse(r=>r.url().endsWith('/national-support')&&r.request().method()==='POST');
 await f.getByRole('button',{name:'Analyze & save national plan',exact:true}).click();
 const saved=await response;expect(saved.status()).toBe(201);const body=await saved.json();
 expect(body.analysis.fiscal_design.scenarios[0].years[1].closing_debt).toBe(125.5);
 expect(body.analysis.transfer_equity.after.poverty_headcount_share).toBe(.25);
 await page.reload();await page.locator('nav [data-page=nationalpage]').click();
 await expect(page.getByRole('heading',{name:'Multi-year fiscal design results',exact:true}).first()).toBeVisible();
 await expect(page.getByRole('heading',{name:'Transfer equity results',exact:true}).first()).toBeVisible();
 await page.setViewportSize({width:390,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 expect(errors).toEqual([]);
});
