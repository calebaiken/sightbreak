#!/usr/bin/env bash
# Install official Android tools for a signed debug APK (not a store release).
set -euo pipefail
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tools_dir="${SIGHTBREAK_TOOLS_DIR:-$(dirname "$repo_dir")/tools}"
state_dir="${SIGHTBREAK_STATE_DIR:-$repo_dir/.local}"
export ANDROID_USER_HOME="$state_dir/android"
sdk_dir="${ANDROID_SDK_ROOT:-$tools_dir/android-sdk}"
java_dir="${JAVA_HOME:-$(dirname "$(dirname "$(readlink -f "$(command -v java)")")")}"
[[ -x "$java_dir/bin/keytool" ]] || { echo 'Install OpenJDK 17 or 21 with keytool first.' >&2; exit 1; }
mkdir -p "$tools_dir" "$sdk_dir/cmdline-tools" "$ANDROID_USER_HOME" "$state_dir/config/godot"
archive="$tools_dir/android-commandline-19.zip"
expected=7ec965280a073311c339e571cd5de778b9975026cfcbe79f2b1cdcb1e15317ee
if [[ ! -f "$archive" ]] || ! printf '%s  %s\n' "$expected" "$archive" | sha256sum --check --status; then
  curl --fail --location --retry 3 https://dl.google.com/android/repository/commandlinetools-linux-13114758_latest.zip -o "$archive.download"
  printf '%s  %s\n' "$expected" "$archive.download" | sha256sum --check
  mv "$archive.download" "$archive"
fi
if [[ ! -x "$sdk_dir/cmdline-tools/19.0/bin/sdkmanager" ]]; then
  unzip -oq "$archive" -d "$sdk_dir/cmdline-tools"
  mv "$sdk_dir/cmdline-tools/cmdline-tools" "$sdk_dir/cmdline-tools/19.0"
fi
sdkmanager="$sdk_dir/cmdline-tools/19.0/bin/sdkmanager"
platform_archive="$tools_dir/android-platform-tools-37.0.1.zip"
platform_sha256=d230f13842f60f782a8645f9c813f8f845bf36089ea7289f28c48f17979313f1
if [[ ! -f "$platform_archive" ]] || ! printf '%s  %s\n' "$platform_sha256" "$platform_archive" | sha256sum --check --status; then
  curl --fail --location --retry 3 https://dl.google.com/android/repository/platform-tools_r37.0.1-linux.zip -o "$platform_archive.download"
  printf '%s  %s\n' "$platform_sha256" "$platform_archive.download" | sha256sum --check
  mv "$platform_archive.download" "$platform_archive"
fi
unzip -oq "$platform_archive" -d "$sdk_dir"
# Accept only licenses prompted by these stable packages. SDK manager verifies package downloads.
set +o pipefail
yes 2>/dev/null | "$sdkmanager" --sdk_root="$sdk_dir" 'build-tools;36.0.0' 'platforms;android-36'
sdk_status=${PIPESTATUS[1]}
set -o pipefail
[[ "$sdk_status" == 0 ]] || exit "$sdk_status"
# Debug credentials are standard development-only credentials, never a release key.
keystore="$state_dir/android/debug.keystore"
if [[ ! -f "$keystore" ]]; then
  "$java_dir/bin/keytool" -genkeypair -keystore "$keystore" -storepass android -alias androiddebugkey -keypass android -dname 'CN=Android Debug,O=Android,C=US' -keyalg RSA -keysize 2048 -validity 10000
fi
python3 - "$state_dir/config/godot/editor_settings-4.7.tres" "$sdk_dir" "$java_dir" "$keystore" <<'PY'
import json,pathlib,re,sys
path=pathlib.Path(sys.argv[1])
text=path.read_text() if path.exists() else '[gd_resource type="EditorSettings" format=3]\n\n[resource]\n'
for key,value in {
 'export/android/android_sdk_path':sys.argv[2],
 'export/android/java_sdk_path':sys.argv[3],
 'export/android/debug_keystore':sys.argv[4],
 'export/android/debug_keystore_user':'androiddebugkey',
 'export/android/debug_keystore_pass':'android',
}.items():
 line=key+' = '+json.dumps(value)
 pattern=r'^'+re.escape(key)+r'\s*=.*$'
 if re.search(pattern,text,re.M): text=re.sub(pattern,lambda _:line,text,flags=re.M)
 else: text=text.rstrip()+'\n'+line+'\n'
path.write_text(text)
PY
printf 'Android SDK and debug signing ready. Run scripts/export.sh android.\n'
