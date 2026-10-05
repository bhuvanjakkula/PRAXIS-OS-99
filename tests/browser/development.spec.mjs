import {test,expect} from '@playwright/test';

test.beforeEach(async({page})=>{
 await page.goto('/');
 await page.getByRole('button',{name:'+ New decision',exact:true}).click();
 await page.getByRole('button',{name:'Fill example',exact:true}).click();
 await page.getByRole('button',{name:'Create decision model →',exact:true}).click();
 await expect(page.getByText('Orchestrator response',{exact:true})).toBeVisible();
});
test('development themes, portfolio validation, save and reload',async({page})=>{
 const errors=[];page.on('pageerror',e=>errors.push(e.message));await page.locator('nav [data-page=nationalpage]').click();
 await page.getByRole('button',{name:'Education, health and social protection',exact:true}).click();await expect(page.locator('#development-theme-detail')).toContainText('exclusion errors');
 await page.locator('#country-data-search').fill('India');await page.locator('[data-country-choice=India]').click();const f=page.locator('#national-form');
 for(const[k,v]of Object.entries({as_of:'2026-10-02',period:'One year',unit:'Synthetic present-value units',source:'Synthetic browser verification',problem:'Compare illustrative programs',objective:'Assess stated hypotheses'}))await f.locator(`[name=${k}]`).fill(v);
 await page.getByRole('button',{name:'Enable development portfolio',exact:true}).click();
 for(const[k,v]of Object.entries({development_budget:'10',development_priority:'3',development_floor:'0',development_drop:'0',development_rise:'0',development_interactions:'Independent synthetic projects with nonoverlapping beneficiaries; same valuation horizon'}))await f.locator(`[name=${k}]`).fill(v);
 for(let i=0;i<2;i++){
  await page.getByRole('button',{name:'Add development project',exact:true}).click();const p=f.locator('[data-development-project]').nth(i);
  for(const[k,v]of Object.entries({dp_name:i?'Training B':'Service A',dp_cost:i?'5':'6',dp_low:i?'10':'12',dp_likely:i?'10':'12',dp_high:i?'10':'12',dp_share:i?'90':'10',dp_evidence:'Synthetic valuation and review; not real policy evidence'}))await p.locator(`[name=${k}]`).fill(v);
  for(const select of await p.locator('[data-development-gate],[data-development-constraint]').all())await select.selectOption('pass');
 }
 const response=page.waitForResponse(r=>r.url().endsWith('/national-support')&&r.request().method()==='POST');await f.getByRole('button',{name:'Analyze & save national plan',exact:true}).click();const saved=await response;expect(saved.status()).toBe(201);
 const body=await saved.json();expect(body.analysis.development_portfolio.top_portfolios[0].projects).toEqual(['Training B']);
 await expect(page.getByRole('heading',{name:'Development portfolio results',exact:true})).toBeVisible();await page.reload();await page.locator('nav [data-page=nationalpage]').click();await expect(page.getByRole('heading',{name:'Development portfolio results',exact:true})).toBeVisible();
 await page.setViewportSize({width:390,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);expect(errors).toEqual([]);
});
