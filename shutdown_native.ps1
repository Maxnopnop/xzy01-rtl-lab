# Default is a capability check. -Execute requires a completed-task receipt.
param(
    [switch]$Execute,
    [string]$CompletionFile,
    [string]$StatusFile,
    [ValidateRange(30,600)][int]$DelaySeconds = 120
)
$ErrorActionPreference = 'Stop'
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class EceShutdownNative {
    [StructLayout(LayoutKind.Sequential)] struct Luid { public uint Low; public int High; }
    [StructLayout(LayoutKind.Sequential)] struct Privilege { public uint Count; public Luid Id; public uint Attributes; }
    [DllImport("kernel32.dll")] static extern IntPtr GetCurrentProcess();
    [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
    [DllImport("advapi32.dll", SetLastError=true)] static extern bool OpenProcessToken(IntPtr p, uint access, out IntPtr token);
    [DllImport("advapi32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern bool LookupPrivilegeValue(string system, string name, out Luid id);
    [DllImport("advapi32.dll", SetLastError=true)] static extern bool AdjustTokenPrivileges(IntPtr token, bool disableAll, ref Privilege state, uint length, IntPtr previous, IntPtr returned);
    [DllImport("user32.dll", SetLastError=true)] static extern bool ExitWindowsEx(uint flags, uint reason);
    public static int EnablePrivilege() {
        IntPtr token;
        if (!OpenProcessToken(GetCurrentProcess(), 0x28, out token)) return Marshal.GetLastWin32Error();
        try {
            Luid id;
            if (!LookupPrivilegeValue(null, "SeShutdownPrivilege", out id)) return Marshal.GetLastWin32Error();
            Privilege state = new Privilege { Count=1, Id=id, Attributes=2 };
            if (!AdjustTokenPrivileges(token, false, ref state, 0, IntPtr.Zero, IntPtr.Zero)) return Marshal.GetLastWin32Error();
            return Marshal.GetLastWin32Error();
        } finally { CloseHandle(token); }
    }
    public static int Shutdown() {
        // EWX_POWEROFF. No EWX_FORCE or EWX_FORCEIFHUNG: unsaved apps may veto.
        return ExitWindowsEx(0x8, 0x80040000) ? 0 : Marshal.GetLastWin32Error();
    }
}
'@
function Save-Status($state, $errorCode) {
    $record = @{status=$state;win32_error=$errorCode;force=$false;native_api='ExitWindowsEx';time=(Get-Date).ToString('o')}
    if ($StatusFile) { $record | ConvertTo-Json | Set-Content -LiteralPath $StatusFile -Encoding utf8 }
    else { $record | ConvertTo-Json }
}
if (!$Execute) {
    $nativeError = [EceShutdownNative]::EnablePrivilege()
    Save-Status 'CAPABILITY_CHECK_ONLY' $nativeError
    exit $nativeError
}
if (!$CompletionFile -or !(Test-Path -LiteralPath $CompletionFile)) { throw 'Missing completion receipt; shutdown not requested.' }
$receiptHash = (Get-FileHash -LiteralPath $CompletionFile -Algorithm SHA256).Hash
$receipt = Get-Content -LiteralPath $CompletionFile -Raw | ConvertFrom-Json
if ($receipt.status -ne 'COMPLETE' -or !$receipt.tests_passed -or !$receipt.github_synced -or !$receipt.archives_saved) {
    throw 'Completion gates not satisfied; shutdown not requested.'
}
Save-Status 'WAITING_AFTER_VERIFIED_COMPLETION' 0
Start-Sleep -Seconds $DelaySeconds
if ((Get-FileHash -LiteralPath $CompletionFile -Algorithm SHA256).Hash -ne $receiptHash) {
    throw 'Completion receipt changed; shutdown cancelled.'
}
$nativeError = [EceShutdownNative]::EnablePrivilege()
if ($nativeError) { Save-Status 'PRIVILEGE_FAILED' $nativeError; exit $nativeError }
Save-Status 'REQUESTING_NORMAL_NATIVE_SHUTDOWN' 0
$nativeError = [EceShutdownNative]::Shutdown()
if ($nativeError) { Save-Status 'NATIVE_SHUTDOWN_FAILED' $nativeError; exit $nativeError }
Save-Status 'NORMAL_NATIVE_SHUTDOWN_REQUESTED' 0
