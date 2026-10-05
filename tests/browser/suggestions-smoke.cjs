const {chromium}=require('playwright');
const assert=require('node:assert/strict');
(async()=>{
  const browser=await chromium.launch({channel:'msedge',headless:true});
  try{
    const page=await browser.newPage({viewport:{width:1440,height:1000}});
    const errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.goto(process.env.PRAXIS_BROWSER_URL||'http://127.0.0.1:8893');
    await page.getByRole('button',{name:'+ New decision',exact:true}).click();
    await page.getByRole('button',{name:'Fill example',exact:true}).click();
    await page.getByRole('button',{name:'Create decision model →',exact:true}).click();
    await page.getByText('Orchestrator response',{exact:true}).waitFor();
    assert.equal(await page.locator('nav [data-page=humanreview]').count(),0);
    await page.locator('[data-suggestion] [data-reject]').first().click();
    await page.locator('[data-suggestion] textarea').first().fill('Too expensive and slow');
    const saved=page.waitForResponse(r=>r.url().endsWith('/responses')&&r.request().method()==='POST');
    await page.getByRole('button',{name:'Generate updated suggestion',exact:true}).first().click();
    assert.equal((await saved).status(),201);
    await page.getByRole('heading',{name:'Updated suggestion',exact:true}).waitFor();
    await page.locator('[data-suggestion] [data-reject]').first().click();
    await page.locator('[data-suggestion] textarea').first().fill('Still too risky');
    await page.getByRole('button',{name:'Generate updated suggestion',exact:true}).first().click();
    await page.waitForFunction(()=>document.querySelectorAll('#suggestion-results h3').length===3);
    await page.locator('[data-suggestion] button[value=accept]').click();
    await page.getByText('accept',{exact:true}).waitFor();
    await page.reload();
    await page.locator('nav [data-page=chat]').click();
    await page.getByText('accept',{exact:true}).waitFor();
    await page.setViewportSize({width:390,height:844});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
    assert.deepEqual(errors,[]);
    console.log('Inline rejection, repeated revisions, acceptance, reload persistence and mobile layout passed');
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
