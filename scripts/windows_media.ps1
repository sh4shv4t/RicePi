param(
    [string]$ArtOut = ""
)

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

$result = @{
    playing = $false
    artist  = $null
    title   = $null
    app     = $null
    art_saved = $false
}

foreach ($session in $mgr.GetSessions()) {
    $appId = $session.SourceAppUserModelId
    $status = $session.GetPlaybackInfo().PlaybackStatus
    if ($status.ToString() -ne 'Playing') { continue }

    $props = Await ($session.TryGetMediaPropertiesAsync()) ([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionMediaProperties])
    if (-not $props.Title) { continue }

    $result.playing = $true
    $result.artist = $props.Artist
    $result.title = $props.Title
    $result.app = $appId

    if ($ArtOut -and $props.Thumbnail) {
        try {
            $stream = Await ($props.Thumbnail.OpenReadAsync()) ([Windows.Storage.Streams.IRandomAccessStream])
            $size = [int]$stream.Size
            if ($size -gt 0) {
                $dotnetStream = $stream.AsStreamForRead()
                $bytes = New-Object byte[] $size
                $offset = 0
                while ($offset -lt $size) {
                    $read = $dotnetStream.Read($bytes, $offset, $size - $offset)
                    if ($read -le 0) { break }
                    $offset += $read
                }
                [System.IO.File]::WriteAllBytes($ArtOut, $bytes)
                $result.art_saved = (Test-Path $ArtOut)
            }
        } catch {
            $result.art_saved = $false
            $result.art_error = $_.Exception.Message
        }
    }

    if ($appId -like '*Spotify*') { break }
}

$result | ConvertTo-Json -Compress
