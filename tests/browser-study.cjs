// Browser smoke test: actual server and UI, explicitly mocked AI response; no paid API call.
const fs = require('fs'), path = require('path'), os = require('os'), cp = require('child_process');
const runtime = path.join(process.env.USERPROFILE,'.cache/codex-runtimes/codex-primary-runtime/dependencies');
const {chromium} = require(path.join(runtime,'node/node_modules/playwright'));
const root = path.resolve(__dirname,'..');
(async()=>{
  const data = fs.mkdtempSync(path.join(os.tmpdir(),'fan-agent-ui-'));
  const child = cp.spawn(path.join(runtime,'python/python.exe'),['-u','-c','import sys; from fan_agent.server import make_server; s=make_server(0,sys.argv[1]); print(s.server_address[1],flush=True); s.serve_forever()',data],{cwd:root,env:{...process.env,FAN_AGENT_AI_PROVIDER:'gemini',GEMINI_API_KEY:'',FAN_AGENT_AI_MODEL:''}});
  let browser;
  try {
    const port=await new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('Server timeout')),15000);child.stdout.once('data',b=>{clearTimeout(timer);resolve(b.toString().trim());});child.once('error',reject);});
    browser=await chromium.launch({channel:'msedge',headless:true});
    const page=await browser.newPage();
    const errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.goto('http://127.0.0.1:'+port);
    await page.getByRole('button',{name:'AI study planner'}).click();
    await page.waitForFunction(()=>document.getElementById('ai-status').textContent.includes('Set OPENAI_API_KEY'));
    if(!await page.locator('#study-submit').isDisabled()) throw Error('Missing configuration not gated');
    await page.route('**/api/ai/status',r=>r.fulfill({json:{configured:true,model:'mock-model',message:'Mock transport for browser test'}}));
    const c={name:'Ceiling fan at 250 RPM',rpm:250,diameter_mm:1200,room_x_m:4,room_y_m:4,room_z_m:3,rotor_height_m:2.5,sampling_height_m:1.2,direction:'cw'};
    await page.route('**/api/studies/propose',r=>r.fulfill({json:{status:'proposal_ready',qualification:'Review every input.',inputs:{rpms:[250,300],diameter_mm:1200},cases:[c,{...c,rpm:300}],missing_inputs:['geometry_id'],issues:[],unsupported:[],can_run:false,results:null}}));
    await page.getByRole('button',{name:'AI study planner'}).click();
    await page.locator('#study-prompt').fill('Compare ceiling fan at 250 and 300 RPM');
    await page.locator('#study-submit').click();
    await page.getByRole('button',{name:'Review 300 RPM in design form'}).click();
    if(await page.locator('[name=rpm]').inputValue()!=='300') throw Error('Proposal not transferred');
    if(await page.locator('[name=diameter_mm]').inputValue()!=='1200') throw Error('Diameter not transferred');
    const cases=await (await page.request.get('http://127.0.0.1:'+port+'/api/cases')).json();
    if(cases.length) throw Error('Proposal unexpectedly saved cases');
    if(errors.length) throw Error(errors.join('\n'));
    console.log('Browser passed: config gate, proposal render, design-form transfer, no saved cases, no JS errors. AI response mocked.');
  } finally {if(browser) await browser.close();child.kill();}
})().catch(e=>{console.error(e.message);process.exitCode=1;});
