from pathlib import Path

page = Path('C:/Users/azelt/answerfirst-ai/public-site/portal-leads.html').read_text()

# Use relative API URLs so they hit the same unified backend regardless of host
page = page.replace('https://answerfirst-ai-backend.onrender.com/portal/api/leads', '/portal/api/leads')
page = page.replace('https://answerfirst-ai-backend.onrender.com/portal/api/appointments', '/portal/api/appointments')

old_body = '''<div class="main">
  <div class="page-header">
    <h1 class="page-title">Leads</h1>
    <p class="page-subtitle">Track your incoming leads and conversion status.</p>
  </div>
  <div class="table-container">
    <table><thead><tr><th>Name</th><th>Email</th><th>Phone</th><th>Source</th><th>Status</th></tr></thead><tbody id="leads-body"><tr><td colspan="5" class="empty-state">No leads yet.</td></tr></tbody></table>
  </div>
</div>'''

new_body = '''<div class="main">
  <div class="page-header">
    <h1 class="page-title">Leads</h1>
    <p class="page-subtitle">Manage leads, follow-up sequences, and attribution.</p>
  </div>
  <div style="display:flex;gap:12px;margin-bottom:24px;flex-wrap:wrap;">
    <button class="btn btn-primary" id="btn-add-lead">+ Add Lead</button>
    <select id="filter-status" class="form-input" style="width:auto;padding:10px 14px;border-radius:100px;">
      <option value="">All Statuses</option>
      <option value="new">New</option>
      <option value="contacted">Contacted</option>
      <option value="qualified">Qualified</option>
      <option value="converted">Converted</option>
      <option value="lost">Lost</option>
    </select>
    <input type="text" id="search-leads" class="form-input" placeholder="Search leads..." style="flex:1;min-width:180px;">
  </div>
  <div class="table-container">
    <table><thead><tr><th>Name</th><th>Email</th><th>Company</th><th>Source</th><th>Score</th><th>Status</th><th>Actions</th></tr></thead><tbody id="leads-body"><tr><td colspan="7" class="empty-state">No leads yet.</td></tr></tbody></table>
  </div>
</div>

<div id="lead-modal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:2000;align-items:center;justify-content:center;">
  <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);padding:24px;width:90%;max-width:520px;max-height:90vh;overflow:auto;">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <h2 style="font-size:1.1rem;font-weight:700;">Add Lead</h2>
      <button id="close-modal" style="background:none;border:none;font-size:1.2rem;cursor:pointer;color:var(--text-muted);">✕</button>
    </div>
    <form id="lead-form">
      <div class="form-group"><label class="form-label">Name *</label><input class="form-input" id="l-name" required></div>
      <div class="form-group"><label class="form-label">Email</label><input class="form-input" id="l-email" type="email"></div>
      <div class="form-group"><label class="form-label">Phone</label><input class="form-input" id="l-phone"></div>
      <div class="form-group"><label class="form-label">Company</label><input class="form-input" id="l-company"></div>
      <div class="form-group"><label class="form-label">Source</label><input class="form-input" id="l-source" placeholder="website, ads, referral"></div>
      <div class="form-group"><label class="form-label">Notes</label><textarea class="form-input" id="l-notes" rows="3"></textarea></div>
      <button type="submit" class="btn btn-primary">Save Lead</button>
    </form>
  </div>
</div>'''

page = page.replace(old_body, new_body)

old_script = '''(async()=>{
  try{
    const token = document.cookie.split('; ').find(row=>row.startsWith('portal_token='))?.split('=')[1];
    if(!token) return;
    const headers = {'X-Portal-Token': token};
    const [leadsR, apptsR] = await Promise.all([
      fetch('https://answerfirst-ai-backend.onrender.com/portal/api/leads', {headers}).catch(()=>null),
      fetch('https://answerfirst-ai-backend.onrender.com/portal/api/appointments', {headers}).catch(()=>null)
    ]);
    const leadsTb = document.getElementById('leads-body');
    const apptsTb = document.getElementById('appt-body');
    if(leadsR && leadsR.ok){
      const leads = await leadsR.json();
      if(!leads.length){ if(leadsTb) leadsTb.innerHTML='<tr><td colspan="5" class="empty-state">No leads yet.</td></tr>'; }
      else {
        if(leadsTb) leadsTb.innerHTML = leads.map(l=>`<tr><td>${l.name||l.business_name||'N/A'}</td><td>${l.email||'N/A'}</td><td>${l.phone||'N/A'}</td><td><span class="badge badge-blue">${l.source||'Web'}</span></td><td><span class="badge badge-green">${l.status||'new'}</span></td></tr>`).join('');
      }
    }
    if(apptsR && apptsR.ok){
      const appts = await apptsR.json();
      if(!appts.length){ if(apptsTb) apptsTb.innerHTML='<tr><td colspan="4" class="empty-state">No appointments scheduled yet.</td></tr>'; }
      else {
        if(apptsTb) apptsTb.innerHTML = appts.map(a=>`<tr><td>${a.scheduled_at||a.created_at?'TBD':'-'}</td><td>${a.customer_name||'N/A'}</td><td>${a.service_type||'Service'}</td><td><span class="badge badge-green">${a.status||'scheduled'}</span></td></tr>`).join('');
      }
    }
  }catch{}
})();'''

