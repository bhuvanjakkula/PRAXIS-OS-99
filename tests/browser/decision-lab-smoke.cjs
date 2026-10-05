// Run against an isolated local workspace: PRAXIS_BROWSER_URL=http://127.0.0.1:8878
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
(async () => {
  const browser = await chromium.launch({channel:'msedge', headless:true});
  try {
    const page = await browser.newPage({viewport:{width:1440,height:1000}});
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(process.env.PRAXIS_BROWSER_URL || 'http://127.0.0.1:8878');
    await page.getByRole('button',{name:'+ New decision',exact:true}).click();
    await page.getByRole('button',{name:'Fill example',exact:true}).click();
    await page.locator('[name=options]').fill('Pilot\nResearch');
    await page.getByRole('button',{name:'Create decision model →',exact:true}).click();
    await page.getByText('Orchestrator response',{exact:true}).waitFor();
    await page.getByRole('button',{name:/Decision lab$/}).click();
    await page.getByRole('heading',{name:'Review radar',exact:true}).waitFor();
    for (let row=0;row<2;row++) {
      for (let col=0;col<3;col++) await page.locator(`[data-score-row="${row}"][data-score-col="${col}"]`).fill(String(row===0?8:5));
      await page.locator(`[data-rationale="${row}"]`).fill('Browser test assessment, not verified evidence.');
    }
    await page.getByRole('button',{name:'Preview tradeoffs',exact:true}).click();
    await page.getByRole('heading',{name:'Comparison results',exact:true}).waitFor();
    await page.getByRole('button',{name:'Save comparison',exact:true}).click();
    await page.getByText('Comparison preserved with its inputs and decision revision.',{exact:true}).waitFor();
    const downloadPending=page.waitForEvent('download');
    await page.getByRole('button',{name:'Download decision brief',exact:true}).click();
    const download=await downloadPending;
    const brief=JSON.parse(await fs.readFile(await download.path(),'utf8'));
    assert.equal(brief.format,'praxis.decision-brief.v1');
    assert.equal(brief.records.filter(r=>r.kind==='option_comparison').length,1);
    assert.deepEqual(brief.records.find(r=>r.kind==='option_comparison').analysis.leaders,['Pilot']);
    await page.reload();
    await page.getByRole('button',{name:/Decision lab$/}).click();
    await page.locator('details.record').first().waitFor();
    await page.screenshot({path:'.test-tmp/decision-lab-desktop.png',fullPage:true});
    await page.setViewportSize({width:390,height:844});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'Mobile page overflows');
    await page.screenshot({path:'.test-tmp/decision-lab-mobile.png',fullPage:true});
    assert.deepEqual(errors,[]);
    console.log('PASS: radar, preview, save, exported brief, reload persistence, desktop/mobile, no page errors');
  } finally { await browser.close(); }
})().catch(error=>{console.error(error);process.exitCode=1;});
