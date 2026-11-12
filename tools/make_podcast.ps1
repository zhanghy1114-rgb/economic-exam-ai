param(
    [string]$SegJson = "",
    [string]$OutDir = "",
    [int]$Rate = -2,
    [int]$StartIndex = 0,
    [int]$EndIndex = 9999
)

# SAPI (System.Speech) segment synthesizer for the finance podcast.
# ASCII-only on purpose: PS 5.1 misreads UTF-8 .ps1 without BOM.
# Text comes from segments.json (UTF-8), written by make_podcast.py split.

Add-Type -AssemblyName System.Speech

if (-not $SegJson) { throw "SegJson required" }
if (-not $OutDir)  { throw "OutDir required" }
if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir -Force | Out-Null }

$json = Get-Content -LiteralPath $SegJson -Raw -Encoding UTF8 | ConvertFrom-Json
$n = $json.Count
Write-Output ("segments: " + $n)

$syn = New-Object System.Speech.Synthesis.SpeechSynthesizer
$voice = $syn.GetInstalledVoices() | Where-Object { $_.VoiceInfo.Culture.Name -like "zh-CN*" } | Select-Object -First 1
if ($voice) {
    $syn.SelectVoice($voice.VoiceInfo.Name)
    Write-Output ("voice: " + $voice.VoiceInfo.Name)
} else {
    Write-Output "voice: default (no zh-CN found)"
}
$syn.Rate = $Rate
$syn.Volume = 100

$fmt = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(
    16000,
    [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen,
    [System.Speech.AudioFormat.AudioChannel]::Mono)

$sw = [System.Diagnostics.Stopwatch]::StartNew()
for ($i = 0; $i -lt $n; $i++) {
    if ($i -lt $StartIndex -or $i -gt $EndIndex) { continue }
    $out = Join-Path $OutDir ("seg{0:d3}.wav" -f $i)
    if ((Test-Path $out) -and ((Get-Item $out).Length -gt 2000)) {
        Write-Output ("skip " + $i)
        continue
    }
    $text = [string]$json[$i]
    $syn.SetOutputToWaveFile($out, $fmt)
    $syn.Speak($text)
    $syn.SetOutputToNull()
    $len = (Get-Item $out).Length
    Write-Output ("ok {0}/{1} chars={2} bytes={3} elapsed={4:n1}s" -f $i, ($n - 1), $text.Length, $len, $sw.Elapsed.TotalSeconds)
}
$syn.Dispose()
Write-Output ("done total=" + [math]::Round($sw.Elapsed.TotalSeconds, 1) + "s")
