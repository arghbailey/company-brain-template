# Scheduled entry point. Draft-only: calls librarian.py, never publish.py.
# Bounded by the Scheduled Task's own ExecutionTimeLimit (see docs/SCHEDULING.md), not here.
$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$ownerLine = (Select-String -Path "config\company.yml" -Pattern '^owner:\s*"?([^"\r\n]+)"?' -ErrorAction SilentlyContinue)
$owner = if ($ownerLine) { $ownerLine.Matches[0].Groups[1].Value.Trim() } else { "unassigned" }

python librarian\librarian.py --owner $owner
exit $LASTEXITCODE
