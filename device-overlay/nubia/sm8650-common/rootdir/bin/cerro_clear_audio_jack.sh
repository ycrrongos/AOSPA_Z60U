#!/system/bin/sh
# AOSPA cerro: clear stuck MTP Headset Jack switch bits (no 3.5mm jack).
# Run longer: AudioService/telecom can re-assert LINE after early clears.
i=0
while [ "$i" -lt 60 ]; do
  for e in /dev/input/event*; do
    n=$(cat /sys/class/input/"$(basename "$e")"/device/name 2>/dev/null) || continue
    case "$n" in
      *"Headset Jack"*)
        /system/bin/sendevent "$e" 5 6 0
        /system/bin/sendevent "$e" 5 7 0
        /system/bin/sendevent "$e" 5 2 0
        /system/bin/sendevent "$e" 5 4 0
        /system/bin/sendevent "$e" 0 0 0
        ;;
    esac
  done
  i=$((i + 1))
  sleep 2
done
