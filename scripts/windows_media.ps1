Add-Type -AssemblyName System.Runtime.WindowsRuntime
$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
})[0]

function Await {
    param($WinRTTask, [Type]$ResultType)
    $netTask = $asTask.MakeGenericMethod($ResultType).Invoke($null, @($WinRTTask))
    $netTask.Wait(-1) | Out-Null
    return $netTask.Result
}

[Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager, Windows, ContentType=WindowsRuntime] | Out-Null
$mgr = Await ([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager]::RequestAsync()) ([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager])

$result = @{ playing = $false; artist = $null; title = $null; app = $null }

foreach ($session in $mgr.GetSessions()) {
    $appId = $session.SourceAppUserModelId
    $status = $session.GetPlaybackInfo().PlaybackStatus
    if ($status.ToString() -ne 'Playing') { continue }

    $props = Await ($session.TryGetMediaPropertiesAsync()) ([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionMediaProperties])
    if (-not $props.Title) { continue }

    $prefer = $appId -like '*Spotify*'
    $result.playing = $true
    $result.artist = $props.Artist
    $result.title = $props.Title
    $result.app = $appId
    if ($prefer) { break }
}

$result | ConvertTo-Json -Compress
