<#
run_test.ps1 - helper to run the Python SQL Server smoke-test on Windows.

Features:
- Detects installed ODBC drivers (looks for Driver 18, then 17)
- Installs Python deps into the active environment if missing
- Defaults to server: Shantanu-PC and database: CollegeDB
- Accepts --Trusted, --Uid, --Pwd, --Server, --Database, --Driver

Usage (PowerShell):
  .\run_test.ps1                    # uses defaults (Shantanu-PC / CollegeDB)
  .\run_test.ps1 -Trusted           # use Windows Authentication
  .\run_test.ps1 -Uid sa -Pwd Pass  # use SQL auth
  .\run_test.ps1 -Server MyHost -Database MyDb -Driver "ODBC Driver 18 for SQL Server"
#>
param(
    [string] $Server = "Shantanu-PC",
    [string] $Database = "CollegeDB",
    [string] $Driver = $null,
    [switch] $Trusted,
    [string] $Uid = $null,
    [string] $Pwd = $null
)

function Find-Preferred-Driver {
    # Check registry for installed ODBC drivers
    $regPath = 'HKLM:\SOFTWARE\ODBC\ODBCINST.INI\ODBC Drivers'
    try {
        $drivers = Get-ItemProperty -Path $regPath -ErrorAction Stop | Get-Member -MemberType NoteProperty | Select-Object -ExpandProperty Name
    } catch {
        # Try the 32-bit registry hive on 64-bit systems
        $regPathWow = 'HKLM:\SOFTWARE\WOW6432Node\ODBC\ODBCINST.INI\ODBC Drivers'
        try {
            $drivers = Get-ItemProperty -Path $regPathWow -ErrorAction Stop | Get-Member -MemberType NoteProperty | Select-Object -ExpandProperty Name
        } catch {
            $drivers = @()
        }
    }

    if ($drivers -contains 'ODBC Driver 18 for SQL Server') { return 'ODBC Driver 18 for SQL Server' }
    if ($drivers -contains 'ODBC Driver 17 for SQL Server') { return 'ODBC Driver 17 for SQL Server' }
    # return first driver that looks like SQL Server driver
    $candidate = $drivers | Where-Object { $_ -match 'SQL Server' } | Select-Object -First 1
    if ($candidate) { return $candidate }
    return $null
}

Write-Host "Running SQL Server smoke-test helper..."

if (-not $Driver) {
    $found = Find-Preferred-Driver
    if ($found) {
        Write-Host "Detected ODBC driver: $found"
        $Driver = $found
    } else {
        Write-Warning "No suitable ODBC driver found in registry. Please install 'ODBC Driver 17 or 18 for SQL Server' and re-run, or pass -Driver explicitly."
    }
}

# Ensure Python is available
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Error "Python executable not found in PATH. Please install Python 3.7+ and add to PATH."
    exit 10
}

# Check pyodbc availability
$checkPyodbc = "import importlib,sys; print(importlib.util.find_spec('pyodbc') is not None)"
$pyodbcInstalled = & python -c $checkPyodbc 2>$null
if ($pyodbcInstalled -ne 'True') {
    Write-Host "pyodbc not found in current Python environment. Installing from requirements.txt..."
    & python -m pip install --upgrade pip
    & python -m pip install -r .\requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to install dependencies. See pip output above."
        exit 11
    }
}

# Build args for the Python script
$argList = @()
if ($Server) { $argList += "--server"; $argList += $Server }
if ($Database) { $argList += "--database"; $argList += $Database }
if ($Driver) { $argList += "--driver"; $argList += $Driver }
if ($Trusted) { $argList += "--trusted" }
if ($Uid) { $argList += "--uid"; $argList += $Uid }
if ($Pwd) { $argList += "--pwd"; $argList += $Pwd }

# If no credentials were passed, try Windows Authentication by default.
if (-not $Trusted -and -not $Uid -and -not $Pwd) {
    Write-Host "No credentials supplied; falling back to Windows Authentication (Trusted) by default."
    $argList += "--trusted"
}

Write-Host "Invoking test_sql_server.py with:"; Write-Host ($argList -join ' ')

# Run the test script and forward exit code
& python .\test_sql_server.py @argList
exit $LASTEXITCODE
