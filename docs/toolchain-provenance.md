# Toolchain provenance

| Component | Official source | Verification |
| --- | --- | --- |
| Godot 4.7.2 native editor/templates | https://github.com/godotengine/godot/releases/tag/4.7.2-stable | Published SHA512 pinned in `scripts/setup.sh`, verified before extraction |
| Android command-line tools 19.0 (13114758) | https://dl.google.com/android/repository/commandlinetools-linux-13114758_latest.zip | Google's repository2-3.xml SHA1 `5fdcc763663eefb86a5b8879697aa6088b041e70` verified initially; SHA256 `7ec965280a073311c339e571cd5de778b9975026cfcbe79f2b1cdcb1e15317ee` pinned in setup |
| Android platform-tools 37.0.1 | https://dl.google.com/android/repository/platform-tools_r37.0.1-linux.zip | Google's repository SHA1 verified initially; SHA256 `d230f13842f60f782a8645f9c813f8f845bf36089ea7289f28c48f17979313f1` pinned in setup |
| Android API36 / build-tools36 | https://dl.google.com/android/repository/ | Official SDK Manager package verification; package versions explicitly selected |
| Optional Xvfb, Debian 13 | https://deb.debian.org/debian/pool/main/x/xorg-server/xvfb_21.1.16-1.3+deb13u3_amd64.deb | Debian trixie InRelease signatures verified with installed Debian archive keyring using sqv, Packages.xz SHA256 checked, package SHA256 `365da2b6c93339f34337c434a9489bb6411a240fa47b9f49693d3091745f28c2` checked |

Godot is MIT licensed; its bundled third-party libraries have notices in `GODOT-COPYRIGHT.txt`. Android SDK packages are subject to Google's Android SDK license; SDK Manager displays and records license acceptance locally. Xvfb is optional development tooling licensed under the package's upstream/Debian notices. No downloaded editor, SDK, signing key, export template, or utility binary is checked into Git.
