<#
.SYNOPSIS
  Create the Solitaire+ code-signing certificate (once, by the person who holds the GitHub secrets).

.DESCRIPTION
  Makes a self-signed certificate that can only sign programs (not websites, not other
  certificates) and writes three files into -OutDir:

    solitaireplus-signing.pfx      THE SECRET: certificate + private key, protected by your password
    solitaireplus-signing.pfx.txt  the same .pfx as Base64 text, to paste into the GitHub secret
    SolitairePlus-Publisher.cer    the PUBLIC certificate (safe to share; the installer ships it)

  It prints the thumbprint, which goes into updater/trusted_publishers.py and README.md.

  Nothing is added to any Windows certificate store, and nothing is uploaded anywhere.
  -OutDir must be outside the repository so the private key can never be committed.
  Step-by-step instructions: docs/CODE_SIGNING.md.

.PARAMETER OutDir
  An empty folder outside the repository, for example a USB stick or C:\SolitairePlusKeys.

.PARAMETER Years
  How long the certificate is valid (default 5).

.EXAMPLE
  .\tools\new_signing_cert.ps1 -OutDir C:\SolitairePlusKeys
#>
param(
    [Parameter(Mandatory = $true)][string]$OutDir,
    [string]$Subject = 'CN="Solitaire+ Developers"',    # quoted: "+" is special in certificate names
    [ValidateRange(1, 10)][int]$Years = 5
)

$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Split-Path $PSScriptRoot -Parent)).Path.TrimEnd("\")
$out = [IO.Path]::GetFullPath($OutDir).TrimEnd("\")
if ($out -eq $repo -or $out.StartsWith($repo + "\", [StringComparison]::OrdinalIgnoreCase)) {
    throw "-OutDir is inside the repository ($repo). Pick a folder outside it, so the private key can never be committed."
}
New-Item -ItemType Directory -Force -Path $out | Out-Null
$pfxPath = Join-Path $out "solitaireplus-signing.pfx"
$base64Path = "$pfxPath.txt"
$cerPath = Join-Path $out "SolitairePlus-Publisher.cer"
foreach ($path in $pfxPath, $base64Path, $cerPath) {
    if (Test-Path -LiteralPath $path) { throw "$path already exists. Never overwrite a signing key; use a new folder." }
}

# The password protects the .pfx file. It becomes the SIGNING_CERT_PASSWORD GitHub secret.
if ($env:SIGNING_CERT_PASSWORD) {
    $password = $env:SIGNING_CERT_PASSWORD
} else {
    $first = Read-Host "Choose a password for the .pfx file (at least 12 characters)" -AsSecureString
    $second = Read-Host "Type it again" -AsSecureString
    $password = [Net.NetworkCredential]::new("", $first).Password
    if ($password -ne [Net.NetworkCredential]::new("", $second).Password) { throw "The two passwords differ." }
}
if ($password.Length -lt 12) { throw "Use a password of at least 12 characters." }

$X509 = "System.Security.Cryptography.X509Certificates"
$rsa = [System.Security.Cryptography.RSA]::Create(3072)
$request = New-Object "$X509.CertificateRequest" $Subject, $rsa,
    ([System.Security.Cryptography.HashAlgorithmName]::SHA256), ([System.Security.Cryptography.RSASignaturePadding]::Pkcs1)
# Not a certificate authority: it cannot be used to vouch for other certificates (or websites).
$request.CertificateExtensions.Add((New-Object "$X509.X509BasicConstraintsExtension" $false, $false, 0, $true))
$request.CertificateExtensions.Add((New-Object "$X509.X509KeyUsageExtension" ([System.Security.Cryptography.X509Certificates.X509KeyUsageFlags]::DigitalSignature), $true))
# Code signing only (1.3.6.1.5.5.7.3.3).
$usages = New-Object System.Security.Cryptography.OidCollection
[void]$usages.Add((New-Object System.Security.Cryptography.Oid "1.3.6.1.5.5.7.3.3"))
$request.CertificateExtensions.Add((New-Object "$X509.X509EnhancedKeyUsageExtension" $usages, $true))
$request.CertificateExtensions.Add((New-Object "$X509.X509SubjectKeyIdentifierExtension" $request.PublicKey, $false))

$cert = $request.CreateSelfSigned([DateTimeOffset]::Now.AddDays(-1), [DateTimeOffset]::Now.AddYears($Years))
$pfx = $cert.Export([System.Security.Cryptography.X509Certificates.X509ContentType]::Pfx, $password)
[IO.File]::WriteAllBytes($pfxPath, $pfx)
[IO.File]::WriteAllText($base64Path, [Convert]::ToBase64String($pfx))
[IO.File]::WriteAllBytes($cerPath, $cert.Export([System.Security.Cryptography.X509Certificates.X509ContentType]::Cert))

Write-Host ""
Write-Host "Created the Solitaire+ signing certificate" -ForegroundColor Green
Write-Host "  Subject:     $($cert.Subject)"
Write-Host "  Valid until: $($cert.NotAfter.ToString('yyyy-MM-dd'))"
Write-Host "  Thumbprint:  $($cert.Thumbprint)" -ForegroundColor Yellow
Write-Host ""
Write-Host "  SECRET  $pfxPath"
Write-Host "  SECRET  $base64Path   (paste into GitHub secret SIGNING_CERT_PFX_BASE64, then delete this .txt)"
Write-Host "  public  $cerPath"
Write-Host ""
Write-Host "Next: docs/CODE_SIGNING.md, part 1 step 3 (GitHub secrets and the thumbprint)."
