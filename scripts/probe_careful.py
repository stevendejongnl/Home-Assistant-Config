import tinytuya, time, json, base64, sys

DEVICE_ID = "bfbecd0dc4a9b8bc17m9jy"
LOCAL_KEY = "Tw.itw`XWQqB[sG/"
IP = "192.168.1.18"
PROTOCOL = 3.5

def check_ack(result):
    """Check a tinytuya response for DPS 124 ACK."""
    if result and "dps" in result:
        dps124 = result["dps"].get("124")
        if dps124:
            try:
                decoded = json.loads(base64.b64decode(dps124))
                return decoded.get("result", "?")
            except:
                pass
    return None

def probe_ids(start, end):
    d = tinytuya.Device(DEVICE_ID, IP, LOCAL_KEY)
    d.set_version(PROTOCOL)
    time.sleep(2)

    s = d.status()
    print("Status: " + str(s.get("dps", {}).get("15", "?")))
    print("Probing room IDs %d-%d with 5s between each...\n" % (start, end))
    sys.stdout.flush()

    accepted = []
    rejected = []

    for room_id in range(start, end + 1):
        payload = {
            "method": "selectRoomsClean",
            "data": {"roomIds": [room_id], "cleanTimes": 1},
            "timestamp": round(time.time() * 1000),
        }
        encoded = base64.b64encode(
            json.dumps(payload, separators=(",", ":")).encode()
        ).decode()

        # Check immediate response from set_value
        result = d.set_value("124", encoded)
        ack = check_ack(result)

        # If no ACK in immediate response, wait and check receive
        if ack is None:
            deadline = time.time() + 4
            while time.time() < deadline:
                result = d.receive()
                ack = check_ack(result)
                if ack is not None:
                    break
                time.sleep(0.3)

        if ack == "O":
            print("  ID %3d: ACK OK  <<<" % room_id)
            accepted.append(room_id)
        elif ack == "F":
            print("  ID %3d: rejected" % room_id)
            rejected.append(room_id)
        else:
            print("  ID %3d: no response (ack=%s)" % (room_id, ack))
        sys.stdout.flush()

        # Wait 5s between probes for clean state
        time.sleep(5)

    print("\n" + "=" * 40)
    print("ACCEPTED (result=O): " + str(accepted or "none"))
    print("REJECTED (result=F): %d IDs" % len(rejected))
    print("=" * 40)
    sys.stdout.flush()

if __name__ == "__main__":
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    end = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    probe_ids(start, end)
