<#
.SYNOPSIS
  Sign Solitaire+ release files with the project's code-signing certificate.

.DESCRIPTION
  Used by the GitHub workflow on release builds (and by Inno Setup to sign the
  installer and uninstaller). Maintainers normally never run it by hand; see
  docs/CODE_SIGNING.md.

  The certificate comes from a .pfx file. Its path and password are read from
  -PfxPath/-Password, or from the environment variables SIGNING_PFX_PATH and
  SIGNING_CERT_PASSWORD (so they never appear on a command line or in logs).

  What it can do, in one call or several:
    -Files a.exe,b.exe     Authenticode-sign programs (what Windows shows as "Verified publisher")
    -Manifest manifest.json  write manifest.json.p7s, the detached signature the updater checks
    -ExportCer x.cer       write the public certificate players import (never the private key)
    -CheckTrusted          stop unless this certificate's thumbprint is listed in
                           updater/trusted_publishers.py (otherwise every player would see
                           the "could not be verified" warnings)

  Uses Microsoft's signtool.exe when installed (always true on GitHub's Windows
  machines), otherwise PowerShell's Set-AuthenticodeSignature.

.EXAMPLE
  $env:SIGNING_PFX_PATH = "C:\keys\solitaireplus.pfx"; $env:SIGNING_CERT_PASSWORD = "..."
  .\tools\sign_release.ps1 -Files dist\SolitairePlus\SolitairePlus.exe -CheckTrusted
#>
param(
    [string]$PfxPath = $env:SIGNING_PFX_PATH,
    [string]$Password = $env:SIGNING_CERT_PASSWORD,
    [string[]]$Files = @(),
    [string]$Manifest,
    [string]$ExportCer,
    [switch]$CheckTrusted,
    [string]$TimestampUrl = "http://timestamp.digicert.com",
    [switch]$NoTimestamp
)

$ErrorActionPreference = "Stop"
$repo = Split-Path $PSScriptRoot -Parent

if (-not $PfxPath -or -not (Test-Path -LiteralPath $PfxPath)) {
    throw "No signing certificate: set SIGNING_PFX_PATH (or -PfxPath) to the .pfx file. See docs/CODE_SIGNING.md."
}
$flags = [System.Security.Cryptography.X509Certificates.X509KeyStorageFlags]::EphemeralKeySet
$cert = [System.Security.Cryptography.X509Certificates.X509Certificate2]::new((Resolve-Path -LiteralPath $PfxPath).Path, $Password, $flags)
if (-not $cert.HasPrivateKey) { throw "The .pfx file does not contain the private key." }
Write-Host "Signing certificate: $($cert.Subject)  thumbprint $($cert.Thumbprint)  valid until $($cert.NotAfter.ToString('yyyy-MM-dd'))"
if ($cert.NotAfter -lt (Get-Date).AddDays(30)) {
    Write-Warning "The signing certificate expires on $($cert.NotAfter.ToString('yyyy-MM-dd')). Plan a replacement (docs/CODE_SIGNING.md)."
}

if ($CheckTrusted) {
    $listed = Select-String -Path (Join-Path $repo "updater\trusted_publishers.py") -Pattern '^\s*\{.*"thumbprint"\s*:\s*"([0-9A-Fa-f]{40})"' -AllMatches |
        ForEach-Object { $_.Matches } | ForEach-Object { $_.Groups[1].Value.ToUpperInvariant() }
    if ($listed -notcontains $cert.Thumbprint.ToUpperInvariant()) {
        throw ("This certificate (thumbprint $($cert.Thumbprint)) is not listed in updater/trusted_publishers.py. " +
               "Add it there first (docs/CODE_SIGNING.md), or every player would see the 'could not be verified' warnings.")
    }
    Write-Host "Certificate is listed in updater/trusted_publishers.py."
}

if ($Files.Count -gt 0) {
    $signtool = Get-ChildItem "${env:ProgramFiles(x86)}\Windows Kits\10\bin\*\x64\signtool.exe" -ErrorAction SilentlyContinue |
        Sort-Object FullName -Descending | Select-Object -First 1
    foreach ($file in $Files) {
        $path = (Resolve-Path -LiteralPath $file).Path
        if ($signtool) {
            $arguments = @("sign", "/fd", "SHA256", "/f", (Resolve-Path -LiteralPath $PfxPath).Path, "/p", $Password)
            if (-not $NoTimestamp) { $arguments += @("/tr", $TimestampUrl, "/td", "SHA256") }
            & $signtool.FullName @arguments $path | Out-Host
            if ($LASTEXITCODE -ne 0) { throw "signtool failed for $path" }
        } else {
            $options = @{ FilePath = $path; Certificate = $cert; HashAlgorithm = "SHA256" }
            if (-not $NoTimestamp) { $options.TimestampServer = $TimestampUrl }
            $result = Set-AuthenticodeSignature @options
            if ($result.Status -notin @("Valid", "UnknownError")) { throw "Signing failed for ${path}: $($result.StatusMessage)" }
        }
        $check = Get-AuthenticodeSignature -LiteralPath $path
        if (-not $check.SignerCertificate -or $check.SignerCertificate.Thumbprint -ne $cert.Thumbprint) {
            throw "Signature check after signing failed for $path"
        }
        Write-Host "Signed $path"
    }
}

if ($Manifest) {
    $content = [IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $Manifest).Path)
    $cms = [System.Security.Cryptography.Pkcs.SignedCms]::new([System.Security.Cryptography.Pkcs.ContentInfo]::new($content), $true)
    $signer = [System.Security.Cryptography.Pkcs.CmsSigner]::new($cert)
    $signer.IncludeOption = [System.Security.Cryptography.X509Certificates.X509IncludeOption]::EndCertOnly
    [void]$signer.SignedAttributes.Add([System.Security.Cryptography.Pkcs.Pkcs9SigningTime]::new())
    $cms.ComputeSignature($signer)
    $out = "$((Resolve-Path -LiteralPath $Manifest).Path).p7s"
    [IO.File]::WriteAllBytes($out, $cms.Encode())
    Write-Host "Wrote $out"
}

if ($ExportCer) {
    [IO.File]::WriteAllBytes($ExportCer, $cert.Export([System.Security.Cryptography.X509Certificates.X509ContentType]::Cert))
    Write-Host "Wrote public certificate $ExportCer (thumbprint $($cert.Thumbprint))"
}
