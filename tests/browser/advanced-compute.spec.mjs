import {test,expect} from '@playwright/test';
test('country justice template and computation precision persist',async({page})=>{
 const errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto('/');await page.locator('nav [data-page=computepage]').click();
 await page.getByRole('button',{name:'Use country economics and justice criteria',exact:true}).click();
 const form=page.locator('#compute-form');await expect(form.locator('[data-compute-weight]')).toHaveCount(6);
 await expect(form.locator('[name=samples]')).toHaveAttribute('max','50000');await form.locator('[name=samples]').fill('200');
 for(const field of await form.locator('[data-compute-option]').all()){
  for(const input of await field.locator('[data-range]').all())await input.fill(({low:'2',likely:'5',high:'8'})[(await input.getAttribute('data-range')).split(':')[1]]);
  await field.locator('[name=source]').fill('Explicit synthetic verification assumptions');
  for(const select of await field.locator('[data-check]').all())await select.selectOption('pass');
 }
 const response=page.waitForResponse(r=>r.url().endsWith('/compute')&&r.request().method()==='POST');await form.getByRole('button',{name:'Compute & save decision analysis',exact:true}).click();
 expect((await response).status()).toBe(201);await expect(page.getByText('Engine: classical-local-monte-carlo-v2',{exact:false})).toBeVisible();
 await page.reload();await page.locator('nav [data-page=computepage]').click();await expect(page.getByText('Engine: classical-local-monte-carlo-v2',{exact:false})).toBeVisible();
 await page.setViewportSize({width:390,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);expect(errors).toEqual([]);
});
