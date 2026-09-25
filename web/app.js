"use strict";
const $ = (id) => document.getElementById(id);
let referenceData, cases = [], geometry = null, expanded = false, notificationTimer;
const number = (n, digits = 2) => Number(n).toLocaleString("en-US", { maximumFractionDigits: digits, minimumFractionDigits: digits });
const escapeText = (s) => String(s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));

async function api(path, options) {
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Request failed.");
  return data;
}
function notify(message, error = false) {
  clearTimeout(notificationTimer);
  $("notification").textContent = message;
  $("notification").className = error ? "error" : "";
  $("notification").hidden = false;
  notificationTimer = setTimeout(() => { $("notification").hidden = true; }, 9000);
}
function switchView(view) {
  if (!["reference", "design", "cases", "method", "simulation", "study"].includes(view)) return;
  document.querySelectorAll("section.page").forEach(el => { el.hidden = el.id !== view + "-view"; });
  document.querySelectorAll(".nav-item").forEach(el => el.classList.toggle("active", el.dataset.view === view));
  $("breadcrumb").textContent = {study:"AI study planner", reference:"Reference study", design:"New design", cases:"Saved cases", method:"Method & readiness", simulation:"Engineering run"}[view];
  if (view === "study") loadAIStatus();
  if (view === "simulation") loadDevelopmentRun().catch(error => { $("development-results").textContent=error.message; });
  if (view === "cases") refreshCases().catch(error => notify(error.message, true));
  window.scrollTo({top:0, behavior:"instant"});
}
async function loadDevelopmentRun() {
  const report=await api("/api/solver-development"), c=report.convergence;
  const rows=Object.entries(report.planes).sort((a,b)=>Number(a[0])-Number(b[0]));
  $("development-results").innerHTML=`
    <h3>${escapeText(c.status.replaceAll("_"," "))} · ${number(report.torque.last_iteration,0)} iterations</h3>
    <p>${escapeText(report.mesh)} · ${number(report.rpm,0)} RPM · ${escapeText(report.model)}</p>
    <p>Torque variation over the last ${number(report.torque.window_iterations,0)} iterations: <strong>${number(report.torque.relative_peak_to_peak*100)}%</strong>. Downward-flow change between the last two saved fields: <strong>${number(c.flow_relative_change*100)}%</strong>. Each stability target is ≤ ${number(c.relative_stability_limit*100)}%.</p>
    ${report.torque.long_window_drift ? `<p>Longer-window torque drift: <strong>${number(report.torque.long_window_drift.relative_change*100)}%</strong> between consecutive ${number(report.torque.long_window_drift.window_samples,0)}-sample averages. This is an additional diagnostic, separate from the unchanged acceptance checks below.</p>` : ""}
    <h3>Convergence checks</h3><ul>${Object.entries(c.checks).map(([k,v])=>`<li>${escapeText(k.replaceAll("_"," "))}: <strong>${v?"passed":"not met"}</strong></li>`).join("")}</ul>
    <h3>Flow through the 16 m² plane at ${number(report.plane_height_m,1)} m above the floor</h3>
    <table><thead><tr><th>Iteration</th><th>Downward (m³/min)</th><th>Reverse (m³/min)</th><th>Mean speed (m/s)</th></tr></thead><tbody>${rows.map(([time,p])=>`<tr><td>${escapeText(time)}</td><td>${number(p.downward_flow_cmm)}</td><td>${number(p.reverse_flow_cmm)}</td><td>${number(p.mean_air_speed_ms)}</td></tr>`).join("")}</tbody></table>
    <h3>Residual trend relative to each target</h3>
    ${residualTrend(report)}
    <p>A ratio of 1 is the target; values above 1 exceed it. Iteration count is not elapsed physical time.</p>
    <h3>Latest wall resolution (y-plus)</h3>
    <table><thead><tr><th>Patch</th><th>Minimum</th><th>Average</th><th>Maximum</th></tr></thead><tbody>${Object.entries(report.diagnostics?.latest_y_plus || {}).map(([patch,v])=>`<tr><td>${escapeText(patch)}</td><td>${number(v.min)}</td><td>${number(v.average)}</td><td>${number(v.max)}</td></tr>`).join("")}</tbody></table>
    <p>Y-plus describes the first cell's distance from the wall in viscous units. These values are diagnostic evidence; wall-treatment qualification is still pending.</p>
    <h3>Final initial residuals</h3><p>${Object.entries(report.final_initial_residuals).map(([k,v])=>`${escapeText(k)}: ${Number(v).toExponential(3)}`).join(" · ")}</p>
    <p>Residuals use the largest initial residual across corrections in the final iteration. Flow integrates the cell velocity over exact tetrahedron intersections with the horizontal plane.</p>
    <h3>Limits of this run</h3><ul>${report.limitations.map(s=>`<li>${escapeText(s)}</li>`).join("")}</ul>`;
}
function residualTrend(report) {
  const history=report.diagnostics?.residual_history || [];
  if(!history.length) return "<p>No history available for this saved assessment.</p>";
  const limits=report.convergence.provisional_residual_limits;
  const fields=Object.keys(limits), colors=["#176559","#227eb5","#8049a0","#bd522b","#777115","#555555"];
  const logs=history.flatMap(row=>fields.map(field=>Math.log10(Math.max(row.residuals[field]/limits[field],1e-6))));
  const low=Math.min(-1,Math.floor(Math.min(...logs))), high=Math.max(1,Math.ceil(Math.max(...logs)));
  const last=Math.max(...history.map(row=>row.iteration));
  const x=t=>55+620*t/last, y=v=>215-180*(v-low)/(high-low);
  let svg='<svg viewBox="0 0 700 270" role="img" aria-label="Residual to target ratio versus iteration, logarithmic vertical scale">';
  for(let v=low;v<=high;v++) svg+=`<line x1="55" x2="675" y1="${y(v)}" y2="${y(v)}" stroke="${v===0?"#9e6824":"#e1e7e5"}"/><text x="45" y="${y(v)+4}" text-anchor="end" font-size="11">${10**v}</text>`;
  fields.forEach((field,i)=>{
    svg+=`<polyline points="${history.map(row=>`${x(row.iteration)},${y(Math.log10(Math.max(row.residuals[field]/limits[field],1e-6)))}`).join(" ")}" fill="none" stroke="${colors[i]}" stroke-width="2"/><text x="${60+i*95}" y="18" font-size="12" fill="${colors[i]}">${escapeText(field)}</text>`;
  });
  for(let i=0;i<=4;i++) svg+=`<text x="${x(last*i/4)}" y="237" text-anchor="middle" font-size="11">${number(last*i/4,0)}</text>`;
  return svg+'<text x="350" y="262" text-anchor="middle" font-size="12">Iteration</text></svg>';
}
document.addEventListener("click", event => {
  const target = event.target.closest("[data-view]");
  if (target) switchView(target.dataset.view);
});
function download(data, filename) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], {type:"application/json"}));
  const a = document.createElement("a"); a.href = url; a.download = filename; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function drawChart() {
  const samples = referenceData.samples;
  const width=700, height=278, left=53, right=18, top=17, bottom=50;
  const x = (v) => left + v/1000*(width-left-right);
  const y = (v) => height-bottom-v/3.5*(height-top-bottom);
  const points = samples.map(s => `${x(s.position_mm)},${y(s.velocity_ms)}`).join(" ");
  let svg = `<svg viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="area" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#609c83" stop-opacity=".20"/><stop offset="100%" stop-color="#609c83" stop-opacity=".015"/></linearGradient></defs>`;
  for(let value=0;value<=3.5;value+=.5) svg += `<line x1="${left}" x2="${width-right}" y1="${y(value)}" y2="${y(value)}" stroke="#edf1eb"/><text x="${left-13}" y="${y(value)+3}" text-anchor="end" font-size="10" fill="#8b9b8a">${value.toFixed(1)}</text>`;
  for(let value=0;value<=1000;value+=200) svg += `<text x="${x(value)}" y="${height-bottom+21}" text-anchor="middle" font-size="10" fill="#8b9b8a">${value}</text>`;
  svg += `<polygon points="${x(40)},${y(0)} ${points} ${x(920)},${y(0)}" fill="url(#area)"/><polyline points="${points}" fill="none" stroke="#256b56" stroke-width="2.8" stroke-linejoin="round"/>`;
  for(const sample of samples) svg += `<circle cx="${x(sample.position_mm)}" cy="${y(sample.velocity_ms)}" r="4" fill="white" stroke="#256b56" stroke-width="2"><title>${sample.position_mm} mm: ${sample.velocity_ms} m/s</title></circle>`;
  svg += `<text x="${width/2}" y="${height-7}" text-anchor="middle" font-size="10" fill="#83917d">Reported position (mm)</text><text x="13" y="${height/2-15}" transform="rotate(-90 13 ${height/2-15})" text-anchor="middle" font-size="10" fill="#83917d">Average velocity (m/s)</text></svg>`;
  $("velocity-chart").innerHTML = svg;
}
function drawSamples() {
  const samples = referenceData.samples;
  const rows = expanded ? 6 : 3;
  $("samples").innerHTML = Array.from({length:rows}, (_,i) => `<tr><td>${samples[i].position_mm}</td><td>${number(samples[i].velocity_ms, 6)}</td><td>${samples[i+6].position_mm}</td><td>${number(samples[i+6].velocity_ms, 6)}</td></tr>`).join("");
  $("toggle-samples").textContent = expanded ? "Show fewer ↑" : "Show all 12 ↓";
  $("toggle-samples").setAttribute("aria-expanded", String(expanded));
}
$("toggle-samples").addEventListener("click", () => { expanded = !expanded; drawSamples(); });
$("export-reference").addEventListener("click", () => { if(referenceData) download(referenceData, "fan-agent-company-reference.json"); });

