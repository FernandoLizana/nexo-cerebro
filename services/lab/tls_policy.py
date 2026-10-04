"""TLS policy for voluntary multi-device labs (S15).

Configures requirements; does not open a public listener by itself.
"""

from __future__ import annotations

import ssl
from dataclasses import dataclass
from typing import Any


class TlsPolicyError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class TlsLabPolicy:
    """Fail-closed transport policy for node ↔ coordinator links."""

    min_tls_version: str = "TLSv1_2"
    require_certificate_verification: bool = True
    allow_plaintext: bool = False
    allow_federated_learning: bool = False  # S15 forbids FL by default

    def validate(self) -> None:
        if self.allow_plaintext:
            raise TlsPolicyError("plaintext coordinator links are forbidden in S15")
        if not self.require_certificate_verification:
            raise TlsPolicyError("certificate verification is required in S15")
        if self.min_tls_version not in {"TLSv1_2", "TLSv1_3"}:
            raise TlsPolicyError(f"unsupported min TLS version: {self.min_tls_version}")
        if self.allow_federated_learning:
            raise TlsPolicyError("federated learning is out of scope for S15 (see S17)")

    def ssl_context(self) -> ssl.SSLContext:
        self.validate()
        ctx = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
        if self.min_tls_version == "TLSv1_3":
            ctx.minimum_version = ssl.TLSVersion.TLSv1_3
        else:
            ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ctx.check_hostname = True
        ctx.verify_mode = ssl.CERT_REQUIRED
        return ctx

    def to_dict(self) -> dict[str, Any]:
        return {
            "min_tls_version": self.min_tls_version,
            "require_certificate_verification": self.require_certificate_verification,
            "allow_plaintext": self.allow_plaintext,
            "allow_federated_learning": self.allow_federated_learning,
            "networking_note": (
                "Physical multi-device runs must use TLS. "
                "In-process rehearsals do not open internet sockets."
            ),
        }