new_script = '''const API_BASE = ''; // same-origin via unified backend
async function getToken(){
  return document.cookie.split('; ').find(row=>row.startsWith('portal_token='))?.split('=')[1];
}
async function loadLeads(){
  const token = await getToken();
  if(!token) return;
  const headers = {'X-Portal-Token': token};
  const q = document.getElementById('search-leads')?.value?.toLowerCase() || '';
  const status = document.getElementById('filter-status')?.value || '';
  const params = new URLSearchParams();
  if(q) params.set('q', q);
  if(status) params.set('status', status);
  const r = await fetch(`/portal/api/leads?${params.toString()}`, {headers}).catch(()=>null);
  const tb = document.getElementById('leads-body');
  if(!r || !r.ok){ if(tb) tb.innerHTML='<tr><td colspan="7" class="empty-state">Unable to load leads.</td></tr>'; return; }
  const leads = await r.json();
  if(!leads.length){ if(tb) tb.innerHTML='<tr><td colspan="7" class="empty-state">No leads yet.</td></tr>'; return; }
  if(tb) tb.innerHTML = leads.map(l=>`<tr>
    <td>${l.name||'N/A'}</td>
    <td>${l.email||'N/A'}</td>
    <td>${l.company||'N/A'}</td>
    <td><span class="badge badge-blue">${l.source||'Web'}</span></td>
    <td>${l.score??0}</td>
    <td><span class="badge badge-green">${l.status||'new'}</span></td>
    <td><select onchange="updateLeadStatus(${l.id}, this.value)" style="padding:6px 8px;border-radius:8px;border:1px solid var(--border);background:var(--bg-alt);color:var(--text);"><option value="new" ${l.status==='new'?'selected':''}>New</option><option value="contacted" ${l.status==='contacted'?'selected':''}>Contacted</option><option value="qualified" ${l.status==='qualified'?'selected':''}>Qualified</option><option value="converted" ${l.status==='converted'?'selected':''}>Converted</option><option value="lost" ${l.status==='lost'?'selected':''}>Lost</option></select></td>
  </tr>`).join('');
}

async function updateLeadStatus(id, status){
  const token = await getToken();
  if(!token) return;
  await fetch(`/portal/api/leads/${id}`, {
    method:'PATCH',
    headers:{'Content-Type':'application/json','X-Portal-Token': token},
    body: JSON.stringify({status})
  });
  loadLeads();
}

document.getElementById('btn-add-lead')?.addEventListener('click', ()=>{
  document.getElementById('lead-modal').style.display='flex';
});
document.getElementById('close-modal')?.addEventListener('click', ()=>{
  document.getElementById('lead-modal').style.display='none';
});
document.getElementById('lead-form')?.addEventListener('submit', async (e)=>{
  e.preventDefault();
  const token = await getToken();
  if(!token) return;
  const data = {
    name: document.getElementById('l-name').value,
    email: document.getElementById('l-email').value,
    phone: document.getElementById('l-phone').value,
    company: document.getElementById('l-company').value,
    source: document.getElementById('l-source').value || 'website',
    notes: document.getElementById('l-notes').value
  };
  const r = await fetch('/portal/api/leads', {method:'POST', headers:{'Content-Type':'application/json','X-Portal-Token': token}, body: JSON.stringify(data)});
  if(r.ok){ document.getElementById('lead-modal').style.display='none'; document.getElementById('lead-form').reset(); loadLeads(); }
});
document.getElementById('filter-status')?.addEventListener('change', loadLeads);
document.getElementById('search-leads')?.addEventListener('input', loadLeads);

(async()=>{ try{ await loadLeads(); }catch{} })();'''

page = page.replace(old_script, new_script)

old_style_end = '@media(max-width:768px){.nav-links{display:none;}}\n</style>'
new_style_end = '''@media(max-width:768px){.nav-links{display:none;}}
.btn{width:auto;padding:12px 24px;border-radius:100px;font-weight:600;font-size:0.95rem;border:none;cursor:pointer;transition:transform var(--transition),box-shadow var(--transition);}
.btn-primary{background:linear-gradient(135deg,var(--accent),#2563eb);color:#fff;box-shadow:0 4px 15px var(--accent-glow);}
.btn-primary:hover{transform:translateY(-2px);box-shadow:0 8px 25px var(--accent-glow);}
.form-input{padding:10px 14px;border-radius:12px;border:1.5px solid var(--border);background:var(--bg-alt);color:var(--text);font-family:inherit;font-size:0.95rem;}
.form-input:focus{outline:none;border-color:var(--accent);}
.form-group{margin-bottom:16px;}
.form-label{display:block;font-weight:600;margin-bottom:6px;font-size:0.85rem;}
</style>'''

page = page.replace(old_style_end, new_style_end)

Path('C:/Users/azelt/answerfirst-ai/public-site/portal-leads.html').write_text(page)
pages_leads = Path('C:/Users/azelt/answerfirst-ai/public-site/pages/portal-leads.html')
if pages_leads.exists():
    pages_leads.write_text(page)
print('Patched portal leads page')
