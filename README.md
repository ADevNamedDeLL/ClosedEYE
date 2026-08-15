# ClosedEYE

ClosedEYE is a cross-platform network exposure auditing and hardening tool written in Python.

Its purpose is simple: help you understand what your computer is exposing to the network and reduce unnecessary inbound exposure through safe, reversible security changes.

ClosedEYE is designed for personal computers, development machines, and home systems where users want a straightforward way to inspect their network attack surface without having to manually inspect every firewall rule and listening service.

## Features

### Close Eyes

The Close Eyes option applies a conservative set of firewall hardening changes.

Before making changes, ClosedEYE asks whether you want to create a backup. Backups are strongly recommended because they allow the firewall configuration to be restored later.

Depending on the operating system, ClosedEYE can:

- Enable the system firewall
- Block unsolicited inbound connections
- Keep outbound connections allowed
- Create a backup before making changes
- Report exactly what was changed

ClosedEYE does not silently modify your system.

### Revert Changes

Every backup created by ClosedEYE can be selected from the Revert Changes menu.

The restoration process uses the saved firewall configuration instead of attempting to guess what the previous configuration looked like.

This makes it possible to undo changes made by ClosedEYE without manually reconstructing your firewall settings.

### Test Vulnerabilities

The vulnerability testing feature performs a local security audit.

It currently checks:

- Listening TCP ports
- Listening addresses
- Common high-risk services
- Firewall status
- Services bound to localhost
- Services bound to LAN interfaces
- Services bound to all interfaces
- Potentially dangerous development servers
- Common database services
- RDP
- SMB
- SSH
- FTP
- Telnet
- Docker API
- VNC

The scanner is audit-only. It does not exploit vulnerabilities or attempt to compromise systems.

## Important: Local Exposure vs Public Exposure

A computer listening on a port does not automatically mean that the port is publicly accessible from the Internet.

For example:

    127.0.0.1:3000

is normally accessible only from the local machine.

Meanwhile:

    0.0.0.0:3000

means the application is listening on all IPv4 interfaces and may be accessible from other devices, depending on firewall and network configuration.

Whether a service is actually reachable from the Internet can also depend on:

- Router configuration
- NAT
- Port forwarding
- UPnP
- IPv6 configuration
- ISP configuration
- Firewall rules
- VPN configuration

Because of this, ClosedEYE does not claim that a machine is completely invisible to Internet scanners based solely on a local scan.

The goal is to reduce unnecessary exposure and identify configurations that deserve further investigation.

## Supported Operating Systems

ClosedEYE is designed to support:

- Windows
- Linux

### Windows

Windows Firewall is currently supported directly through `netsh`.

ClosedEYE can:

- Back up Windows Firewall configuration
- Enable Windows Firewall
- Set inbound traffic to blocked by default
- Restore a previous firewall configuration
- Inspect listening TCP services

Administrator privileges are required for firewall modifications.

Run:

    python ClosedEYE.py

If firewall operations fail because of permissions, run the program from an Administrator terminal.

### Linux

Linux support currently uses UFW.

ClosedEYE can:

- Back up UFW configuration
- Set incoming traffic to denied by default
- Allow outgoing traffic
- Enable UFW
- Restore the previous UFW configuration
- Inspect listening TCP services

Root privileges are required for firewall modifications.

Run:

    sudo python3 ClosedEYE.py

ClosedEYE currently does not automatically modify arbitrary `iptables`, `nftables`, or `firewalld` configurations.

If UFW is not installed, ClosedEYE will refuse to modify the firewall rather than risk replacing or damaging an existing firewall configuration.

## Requirements

Python 3.10 or newer is recommended.

Install the Python dependency:

    pip install -r requirements.txt

The current requirements file contains:

    psutil>=6.0.0

`psutil` is used for detailed process and network connection information.

ClosedEYE also contains fallback methods using native operating-system tools when possible.

On Linux, the fallback scanner can use:

    ss

On Windows, the fallback scanner can use:

    netstat

## Installation

Clone the repository:

    git clone https://github.com/YOUR_USERNAME/ClosedEYE.git

