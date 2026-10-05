from pathlib import Path
root=Path(__file__).parent
p=root/'src/praxis/web/studio.js'
s=p.read_text(encoding='utf-8-sig')
s=s.replace("['stress','Stress test']", "['stress','Stress test'],['five_cases','Five cases']")
s=s.replace('Profit = customers × price − fixed cost. This starter model uses one period and one consistent currency.',
            'Revenue = customers × price. Operating result = revenue − variable, fixed, technology, compliance and training costs.')
needle='<div class="two-col"><label>Monte Carlo samples'
addition='<div class="two-col"><label>Variable cost per customer<input name="variable_cost" type="number" min="0" max="1000000000" step="any" required value="0"></label><label>Technology cost<input name="technology_cost" type="number" min="0" max="1000000000000" step="any" required value="0"></label></div><div class="two-col"><label>Legal / compliance cost<input name="legal_cost" type="number" min="0" max="1000000000000" step="any" required value="0"></label><label>Human / training cost<input name="human_cost" type="number" min="0" max="1000000000000" step="any" required value="0"></label></div>'
if 'name="variable_cost"' not in s:s=s.replace(needle,addition+needle)
s=s.replace('<option value="revise">Request revision</option>', '<option value="investigate">Investigate</option><option value="modify">Modify</option><option value="revise">Request revision</option>')
s=s.replace("state.simulation=state.workspace.records.find(x=>x.id===b.dataset.run);render();", "state.simulation=state.workspace.records.find(x=>x.id===b.dataset.run);state.mode=state.simulation.mode;render();")
s=s.replace("$('#simulation-form')?.addEventListener", "if(state.page==='simulation' && state.simulation){for(const [key,value]of Object.entries(state.simulation.inputs)){const field=$('#simulation-form')?.elements.namedItem(key);if(field)field.value=key==='change'?value*100:value;}}\n  $('#simulation-form')?.addEventListener")
s=s.replace("state.selected=null;$('#main').innerHTML='';", "state.selected=null;state.page='dashboard';for(const key of Object.keys(labState))labState[key]=[];$('#main').innerHTML='';")
s=s.replace("await load();$('#identity-label')", "await load();if(state.page==='labs'||state.page==='sources')await loadLabs();$('#identity-label')")
p.write_text(s,encoding='utf-8')
for relative in ['pyproject.toml','src/praxis/__init__.py','tests/test_api.py']:
 p=root/relative;s=p.read_text(encoding='utf-8-sig');p.write_text(s.replace('0.8.0','0.9.0'),encoding='utf-8')
