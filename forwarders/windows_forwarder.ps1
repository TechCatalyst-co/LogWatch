<#
  windows_forwarder.ps1 - stream a Windows PC's security events to LogWatch.

  Run in an ADMIN PowerShell (the Security log needs admin):
    powershell -ExecutionPolicy Bypass -File .\windows_forwarder.ps1 -Server https://logwatch-api.onrender.com -Key YOUR_INGEST_KEY

  Optional:  -Device "Booth laptop"   -Backfill 30  (minutes of history to send first)

  Events sent: sign-ins (4624/4625/4634/4647/4740), new accounts / admin groups
  (4720/4728/4732), scheduled tasks (4698), log cleared (1102), new services (7045),
  Defender detections (1116/1117), startup/shutdown (6005/6006/1074).

  Tip for the demo: type a wrong password at the lock screen a few times, or run
    net user demo_intruder P@ssw0rd123! /add     (then: net user demo_intruder /delete)
  and watch the big screen react.
#>
param(
  [Parameter(Mandatory=$true)][string]$Server,
  [Parameter(Mandatory=$true)][string]$Key,
  [string]$Device = "$env:COMPUTERNAME (Windows)",
  [int]$Backfill = 10,
  [int]$Interval = 3
)

$ErrorActionPreference = "SilentlyContinue"
$filters = @(
  @{ LogName = 'Security'; Id = 4624,4625,4634,4647,4698,4720,4728,4732,4740,1102 },
  @{ LogName = 'System';   Id = 7045,6005,6006,1074 },
  @{ LogName = 'Microsoft-Windows-Windows Defender/Operational'; Id = 1116,1117 }
)
$uri = "$Server/api/ingest?source=windows&device=" + [uri]::EscapeDataString($Device)
$since = (Get-Date).AddMinutes(-$Backfill)
Write-Host "Forwarding $Device -> $Server   (Ctrl+C to stop)"

function Get-Field($xml, $name) {
  ($xml.Event.EventData.Data | Where-Object { $_.Name -eq $name }).'#text'
}

while ($true) {
  $now = Get-Date
  $batch = @()
  foreach ($f in $filters) {
    $q = $f.Clone(); $q.StartTime = $since
    foreach ($e in (Get-WinEvent -FilterHashtable $q -ErrorAction SilentlyContinue | Sort-Object TimeCreated)) {
      $x = [xml]$e.ToXml()
      $batch += [ordered]@{
        TimeCreated     = $e.TimeCreated.ToString("s")
        EventID         = $e.Id
        TargetUserName  = Get-Field $x 'TargetUserName'
        SubjectUserName = Get-Field $x 'SubjectUserName'
        LogonType       = Get-Field $x 'LogonType'
        IpAddress       = Get-Field $x 'IpAddress'
        TaskName        = Get-Field $x 'TaskName'
        ServiceName     = Get-Field $x 'ServiceName'
        Threat          = Get-Field $x 'Threat Name'
        Message         = ($e.Message -split "`r?`n")[0]
      }
    }
  }
  if ($batch.Count -gt 0) {
    $headers = @{ 'X-Ingest-Key' = $Key }
    try {
      $body = ConvertTo-Json -InputObject @($batch) -Depth 3 -Compress
      $r = Invoke-RestMethod -Uri $uri -Method Post -Body $body -ContentType 'application/json' -Headers $headers
      Write-Host ("{0:HH:mm:ss}  sent {1} events" -f $now, $r.received)
    } catch { Write-Warning "Could not reach $Server : $_" }
  }
  $since = $now
  Start-Sleep -Seconds $Interval
}
