#!/bin/bash
# Build manual (sem Gradle): gerar.py -> aapt2 -> javac -> d8 -> zipalign -> apksigner.
# Saída: build/m7s-tema.apk (assinado com a keystore de debug do ~/.android).
# A API do Xposed entra só em tempo de compilação (stubs/), nunca no dex.
set -euo pipefail
cd "$(dirname "$0")"
SDK="${ANDROID_HOME:-$HOME/Library/Android/sdk}"
BT="$SDK/build-tools/35.0.0"
JAR="$SDK/platforms/android-31/android.jar"   # compileSdk 31; minSdk/targetSdk 19
OUT=build
APK="$OUT/m7s-tema.apk"

[ -d stock/fw/res ] || { echo "falta stock/ (ver README de tools/: extrair framework-res.apk e SystemUI.apk)"; exit 1; }
python3 -P tools/gerar.py
python3 -P tools/material.py   # linguagem visual da Taleszin OS por cima da recoloração

rm -rf "$OUT/res" "$OUT/gen" "$OUT/classes" "$OUT/stubs" "$OUT/dex" "$OUT"/*.apk
mkdir -p "$OUT/res" "$OUT/gen" "$OUT/classes" "$OUT/stubs" "$OUT/dex"

"$BT/aapt2" compile --dir res -o "$OUT/res/res.zip"
"$BT/aapt2" link -I "$JAR" --manifest AndroidManifest.xml \
  --min-sdk-version 19 --target-sdk-version 19 -A assets \
  --java "$OUT/gen" -o "$OUT/unsigned.apk" "$OUT/res/res.zip"

javac -nowarn -Xlint:-options -source 8 -target 8 -encoding UTF-8 \
  -bootclasspath "$JAR" -classpath "$JAR" -d "$OUT/stubs" $(find stubs -name '*.java')
javac -nowarn -Xlint:-options -source 8 -target 8 -encoding UTF-8 \
  -bootclasspath "$JAR" -classpath "$JAR:$OUT/stubs" -d "$OUT/classes" \
  $(find src "$OUT/gen" -name '*.java')

# só as classes do módulo (com.m7s.tema); os stubs ficam de fora
"$BT/d8" --release --min-api 19 --lib "$JAR" --classpath "$OUT/stubs" --output "$OUT/dex" \
  $(find "$OUT/classes" -name '*.class')
(cd "$OUT/dex" && zip -q -j ../unsigned.apk classes.dex)

"$BT/zipalign" -f -p 4 "$OUT/unsigned.apk" "$OUT/aligned.apk"
"$BT/apksigner" sign --ks "$HOME/.android/debug.keystore" --ks-pass pass:android \
  --ks-key-alias androiddebugkey --key-pass pass:android \
  --out "$APK" "$OUT/aligned.apk"
rm -f "$OUT/unsigned.apk" "$OUT/aligned.apk"
"$BT/apksigner" verify --min-sdk-version 19 "$APK"

python3 -P tools/verificar.py "$APK"
ls -la "$APK"; shasum -a 256 "$APK"
