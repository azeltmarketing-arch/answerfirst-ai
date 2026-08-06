# AnswerFirst AI — Deployment Guide

## Local Startup
1. Run CRM: `cd crm && python -m flask run --port=5050`
2. Run Dashboard: `cd dashboard && python -m http.server 8080`
3. Run Unified+Portal: `cd unified && python app.py`
4. Visit: `http://localhost:5070`

## Free 24/7 Hosting

### Frontend — Vercel (public-site)
1. Push `public-site/` to GitHub
2. Go to vercel.com → Import Project
3. Root Directory: `public-site`
4. Framework: Other
5. Deploy

### Backend — Render (unified + crm)
1. Go to render.com → New Web Service
2. Connect GitHub repo
3. Service 1 (unified):
   - Root: `unified`
   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn app:app`
   - Plan: Free
4. Service 2 (crm):
   - Root: `crm`
   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn app:app`
   - Plan: Free

### Connect Frontend to Backend
Update API URLs in `public-site/pages/portal-*.html`:
- `http://localhost:5070/portal/api/...` → `https://<unified-url>.onrender.com/portal/api/...`
- `http://127.0.0.1:5050/api/...` → `https://<crm-url>.onrender.com/api/...`

### CORS
Add to both `unified/app.py` and `crm/app.py`:
```python
from flask_cors import CORS
CORS(app)
```

### PayPal
Order page redirects to: `https://www.paypal.com/ncp/payment/GCMFXKYWWZKG4`
