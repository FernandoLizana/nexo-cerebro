#!/usr/bin/env python3
"""Inject hub URL + presence token into debug Android SharedPreferences via adb.

Usage:
  python scripts/adb_inject_presence_prefs.py [--serial emulator-5554]

Does not print the token. Requires a debuggable install of org.nexo.node.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import xml.sax.saxutils
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = "org.nexo.node"
PREFS = "nexo_presence.xml"


def _adb(serial: str | None, *args: str) -> subprocess.CompletedProcess[str]:
    cmd = ["adb"]
    if serial:
        cmd += ["-s", serial]
    cmd.extend(args)
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def _token() -> str:
    import os

    env = os.environ.get("NEXO_PRESENCE_TOKEN", "").strip()
    if env:
        return env
    path = ROOT / "data" / "presence_hub" / "token.txt"
    if path.is_file():
        return path.read_text(encoding="utf-8").strip()
    raise SystemExit("missing presence token")


def _prefs_xml(hub: str, token: str) -> str:
    hub_e = xml.sax.saxutils.escape(hub)
    tok_e = xml.sax.saxutils.escape(token)
    return (
        "<?xml version='1.0' encoding='utf-8' standalone='yes' ?>\n"
        "<map>\n"
        f'    <string name="hub_base_url">{hub_e}</string>\n'
        f'    <string name="presence_token">{tok_e}</string>\n'
        "</map>\n"
    )


def inject(serial: str | None, hub: str) -> None:
    token = _token()
    xml_body = _prefs_xml(hub, token)
    # Ensure dirs exist and write prefs as the app user.
    script = (
        f"mkdir -p shared_prefs && "
        f"cat > shared_prefs/{PREFS} << 'NEXOEOF'\n"
        f"{xml_body}"
        f"NEXOEOF\n"
        f"chmod 660 shared_prefs/{PREFS}\n"
    )
    # Pipe script to run-as sh
    proc = _adb(serial, "shell", f"run-as {PKG} sh -c {repr(script)}")
    if proc.returncode != 0:
        # Fallback: push via temporary file in /data/local/tmp then copy with run-as
        tmp = ROOT / "dist" / f"_nexo_prefs_{serial or 'default'}.xml"
        tmp.parent.mkdir(exist_ok=True)
        tmp.write_text(xml_body, encoding="utf-8")
        remote = f"/data/local/tmp/{PREFS}"
        push = _adb(serial, "push", str(tmp), remote)
        if push.returncode != 0:
            raise SystemExit(f"adb push failed: {push.stderr}")
        copy = _adb(
            serial,
            "shell",
            f"run-as {PKG} sh -c 'mkdir -p shared_prefs && cp {remote} shared_prefs/{PREFS}'",
        )
        tmp.unlink(missing_ok=True)
        if copy.returncode != 0:
            raise SystemExit(
                f"run-as inject failed (is the APK debuggable?): {copy.stderr or proc.stderr}"
            )
    # Force-stop so next launch reloads prefs
    _adb(serial, "shell", "am", "force-stop", PKG)
    print(f"ok serial={serial or 'default'} hub={hub} prefs_written=true")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--serial", default=None)
    parser.add_argument("--hub", default="http://127.0.0.1:8770")
    parser.add_argument("--all-emulators", action="store_true")
    args = parser.parse_args()
    if args.all_emulators:
        listed = _adb(None, "devices")
        serials = [
            line.split()[0]
            for line in listed.stdout.splitlines()
            if line.startswith("emulator-") and "\tdevice" in line
        ]
        if not serials:
            print("no emulators in device state", file=sys.stderr)
            return 1
        for s in serials:
            inject(s, args.hub)
        return 0
    inject(args.serial, args.hub)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
