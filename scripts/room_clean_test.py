"""
Room ID discovery script for Eufy X8 Pro SES (T2276) — Freddy.

Protocol discovered via packet capture:
  1. Send selectRoomsClean on DPS 124 (base64 JSON)
  2. Wait for ACK: DPS 124 with result="O"
  3. Send DPS 2 = true to start cleaning
  4. Vacuum transitions: Locating → Running

Valid room IDs from probe: 2, 3, 4, 6, 8, 10
(User has 4 physical rooms — some IDs may be sub-areas)

Usage (run from HA shell):
    python3 /config/scripts/room_clean_test.py [room_id]
    python3 /config/scripts/room_clean_test.py          # interactive mode
    python3 /config/scripts/room_clean_test.py 2        # test room ID 2 only

After each test, the vacuum returns to dock before the next room.
Press Enter to advance, or 'q' to quit.
"""

import base64
import json
import sys
import time

import tinytuya

# Freddy connection details
DEVICE_ID = "bfbecd0dc4a9b8bc17m9jy"
LOCAL_KEY = "Tw.itw`XWQqB[sG/"
IP_ADDRESS = "192.168.1.18"
PROTOCOL = "3.5"

DPS_ROOM_CLEAN = "124"
DPS_ACTIVATE = "2"
DPS_RETURN_HOME = "101"

# Room IDs that returned result="O" during probe
VALID_ROOM_IDS = [2, 3, 4, 6, 8, 10]


def build_room_clean_payload(room_ids: list[int], clean_times: int = 1) -> str:
    """Build a base64-encoded JSON payload for room cleaning."""
    payload = {
        "method": "selectRoomsClean",
        "data": {"roomIds": room_ids, "cleanTimes": clean_times},
        "timestamp": round(time.time() * 1000),
    }
    raw = json.dumps(payload, separators=(",", ":"))
    return base64.b64encode(raw.encode()).decode()


def connect() -> tinytuya.Device:
    """Connect to Freddy via tinytuya."""
    device = tinytuya.Device(DEVICE_ID, IP_ADDRESS, LOCAL_KEY)
    device.set_version(float(PROTOCOL))
    print(f"Connected to {IP_ADDRESS} (protocol {PROTOCOL})")
    return device


def send_room_clean(device: tinytuya.Device, room_id: int) -> bool:
    """Send room clean: DPS 124 (select) + DPS 2 (activate)."""
    encoded = build_room_clean_payload([room_id])
    print(f"  Step 1: Sending selectRoomsClean on DPS 124 (roomId={room_id})")
    result = device.set_value(DPS_ROOM_CLEAN, encoded)
    print(f"    Response: {result}")

    # Check for ACK
    ack = False
    if result and "dps" in result:
        dps = result.get("dps", {})
        if DPS_ROOM_CLEAN in dps:
            try:
                decoded = json.loads(base64.b64decode(dps[DPS_ROOM_CLEAN]))
                if decoded.get("result") == "O":
                    print(f"    ACK received: {decoded}")
                    ack = True
            except Exception:
                pass

    if not ack:
        # Wait a moment and check for delayed ACK
        time.sleep(2)
        result = device.receive()
        if result and "dps" in result:
            dps = result.get("dps", {})
            if DPS_ROOM_CLEAN in dps:
                try:
                    decoded = json.loads(base64.b64decode(dps[DPS_ROOM_CLEAN]))
                    if decoded.get("result") == "O":
                        print(f"    Delayed ACK received: {decoded}")
                        ack = True
                except Exception:
                    pass

    if not ack:
        print("    WARNING: No ACK received — room ID may be invalid")
        return False

    print(f"  Step 2: Sending DPS 2 = true (activate cleaning)")
    result = device.set_value(DPS_ACTIVATE, True)
    print(f"    Response: {result}")

    # Monitor status for a few seconds
    print("  Monitoring status (10s)...")
    end_time = time.time() + 10
    while time.time() < end_time:
        data = device.receive()
        if data and "dps" in data:
            dps = data.get("dps", {})
            for k, v in dps.items():
                if k == "15":
                    print(f"    Status (DPS 15): {v}")
                elif k == "5":
                    print(f"    Mode (DPS 5): {v}")
                elif k == "142":
                    try:
                        decoded = json.loads(base64.b64decode(v))
                        print(f"    Event (DPS 142): {decoded}")
                    except Exception:
                        print(f"    DPS {k}: {v}")
                elif k not in ("115",):  # Skip diagnostics
                    print(f"    DPS {k}: {v}")

    return ack


def send_return_home(device: tinytuya.Device):
    """Send return-to-dock command."""
    print("  Sending return_home (DPS 101 = True)...")
    result = device.set_value(DPS_RETURN_HOME, True)
    print(f"    Response: {result}")


def main():
    if not LOCAL_KEY:
        print("ERROR: Set LOCAL_KEY before running this script.")
        return

    # Single room mode: python3 room_clean_test.py <room_id>
    if len(sys.argv) > 1:
        room_id = int(sys.argv[1])
        print(f"Testing single room ID: {room_id}")
        device = connect()
        time.sleep(2)
        ack = send_room_clean(device, room_id)
        if ack:
            print("\n  Waiting 30s for you to observe, then sending home...")
            time.sleep(30)
        else:
            print("\n  Room ID was rejected, skipping activate wait.")
        send_return_home(device)
        print("  Done. Freddy is heading home.")
        return

    # Interactive mode: test all valid room IDs
    device = connect()
    time.sleep(2)

    room_names = {}
    for i, room_id in enumerate(VALID_ROOM_IDS):
        print(f"\n{'='*50}")
        print(f"TEST {i+1}/{len(VALID_ROOM_IDS)}: room_id={room_id}")
        print(f"{'='*50}")

        send_room_clean(device, room_id)

        room_name = input(
            "\n  Which room did Freddy go to? (skip=unknown, q=quit): "
        ).strip()

        if room_name.lower() == "q":
            print("  Sending Freddy home before quitting...")
            send_return_home(device)
            break

        if room_name and room_name.lower() != "skip":
            room_names[room_id] = room_name

        if i < len(VALID_ROOM_IDS) - 1:
            print("\n  Returning Freddy to dock before next test...")
            send_return_home(device)
            input("  Press Enter when Freddy is docked... ")

    print(f"\n{'='*50}")
    print("ROOM ID MAPPING")
    print(f"{'='*50}")
    for rid, name in sorted(room_names.items()):
        print(f"  {rid} = {name}")

    if room_names:
        print("\nUpdate scripts.yaml and SETUP.md with these IDs.")


if __name__ == "__main__":
    main()
