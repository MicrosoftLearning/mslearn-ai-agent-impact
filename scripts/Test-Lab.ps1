# Offline only. This command does not sign in, deploy resources, or certify cloud readiness.
[CmdletBinding()]
param([ValidateSet('starter', 'repaired')][string]$FixtureState = 'starter')
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$python = Get-Command python -ErrorAction Stop
& $python.Source (Join-Path $PSScriptRoot 'validate_repository.py') --fixture-state $FixtureState
if ($LASTEXITCODE -ne 0) { throw 'Offline package validation failed. Review the output above.' }
