# 🐧 Linux Capture Node – Dev Summary

*Last Updated: July 21, 2025*

---

## 🎯 Purpose

This document covers the **MX Linux capture environment** used as a secondary recording interface in the HexForge Content Automation Engine. It allows users to record and log dev sessions on a Linux system while feeding them into the same AI pipeline as the Windows-based HexForgeRunner.

---

## 🖥️ Linux Capture Setup

| Item                | Description                                                     |
| ------------------- | --------------------------------------------------------------- |
| **Distro**          | MX Linux 23.6 (Debian-based)                                    |
| **Hostname**        | `hex-sandbox`                                                   |
| **OBS**             | Installed via Flatpak with devblog profile support              |
| **Logger**          | `hexforge-shell.sh` for CLI logging (manually triggered)        |
| **Transfer Method** | SCP → `/mnt/hdd-storage/hexforge-content-engine/uploads/linux/` |

---

## ⚙️ Installed Tools

* `OBS Studio` (Flatpak)
* `xclip` (for clipboard integration)
* `scrot` (for screenshots, optional)
* `OpenSSH` (for sending via SCP)
* `hexforge-shell.sh` (lightweight logger)

---

## 🗂️ Folder Locations

| Path                 | Purpose            |
| -------------------- | ------------------ |
| `~/Videos/HexForge/` | Session recordings |
| `~/Logs/HexForge/`   | Shell session logs |
| `~/Screenshots/`     | Manual screenshots |

---

## 🔁 Workflow Integration

1. **User starts OBS manually** (or uses saved devblog profile)
2. **Shell session is launched** using `hexforge-shell.sh`
3. **At session end**, files are zipped and uploaded via SCP
4. Remote Proxmox backend unpacks and triggers pipeline

---

## 🔒 Access & Networking

* SCP key is configured for passwordless transfer
* SSH-only access is enabled via firewall rules
* Local dev box can push assets to shared mount or `uploads/linux`

---

Return to [📄 Backend Engine Overview](backend.md#proxmox-backend-engine) or jump to the [📄 Runner Module](runner.md) for Windows-side automation.
