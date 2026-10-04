"""Lab-local self-signed TLS certificate. RSA-2048 for handshake compatibility.

Node identity stays Ed25519. TLS here is only the lab link, pinned by SHA-256
of the certificate DER. Ed25519 certificates are not reliable on Android TLS stacks.
"""

from __future__ import annotations

import hashlib
import ipaddress
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


def fingerprint_sha256(cert_pem: bytes) -> str:
    cert = x509.load_pem_x509_certificate(cert_pem)
    return hashlib.sha256(cert.public_bytes(serialization.Encoding.DER)).hexdigest()


def load_or_create_lab_cert(directory: Path, *, host: str) -> tuple[Path, Path, str]:
    directory.mkdir(parents=True, exist_ok=True)
    cert_path = directory / "lab_cert.pem"
    key_path = directory / "lab_key.pem"
    if cert_path.is_file() and key_path.is_file():
        return cert_path, key_path, fingerprint_sha256(cert_path.read_bytes())

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, f"nexo-lab-{host}")])
    now = datetime.now(timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(days=7))
        .add_extension(
            x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address(host))]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )
    key_path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    try:
        key_path.chmod(0o600)
    except OSError:
        pass
    return cert_path, key_path, fingerprint_sha256(cert_path.read_bytes())
