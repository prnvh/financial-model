[CmdletBinding()]
param(
  [ValidateSet('linked', 'local', 'db-url')]
  [string]$Source = 'linked',

  [string]$DatabaseUrl,

  [string]$OutputDirectory = $(if ($env:BACKUP_ROOT) {
      Join-Path $env:BACKUP_ROOT 'db'
    } else {
      'backups/db'
    }),

  [switch]$DataOnly,

  [switch]$RoleOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($DataOnly -and $RoleOnly) {
  throw 'Choose either -DataOnly or -RoleOnly, not both.'
}

if ($Source -eq 'db-url' -and [string]::IsNullOrWhiteSpace($DatabaseUrl)) {
  throw 'When -Source db-url is used, provide a percent-encoded -DatabaseUrl.'
}

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $scriptRoot '_supabase-cli.ps1')

New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null

$timestamp = Get-Date -Format 'yyyy-MM-dd_HHmmss'
$dumpType = if ($RoleOnly) {
  'roles'
} elseif ($DataOnly) {
  'data'
} else {
  'schema'
}

$outputPath = Join-Path $OutputDirectory "db_${timestamp}_${dumpType}.sql"
$arguments = @('db', 'dump', '-f', $outputPath)

switch ($Source) {
  'linked' {
    $arguments += '--linked'
  }
  'local' {
    $arguments += '--local'
  }
  'db-url' {
    $arguments += @('--db-url', $DatabaseUrl)
  }
}

if ($DataOnly) {
  $arguments += '--data-only'
}

if ($RoleOnly) {
  $arguments += '--role-only'
}

Invoke-SupabaseCli -Arguments $arguments

Write-Host "Database dump created at $outputPath"
