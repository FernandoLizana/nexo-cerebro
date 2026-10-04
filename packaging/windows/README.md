# NEXO Windows packaging (S13)

## Goals

- Produce `NEXO-Node.exe` for Win10/11 x64 (PyInstaller).
- **Explicit consent** before first run / install recording.
- **No silent install** (`/S`, `/quiet`, … rejected).
- **No Windows Service** registration.
- **Manual** update channel (no forced auto-update).
- **Kill switch:** `NEXO-Node.exe stop` (same as `nexo-node stop`).

## Commands

```powershell
# Record consent into a user install root
python -m services.packaging.windows.cli accept-consent --i-accept-all --install-root "$env:LOCALAPPDATA\NEXO\Node"

# Build (optional; needs pyinstaller)
powershell -File packaging\windows\build_exe.ps1

# Uninstall dry-run / execute
powershell -File packaging\windows\uninstall.ps1 -InstallRoot "$env:LOCALAPPDATA\NEXO\Node"
powershell -File packaging\windows\uninstall.ps1 -InstallRoot "$env:LOCALAPPDATA\NEXO\Node" -Execute
```

## Signing

Release builds should be signed with `signtool`. Certificates are **not** stored in this repository.
