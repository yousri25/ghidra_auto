#!/usr/bin/env python3
"""
Automatically import + analyze the given binary in Ghidra and open it,
or open an already created project (.gpr).

Based on Crypto-Cat's auto_ghidra.py (via xHacka's gist), with:
  - clean 4-space indentation
  - checksec output actually printed
  - safe subprocess calls (no shell), error checks, temp project cleanup
  - optional auto-open of the program in CodeBrowser (needs xdotool + X11)
"""

import os
import shutil
import sys
import tempfile
import time
from pathlib import Path
from subprocess import DEVNULL, Popen, check_output, run

import click

# Ghidra install dir (must end with a slash). Override with: export GHIDRA_PATH=/some/dir/
_default = '/usr/share/ghidra/' if os.path.isdir('/usr/share/ghidra') else '/opt/ghidra/'
GHIDRA_PATH = os.environ.get('GHIDRA_PATH', _default)
if not GHIDRA_PATH.endswith('/'):
    GHIDRA_PATH += '/'

ANALYZER = f"{GHIDRA_PATH}support/analyzeHeadless"
GHIDRA_RUN = f"{GHIDRA_PATH}ghidraRun"
GHIDRA_EXTENSION = '.gpr'

# Where to double-click inside the Ghidra project window to open the first file
# (pixels from the window's top-left). Adjust if it misses.
CLICK_X = 90
CLICK_Y = 110


def check_ghidra():
    if not os.path.isfile(ANALYZER):
        click.secho(f"[-] Ghidra not found at {GHIDRA_PATH}", fg='red')
        click.secho("    Set it with: export GHIDRA_PATH=/path/to/ghidra/", fg='red')
        sys.exit(1)


def analyze(project_dir, project_name, filename, verbose):
    cmd = [ANALYZER, project_dir, project_name, '-import', str(filename), '-overwrite']
    result = run(cmd, stdout=None if verbose else DEVNULL)
    return result.returncode == 0


def start(project_file):
    """Open the project in Ghidra; try to auto-open the program with xdotool."""
    if not shutil.which('xdotool') or os.environ.get('XDG_SESSION_TYPE') == 'wayland':
        run([GHIDRA_RUN, project_file])
        return

    proc = Popen([GHIDRA_RUN, project_file])

    # Wait for the project window to appear
    wid = None
    for _ in range(60):
        out = run(['xdotool', 'search', '--name', '^Ghidra:'],
                  capture_output=True, text=True).stdout.split()
        if out:
            wid = out[-1]
            break
        time.sleep(1)

    if wid:
        time.sleep(4)  # let the window finish loading
        run(['xdotool', 'windowactivate', '--sync', wid])
        # Double-click the first item in the project tree
        run(['xdotool', 'mousemove', '--window', wid, str(CLICK_X), str(CLICK_Y),
             'click', '--repeat', '2', '--delay', '100', '1'])

    proc.wait()


def file_info(filename):
    out = check_output(['file', '-b', str(filename)]).decode().strip()
    return '\t' + out.replace(', ', '\n\t')


def pwn_checksec(filename):
    click.secho("[+] Pwntools Checksec:\n", fg='green')
    try:
        run(['pwn', 'checksec', str(filename)], check=True)
    except Exception:
        click.secho("[-] Checksec Failed (is pwntools installed?)", fg='red')
    print()


@click.command()
@click.argument('filename', type=click.Path(exists=True, file_okay=True, dir_okay=False))
@click.option('-t', '--temp', 'temp', is_flag=True, help="Make project temporary")
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False, help="Add verbosity to analyzer")
@click.option('-c', '--checksec', 'checksec', is_flag=True, default=False,
              help="Use pwntools checksec to check securities of binary")
def main(filename, temp, verbose, checksec):
    check_ghidra()
    filename = Path(filename).resolve()

    if filename.suffix == GHIDRA_EXTENSION:
        click.secho("[+] Project Exists... Opening...", fg="yellow")
        start(str(filename))
        return

    project_dir = tempfile.mkdtemp() if temp else str(Path.cwd())
    project_name = filename.stem.replace(' ', '_')
    project_file = f'{project_dir}/{project_name}{GHIDRA_EXTENSION}'

    click.secho(f"[*] File Output:\n{file_info(filename)}\n", fg='green')

    if checksec:
        pwn_checksec(filename)

    click.secho("[*] Running Analysis...", fg='green')
    if not analyze(project_dir, project_name, filename, verbose):
        click.secho("[-] Analysis failed. Re-run with -v to see why.", fg='red')
        sys.exit(1)

    click.secho("[+] Analysis Complete\n[*] Opening Ghidra...", fg='green')
    click.secho(f"[*] Project Directory: {project_dir}", fg='green')
    click.secho(f"[*] Project File: {project_file}", fg='green')
    try:
        start(project_file)
    finally:
        if temp:
            shutil.rmtree(project_dir, ignore_errors=True)


if __name__ == '__main__':
    main()
