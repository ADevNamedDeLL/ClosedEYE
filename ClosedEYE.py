"""
ClosedEYE
---------
Menu:
  1. Close Eyes       - create a backup, then harden inbound firewall exposure
  2. Revert Changes   - restore a ClosedEYE backup
  3. Test Vulnerabilities - audit listening services and firewall state
  4. Exit

Run as Administrator on Windows or with sudo on Linux for firewall changes.
ClosedEYE does NOT exploit vulnerabilities or attack external systems.
"""

from __future__ import annotations

import ctypes
import datetime as dt
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
from pathlib import Path


APP_NAME = "ClosedEYE"
VERSION = "0.1.0"

IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"

if IS_WINDOWS:
    DATA_DIR = Path(os.environ.get("PROGRAMDATA", ".")) / "ClosedEYE"
else:
    DATA_DIR = Path.home() / ".closedeeye"

BACKUP_DIR = DATA_DIR / "backups"


def run(cmd: list[str], check: bool = False) -> subprocess.CompletedProcess:
    """Run a command and return its result."""
    return subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        check=check,
        encoding="utf-8",
        errors="replace",
    )


def is_admin() -> bool:
    if IS_WINDOWS:
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False
    return os.geteuid() == 0 if hasattr(os, "geteuid") else False


def pause() -> None:
    input("\nPress Enter to continue...")


def clear() -> None:
    os.system("cls" if IS_WINDOWS else "clear")


def timestamp() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def print_header() -> None:
    print(r"""
╔══════════════════════════════════════════════╗
║                  ClosedEYE                   ║
║        Network Exposure Protection           ║
╠══════════════════════════════════════════════╣
║  1. Close Eyes                               ║
║  2. Revert Changes                           ║
║  3. Test Vulnerabilities                     ║
║  4. Exit                                     ║
╚══════════════════════════════════════════════╝
""")


def backup_windows(backup: Path) -> dict:
    firewall_file = backup / "firewall.wfw"
    result = run(["netsh", "advfirewall", "export", str(firewall_file)])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "netsh firewall export failed")

    return {
        "platform": "Windows",
        "type": "netsh_advfirewall",
        "file": str(firewall_file),
    }


