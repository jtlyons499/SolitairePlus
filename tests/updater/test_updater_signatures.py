"""The updater's REAL signature check (Windows PowerShell + .NET), end to end.

The test makes a throwaway code-signing certificate in memory (never added to
any Windows certificate store), signs a manifest and an exe with it, and
checks that the updater accepts them, and rejects tampered or foreign ones.
Skipped automatically on PCs without PowerShell (e.g. Linux).
"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from updater import signing

MAKE_TEST_SIGNATURES = r"""
param([string]$Dir)
$ErrorActionPreference = 'Stop'
$rsa = [System.Security.Cryptography.RSA]::Create(2048)
$req = [System.Security.Cryptography.X509Certificates.CertificateRequest]::new('CN="Solitaire+ Test Signing"', $rsa,
  [System.Security.Cryptography.HashAlgorithmName]::SHA256, [System.Security.Cryptography.RSASignaturePadding]::Pkcs1)
$eku = [System.Security.Cryptography.OidCollection]::new(); [void]$eku.Add([System.Security.Cryptography.Oid]::new('1.3.6.1.5.5.7.3.3'))
$req.CertificateExtensions.Add([System.Security.Cryptography.X509Certificates.X509EnhancedKeyUsageExtension]::new($eku, $true))
$cert = $req.CreateSelfSigned([DateTimeOffset]::Now.AddDays(-1), [DateTimeOffset]::Now.AddDays(30))
$cms = [System.Security.Cryptography.Pkcs.SignedCms]::new([System.Security.Cryptography.Pkcs.ContentInfo]::new([IO.File]::ReadAllBytes("$Dir\manifest.json")), $true)
$cms.ComputeSignature([System.Security.Cryptography.Pkcs.CmsSigner]::new($cert))
[IO.File]::WriteAllBytes("$Dir\manifest.json.p7s", $cms.Encode())
$null = Set-AuthenticodeSignature -FilePath "$Dir\Signed.exe" -Certificate $cert -HashAlgorithm SHA256
$cert.Thumbprint
"""


@unittest.skipUnless(sys.platform == "win32" and shutil.which("powershell.exe"), "needs Windows PowerShell")
class RealSignatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.tmp.name)
        (cls.dir / "manifest.json").write_text('{"schema": 1}\n')
        shutil.copy2(sys.executable, cls.dir / "Signed.exe")
        shutil.copy2(sys.executable, cls.dir / "Unsigned.exe")
        script = cls.dir / "make.ps1"
        script.write_text(MAKE_TEST_SIGNATURES, encoding="utf-8")
        shell = shutil.which("pwsh") or "powershell.exe"
        done = subprocess.run([shell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), "-Dir", str(cls.dir)],
                              capture_output=True, text=True, timeout=120)
        lines = done.stdout.strip().splitlines()
        if done.returncode != 0 or not lines:
            raise unittest.SkipTest("could not create a test certificate here: " + done.stderr[-300:])
        cls.thumbprint = lines[-1].strip()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def verify(self, manifest="manifest.json", exe="Signed.exe", trusted=None):
        publishers = [{"name": "Test", "thumbprint": trusted or self.thumbprint}]
        with mock.patch.object(signing.config, "trusted_publishers", return_value=publishers):
            return signing.verify(self.dir / manifest, self.dir / "manifest.json.p7s", [self.dir / exe])

    def test_genuine_signatures_are_verified(self):
        result = self.verify()
        self.assertTrue(result.verified, result.details())

    def test_a_changed_file_list_is_rejected(self):
        (self.dir / "edited.json").write_text('{"schema": 1, "extra": true}\n')
        self.assertFalse(self.verify(manifest="edited.json").verified)

    def test_a_changed_exe_is_rejected(self):
        data = bytearray((self.dir / "Signed.exe").read_bytes())
        data[600] ^= 0xFF
        (self.dir / "Changed.exe").write_bytes(bytes(data))
        self.assertFalse(self.verify(exe="Changed.exe").verified)

    def test_an_unsigned_exe_is_rejected(self):
        # The venv's python.exe may carry the Python Software Foundation's signature;
        # either way it is not signed by our certificate.
        self.assertFalse(self.verify(exe="Unsigned.exe").verified)

    def test_someone_elses_certificate_is_rejected(self):
        self.assertFalse(self.verify(trusted="C" * 40).verified)


if __name__ == "__main__":
    unittest.main()
