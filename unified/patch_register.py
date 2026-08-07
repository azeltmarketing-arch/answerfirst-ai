from pathlib import Path

# Update portal register to route through unified backend and capture source/campaign
reg = Path('C:/Users/azelt/answerfirst-ai/public-site/portal-register.html').read_text()

reg = reg.replace('https://answerfirst-ai-backend.onrender.com/portal/api/register', '/portal/api/register')

# Add hidden source/campaign fields and capture from URL
old_form_start = '''  <form id="register-form">\r\n    <div class="form-group"><label>Business Name</label><input type="text" id="reg-business" required></div>\r\n    <div class="form-group"><label>Full Name</label><input type="text" id="reg-name" required></div>\r\n    <div class="form-group"><label>Email</label><input type="email" id="reg-email" required></div>\r\n    <div class="form-group"><label>Phone</label><input type="tel" id="reg-phone"></div>\r\n    <div class="form-group"><label>Password</label><input type="password" id="reg-password" required minlength="6"></div>'''

new_form_start = '''  <form id="register-form">\r\n    <input type="hidden" id="reg-source" value="">\r\n    <input type="hidden" id="reg-campaign" value="">\r\n    <input type="hidden" id="reg-utm_source" value="">\r\n    <input type="hidden" id="reg-utm_medium" value="">\r\n    <input type="hidden" id="reg-utm_campaign" value="">\r\n    <div class="form-group"><label>Business Name</label><input type="text" id="reg-business" required></div>\r\n    <div class="form-group"><label>Full Name</label><input type="text" id="reg-name" required></div>\r\n    <div class="form-group"><label>Email</label><input type="email" id="reg-email" required></div>\r\n    <div class="form-group"><label>Phone</label><input type="tel" id="reg-phone"></div>\r\n    <div class="form-group"><label>Password</label><input type="password" id="reg-password" required minlength="6"></div>'''

reg = reg.replace(old_form_start, new_form_start)

# Update submit handler to capture UTM and route correctly
old_submit = """document.getElementById('register-form').addEventListener('submit',async(e)=>{
  e.preventDefault();const err=document.getElementById('register-error');
  try{const r=await fetch('https://answerfirst-ai-backend.onrender.com/portal/api/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({business_name:document.getElementById('reg-business').value,name:document.getElementById('reg-name').value,email:document.getElementById('reg-email').value,phone:document.getElementById('reg-phone').value,password:document.getElementById('reg-password').value})});const j=await r.json();if(r.ok&&j._session_token&&!j.verification_required){window.location.href='/portal-dashboard.html';}else{err.style.display='block';err.textContent=j.error||'Registration failed';if(j.verification_required){const b=document.getElementById('verify-banner');if(b){b.style.display='block';}}}}catch(ex){err.style.display='block';err.textContent='Connection error';}
});"""

new_submit = """document.getElementById('register-form').addEventListener('submit',async(e)=>{
  e.preventDefault();const err=document.getElementById('register-error');
  const urlParams = new URLSearchParams(window.location.search);
  document.getElementById('reg-source').value = urlParams.get('source') || 'register';
  document.getElementById('reg-campaign').value = urlParams.get('campaign') || '';
  document.getElementById('reg-utm_source').value = urlParams.get('utm_source') || '';
  document.getElementById('reg-utm_medium').value = urlParams.get('utm_medium') || '';
  document.getElementById('reg-utm_campaign').value = urlParams.get('utm_campaign') || '';
  try{const r=await fetch('/portal/api/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({business_name:document.getElementById('reg-business').value,name:document.getElementById('reg-name').value,email:document.getElementById('reg-email').value,phone:document.getElementById('reg-phone').value,password:document.getElementById('reg-password').value,source:document.getElementById('reg-source').value,campaign:document.getElementById('reg-campaign').value,utm_source:document.getElementById('reg-utm_source').value,utm_medium:document.getElementById('reg-utm_medium').value,utm_campaign:document.getElementById('reg-utm_campaign').value})});const j=await r.json();if(r.ok&&j._session_token){window.location.href='/portal-dashboard.html';}else{err.style.display='block';err.textContent=j.error||'Registration failed';}}catch(ex){err.style.display='block';err.textContent='Connection error';}
});"""

reg = reg.replace(old_submit, new_submit)

# Write updated register page
Path('C:/Users/azelt/answerfirst-ai/public-site/portal-register.html').write_text(reg)
pages_reg = Path('C:/Users/azelt/answerfirst-ai/public-site/pages/portal-register.html')
if pages_reg.exists():
    pages_reg.write_text(reg)
print('Patched portal-register.html')
