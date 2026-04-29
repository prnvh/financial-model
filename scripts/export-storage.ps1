[CmdletBinding()]
param(
  [ValidateSet('linked', 'local')]
  [string]$Source = 'linked',

  [string[]]$Buckets = @(
    'raw-documents',
    'generated-deliverables',
    'snapshots',
    'exports'
  ),

  [string]$OutputDirectory = $(if ($env:BACKUP_ROOT) {
      Join-Path $env:BACKUP_ROOT 'storage'
    } else {
      'backups/storage'
    }),

  [ValidateRange(1, 32)]
  [int]$Jobs = 4
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $scriptRoot '_supabase-cli.ps1')

New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null

foreach ($bucket in $Buckets) {
  $bucketDirectory = Join-Path $OutputDirectory $bucket
  New-Item -ItemType Directory -Path $bucketDirectory -Force | Out-Null

  $arguments = @(
    'storage',
    'cp',
    "$bucket/",
    $bucketDirectory,
    '--experimental',
    '-r',
    '-j',
    "$Jobs"
  )

  if ($Source -eq 'linked') {
    $arguments += '--linked'
  } else {
    $arguments += '--local'
  }

  Invoke-SupabaseCli -Arguments $arguments
}

Write-Host "Storage export completed at $OutputDirectory"