function drawGeometry(report) {
  const canvas = $("geometry-canvas"), ctx=canvas.getContext("2d");
  const mid = report.bounds_m[0].map((v,i) => (v+report.bounds_m[1][i])/2);
  const project = v => { const [x,y,z]=v.map((a,i)=>a-mid[i]); return [(x-y)*.8, (x+y)*.35-z]; };
  const triangles = report.preview_triangles_m.map(t=>t.map(project));
  const vertices=triangles.flat(), bound = Math.max(...vertices.map(v=>Math.max(Math.abs(v[0]), Math.abs(v[1]))), 1e-9);
  const scale=145/bound;
  ctx.clearRect(0,0,canvas.width,canvas.height);
  ctx.strokeStyle="#5b8b70"; ctx.lineWidth=.65; ctx.fillStyle="#cadbcb66";
  for(const triangle of triangles) { ctx.beginPath(); triangle.forEach((v,i)=>ctx[i ? "lineTo" : "moveTo"](300+v[0]*scale,180+v[1]*scale)); ctx.closePath(); ctx.fill(); ctx.stroke(); }
}
function clearGeometry() {
  geometry = null; $("stl-file").value = ""; $("geometry-report").hidden = true;
}
$("clear-geometry").addEventListener("click", clearGeometry);
$("stl-units").addEventListener("change", () => { if(geometry) {clearGeometry(); notify("Coordinate units changed. Upload the STL again to inspect it with the new units.");} });
$("stl-file").addEventListener("change", async event => {
  const file=event.target.files[0];
  if(!file) return;
  const units=$("stl-units").value;
  const isStep=/\.(step|stp)$/i.test(file.name);
  if(!isStep && !units) { clearGeometry(); notify("Choose STL coordinate units before uploading.",true); return; }
  if(!isStep && !file.name.toLowerCase().endsWith(".stl")) { clearGeometry(); notify("Choose a STEP or STL file.",true); return; }
  if(file.size>32*1024*1024) { clearGeometry(); notify("STL exceeds the 32 MiB limit.",true); return; }
  geometry=null; $("geometry-report").hidden=true;
  $("stl-file").disabled=true; $("stl-units").disabled=true; $("save-case").disabled=true;
  notify("Inspecting geometry locally…");
  try {
    geometry=await api(`/api/geometry?units=${units}&format=${isStep?"step":"stl"}`,{method:"POST",headers:{"Content-Type":"application/octet-stream"},body:file});
    $("geometry-report").hidden=false;
    $("geometry-details").innerHTML=`<p><strong>${escapeText(file.name)}</strong></p><p>${number(geometry.triangle_count,0)} triangles · ${escapeText(geometry.source_format || geometry.format)}</p><p>Bounds: ${geometry.extent_m.map(v=>number(v*1000,1)).join(" × ")} mm</p><p class="${geometry.surface_preflight_pass?"success-text":"error-text"}">${geometry.boundary_edges} open edges · ${geometry.nonmanifold_edges} nonmanifold edges · ${geometry.degenerate_triangles} degenerate triangles</p><p class="field-note">${escapeText(geometry.limitations)} Preview uses at most 1,800 triangles; checks use the full file.</p>`;
    drawGeometry(geometry); notify(geometry.surface_preflight_pass?"Basic STL checks passed. Geometry placement still needs review.":"Geometry stored with surface issues. Solver readiness remains blocked.",!geometry.surface_preflight_pass);
  } catch(error) {clearGeometry();notify(error.message,true);}
  finally {$("stl-file").disabled=false;$("stl-units").disabled=false;$("save-case").disabled=false;}
});
$("case-form").addEventListener("submit", async event => {
  event.preventDefault();
  const raw=Object.fromEntries(new FormData(event.target)); raw.geometry_id=geometry?.id||"";
  $("save-case").disabled=true;
  try {
    const record=await api("/api/cases",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(raw)});
    await refreshCases();switchView("cases");showCase(record.id);notify("Case saved. Review its readiness checks below.");
  } catch(error) {notify(error.message,true);}
  finally {$("save-case").disabled=false;}
});
async function refreshCases() {
  cases=await api("/api/cases"); $("case-count").textContent=cases.length;
  if(!cases.length) {$("case-list").innerHTML='<div class="empty-state"><p class="eyebrow">YOUR NEXT DESIGN STARTS HERE</p><h2>No cases saved yet.</h2><p>Create a design specification and review what it needs before simulation.</p><button class="button primary" data-view="design">＋ Create your first case</button></div>';return;}
  $("case-list").innerHTML=cases.map(c=>`<article class="case-row"><span class="case-icon">✳</span><div class="case-title"><strong>${escapeText(c.parameters.name)}</strong><p>${number(c.parameters.rpm,0)} RPM · ${number(c.parameters.diameter_mm,0)} mm · ${escapeText(new Date(c.created_at).toLocaleString())}</p></div><span class="badge amber">Qualification needed</span><button class="button secondary" data-case="${c.id}">View readiness →</button></article>`).join("");
}
function showCase(id) {
  const record=cases.find(c=>c.id===id);if(!record)return;
  $("case-detail").hidden=false;
  const p=record.parameters;
  $("case-detail").innerHTML=`<article class="panel detail-panel"><div class="detail-top"><h2>${escapeText(p.name)}</h2><button class="button secondary" id="export-case">↓ Export specification</button></div><p>${escapeText(record.preflight.summary)}</p><p>Room: ${p.room_x_m} × ${p.room_y_m} × ${p.room_z_m} m · Rotor height: ${p.rotor_height_m} m · ${p.direction.toUpperCase()} viewed from above · Tip speed: ${number(p.tip_speed_ms,2)} m/s</p>${record.preflight.checks.map(check=>`<div class="check-row"><span class="badge ${check.status==="pass"?"green":"amber"}">${check.status==="pass"?"Checked":"Pending"}</span><div><strong>${escapeText(check.label)}</strong><p>${escapeText(check.detail)}</p></div></div>`).join("")}<p class="field-note">Saved recipe: ${escapeText(record.recipe.id)} · Execution: not started · Results: none</p></article>`;
  $("export-case").addEventListener("click",()=>download(record,`fan-agent-case-${id.slice(0,8)}.json`));
  $("case-detail").scrollIntoView({behavior:"smooth",block:"start"});
}
$("case-list").addEventListener("click",event=>{const button=event.target.closest("[data-case]");if(button)showCase(button.dataset.case);});
async function init() {
  try {
    referenceData=await api("/api/reference");
    $("air-cmm").innerHTML=`${number(referenceData.air_delivery_cmm)} <small>CMM</small>`;
    $("air-cfm").textContent=`≈ ${number(referenceData.air_delivery_cfm,0)} CFM · converted`;
    $("torque").innerHTML=`${number(referenceData.torque_nm)} <small>N·m</small>`;
    $("power").innerHTML=`${number(referenceData.shaft_power_w,1)} <small>W</small>`;
    $("unknowns").innerHTML=referenceData.unknowns.map(u=>`<li>${escapeText(u)}</li>`).join("");
    drawChart();drawSamples();await refreshCases();
  } catch(error) {notify("Unable to load the local application: "+error.message,true);}
}
init();

