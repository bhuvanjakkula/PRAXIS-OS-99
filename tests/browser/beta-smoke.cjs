const {chromium}=require('playwright');const assert=require('node:assert/strict');
(async()=>{const browser=await chromium.launch({channel:'msedge',headless:true});try{
 const page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 const url='http://127.0.0.1:8899';
 assert.equal((await page.request.get(url+'/v1/decision-models')).status(),401);
 assert.equal((await page.request.get(url+'/docs')).status(),404);
 await page.goto(url);await page.locator('#login-dialog').waitFor({state:'visible'});
 await page.locator('#login-form [name=credential]').fill(process.env.PRAXIS_BETA_TEST_TOKEN);
 await page.getByRole('button',{name:'Connect securely',exact:true}).click();await page.locator('#login-dialog').waitFor({state:'hidden'});
 await page.getByRole('button',{name:'+ New decision',exact:true}).click();await page.getByRole('button',{name:'Fill example',exact:true}).click();await page.getByRole('button',{name:'Create decision model →',exact:true}).click();await page.getByText('Orchestrator response',{exact:true}).waitFor();
 for(const [section,heading]of [['computepage','Explore how robust your choice is.'],['inquirypage','Turn an idea into a test.'],['aircrewpage','Aircrew incident support'],['shipcaptainpage','Ship captain incident support']]){await page.locator('nav [data-page='+section+']').click();await page.getByRole('heading',{name:heading,exact:true}).waitFor();}
 await page.setViewportSize({width:390,height:844});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
 await page.locator('#signout').click();await page.locator('#login-dialog').waitFor({state:'visible'});assert.deepEqual(errors,[]);
 console.log('Authenticated beta login, private routes, all new sections, mobile and signout passed');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exit(1)});
