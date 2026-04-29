Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Invoke-SupabaseCli {
  param(
    [Parameter(Mandatory = $true)]
    [string[]]$Arguments
  )

  $command = $null

  if (Get-Command supabase -ErrorAction SilentlyContinue) {
    $command = @('supabase')
  } elseif (Get-Command npx -ErrorAction SilentlyContinue) {
    $command = @('npx', '--yes', 'supabase')
  } else {
    throw 'Supabase CLI was not found. Install it globally or make npx available on PATH.'
  }

  $fullArguments = @()

  if ($command.Length -gt 1) {
    $fullArguments += $command[1..($command.Length - 1)]
  }

  $fullArguments += $Arguments

  & $command[0] @fullArguments

  if ($LASTEXITCODE -ne 0) {
    throw "Supabase CLI command failed with exit code $LASTEXITCODE."
  }
}
