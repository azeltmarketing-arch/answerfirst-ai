from pathlib import Path

# Fix portal-login.html to use relative backend URLs
login = Path('C:/Users/azelt/answerfirst-ai/public-site/portal-login.html').read_text()

login = login.replace('https://answerfirst-ai-backend.onrender.com/portal/api/login', '/portal/api/login')
login = login.replace('https://answerfirst-ai-backend.onrender.com/portal/api/forgot-password', '/portal/api/forgot-password')

Path('C:/Users/azelt/answerfirst-ai/public-site/portal-login.html').write_text(login)
print('Patched portal-login.html')

# Also patch pages/ version if exists
pages_login = Path('C:/Users/azelt/answerfirst-ai/public-site/pages/portal-login.html')
if pages_login.exists():
    pages_login.write_text(login)
    print('Patched pages/portal-login.html')
