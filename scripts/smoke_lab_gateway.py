#!/usr/bin/env python3
"""Smoke: start lab gateway on loopback briefly, assert cert fingerprint, stop.

Binds 127.0.0.1 only (requires --allow-loopback). Never binds public interfaces.
"""

from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from services.lab_gateway.certs import load_or_create_lab_cert
    from services.lab_gateway.server import start_gateway, stop_gateway
    from services.lab_gateway.store import GatewayStore

    with tempfile.TemporaryDirectory(prefix="nexo-lab-smoke-") as tmp:
        root = Path(tmp)
        host = "127.0.0.1"
        port = 18767
        httpd = start_gateway(
            host=host,
            port=port,
            root=root,
            enable_mobile_lab=True,
            acknowledge_risks=True,
            allow_loopback=True,
            lab_id="smoke-lab",
        )
        try:
            cert_path, _key, fingerprint = load_or_create_lab_cert(root, host=host)
            store = GatewayStore(root)
            fp_store = str(store.state.get("fingerprint") or "")
            if not fingerprint or len(fingerprint) < 32:
                print({"ok": False, "error": "missing cert fingerprint"})
                return 1
            if not cert_path.is_file():
                print({"ok": False, "error": "lab_cert.pem missing"})
                return 1
            if fp_store and fp_store != fingerprint:
                print({"ok": False, "error": "fingerprint mismatch", "cert": fingerprint, "store": fp_store})
                return 1
            time.sleep(0.2)
            print(
                {
                    "ok": True,
                    "host": host,
                    "port": port,
                    "fingerprint_sha256": fingerprint,
                    "cert": str(cert_path.name),
                    "note": "loopback only; stopped after smoke",
                }
            )
            return 0
        finally:
            stop_gateway(root)
            try:
                httpd.server_close()
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
