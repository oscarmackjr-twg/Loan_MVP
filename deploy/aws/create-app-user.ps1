# Create a user in the deployed Loan Engine app via admin API.
# This script logs in as an admin and calls /api/auth/register.
#
# Examples:
#   .\deploy\aws\create-app-user.ps1 `
#     -BaseUrl "http://your-alb-url" `
#     -AdminUsername "admin" `
#     -AdminPassword "admin123" `
#     -Username "jdoe" `
#     -Email "jdoe@company.com" `
#     -Password "TempPass!123" `
#     -FullName "Jane Doe" `
#     -Role analyst
#
#   # List sales teams first (for sales_team users):
#   .\deploy\aws\create-app-user.ps1 `
#     -BaseUrl "http://your-alb-url" `
#     -AdminUsername "admin" `
#     -AdminPassword "admin123" `
#     -ListSalesTeams
#
#   # Create sales_team user:
#   .\deploy\aws\create-app-user.ps1 `
#     -BaseUrl "http://your-alb-url" `
#     -AdminUsername "admin" `
#     -AdminPassword "admin123" `
#     -Username "steam1" `
#     -Email "steam1@company.com" `
#     -Password "TempPass!123" `
#     -FullName "Sales Team User" `
#     -Role sales_team `
#     -SalesTeamId 1

param(
    [Parameter(Mandatory = $true)]
    [string]$BaseUrl,

    [string]$AdminUsername = "admin",

    [Parameter(Mandatory = $true)]
    [string]$AdminPassword,

    [string]$Username,
    [string]$Email,
    [string]$Password,
    [string]$FullName,

    [ValidateSet("admin", "analyst", "sales_team")]
    [string]$Role = "analyst",

    [int]$SalesTeamId,

    [switch]$ListSalesTeams
)

$ErrorActionPreference = "Stop"

function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Warn { Write-Host $args -ForegroundColor Yellow }
function Write-Fail { Write-Host $args -ForegroundColor Red }

function Get-HttpErrorDetail {
    param([System.Management.Automation.ErrorRecord]$Err)
    try {
        $resp = $Err.Exception.Response
        if ($null -eq $resp) { return $Err.Exception.Message }
        $stream = $resp.GetResponseStream()
        if ($null -eq $stream) { return $Err.Exception.Message }
        $reader = New-Object System.IO.StreamReader($stream)
        $body = $reader.ReadToEnd()
        if ([string]::IsNullOrWhiteSpace($body)) { return $Err.Exception.Message }
        return $body
    } catch {
        return $Err.Exception.Message
    }
}

$base = $BaseUrl.TrimEnd("/")
Write-Info "Target API: $base"

# 1) Admin login
$loginUri = "$base/api/auth/login"
$loginBody = "username=$([uri]::EscapeDataString($AdminUsername))&password=$([uri]::EscapeDataString($AdminPassword))"

Write-Info "Logging in as admin user '$AdminUsername'..."
try {
    $loginResp = Invoke-RestMethod -Method Post -Uri $loginUri -ContentType "application/x-www-form-urlencoded" -Body $loginBody
} catch {
    $detail = Get-HttpErrorDetail -Err $_
    Write-Fail "Admin login failed."
    Write-Host $detail -ForegroundColor Gray
    exit 1
}

if (-not $loginResp.access_token) {
    Write-Fail "Login succeeded but no access token was returned."
    exit 1
}

$headers = @{
    Authorization = "Bearer $($loginResp.access_token)"
}

Write-Success "Admin login successful."

# Optional: list sales teams for lookup
if ($ListSalesTeams) {
    Write-Info "Fetching sales teams..."
    try {
        $teams = Invoke-RestMethod -Method Get -Uri "$base/api/sales-teams" -Headers $headers
        if ($teams -and $teams.Count -gt 0) {
            Write-Host ""
            Write-Host "Sales Teams:" -ForegroundColor Cyan
            $teams | ForEach-Object {
                Write-Host ("  ID={0}  Name={1}  Users={2}" -f $_.id, $_.name, $_.user_count) -ForegroundColor Gray
            }
            Write-Host ""
        } else {
            Write-Warn "No active sales teams found."
        }
    } catch {
        $detail = Get-HttpErrorDetail -Err $_
        Write-Fail "Failed to list sales teams."
        Write-Host $detail -ForegroundColor Gray
        exit 1
    }
}

# If only listing sales teams, allow early exit
if ($ListSalesTeams -and [string]::IsNullOrWhiteSpace($Username) -and [string]::IsNullOrWhiteSpace($Email)) {
    Write-Success "Done."
    exit 0
}

# 2) Validate required user fields
$missing = @()
if ([string]::IsNullOrWhiteSpace($Username)) { $missing += "Username" }
if ([string]::IsNullOrWhiteSpace($Email)) { $missing += "Email" }
if ([string]::IsNullOrWhiteSpace($Password)) { $missing += "Password" }
if ([string]::IsNullOrWhiteSpace($FullName)) { $missing += "FullName" }

if ($missing.Count -gt 0) {
    Write-Fail ("Missing required parameters for user creation: " + ($missing -join ", "))
    exit 1
}

if ($Role -eq "sales_team" -and -not $PSBoundParameters.ContainsKey("SalesTeamId")) {
    Write-Fail "Role 'sales_team' requires -SalesTeamId."
    exit 1
}

# 3) Create user
$payload = @{
    email = $Email
    username = $Username
    password = $Password
    full_name = $FullName
    role = $Role
}

if ($Role -eq "sales_team") {
    $payload.sales_team_id = $SalesTeamId
}

$registerUri = "$base/api/auth/register"
Write-Info "Creating user '$Username' with role '$Role'..."
try {
    $created = Invoke-RestMethod -Method Post -Uri $registerUri -Headers ($headers + @{ "Content-Type" = "application/json" }) -Body ($payload | ConvertTo-Json)
} catch {
    $detail = Get-HttpErrorDetail -Err $_
    Write-Fail "User creation failed."
    Write-Host $detail -ForegroundColor Gray
    exit 1
}

Write-Success "User created successfully."
Write-Host ("  ID: {0}" -f $created.id) -ForegroundColor Gray
Write-Host ("  Username: {0}" -f $created.username) -ForegroundColor Gray
Write-Host ("  Email: {0}" -f $created.email) -ForegroundColor Gray
Write-Host ("  Role: {0}" -f $created.role) -ForegroundColor Gray
Write-Host ("  SalesTeamId: {0}" -f $created.sales_team_id) -ForegroundColor Gray
