#!/usr/bin/python3
"""
Automatically import + analyze the given binary in Ghidra and open it,
or open an already created project (.gpr).

Based on Crypto-Cat's auto_ghidra.py (via xHacka's gist), with:
  - clean 4-space indentation
  - checksec output actually printed
  - optional auto-open of the program in CodeBrowser (needs xdotool + X11)
"""

import os
import shutil
import tempfile
import time
from pathlib import Path
from subprocess import check_output, run, Popen

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


def analyze(project, project_name, filename, verbose):
    command = f"{ANALYZER} '{project}' '{project_name}' -import '{filename}' -overwrite"
    if not verbose:
        command += " >/dev/null"
    run(command, shell=True)


def start(project):
    """Open the project in Ghidra; try to auto-open the program with xdotool."""
    if not shutil.which('xdotool') or os.environ.get('XDG_SESSION_TYPE') == 'wayland':
        run([GHIDRA_RUN, project])
        return

    proc = Popen([GHIDRA_RUN, project])

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


def file(filename):  # Run `file` Command
    return '\t' + ''.join(
        check_output(["file", filename.absolute()])
        .decode()
        .split(': ', maxsplit=1)[1]
        .replace(', ', '\n\t')
    ).strip()


def pwn_checksec(filename):
    click.secho("[+] Pwntools Checksec:\n", fg='green')
    try:
        run(['pwn', 'checksec', str(filename)], check=True)
    except Exception:
        click.secho("[-] Checksec Failed...", fg='red')
    print()


@click.command()
@click.argument('filename', type=click.Path(exists=True, file_okay=True, dir_okay=False))
@click.option('-t', '--temp', 'temp', is_flag=True, help="Make project temporary")
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False, help="Add verbosity to analyzer")
@click.option('-c', '--checksec', 'checksec', is_flag=True, default=False,
              help="Use pwntools checksec to check securities of binary")
def main(filename, temp, verbose, checksec):
    filename = Path(filename.replace(' ', '_'))

    project = f'{Path.cwd()}' if not temp else tempfile.mkdtemp()
    project = project.replace(' ', '_')
    project_name = f'{project}/{filename.stem}{GHIDRA_EXTENSION}'

    if filename.suffix == GHIDRA_EXTENSION:
        click.secho("[+] Project Exists... Opening...", fg="yellow")
        start(project_name)
        return

    click.secho(f"[*] File Output:\n{file(filename)}\n", fg='green')

    if checksec:
        pwn_checksec(filename)

    click.secho("[*] Running Analysis...", fg='green')
    analyze(project, filename.stem, filename, verbose)

    click.secho("[+] Analysis Complete\n[*] Opening Ghidra...", fg='green')
    click.secho(f"[*] Project Directory: {project}", fg='green')
    click.secho(f"[*] Project File: {project_name}", fg='green')
    start(project_name)


if __name__ == '__main__':
    main()
