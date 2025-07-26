# 🧠 HexForgeRunner – Windows Capture Toolkit

**HexForgeRunner** is a modular PowerShell-based interface that captures your dev sessions in real time. It supports screen recordings, terminal logs, screenshots, and clipboard exports, routing them into the full HexForge Content Automation Engine pipeline.

---

## 📁 Directory Structure

```
windows/HexForgeRunner/
├── assets/               # OBS profiles, screenshots, video, clipboard dumps
├── projects/             # Session folders organized by project/part
├── Logs/                 # Global logs not tied to a project
├── HexForgeRunner.psm1   # Main menu interface and dispatcher
├── hexforge-shell.ps1    # Starts labeled shell + logs
├── pack-and-send.ps1     # Zips + SCP uploads the latest session
├── stop-hexforge-session.ps1  # Final transcript, screenshots, blog.json
├── launch-obs.ps1        # Opens OBS in configured mode
├── watch-for-obs.ps1     # Waits until OBS closes, used in automation
├── configure-obs.ps1     # Sets up profiles and output dir in OBS
├── set-project.ps1       # Handles naming + folder creation for project/part
```

---

## 🧭 Workflow Overview

1. User launches `Show-HexForgeMenu` (from profile or manually)
2. Menu options control:

   * `[1]` Start shell logger
   * `[5]` Launch OBS
   * `[6]` Full capture (OBS + logger + upload)
3. Upon session end, user selects `[0]` Exit which triggers:

   * OBS stop and video move
   * Screenshot capture from `Pictures/Screenshots`
   * Prompt for ChatGPT transcript
   * Blog metadata JSON build
   * Auto-ZIP and SCP upload

---

## 📦 Project Folder Output

Each session is organized under:

```
windows/HexForgeRunner/projects/<project>/<part>/
├── Logs/
├── Screenshots/
├── Videos/
├── chatgpt-transcript.txt
├── blog.json
├── HexForge_Pack_<timestamp>.zip
```

These folders are automatically created by `set-project.ps1` and reused or incremented when `[6]` is used.

---

## ✨ Features

* Automatic part incrementation if reuse is declined
* Screenshot auto-move based on timestamp
* Clipboard capture support for ChatGPT transcript
* SCP upload with fallback handling
* Blog metadata generation (`blog.json`) includes:

  * Project name, part, timestamps
  * Log file name, video file, screenshot count
  * Optional transcript or notes block

---

## 🧠 Dev Notes

* All paths are local to user profile or relative to `HexForgeRunner`
* Timestamps follow `yyyy-MM-dd_HH-mm-ss`
* OBS profile setup assumes `assets/OBS-Profiles/*` exists
* `.gitignore` should exclude full `projects/`, `assets/Latest`, and `Logs`

---

## ✅ Status (July 2025)

| Feature                      | Status |
| ---------------------------- | ------ |
| PowerShell menu runner       | ✅      |
| Shell session logging        | ✅      |
| OBS launcher + watcher       | ✅      |
| Screenshot folder capture    | ✅      |
| Clipboard to transcript      | ✅      |
| JSON metadata + packager     | ✅      |
| SCP upload to content engine | ✅      |
| Reuse project/part logic     | ✅      |

---

Next: [View backend pipeline and Proxmox setup →](backend.md)
