<# Capture real PowerShell windows showing recorded output. Requires an unlocked desktop. #>
param([switch] $DisplayChild, [string] $Target, [string] $WindowTitle)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms
Add-Type -TypeDefinition @'
using System;
using System.Text;
using System.Runtime.InteropServices;
public static class EvidenceCapture {
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
    [StructLayout(LayoutKind.Sequential)] public struct COORD { public short X, Y; }
    [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)] public struct FONT {
        public uint cbSize, nFont;
        public COORD dwFontSize;
        public int FontFamily, FontWeight;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst=32)] public string FaceName;
    }
    public delegate bool WindowCallback(IntPtr hwnd, IntPtr param);
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
    [DllImport("user32.dll")] public static extern bool EnumWindows(WindowCallback callback, IntPtr param);
    [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr hwnd, StringBuilder text, int max);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hwnd);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hwnd, out RECT rect);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hwnd, int command);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hwnd);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr hwnd, IntPtr after, int x, int y, int w, int h, uint flags);
    [DllImport("kernel32.dll")] public static extern IntPtr GetStdHandle(int handle);
    [DllImport("kernel32.dll")] public static extern bool SetCurrentConsoleFontEx(IntPtr console, bool maximum, ref FONT font);
    public static void FontSize(short height) {
        FONT font = new FONT();
        font.cbSize = (uint)Marshal.SizeOf(typeof(FONT));
        font.dwFontSize.Y = height; font.FontWeight = 400; font.FontFamily = 54; font.FaceName = "Consolas";
        SetCurrentConsoleFontEx(GetStdHandle(-11), false, ref font);
    }
    public static IntPtr Find(string title) {
        IntPtr result = IntPtr.Zero;
        EnumWindows((hwnd, param) => {
            StringBuilder text = new StringBuilder(512);
            GetWindowText(hwnd, text, text.Capacity);
            if (IsWindowVisible(hwnd) && text.ToString().Contains(title)) { result=hwnd; return false; }
            return true;
        }, IntPtr.Zero);
        return result;
    }
}
'@
[EvidenceCapture]::SetProcessDPIAware() | Out-Null

if ($DisplayChild) {
    $Host.UI.RawUI.WindowTitle = $WindowTitle
    [EvidenceCapture]::FontSize(14)
    if ($Host.UI.RawUI.MaxPhysicalWindowSize.Width -lt 205) { [EvidenceCapture]::FontSize(12) }
    $size = $Host.UI.RawUI.WindowSize
    $size.Width = [Math]::Min(210, $Host.UI.RawUI.MaxPhysicalWindowSize.Width - 3)
    $size.Height = [Math]::Min(65, $Host.UI.RawUI.MaxPhysicalWindowSize.Height - 3)
    $buffer = $Host.UI.RawUI.BufferSize
    $buffer.Width = [Math]::Max($size.Width, 210)
    $buffer.Height = [Math]::Max($size.Height, 500)
    $Host.UI.RawUI.BufferSize = $buffer
    $Host.UI.RawUI.WindowSize = $size
    Set-Location (Split-Path $PSScriptRoot -Parent)
    $readyFile = Join-Path (Get-Location) ".local-logs/$WindowTitle.ready"
    $readyDeadline = [DateTime]::UtcNow.AddSeconds(30)
    while (-not (Test-Path -LiteralPath $readyFile)) {
        if ([DateTime]::UtcNow -gt $readyDeadline) { throw 'Screenshot controller did not signal readiness' }
        Start-Sleep -Milliseconds 100
    }
    Clear-Host
    Write-Host "PowerShell evidence: $Target" -ForegroundColor Yellow
    & (Join-Path $PSScriptRoot 'show-evidence.ps1') $Target
    # Keep the actual console stable until the controller has taken its screenshot.
    while ($true) { Start-Sleep -Milliseconds 500 }
}

$shots = @(
    @('probe', '01-hardware-probe.png'),
    @('bench', '02-bench.png'),
    @('smoke', '03-serve-and-smoke.png'),
    @('load-10', '04-locust-10.png'),
    @('load-50', '05-locust-50.png')
)
$outputDir = Join-Path (Split-Path $PSScriptRoot -Parent) 'submission/screenshots'
New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
foreach ($shot in $shots) {
    $title = 'Day20-Evidence-' + [Guid]::NewGuid().ToString('N')
    $arguments = '-NoProfile -ExecutionPolicy Bypass -File "' + $PSCommandPath + '" -DisplayChild -Target ' + $shot[0] + ' -WindowTitle ' + $title
    # User explicitly requested visible PowerShell windows for these screenshots.
    $child = Start-Process powershell.exe -ArgumentList $arguments -WindowStyle Normal -PassThru
    try {
        $deadline = [DateTime]::UtcNow.AddSeconds(20)
        $handle = [IntPtr]::Zero
        while ($handle -eq [IntPtr]::Zero -and [DateTime]::UtcNow -lt $deadline) {
            Start-Sleep -Milliseconds 250
            if ($child.HasExited) { throw "PowerShell exited before showing $($shot[0])" }
            $handle = [EvidenceCapture]::Find($title)
        }
        if ($handle -eq [IntPtr]::Zero) { throw 'No visible PowerShell window; check that the Windows desktop is unlocked.' }
        Start-Sleep -Seconds 2
        [EvidenceCapture]::ShowWindow($handle, 9) | Out-Null
        [EvidenceCapture]::SetWindowPos($handle, [IntPtr](-1), 20, 20, 0, 0, 0x0001) | Out-Null
        [EvidenceCapture]::SetForegroundWindow($handle) | Out-Null
        Start-Sleep -Milliseconds 500
        # Windows Terminal owns its font setting; console font APIs alone do not resize it.
        # Send shortcuts only to the uniquely titled window created for this capture.
        if ([EvidenceCapture]::Find($title) -ne $handle) { throw 'Capture window changed' }
        for ($zoom = 0; $zoom -lt 5; $zoom++) {
            if ([EvidenceCapture]::GetForegroundWindow() -ne $handle) { throw 'Capture window lost keyboard focus' }
            [System.Windows.Forms.SendKeys]::SendWait('^-')
            Start-Sleep -Milliseconds 100
        }
        $readyFile = Join-Path (Split-Path $PSScriptRoot -Parent) ".local-logs/$title.ready"
        [System.IO.File]::WriteAllText($readyFile, 'ready')
        Start-Sleep -Seconds 2
        $rect = New-Object EvidenceCapture+RECT
        [EvidenceCapture]::GetWindowRect($handle, [ref] $rect) | Out-Null
        $width = $rect.Right - $rect.Left
        $height = $rect.Bottom - $rect.Top
        if ($width -le 0 -or $height -le 0) { throw 'Invalid visible window bounds' }
        $bitmap = New-Object System.Drawing.Bitmap($width, $height)
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
        try {
            $graphics.CopyFromScreen($rect.Left, $rect.Top, 0, 0, $bitmap.Size)
            $destination = Join-Path $outputDir $shot[1]
            $bitmap.Save($destination, [System.Drawing.Imaging.ImageFormat]::Png)
            Write-Output "Captured $destination ($width x $height)"
        } finally { $graphics.Dispose(); $bitmap.Dispose() }
        [EvidenceCapture]::SetWindowPos($handle, [IntPtr](-2), 0, 0, 0, 0, 0x0003) | Out-Null
    } finally {
        if (-not $child.HasExited) { Stop-Process -Id $child.Id }
        if ($readyFile -and (Test-Path -LiteralPath $readyFile)) { Remove-Item -LiteralPath $readyFile }
    }
}
