# Actual CS2 reference access

The official `https://www.counter-strike.net/cs2` request again returned proxy
CONNECT 403 in this execution. The original result is retained beside this note.
No CS2 screenshot or footage was inspected from that page.

A separate search through the supported GitHub connector found actual reported
CS2 screenshots in Valve's public Linux issue tracker:

- [Issue 3477](https://github.com/ValveSoftware/csgo-osx-linux/issues/3477), including an in-game Inferno view and menu screenshots from October 2023.
- [Issue 3325](https://github.com/ValveSoftware/csgo-osx-linux/issues/3325), two reported native/Wine gameplay screenshots from September 2023.
- [Issue 3282](https://github.com/ValveSoftware/csgo-osx-linux/issues/3282), a reported game-window screenshot concerning multi-monitor behavior.

These identify real source candidates, not inspected image benchmarks. An ordinary
request to the first issue 3325 image URL below returned HTTP 403; its response
headers are retained. No file image was produced and no alternate route around
the denied host was attempted.

```text
https://github.com/ValveSoftware/csgo-osx-linux/assets/25158549/1b60ac6c-7181-4d18-987a-37fd0a13df43
```

The source reports date from launch-era CS2 and would need version/context labels
even if retrieved. Bug-report performance claims are not SIGHTBREAK benchmarks.
No image or protected game asset was copied into the product. G18 remains blocked
for actual presentation/animation/feel comparison. Available native correctness,
previous-build comparisons and independent rendered-output reviews continue.
