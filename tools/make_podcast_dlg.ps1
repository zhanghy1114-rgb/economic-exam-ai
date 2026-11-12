param(
    [string]$SegJson = "",
    [string]$OutDir = "",
    [int]$RatePct = -8,
    [int]$StartIndex = 0,
    [int]$EndIndex = 9999
)

# WinRT dual-voice synthesizer: Kangkang (male, "K") + Yaoyao (female, "Y").
# ASCII-only on purpose: PS 5.1 misreads UTF-8 .ps1 without BOM.
# Input json: {"segs":[{"s":"K"|"Y","t":"text"}]}
# Output: segNNN.wav per segment (WinRT default: 16kHz 16bit mono wav).

[Windows.Media.SpeechSynthesis.SpeechSynthesizer,Windows.Media.SpeechSynthesis,ContentType=WindowsRuntime] | Out-Null
[System.Reflection.Assembly]::Load("System.Runtime.WindowsRuntime, Version=4.0.0.0, Culture=neutral, PublicKeyToken=b77a5c561934e089") | Out-Null

if (-not $SegJson) { throw "SegJson required" }
if (-not $OutDir)  { throw "OutDir required" }
if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir -Force | Out-Null }

$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() |
    Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
        $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]

function Await($WinRtTask, $ResultType) {
    $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($WinRtTask))
    $netTask.Wait(-1) | Out-Null
    $netTask.Result
}

function Esc($t) {
    $t = [string]$t
    $t = $t.Replace("&", "&amp;").Replace("<", "&lt;").Replace(">", "&gt;")
    return $t
}

$meta = Get-Content -LiteralPath $SegJson -Raw -Encoding UTF8 | ConvertFrom-Json
$json = $meta.segs
$n = $json.Count
Write-Output ("segments: " + $n)

$syn = New-Object Windows.Media.SpeechSynthesis.SpeechSynthesizer
$vk = $null; $vy = $null
foreach ($v in [Windows.Media.SpeechSynthesis.SpeechSynthesizer]::AllVoices) {
    if ($v.DisplayName -eq "Microsoft Kangkang") { $vk = $v }
    if ($v.DisplayName -eq "Microsoft Yaoyao")   { $vy = $v }
}
if (-not $vk) { throw "Microsoft Kangkang not found" }
if (-not $vy) { throw "Microsoft Yaoyao not found" }
Write-Output "voices: Kangkang(K) + Yaoyao(Y)"

$sw = [System.Diagnostics.Stopwatch]::StartNew()
for ($i = 0; $i -lt $n; $i++) {
    if ($i -lt $StartIndex -or $i -gt $EndIndex) { continue }
    $out = Join-Path $OutDir ("seg{0:d3}.wav" -f $i)
    if ((Test-Path $out) -and ((Get-Item $out).Length -gt 2000)) {
        Write-Output ("skip " + $i)
        continue
    }
    $seg = $json[$i]
    $text = [string]$seg.t
    if ($seg.s -eq "Y") { $syn.Voice = $vy } else { $syn.Voice = $vk }

    $stream = $null
    try {
        $ssml = "<speak version='1.0' xml:lang='zh-CN'><prosody rate='" + $RatePct + "%'>" + (Esc $text) + "</prosody></speak>"
        $stream = Await ($syn.SynthesizeSsmlToStreamAsync($ssml)) ([Windows.Media.SpeechSynthesis.SpeechSynthesisStream])
    } catch {
        Write-Output ("  ssml failed on " + $i + ", plain fallback")
        $stream = Await ($syn.SynthesizeTextToStreamAsync($text)) ([Windows.Media.SpeechSynthesis.SpeechSynthesisStream])
    }

    $netStream = [System.IO.WindowsRuntimeStreamExtensions]::AsStreamForRead($stream)
    $ms = New-Object System.IO.MemoryStream
    $netStream.CopyTo($ms)
    [System.IO.File]::WriteAllBytes($out, $ms.ToArray())
    $netStream.Dispose(); $ms.Dispose(); $stream.Dispose()

    $len = (Get-Item $out).Length
    Write-Output ("ok {0}/{1} v={2} chars={3} bytes={4} elapsed={5:n1}s" -f $i, ($n - 1), $seg.s, $text.Length, $len, $sw.Elapsed.TotalSeconds)
}
$syn.Dispose()
Write-Output ("done total=" + [math]::Round($sw.Elapsed.TotalSeconds, 1) + "s")
