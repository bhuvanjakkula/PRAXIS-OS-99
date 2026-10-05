$ErrorActionPreference = 'Stop'
$pgRoot = Join-Path $env:LOCALAPPDATA 'PRAXIS-OS\postgresql'
New-Item -ItemType Directory -Path $pgRoot -Force | Out-Null
$archive = Join-Path $pgRoot 'postgresql-16-windows.zip'
if (Test-Path -LiteralPath (Join-Path $pgRoot 'postgresql-server-16.zip')) {
    $archive = Join-Path $pgRoot 'postgresql-server-16.zip'
}
if (-not (Test-Path -LiteralPath $archive)) {
    # Official EDB Windows x64 PostgreSQL 16.15 archive.
    Invoke-WebRequest -Uri 'https://get.enterprisedb.com/postgresql/postgresql-16.15-4-windows-x64-binaries.zip' -OutFile ($archive + '.partial')
    Move-Item -LiteralPath ($archive + '.partial') -Destination $archive
}
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
& $python -m pip install -e "$PSScriptRoot[production]"
if ($LASTEXITCODE -ne 0) { throw 'Production dependencies could not be installed' }
& $python -m praxis.product.local_postgres setup --archive $archive
if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL setup failed; existing data was preserved' }