let studyProposal = null;
async function loadAIStatus() {
  try {
    const status = await api("/api/ai/status");
    $("ai-status").textContent = status.message + (status.model ? " Model: " + status.model : "");
    $("ai-provider-note").textContent = `Only the text you enter here is sent to ${status.provider || "the configured AI provider"}. CAD files and saved cases stay local.`;
    $("study-submit").disabled = !status.configured;
  } catch (error) { $("ai-status").textContent = error.message; $("study-submit").disabled = true; }
}
$("study-form").addEventListener("submit", async event => {
  event.preventDefault(); studyProposal = null; $("study-submit").disabled = true;
  $("study-result").textContent = "Interpreting your request…";
  try {
    const p = await api("/api/studies/propose", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({prompt:$("study-prompt").value})});
    studyProposal = p;
    const list = items => `<ul>${items.map(v=>`<li>${escapeText(v)}</li>`).join("")}</ul>`;
    $("study-result").innerHTML = `<h2>${escapeText(p.status.replaceAll("_"," "))}</h2><p>${escapeText(p.qualification)}</p>
      <h3>Extracted inputs — review before use</h3><dl>${Object.entries(p.inputs).filter(([k])=>k!=="unsupported").map(([k,v])=>`<dt>${escapeText(k)}</dt><dd>${escapeText(v === null ? "Not supplied" : Array.isArray(v) ? v.join(", ") : v)}</dd>`).join("")}</dl>
      <h3>Still needed</h3>${list(p.missing_inputs)}${p.issues.length?"<h3>Input issues</h3>"+list(p.issues):""}${p.unsupported.length?"<h3>Outside current scope</h3>"+list(p.unsupported):""}
      ${p.cases.map((c,i)=>`<p><button class="button secondary" data-proposal-case="${i}">Review ${escapeText(c.rpm)} RPM in design form</button></p>`).join("")}
      <button class="button secondary" id="export-study">Download proposal</button><p>Simulation: blocked · Results: none</p>`;
    $("export-study").addEventListener("click",()=>download(p,"fan-agent-study-proposal.json"));
  } catch(error) { $("study-result").textContent = error.message; }
  finally { $("study-submit").disabled = false; }
});
$("study-result").addEventListener("click", event => {
  const button = event.target.closest("[data-proposal-case]");
  if (!button || !studyProposal) return;
  const c = studyProposal.cases[Number(button.dataset.proposalCase)];
  if (!c) return;
  for (const [k,v] of Object.entries(c)) {
    const input = $("case-form").elements.namedItem(k); if(input) input.value = v;
  }
  switchView("design"); notify("Proposal copied for review. Attach or confirm local geometry, then save the case.");
});
