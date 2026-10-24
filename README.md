# ghidra_auto

A small CLI script that imports a binary into Ghidra, runs the headless analysis, and opens the result in Ghidra. It can also reopen an existing `.gpr` project.

Based on Crypto-Cat's `auto_ghidra.py`, with cleaner formatting, working checksec output, and optional auto-open in CodeBrowser.

## Features

- Imports and analyzes a binary with `analyzeHeadless`
- Prints `file` info about the binary
- Optional `pwn checksec` output (`-c`)
- Optional temporary project (`-t`)
- Opens existing `.gpr` projects
- Auto-opens the program in CodeBrowser (needs `xdotool` + X11)

## Requirements

- Python 3.8+
- [Ghidra](https://ghidra-sre.org/) installed (and a JDK)
- `file` command (preinstalled on most Linux distros)
- Optional: `xdotool` for auto-open (X11 only, not Wayland)

## Installation

```bash
git clone https://github.com/yousri25/ghidra_auto.git
cd ghidra_auto
pip install -r requirements.txt
chmod +x ghidra_auto.py
```

Optional, to run it from anywhere:

```bash
sudo cp ghidra_auto.py /usr/local/bin/ghidra_auto
```

## Setup

The script looks for Ghidra in `/usr/share/ghidra/` or `/opt/ghidra/`. If yours is elsewhere, set:

```bash
export GHIDRA_PATH=/path/to/ghidra/
```

(Add it to your `~/.bashrc` or `~/.zshrc` to make it permanent.)

If the auto-click misses the file in the project window, adjust `CLICK_X` and `CLICK_Y` at the top of the script.

## Usage

```bash
./ghidra_auto.py ./binary            # import, analyze, open
./ghidra_auto.py ./binary -c         # also run checksec
./ghidra_auto.py ./binary -t         # use a temporary project
./ghidra_auto.py ./binary -v         # verbose analyzer output
./ghidra_auto.py ./binary.gpr        # open an existing project
```
