<#!
.SYNOPSIS
Windows PowerShell quality gate; does not require WSL.

.DESCRIPTION
Equivalent to scripts/quality-gate.sh. On Windows, Impeccable is resolved directly from
node_modules or the npm npx cache so npx does not download a package for every run.

.PARAMETER Staged
Checks only the staged area; used by .githooks/pre-commit.

.NOTES
Set IMPECCABLE_BIN to an absolute impeccable(.cmd) path when the cache is elsewhere.
#>
[CmdletBinding()]
param(
    [switch]$Staged
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Result {
    param(
        [ValidateSet('OK', 'FAIL', 'SKIP')][string]$Kind,
        [string]$Message
    )

    Write-Host ("{0,-5} {1}" -f $Kind, $Message)
}

function Get-ChangedFiles {
    param([bool]$UseStaged)

    if ($UseStaged) {
        $tracked = @(& git diff --cached --name-only --diff-filter=ACMR)
    }
    else {
        $tracked = @(& git diff --name-only --diff-filter=ACMR HEAD)
        $untracked = @(& git ls-files --others --exclude-standard)
        $tracked += $untracked
    }

    return @($tracked | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
}

function Resolve-Impeccable {
    param([string]$RepositoryRoot)

    $candidates = [System.Collections.Generic.List[string]]::new()
    if (-not [string]::IsNullOrWhiteSpace($env:IMPECCABLE_BIN)) {
        $candidates.Add($env:IMPECCABLE_BIN)
    }

    $candidates.Add((Join-Path $RepositoryRoot 'node_modules\.bin\impeccable.cmd'))
    $candidates.Add((Join-Path $RepositoryRoot 'node_modules\.bin\impeccable'))

    if (-not [string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
        $npxRoot = Join-Path $env:LOCALAPPDATA 'npm-cache\_npx'
        if (Test-Path -LiteralPath $npxRoot) {
            $cachedPackages = Get-ChildItem -LiteralPath $npxRoot -Directory |
                Sort-Object LastWriteTime -Descending
            foreach ($cachedPackage in $cachedPackages) {
                $candidates.Add((Join-Path $cachedPackage.FullName 'node_modules\.bin\impeccable.cmd'))
                $candidates.Add((Join-Path $cachedPackage.FullName 'node_modules\.bin\impeccable'))
            }
        }
    }

    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return $candidate
        }
    }

    return $null
}

$repoRoot = (& git rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($repoRoot)) {
    Write-Error 'quality-gate: not inside a git repository.'
    exit 1
}

Set-Location -LiteralPath $repoRoot
$modeName = if ($Staged) { 'staged' } else { 'worktree' }
$failed = $false
$changedFiles = Get-ChangedFiles -UseStaged $Staged.IsPresent

Write-Host "quality-gate (mode: $modeName)"
Write-Host '---------------------------------------------'

# 1. Impeccable detect on UI surfaces.
$uiDirectories = @('webapp/frontend', 'slides', 'reports') |
    Where-Object { Test-Path -LiteralPath $_ -PathType Container }

if ($uiDirectories.Count -eq 0) {
    Write-Result SKIP 'impeccable detect — no UI directory exists (webapp/frontend, slides, reports)'
}
else {
    $impeccable = Resolve-Impeccable -RepositoryRoot $repoRoot
    if ($null -eq $impeccable) {
        Write-Result FAIL 'impeccable detect — local binary not found. Install Impeccable or set IMPECCABLE_BIN.'
        $failed = $true
    }
    else {
        New-Item -ItemType Directory -Path '.impeccable' -Force | Out-Null
        foreach ($uiDirectory in $uiDirectories) {
            & $impeccable detect --json $uiDirectory 1> '.impeccable/detect-report.json' 2> '.impeccable/detect-stderr.log'
            if ($LASTEXITCODE -eq 0) {
                Write-Result OK "impeccable detect $uiDirectory"
            }
            else {
                Write-Result FAIL "impeccable detect $uiDirectory"
                Write-Host '      report: .impeccable/detect-report.json'
                Write-Host '      stderr: .impeccable/detect-stderr.log'
                $failed = $true
            }
        }
    }
}

# 2. splits/ is immutable.
$splitTouched = @($changedFiles | Where-Object { $_ -like 'splits/*' })
if ($splitTouched.Count -gt 0) {
    if ($env:ALLOW_SPLIT_CHANGE -eq '1') {
        Write-Result OK 'splits/ changed — allowed through ALLOW_SPLIT_CHANGE=1'
    }
    else {
        Write-Result FAIL 'splits/ changed. This data is locked.'
        $splitTouched | ForEach-Object { Write-Host "      $_" }
        $failed = $true
    }
}
else {
    Write-Result OK 'splits/ unchanged'
}

# 3. Prevent patient data or checkpoints from entering git.
$badFiles = @($changedFiles | Where-Object { $_ -match '\.(nii(\.gz)?|dcm|dicom|pt|pth|ckpt|h5|npz)$' })
if ($badFiles.Count -gt 0) {
    Write-Result FAIL 'patient-data/checkpoint file is about to enter git:'
    $badFiles | ForEach-Object { Write-Host "      $_" }
    $failed = $true
}
else {
    Write-Result OK 'no patient-data/checkpoint file'
}

# 4. Python lint only when ruff and at least one Python surface exist.
# Ruff cai bang pip khong phai luc nao cung co shim `ruff.exe` tren PATH, nhung
# `python -m ruff` van chay. Gate cu chi thu lenh tran nen bao SKIP suot va lint
# khong bao gio chay tren may Windows nay (WORKLOG S-079).
$ruffTargets = @('src', 'tests', 'webapp', 'scripts') |
    Where-Object { Test-Path -LiteralPath $_ -PathType Container }
$ruffCmd = $null
if (Get-Command ruff -ErrorAction SilentlyContinue) {
    $ruffCmd = @('ruff')
}
elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $previousErrorActionPreference = $ErrorActionPreference
    try {
        # Ruff is optional.  Its non-zero exit when absent must not abort the
        # gate before it can report a normal SKIP.
        $ErrorActionPreference = 'Continue'
        & python -m ruff --version *> $null
        $ruffAvailable = $LASTEXITCODE -eq 0
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
    if ($ruffAvailable) { $ruffCmd = @('python', '-m', 'ruff') }
}

if ($ruffCmd -and $ruffTargets.Count -gt 0) {
    $exe = $ruffCmd[0]
    $prefix = if ($ruffCmd.Count -gt 1) {
        @($ruffCmd[1..($ruffCmd.Count - 1)])
    }
    else {
        @()
    }
    & $exe @prefix check @ruffTargets
    if ($LASTEXITCODE -eq 0) {
        Write-Result OK 'ruff check'
    }
    else {
        Write-Result FAIL 'ruff check'
        $failed = $true
    }
}
else {
    Write-Result SKIP 'ruff - not installed or no Python surface exists'
}

Write-Host '---------------------------------------------'
if ($failed) {
    Write-Result FAIL 'quality-gate: FAIL'
    exit 1
}

Write-Result OK 'quality-gate: PASS'
