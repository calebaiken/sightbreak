# ARM SDK native outcome

The unsigned generic-device Debug compile slice passes at exact source `2a2b732c9f4637e9c2c68890cdd0f13d8fa89906` in run `39721286005`. [REPORT.md](REPORT.md) records the real probe, full compile/link, unsigned-app, PCK and unchanged-source evidence, plus its binary reinspection limits.

This new result preserves the earlier `0ca125d`/`39719407304` link failure. It supplies no installation, runtime, simulator, physical-device, Mac gameplay or release acceptance. The original Intel feature investigation remains a separate run.

`ARTIFACTS.json` and `SHA256SUMS` bind the retained archive originals and review evidence. Run `bash commands.sh` in a fresh checkout with Python and Pillow to restore and independently audit the raw receipts and startup PNGs. Existing extracted directories are refused. All review work was foreground session work.
