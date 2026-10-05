const {chromium}=require('playwright');
const assert=require('node:assert/strict');
(async()=>{
  const browser=await chromium.launch({channel:'msedge',headless:true});
  try {
    const page=await browser.newPage({viewport:{width:1440,height:1000}});
    const errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.goto(process.env.PRAXIS_BROWSER_URL||'http://127.0.0.1:8880');
    await page.getByRole('button',{name:'+ New decision',exact:true}).click();
    await page.getByRole('button',{name:'Fill example',exact:true}).click();
    await page.getByRole('button',{name:'Create decision model →',exact:true}).click();
    await page.getByText('Orchestrator response',{exact:true}).waitFor();
    await page.getByRole('button',{name:/Human review$/}).click();
    assert.equal(await page.locator('[name=disposition]').inputValue(),'');
    for(const disposition of ['accept','reject']) {
      await page.getByText('Mental model and learning notes (optional)',{exact:true}).click();
      await page.locator('[name=expected_behavior]').fill('Use supplied scores');
      await page.locator('[name=mental_model_update]').fill('Check missing context');
      await page.locator('[name=independent_assessment]').fill('Start with a reversible trial');
      await page.locator('[name=advice_id]').selectOption('revision:1');
      await page.locator('[name=disposition]').selectOption(disposition);
      await page.locator('[name=reviewer]').fill('Human reviewer');
      await page.locator('[name=rationale]').fill(disposition==='accept'?'A small trial can test the assumption':'New concerns require a different approach');
      await page.locator('[name=reconsider_when]').fill('Review adverse outcomes after one week');
      const response=page.waitForResponse(r=>r.url().endsWith('/judgments')&&r.request().method()==='POST');
      await page.getByRole('button',{name:'Save human review',exact:true}).click();
      const saved=await response;
      assert.equal(saved.status(),201);
      assert.equal((await saved.json()).mental_model_update,'Check missing context');
      await page.getByText(disposition==='accept'?'A small trial can test the assumption':'New concerns require a different approach',{exact:true}).waitFor();
    }
    await page.reload();
    await page.getByRole('button',{name:/Human review$/}).click();
    await page.getByText('A small trial can test the assumption',{exact:true}).waitFor();
    await page.getByText('New concerns require a different approach',{exact:true}).waitFor();
    await page.locator('[name=advice_id]').selectOption('revision:1');
    assert.match(await page.locator('#human-advice-details').innerText(),/Latest response: reject/);
    await page.screenshot({path:'.test-tmp/human-review-desktop.png',fullPage:true});
    await page.setViewportSize({width:390,height:844});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
    await page.screenshot({path:'.test-tmp/human-review-mobile.png',fullPage:true});
    assert.deepEqual(errors,[]);
    console.log('PASS: explicit choice, accept, reject, changed mind with preserved history, persistence, desktop/mobile, no page errors');
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