Enter the project directory:

    cd ClosedEYE

Install the dependencies:

    pip install -r requirements.txt

Run ClosedEYE.

Windows:

    python ClosedEYE.py

Linux:

    sudo python3 ClosedEYE.py

## Usage

When started, ClosedEYE presents the following menu:

    ╔══════════════════════════════════════════════╗
    ║                  ClosedEYE                   ║
    ║        Network Exposure Protection           ║
    ╠══════════════════════════════════════════════╣
    ║  1. Close Eyes                               ║
    ║  2. Revert Changes                           ║
    ║  3. Test Vulnerabilities                     ║
    ║  4. Exit                                     ║
    ╚══════════════════════════════════════════════╝

### 1. Close Eyes

Select:

    1

ClosedEYE will first ask whether you want to create a backup.

Recommended:

    Create a backup first? [Y/n]:

If the backup is created successfully, ClosedEYE asks for confirmation before making changes.

This is intentional. Firewall modifications can affect applications, games, development servers, remote access, and other network-dependent software.

### 2. Revert Changes

Select:

    2

ClosedEYE displays available backups and allows you to choose which configuration to restore.

You must confirm the restoration before any changes are made.

### 3. Test Vulnerabilities

Select:

    3

ClosedEYE performs an audit without attempting to exploit any service.

Example output:

    [*] Listening TCP services

    PORT   ADDRESS                                  RISK        SERVICE
    -------------------------------------------------------------------------
    22     0.0.0.0                                  MEDIUM      SSH
    80     127.0.0.1                                MEDIUM      HTTP
    3389   0.0.0.0                                  HIGH        RDP
    3000   127.0.0.1                                MEDIUM      Node/dev server

The scanner then reports potentially exposed services.

## Backups

ClosedEYE stores backups locally.

On Windows, backups are stored under:

    %PROGRAMDATA%\ClosedEYE\backups

On Linux, backups are stored under:

    ~/.closedeeye/backups

Each backup contains metadata describing:

- Creation time
- ClosedEYE version
- Operating system
- Firewall backend
- Backup files

Do not delete a backup if you intend to use ClosedEYE's Revert Changes feature.

## Security Philosophy

ClosedEYE follows a few important principles.

### Ask before changing anything

The program should never silently change security-sensitive settings.

### Back up before modifying

Users should have a straightforward way to return to their previous configuration.

### Prefer conservative changes

The goal is to reduce unnecessary exposure rather than aggressively disable everything.

### Do not exploit systems

ClosedEYE is intended as a defensive auditing and hardening tool.

The vulnerability scanner identifies potentially risky configurations but does not attempt to compromise services.

### Do not claim absolute security

No local tool can guarantee that a computer is invisible to Shodan or other Internet scanners.

A machine's actual Internet exposure depends on the entire network path, including routers, NAT, IPv6, firewalls, VPNs, port forwarding, and ISP configuration.

ClosedEYE reports what it can determine locally and clearly distinguishes potential exposure from confirmed public accessibility.

## Limitations

ClosedEYE should not be treated as a replacement for a properly configured firewall, router, endpoint security solution, or professional security assessment.

A local scan cannot determine every possible Internet exposure.

For example, ClosedEYE may detect:

    0.0.0.0:8080

but this alone does not prove that:

    Internet -> Router -> Computer:8080

is reachable.

Conversely, a machine may have no obvious IPv4 exposure while still being reachable through IPv6.

These limitations are intentional considerations in the design of the project.

## Responsible Use

ClosedEYE is intended for systems that you own or are authorized to administer.

Use the auditing and hardening functionality responsibly.

Do not use ClosedEYE to interfere with networks or systems that you do not own or have permission to administer.

## License

ClosedEYE is licensed under the GNU General Public License v3.0 (GPLv3).

See the [LICENSE](LICENSE) file for the full license text.

## Disclaimer

ClosedEYE is provided for defensive security auditing and system hardening.

The authors are not responsible for damage, data loss, connectivity problems, service interruptions, or other consequences resulting from the use or modification of this software.

Always maintain a backup of important system configurations before making security or networking changes.