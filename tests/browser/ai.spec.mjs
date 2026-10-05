import {test,expect} from '@playwright/test';
test('AI analysis UI uses explicit requests and preserves review status',async({page})=>{
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  let saved=false,requestBody;
  const fixture={id:'test-run',decision_version:1,provider:'openai',model:'fixture-model',
    created_at:'2026-10-02T12:00:00Z',status:'unverified_analysis',execution_status:'not_executed',
    citation_check:'IDs exist in supplied context; claim support is not established',
    rounds:['proposer','critic','synthesis'].map(role=>({role,analysis:{summary:'Synthetic policy analysis',
      assumptions:['Supplied input'],uncertainties:['Measure effects'],proposed_experiment:'Reversible pilot',cited_document_ids:[]}}))};
  await page.route('**/v2/enterprise/capabilities',route=>route.fulfill({json:{reasoning_provider_configured:true,reasoning_provider:'openai',reasoning_model:'fixture-model',reasoning_allowed_classifications:['public']}}));
  await page.route('**/reasoning',route=>{if(route.request().method()==='POST'){saved=true;requestBody=route.request().postDataJSON();return route.fulfill({status:201,json:fixture});}return route.fulfill({json:saved?[fixture]:[]});});
  await page.goto('/');await page.getByRole('button',{name:'+ New decision',exact:true}).click();
  await page.getByRole('button',{name:'Fill example',exact:true}).click();await page.getByRole('button',{name:'Create decision model →',exact:true}).click();
  await expect(page.getByText('Orchestrator response',{exact:true})).toBeVisible();
  await page.locator('nav [data-page=aipage]').click();
  await expect(page.getByText(/Each analysis makes three API requests/)).toBeVisible();
  expect(saved).toBe(false);
  await page.locator('#ai-analysis-form textarea').fill('How can a small pilot test the policy?');
  await page.getByRole('button',{name:'Generate evidence-led analysis',exact:true}).click();
  await expect(page.getByText(/revision 1.*unverified_analysis/)).toBeVisible();
  expect(requestBody).toEqual({base_version:1,query:'How can a small pilot test the policy?'});
  await expect(page.getByText(/Action status: not_executed/)).toBeVisible();
  await page.setViewportSize({width:390,height:844});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  expect(errors).toEqual([]);
});
