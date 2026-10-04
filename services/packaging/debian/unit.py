"""Optional systemd --user unit (disabled by default)."""

from __future__ import annotations


UNIT_NAME = "nexo-node.service"


def user_unit_text(*, description: str = "NEXO Node (voluntary scientific lab)") -> str:
    """Generate a user-level unit that does NOT install as a system service."""
    return f"""[Unit]
Description={description}
Documentation=https://github.com/
# Optional user unit — not enabled by package postinst.
# Start manually: systemctl --user start nexo-node.service
# Stop / kill switch: nexo-node stop   OR   systemctl --user stop nexo-node.service

[Service]
Type=simple
ExecStart=%h/.local/bin/nexo-node start --data-dir %h/.local/share/nexo/node
ExecStop=%h/.local/bin/nexo-node stop
Restart=no
# Do not linger; do not survive logout unless the owner opts in manually.

[Install]
WantedBy=default.target
"""


def unit_is_enabled_by_default() -> bool:
    return False
