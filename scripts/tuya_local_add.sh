#!/bin/sh
# tuya_local_add.sh — Add a tuya_local device to Home Assistant via config flow API.
# Usage: tuya_local_add.sh --device-id ID --host IP --key KEY --protocol VER --type TYPE --name NAME

set -e

HA_URL="http://192.168.1.25:8123"
TOKEN=$(grep 'homeassistant_hass_token:' /homeassistant/secrets.yaml | awk '{print $2}')

DEVICE_ID=""
HOST=""
LOCAL_KEY=""
PROTOCOL="3.5"
DEVICE_TYPE=""
NAME=""

while [ $# -gt 0 ]; do
  case "$1" in
    --device-id) DEVICE_ID="$2"; shift 2 ;;
    --host)      HOST="$2";      shift 2 ;;
    --key)       LOCAL_KEY="$2"; shift 2 ;;
    --protocol)  PROTOCOL="$2";  shift 2 ;;
    --type)      DEVICE_TYPE="$2"; shift 2 ;;
    --name)      NAME="$2";      shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

if [ -z "$DEVICE_ID" ] || [ -z "$HOST" ] || [ -z "$LOCAL_KEY" ] || [ -z "$DEVICE_TYPE" ] || [ -z "$NAME" ]; then
  echo "Usage: $0 --device-id ID --host IP --key KEY [--protocol 3.5] --type TYPE --name NAME"
  exit 1
fi

echo "Starting tuya_local config flow..."
FLOW=$(curl -sf -X POST "$HA_URL/api/config/config_entries/flow" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"handler":"tuya_local","show_advanced_options":false}')
FLOW_ID=$(echo "$FLOW" | python3 -c "import sys,json; print(json.load(sys.stdin)['flow_id'])")
echo "  Flow ID: $FLOW_ID"

echo "  Selecting manual setup..."
curl -sf -X POST "$HA_URL/api/config/config_entries/flow/$FLOW_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"setup_mode":"manual"}' > /dev/null

echo "  Submitting device credentials (protocol $PROTOCOL)..."
curl -sf -X POST "$HA_URL/api/config/config_entries/flow/$FLOW_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"device_id\":\"$DEVICE_ID\",\"host\":\"$HOST\",\"local_key\":\"$LOCAL_KEY\",\"protocol_version\":$PROTOCOL,\"poll_only\":false}" > /dev/null

echo "  Selecting device type: $DEVICE_TYPE..."
curl -sf -X POST "$HA_URL/api/config/config_entries/flow/$FLOW_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"type\":\"$DEVICE_TYPE\"}" > /dev/null

echo "  Setting name: $NAME..."
RESULT=$(curl -sf -X POST "$HA_URL/api/config/config_entries/flow/$FLOW_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"$NAME\"}")

STATE=$(echo "$RESULT" | python3 -c "import sys,json; r=json.load(sys.stdin); print(r.get('result',{}).get('state','unknown'))" 2>/dev/null || echo "unknown")
ENTRY_ID=$(echo "$RESULT" | python3 -c "import sys,json; r=json.load(sys.stdin); print(r.get('result',{}).get('entry_id',''))" 2>/dev/null || echo "")

if [ "$STATE" = "loaded" ]; then
  echo "Done! Entry $ENTRY_ID loaded successfully."
else
  echo "Warning: state=$STATE (expected 'loaded'). Full response:"
  echo "$RESULT" | python3 -m json.tool 2>/dev/null || echo "$RESULT"
fi
