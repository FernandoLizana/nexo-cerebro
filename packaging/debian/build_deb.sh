#!/usr/bin/env bash
# Build helper for nexo-node.deb (S14) — run on Debian/Ubuntu.
# Does not enable system services. arm64 can be passed later via ARCH=.

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ARCH="${ARCH:-amd64}"
VERSION="${VERSION:-0.2.0}"
STAGE="${ROOT}/build/debian/nexo-node_${VERSION}_${ARCH}"

echo "S14 policy: user-level default; no forced root persistence"
python3 -m services.packaging.debian.cli check-scripts \
  "${ROOT}/packaging/debian/postinst" \
  "${ROOT}/packaging/debian/prerm" \
  "${ROOT}/packaging/debian/postrm"

rm -rf "${STAGE}"
mkdir -p "${STAGE}/DEBIAN" \
  "${STAGE}/usr/local/share/nexo-node" \
  "${STAGE}/usr/lib/systemd/user"

cp "${ROOT}/packaging/debian/control" "${STAGE}/DEBIAN/control"
cp "${ROOT}/packaging/debian/postinst" "${STAGE}/DEBIAN/postinst"
cp "${ROOT}/packaging/debian/prerm" "${STAGE}/DEBIAN/prerm"
cp "${ROOT}/packaging/debian/postrm" "${STAGE}/DEBIAN/postrm"
chmod 0755 "${STAGE}/DEBIAN/postinst" "${STAGE}/DEBIAN/prerm" "${STAGE}/DEBIAN/postrm"
cp "${ROOT}/packaging/debian/nexo-node.service" "${STAGE}/usr/lib/systemd/user/nexo-node.service"

# Placeholder payload note (real wheel install left to release operator)
cat > "${STAGE}/usr/local/share/nexo-node/README.txt" <<EOF
Install application files via pip/wheel into user or system site-packages.
This package ships policy + optional systemd --user unit (disabled by default).
Kill switch: nexo-node stop
EOF

dpkg-deb --build "${STAGE}" "${ROOT}/dist/nexo-node_${VERSION}_${ARCH}.deb"
echo "Built dist/nexo-node_${VERSION}_${ARCH}.deb"
echo "Remember: do not systemctl enable the system unit (there isn't one)."
