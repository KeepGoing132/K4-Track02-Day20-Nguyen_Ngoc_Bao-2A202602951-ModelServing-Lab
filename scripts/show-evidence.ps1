<# Display saved, unedited outputs for real screenshots; does not rerun a test. #>
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('probe', 'bench', 'smoke', 'load-10', 'load-50')]
    [string] $Target
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$evidenceDir = Join-Path $PSScriptRoot '../benchmarks/evidence'
Write-Host 'RECORDED OUTPUT FROM THE ACTUAL LAB RUN' -ForegroundColor Cyan
switch ($Target) {
    'probe' { Get-Content -Encoding UTF8 -LiteralPath (Join-Path $evidenceDir 'probe.txt') }
    'bench' {
        $benchLog = Get-Content -Encoding UTF8 -LiteralPath (Join-Path $evidenceDir 'bench.txt')
        $benchLog | Select-Object -First 3
        $inTable = $false
        foreach ($line in $benchLog) {
            if ($line -like '# 01 - Measure:*') { $inTable = $true }
            if ($line -like '## Your observation*') { break }
            if ($inTable) { Write-Output $line }
        }
    }
    'smoke' {
        Get-Content -Encoding UTF8 -LiteralPath (Join-Path $evidenceDir 'server.txt') |
            Select-String -Pattern 'Started UTC:|Command:|Environment:|listening|model loaded'
        Get-Content -Encoding UTF8 -LiteralPath (Join-Path $evidenceDir 'smoke.txt')
    }
    default {
        $users = $Target.Replace('load-', '')
        $loadLog = Get-Content -Encoding UTF8 -LiteralPath (Join-Path $evidenceDir "locust-$users.txt")
        $loadLog | Select-Object -First 3
        # Include final statistics and final percentile rows on one screen.
        $tableStarts = @()
        for ($i = 0; $i -lt $loadLog.Count; $i++) {
            if ($loadLog[$i] -match '^Type\s+Name\s+') { $tableStarts += $i }
        }
        if ($tableStarts.Count -ge 2) {
            $loadLog | Select-Object -Skip $tableStarts[-2]
        } else { $loadLog }
    }
}
