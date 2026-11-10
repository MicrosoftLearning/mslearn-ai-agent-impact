[CmdletBinding()]
param([Parameter(Mandatory)][ValidatePattern('^[a-z0-9]{5,50}$')][string]$Registry,
      [Parameter(Mandatory)][ValidatePattern('^[a-f0-9]{7,40}$')][string]$Revision)
$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Push-Location $repoRoot
try {
    $actualRevision = git rev-parse HEAD
    if ($LASTEXITCODE -ne 0 -or $actualRevision -ne $Revision) { throw 'Revision must be the exact full checked-out commit ID' }
    $pending = git status --porcelain --untracked-files=all
    if ($LASTEXITCODE -ne 0 -or $pending) { throw 'Commit reviewed source changes before building; local config and evidence must remain ignored' }
    $images = @{}
    foreach ($target in @('core','fixture')) {
        $tag = "caldova-$($target):$Revision"
        az acr build --registry $Registry --image $tag --target $target --file deploy/Dockerfile .
        if ($LASTEXITCODE -ne 0) { throw "Build failed for $target" }
        $digest = az acr repository show --name $Registry --image $tag --query digest --output tsv
        if ($LASTEXITCODE -ne 0 -or $digest -notmatch '^sha256:[a-f0-9]{64}$') { throw 'No immutable build digest returned' }
        $images[$target] = "$Registry.azurecr.io/caldova-$target@$digest"
    }
    New-Item -ItemType Directory -Path state -Force | Out-Null
    $images | ConvertTo-Json | Set-Content -LiteralPath "state/images-$Revision.json" -Encoding utf8
} finally { Pop-Location }
