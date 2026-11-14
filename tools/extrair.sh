#!/bin/bash
# Extrai framework-res.apk e SystemUI.apk do system.img (ext4) para stock/ e descompacta os res/.
set -euo pipefail
cd "$(dirname "$0")/.."
IMG="${1:-/Users/macbookpro/dev/m7s-kitkat-rom/out/images/system.img}"
DEBUGFS=$(ls /usr/local/opt/e2fsprogs/sbin/debugfs /opt/homebrew/opt/e2fsprogs/sbin/debugfs 2>/dev/null | head -1)
BT="${ANDROID_HOME:-$HOME/Library/Android/sdk}/build-tools/35.0.0"
rm -rf stock; mkdir -p stock/fw stock/ui
"$DEBUGFS" -R "dump /framework/framework-res.apk stock/framework-res.apk" "$IMG"
"$DEBUGFS" -R "dump /priv-app/SystemUI.apk stock/SystemUI.apk" "$IMG"
unzip -q stock/framework-res.apk 'res/*' -d stock/fw
unzip -q stock/SystemUI.apk 'res/*' -d stock/ui
"$BT/aapt" dump --values resources stock/framework-res.apk > stock/fw-res.txt
shasum -a 256 stock/*.apk
