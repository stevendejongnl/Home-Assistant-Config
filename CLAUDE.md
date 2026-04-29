# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Home Assistant configuration repository** for a residential smart home. It tracks YAML configurations, automations, custom sensor templates, shell commands, blueprints, ESPHome device configs, and PyScript automations. Custom components and frontend assets are managed by HACS and excluded from git.

## Path Mapping (Add-on Container)

In the Claude Code add-on container, paths differ from HA Core:
- `/homeassistant` = HA config directory (equivalent to `/config` in HA Core)
- References to `/config/...` in HA YAML (e.g., shell_command.yaml) map to `/homeassistant/...` on disk

## Configuration Architecture

`configuration.yaml` is the entry point. It uses `!include` and `!include_dir_merge_*` directives to load modular configs:

```
configuration.yaml
├── customize.yaml          # Entity picture/icon overrides
├── automations.yaml        # UI-generated automations (legacy, "automation old:")
├── automations/            # YAML-based automations ("automation:", merge list)
│   ├── homeassistant.yaml
│   └── traccar.yaml
├── scripts.yaml            # Named scripts (vacuum, radio, notifications)
├── sensors/                # REST & average sensors (merge list)
│   ├── temperatures.yaml
│   └── tweakers.yaml
├── templates/              # Jinja2 template sensors (merge list)
│   ├── appliances.yaml     # NordPool energy slot optimization
│   ├── displays.yaml       # OpenHASP display metadata
│   └── sensor.yaml         # Misc template sensors
├── shell_command.yaml      # External commands (Proxmox API, Frigate, convert)
├── climate.yaml            # Climate group configs (radiator zones)
├── homekit.yaml            # Apple HomeKit bridge entity filters
├── notify.yaml             # Notification groups (steven, anja, family, security)
├── input_boolean.yaml      # Toggle helpers (cooldowns, control flags)
├── input_button.yaml       # One-shot trigger buttons
├── input_datetime.yaml     # Date/time helpers
├── input_number.yaml       # Numeric sliders (energy scheduling)
├── panel_custom.yaml       # Custom frontend panels
├── themes/                 # Lovelace themes (merge named)
└── openhasp_configs/       # OpenHASP touch-screen display configs (merge named)
```

## Key Integration Areas

- **Energy Management**: NordPool electricity pricing with template sensors that calculate cheapest time windows for appliances (washing machine, dryer, dishwasher). Configurable via `input_number` helpers for slot duration.
- **Climate Control**: Climate groups combining multiple TRV radiators into zones (all/downstairs/upstairs). Uses `better_thermostat` and calibration blueprints.
- **Camera/NVR**: Frigate integration with Proxmox API shell commands for container lifecycle. Snapshot download and retention via shell commands.
- **PyScript**: Python scripting engine (`pyscript/` submodule from `stevendejongnl/Home-Assistant-PyScripts`). Configured with `allow_all_imports: true` and `hass_is_global: true`.
- **Notifications**: Groups target mobile apps for Steven and Anja, plus Telegram bot.

## SSH Access Rules

**NEVER SSH directly to a raw LAN IP address.** Always use:
- Named hosts from `~/.ssh/config`: `ssh home-assistant` (port 24, HAOS SSH addon)
- Or the `mcp__infrastructure__infra_ssh_exec` MCP tool — handles ProxyJump automatically

Direct IP SSH (`ssh root@192.168.1.25`) fails when VPN is not active.

On HAOS, `ha` CLI is only in PATH for **login shells**. Always prefix with `bash -l -c`:
```bash
# Correct — login shell loads the ha PATH
bash -l -c 'ha core start'
bash -l -c 'ha core info'

# Wrong — ha not found in non-login shell
ha core start
```

## Validating Configuration

```bash
# Check HA configuration is valid
ha core check

# View HA logs
ha core logs 2>&1 | tail -100

# Filter for errors
ha core logs 2>&1 | grep -iE "(error|exception)"

# Reload specific domains after YAML changes (no restart needed)
# Use the Home Assistant MCP tools to call services like:
#   domain="automation", service="reload"
#   domain="input_boolean", service="reload"
#   domain="template", service="reload"
#   domain="shell_command", service="reload"
```

## Git Conventions

- **Gitleaks CI**: Runs on push/PR to detect secrets (`.github/workflows/leaks.yml`)
- **Secrets**: All sensitive values go in `secrets.yaml` (gitignored), referenced via `!secret key_name`
- **Gitignored auto-managed content**: `custom_components/`, `www/community/`, `www/lovelace-*/`, databases, logs, `.storage/`
- **Submodule**: `pyscript/` points to `git@github.com:stevendejongnl/Home-Assistant-PyScripts.git`

## Automation Patterns

There are two automation systems in use:
1. **`automations.yaml`** (loaded as `automation old:`): Large file of UI-generated automations. Edited via HA frontend; avoid manual edits.
2. **`automations/`** directory (loaded as `automation:`): Structured YAML automations for version-controlled, hand-written logic.

Blueprints in `blueprints/automations/` provide reusable automation templates (battery alerts, appliance notifications, TRV calibration, heating control).
