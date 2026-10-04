# NEXO Debian packaging (S14)

## Policy

- Artifact: `nexo-node.deb` (amd64 now; arm64 later)
- **No forced root persistence**
- Optional `systemd --user` unit — **disabled by default**
- Kill switch: `nexo-node stop`
- Disable: `systemctl --user disable --now nexo-node.service`

## Check maintainer scripts

```bash
python -m services.packaging.debian.cli check-scripts \
  packaging/debian/postinst packaging/debian/prerm packaging/debian/postrm
```

## Build (on Debian/Ubuntu)

```bash
bash packaging/debian/build_deb.sh
```
