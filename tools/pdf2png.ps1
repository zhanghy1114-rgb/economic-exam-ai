param(
    [Parameter(Mandatory=$true)][string]$PdfPath,
    [Parameter(Mandatory=$true)][string]$OutDir,
    [int]$Width = 1500,
    [int]$StartPage = 1,
    [int]$EndPage = 0
)

# Render PDF pages to PNG with Windows.Data.Pdf (WinRT). No Add-Type compilation.
# OutDir receives pgNNN.png (1-based page numbers).

[Windows.Data.Pdf.PdfDocument,Windows.Data.Pdf,ContentType=WindowsRuntime] | Out-Null
[Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime] | Out-Null
[Windows.Storage.StorageFolder,Windows.Storage,ContentType=WindowsRuntime] | Out-Null
[System.Reflection.Assembly]::Load("System.Runtime.WindowsRuntime, Version=4.0.0.0, Culture=neutral, PublicKeyToken=b77a5c561934e089") | Out-Null

$ms = [System.WindowsRuntimeSystemExtensions].GetMethods()
$asTaskOp = ($ms | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
        $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
$asTaskAct = ($ms | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
        $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncAction' })[0]

function Await($WinRtTask, $ResultType) {
    $t = $asTaskOp.MakeGenericMethod($ResultType)
    $task = $t.Invoke($null, @($WinRtTask))
    $task.Wait(-1) | Out-Null
    $task.Result
}

function AwaitAct($WinRtAction) {
    $task = $asTaskAct.Invoke($null, @($WinRtAction))
    $task.Wait(-1) | Out-Null
}

if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir -Force | Out-Null }

$file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($PdfPath)) ([Windows.Storage.StorageFile])
$doc  = Await ([Windows.Data.Pdf.PdfDocument]::LoadFromFileAsync($file)) ([Windows.Data.Pdf.PdfDocument])
$folder = Await ([Windows.Storage.StorageFolder]::GetFolderFromPathAsync($OutDir)) ([Windows.Storage.StorageFolder])
$n = $doc.PageCount
Write-Output ("pages: " + $n)

$last = $EndPage
if ($last -le 0 -or $last -gt $n) { $last = $n }
$sw = [System.Diagnostics.Stopwatch]::StartNew()

for ($i = $StartPage - 1; $i -lt $last; $i++) {
    $name = "pg{0:d3}.png" -f ($i + 1)
    $out = Join-Path $OutDir $name
    if ((Test-Path $out) -and ((Get-Item $out).Length -gt 5000)) {
        Write-Output ("skip " + ($i + 1))
        continue
    }
    $page = $doc.GetPage([uint32]$i)
    $opt = New-Object Windows.Data.Pdf.PdfPageRenderOptions
    $ratio = $Width / $page.Size.Width
    $opt.DestinationWidth = [uint32]$Width
    $opt.DestinationHeight = [uint32]([math]::Round($page.Size.Height * $ratio))
    $sf = Await ($folder.CreateFileAsync($name, [Windows.Storage.CreationCollisionOption]::ReplaceExisting)) ([Windows.Storage.StorageFile])
    $stream = Await ($sf.OpenAsync([Windows.Storage.FileAccessMode]::ReadWrite)) ([Windows.Storage.Streams.IRandomAccessStream])
    AwaitAct ($page.RenderToStreamAsync($stream, $opt))
    $stream.Dispose()
    $page.Dispose()
    Write-Output ("ok {0}/{1} bytes={2} t={3:n1}s" -f ($i + 1), $n, (Get-Item $out).Length, $sw.Elapsed.TotalSeconds)
}
Write-Output "done"