def backup_linux(backup: Path) -> dict:
    """
    Back up UFW's complete configuration when UFW is installed.
    We deliberately refuse to alter Linux firewall state if UFW isn't
    available, because silently replacing nftables/iptables rules would
    be unsafe.
    """
    ufw = shutil.which("ufw")
    if not ufw:
        raise RuntimeError(
            "UFW is not installed. ClosedEYE currently refuses to modify "
            "unknown nftables/iptables configurations."
        )

    archive = backup / "ufw-backup.tar"
    result = run(
        [
            "tar",
            "-cf",
            str(archive),
            "/etc/ufw",
        ]
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Could not back up /etc/ufw")

    status = run([ufw, "status", "verbose"])
    (backup / "ufw-status.txt").write_text(
        status.stdout + status.stderr,
        encoding="utf-8",
    )

    return {
        "platform": "Linux",
        "type": "ufw",
        "file": str(archive),
    }


def create_backup() -> Path | None:
    ensure_dirs()
    backup = BACKUP_DIR / timestamp()
    backup.mkdir(parents=True, exist_ok=True)

    try:
        if IS_WINDOWS:
            details = backup_windows(backup)
        elif IS_LINUX:
            details = backup_linux(backup)
        else:
            raise RuntimeError(
                f"Unsupported operating system: {platform.system()}"
            )

        metadata = {
            "created": dt.datetime.now().isoformat(),
            "version": VERSION,
            **details,
        }
        (backup / "metadata.json").write_text(
            json.dumps(metadata, indent=2),
            encoding="utf-8",
        )

        print(f"[✓] Backup created: {backup}")
        return backup

    except Exception as exc:
        shutil.rmtree(backup, ignore_errors=True)
        print(f"[!] Backup failed: {exc}")
        return None


def close_eyes_windows() -> bool:
    print("[*] Enabling Windows Firewall...")
    result = run(["netsh", "advfirewall", "set", "allprofiles", "state", "on"])
    if result.returncode != 0:
        print("[!] Could not enable Windows Firewall.")
        print(result.stderr.strip())
        return False

    print("[*] Blocking unsolicited inbound connections...")
    result = run(
        [
            "netsh",
            "advfirewall",
            "set",
            "allprofiles",
            "firewallpolicy",
            "blockinbound,allowoutbound",
        ]
    )
    if result.returncode != 0:
        print("[!] Could not change the inbound firewall policy.")
        print(result.stderr.strip())
        return False

    return True


def close_eyes_linux() -> bool:
    ufw = shutil.which("ufw")
    if not ufw:
        print("[!] UFW is not installed.")
        return False

    print("[*] Setting UFW default inbound policy to DENY...")
    result = run([ufw, "default", "deny", "incoming"])
    if result.returncode != 0:
        print(result.stderr.strip())
        return False

    print("[*] Keeping outbound traffic allowed...")
    result = run([ufw, "default", "allow", "outgoing"])
    if result.returncode != 0:
        print(result.stderr.strip())
        return False

    print("[*] Enabling UFW...")
    result = run([ufw, "--force", "enable"])
    if result.returncode != 0:
        print(result.stderr.strip())
        return False

    return True


def close_eyes() -> None:
    clear()
    print_header()
    print("[!] CLOSE EYES WILL MODIFY NETWORK SECURITY SETTINGS.\n")

    if not is_admin():
        print(
            "[!] ClosedEYE needs Administrator/root privileges for "
            "firewall changes."
        )
        pause()
        return

    print("A backup is strongly recommended so the changes can be reverted.")
    answer = input("\nCreate a backup first? [Y/n]: ").strip().lower()

    backup = None
    if answer in ("", "y", "yes"):
        backup = create_backup()
        if backup is None:
            print("\n[!] No changes were made because the backup failed.")
            pause()
            return
    else:
        print(
            "\n⚠ WARNING: Without a backup, ClosedEYE may not be able to "
            "automatically restore your previous firewall configuration."
        )
        confirm = input("Continue WITHOUT a backup? [y/N]: ").strip().lower()
        if confirm not in ("y", "yes"):
            print("[*] Cancelled.")
            pause()
            return

    confirm = input("\nContinue with Close Eyes? [y/N]: ").strip().lower()
    if confirm not in ("y", "yes"):
        print("[*] Cancelled. No changes made.")
        pause()
        return

    print("\n[*] Closing network exposure...\n")

    success = False
    try:
        if IS_WINDOWS:
            success = close_eyes_windows()
        elif IS_LINUX:
            success = close_eyes_linux()
    except Exception as exc:
        print(f"[!] Error: {exc}")

    if success:
        print("\n╔══════════════════════════════════════╗")
        print("║          CLOSED EYE ACTIVE           ║")
        print("╠══════════════════════════════════════╣")
        print("║  Inbound firewall: BLOCKED          ║")
        print("║  Outbound traffic: ALLOWED          ║")
        print("║  Backup:             AVAILABLE      ║")
        print("╚══════════════════════════════════════╝")
        if backup:
            print(f"\nBackup: {backup}")
    else:
        print("\n[!] ClosedEYE could not complete all hardening changes.")

    pause()


def list_backups() -> list[Path]:
    ensure_dirs()
    return sorted(
        [p for p in BACKUP_DIR.iterdir() if p.is_dir()],
        reverse=True,
    )


def restore_windows(backup: Path, metadata: dict) -> bool:
    firewall_file = Path(metadata["file"])
    if not firewall_file.exists():
        print("[!] Firewall backup file is missing.")
        return False

    print("[*] Restoring Windows Firewall configuration...")
    result = run(["netsh", "advfirewall", "import", str(firewall_file)])
    if result.returncode != 0:
        print(result.stderr.strip())
        return False
    return True


def restore_linux(backup: Path, metadata: dict) -> bool:
    archive = Path(metadata["file"])
    if not archive.exists():
        print("[!] UFW backup archive is missing.")
        return False

    print("[*] Restoring /etc/ufw from backup...")
    result = run(["tar", "-xf", str(archive), "-C", "/"])
    if result.returncode != 0:
        print(result.stderr.strip())
        return False

    ufw = shutil.which("ufw")
    if ufw:
        # Reload the restored configuration.
        run([ufw, "--force", "enable"])
        run([ufw, "reload"])

    return True


def revert_changes() -> None:
    clear()
    print_header()
    print("CLOSED EYE RESTORE\n")

    if not is_admin():
        print("[!] Administrator/root privileges are required.")
        pause()
        return

    backups = list_backups()
    if not backups:
        print("[!] No ClosedEYE backups were found.")
        pause()
        return

    for i, backup in enumerate(backups, 1):
        metadata_file = backup / "metadata.json"
        label = backup.name
        details = ""
        if metadata_file.exists():
            try:
                metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
                label = metadata.get("created", backup.name)
                details = metadata.get("platform", "")
            except Exception:
                pass
        print(f"{i}. {label}  [{details}]")

    print("0. Cancel")
    choice = input("\nSelect backup: ").strip()

    if choice == "0":
        return

    try:
        selected = backups[int(choice) - 1]
    except (ValueError, IndexError):
        print("[!] Invalid selection.")
        pause()
        return

    metadata_file = selected / "metadata.json"
    if not metadata_file.exists():
        print("[!] Backup metadata is missing.")
        pause()
        return

    metadata = json.loads(metadata_file.read_text(encoding="utf-8"))

    print("\n[!] This will restore the selected firewall configuration.")
    print(f"    Backup: {selected.name}")
    confirm = input("Restore it? [y/N]: ").strip().lower()

    if confirm not in ("y", "yes"):
        print("[*] Cancelled.")
        pause()
        return

    if metadata.get("platform") == "Windows":
        success = restore_windows(selected, metadata)
    elif metadata.get("platform") == "Linux":
        success = restore_linux(selected, metadata)
    else:
        print("[!] Unsupported backup platform.")
        success = False

    print(
        "\n[✓] ClosedEYE changes reverted."
        if success
        else "\n[!] Restore failed."
    )
    pause()


def get_listening_ports() -> list[dict]:
    """
    Prefer psutil if installed. Otherwise use OS commands.
    This is intentionally an audit-only operation.
    """
    try:
        import psutil  # type: ignore

        rows = []
        for conn in psutil.net_connections(kind="inet"):
            if conn.status != psutil.CONN_LISTEN:
                continue

            addr = conn.laddr
            ip = getattr(addr, "ip", "")
            port = getattr(addr, "port", "")
            rows.append(
                {
                    "proto": "TCP",
                    "address": ip,
                    "port": port,
                    "pid": conn.pid,
                }
            )
        return sorted(rows, key=lambda x: (x["port"], x["address"]))
    except ImportError:
        pass

    rows = []
    if IS_WINDOWS:
        result = run(["netstat", "-ano", "-p", "TCP"])
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 5 and parts[0].upper() == "TCP":
                state = parts[3].upper()
                if state == "LISTENING":
                    local = parts[1]
                    pid = parts[4]
                    host, _, port = local.rpartition(":")
                    rows.append(
                        {
                            "proto": "TCP",
                            "address": host.strip("[]"),
                            "port": port,
                            "pid": pid,
                        }
                    )
    else:
        result = run(["ss", "-lntp"])
        for line in result.stdout.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 4:
                local = parts[3]
                host, _, port = local.rpartition(":")
                rows.append(
                    {
                        "proto": "TCP",
                        "address": host.strip("[]"),
                        "port": port,
                        "pid": "",
                    }
                )

    return rows


def firewall_status() -> str:
    if IS_WINDOWS:
        result = run(["netsh", "advfirewall", "show", "allprofiles"])
        return result.stdout + result.stderr

    ufw = shutil.which("ufw")
    if ufw:
        result = run([ufw, "status", "verbose"])
        return result.stdout + result.stderr

    return "UFW not installed; Linux firewall backend not assessed."


COMMON_RISK_PORTS = {
    21: ("FTP", "HIGH"),
    22: ("SSH", "MEDIUM"),
    23: ("Telnet", "CRITICAL"),
    25: ("SMTP", "MEDIUM"),
    53: ("DNS", "MEDIUM"),
    80: ("HTTP", "MEDIUM"),
    110: ("POP3", "MEDIUM"),
    139: ("NetBIOS/SMB", "HIGH"),
    443: ("HTTPS", "LOW"),
    445: ("SMB", "HIGH"),
    3389: ("RDP", "HIGH"),
    5900: ("VNC", "HIGH"),
    6379: ("Redis", "CRITICAL"),
    27017: ("MongoDB", "CRITICAL"),
    2375: ("Docker API", "CRITICAL"),
    3306: ("MySQL", "HIGH"),
    5432: ("PostgreSQL", "HIGH"),
    8000: ("Common dev server", "MEDIUM"),
    8080: ("HTTP/dev server", "MEDIUM"),
    3000: ("Node/dev server", "MEDIUM"),
}


def exposure_level(address: str) -> str:
    a = address.lower()

    if a in ("127.0.0.1", "::1", "localhost"):
        return "LOCAL"

    if a.startswith("127."):
        return "LOCAL"

    # 0.0.0.0 / :: means all interfaces.
    if a in ("0.0.0.0", "::", ""):
        return "ALL"

    # RFC1918 IPv4 and common local IPv6 ranges.
    try:
        import ipaddress

        ip = ipaddress.ip_address(a)
        if ip.is_private or ip.is_link_local:
            return "LAN"
    except ValueError:
        pass

    return "PUBLIC"


def test_vulnerabilities() -> None:
    clear()
    print_header()
    print("VULNERABILITY TEST\n")
    print("Audit only: ClosedEYE will not exploit services.\n")

    ports = get_listening_ports()

    print("[*] Listening TCP services\n")
    print(f"{'PORT':<7}{'ADDRESS':<40}{'RISK':<12}{'SERVICE'}")
    print("-" * 85)

    findings = []

    for item in ports:
        try:
            port = int(item["port"])
        except (ValueError, TypeError):
            continue

        service, risk = COMMON_RISK_PORTS.get(
            port, ("Unknown service", "INFO")
        )
        exposure = exposure_level(str(item["address"]))

        if exposure in ("ALL", "PUBLIC") and risk in (
            "CRITICAL",
            "HIGH",
            "MEDIUM",
        ):
            findings.append((port, service, risk, item["address"]))

        print(
            f"{port:<7}"
            f"{str(item['address']):<40}"
            f"{risk:<12}"
            f"{service}"
        )

    print("\n[*] Firewall status\n")
    status = firewall_status()
    print(status[:5000])

    print("\n╔══════════════════════════════════════╗")
    print("║          VULNERABILITY REPORT        ║")
    print("╚══════════════════════════════════════╝")

    if findings:
        print(f"\n[!] {len(findings)} potentially exposed service(s):\n")
        for port, service, risk, address in findings:
            print(
                f"  {risk:<9} TCP/{port:<5} {service:<20} "
                f"bound to {address}"
            )
        print(
            "\nRecommendation: review these services and firewall rules. "
            "A listener alone does not prove internet exposure."
        )
    else:
        print("\n[✓] No obvious high-risk exposed listeners detected.")

    print("\nNote:")
    print(
        "ClosedEYE cannot guarantee that a host is invisible to Shodan "
        "or other internet scanners from a local audit alone."
    )
    pause()


def main() -> None:
    ensure_dirs()

    while True:
        clear()
        print_header()
        choice = input("Select an option: ").strip()

        if choice == "1":
            close_eyes()
        elif choice == "2":
            revert_changes()
        elif choice == "3":
            test_vulnerabilities()
        elif choice == "4":
            print("\nGoodbye.")
            break
        else:
            print("\n[!] Invalid option.")
            pause()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nClosedEYE terminated.")
        sys.exit(0)