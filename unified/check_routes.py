import requests
s = requests.Session()
urls = [
    '/',
    '/products',
    '/about',
    '/portal/login',
    '/portal/register',
    '/portal/dashboard',
    '/portal/appointments',
    '/portal/leads',
    '/portal/account',
    '/portal/billing',
    '/portal/support',
    '/portal/calls',
    '/portal/onboarding',
    '/portal/order?package=Premium',
]
for u in urls:
    try:
        r = s.get('http://localhost:5070' + u, timeout=5)
        print(u, r.status_code)
    except Exception as e:
        print(u, 'ERR', e)
