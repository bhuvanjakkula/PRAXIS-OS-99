import {test,expect} from '@playwright/test';
test('country leadership lists global countries and selects profiles',async({page})=>{
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('/');
  await page.locator('nav [data-page=nationalpage]').click();
  await expect(page.locator('#country-data-table [data-country-profile]')).toHaveCount(217);
  await expect(page.locator('#national-country option')).toHaveCount(219);
  await expect(page.locator('#country-data-picker button')).toHaveCount(217);
  await page.locator('[data-country-choice=Japan]').click();
  await expect(page.locator('#country-data-profile h3')).toContainText('Japan');
  await expect(page.locator('#national-country')).toHaveValue('Japan');
  await page.locator('#country-data-search').fill('');
  await page.locator('[data-country-income="High income"]').click();
  await expect(page.locator('[data-country-profile="United States"]')).toBeVisible();
  await expect(page.locator('[data-country-profile="India"]')).toHaveCount(0);
  await page.locator('#country-data-search').fill('India');
  await expect(page.locator('#country-data-income')).toHaveValue('');
  await expect(page.locator('[data-country-profile="India"]')).toBeVisible();
  for(const country of ['India','United States','Japan','Nigeria','Brazil']){
    await page.locator('#country-data-search').fill(country);
    await page.locator(`[data-country-profile="${country}"]`).click();
    await expect(page.locator('#country-data-profile h3')).toContainText(country);
    await expect(page.locator('#national-country')).toHaveValue(country);
  }
  await page.locator('#country-data-search').fill('IND');
  await expect(page.locator('[data-country-profile="India"]')).toBeVisible();
  expect(errors).toEqual([]);
});

test('every country button opens its matching profile and planning selection',async({page})=>{
 test.setTimeout(120000);const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/#country');await expect(page.locator('[data-country-profile]')).toHaveCount(217);
 const names=await page.locator('[data-country-choice]').evaluateAll(bs=>bs.map(b=>b.dataset.countryChoice));
 for(const name of names){await page.locator('#country-data-search').fill('');
 await page.getByRole('group',{name:'Find a country',exact:true}).getByRole('button',{name,exact:true}).click();
 await expect(page.locator('#country-data-profile h3')).toContainText(name);await expect(page.locator('#national-country')).toHaveValue(name);}
 expect(errors).toEqual([]);
});

test('income buttons reset search and restore all country buttons',async({page})=>{
 await page.goto('/#country');await expect(page.locator('[data-country-profile]')).toHaveCount(217);
 await page.locator('#country-data-search').fill('India');
 await page.locator('[data-country-income="Low income"]').click();
 await expect(page.locator('#country-data-search')).toHaveValue('');
 await expect(page.locator('[data-country-choice=Afghanistan]')).toBeVisible();
 await page.locator('[data-country-income=""]').click();
 await expect(page.locator('[data-country-choice]:not([hidden])')).toHaveCount(217);
 await page.locator('[data-country-choice=India]').click();
 await expect(page.locator('[data-country-choice]:not([hidden])')).toHaveCount(217);
 await expect(page.locator('#country-data-profile h3')).toContainText('India');
});
