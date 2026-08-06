$paths = @('/','/products','/about','/portal/login','/portal/register','/portal/dashboard','/portal/appointments','/portal/leads','/portal/account','/portal/billing','/portal/support','/portal/calls','/portal/onboarding','/portal/order?package=Premium')
foreach($p in $paths){
    try {
        $r = Invoke-WebRequest -Uri ('http://localhost:5070' + $p) -UseBasicParsing -TimeoutSec 5
        Write-Host $p $r.StatusCode
    } catch {
        Write-Host $p ERR
    }
}
