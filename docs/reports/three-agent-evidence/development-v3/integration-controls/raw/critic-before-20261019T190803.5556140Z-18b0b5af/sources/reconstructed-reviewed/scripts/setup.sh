#!/usr/bin/env bash
# Linux x86_64 development/export toolchain, pinned and checksum verified.
set -euo pipefail
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tools_dir="${SIGHTBREAK_TOOLS_DIR:-$(dirname "$repo_dir")/tools}"
state_dir="${SIGHTBREAK_STATE_DIR:-$repo_dir/.local}"
version=4.7.2
release="https://github.com/godotengine/godot/releases/download/${version}-stable"
install_dir="$tools_dir/godot-$version"
mkdir -p "$install_dir"
[[ "$(uname -s)-$(uname -m)" == Linux-x86_64 ]] || { echo 'Automatic toolchain setup supports Linux x86_64. Install matching Godot 4.7.2 for your OS and set GODOT_BIN.' >&2; exit 1; }
fetch_verified() {
  local url="$1" path="$2" hash="$3"
  if [[ ! -f "$path" ]] || ! printf '%s  %s\n' "$hash" "$path" | sha512sum --check --status; then
    curl --fail --location --retry 3 "$url" -o "$path.download"
    printf '%s  %s\n' "$hash" "$path.download" | sha512sum --check
    mv "$path.download" "$path"
  fi
}
fetch_verified "$release/Godot_v${version}-stable_linux.x86_64.zip" "$install_dir/godot.zip" 9aa00f7a605200940bce3027a567b782f49bd8e940dd06ae9e987bd65aee1b1467edd56ed84fcdcbdd44354bf613bdbb4e5d2913e925850368e150c59ed54c65
unzip -oq "$install_dir/godot.zip" -d "$install_dir"
chmod +x "$install_dir/Godot_v${version}-stable_linux.x86_64"
if [[ "${1:-}" != --editor-only ]]; then
  fetch_verified "$release/Godot_v${version}-stable_export_templates.tpz" "$install_dir/templates.tpz" ca4d71c4d7b81dfc15d1a98baa07534aa95b03fdda78a0075b06672e1648d2e5f40980c9adc28d23e1b92e732ee7bf3461997aa804af74ec2fcd7a93ccb84079
  template_dir="$state_dir/data/godot/export_templates/$version.stable"
  mkdir -p "$template_dir"
  # Only native target templates needed by this project (avoids several GB of unrelated targets).
  unzip -ojq "$install_dir/templates.tpz" 'templates/linux_*x86_64' 'templates/android_debug.apk' 'templates/android_release.apk' 'templates/ios.zip' 'templates/version.txt' -d "$template_dir"
fi
"$repo_dir/scripts/godot.sh" --headless --version
printf 'Godot ready. Run scripts/godot.sh --editor or scripts/export.sh linux.\n'
