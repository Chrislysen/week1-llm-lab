"""run_queue.py: run commands one after another, detached, once a process has exited.

    python run_queue.py --after PID --log results/queue.log -- "python a.py --x" "python b.py"

Used to chain long local-model runs so the GPU is never shared between two of
them. Each command's output goes to the log; a failing command is logged and
the queue moves on.

Each command runs without a shell, without a console window and in its own process
group. A queued command started through `cmd /c` inside a console died with
STATUS_CONTROL_C_EXIT (rc 3221225786) when the command that launched the queue
returned. A process with no console cannot receive a console Ctrl+C.
"""
import argparse
import os
import subprocess
import sys
import time

NO_WINDOW, NEW_GROUP, DETACHED, BREAKAWAY = 0x08000000, 0x00000200, 0x00000008, 0x01000000


def pid_alive(pid):
    out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True).stdout
    return str(pid) in out


def argv(cmd):
    """'python -u x.py --all' -> [this interpreter, '-u', 'x.py', '--all']."""
    parts = cmd.split()
    return [sys.executable] + parts[1:] if parts[0] in ("python", "python.exe") else parts


def work(after, cmds, log):
    with open(log, "a", encoding="utf-8") as fh:
        if after:
            fh.write(f"waiting for process {after} to exit ...\n"); fh.flush()
            while pid_alive(after):
                time.sleep(30)
        for c in cmds:
            fh.write(f"\n### {time.strftime('%H:%M:%S')} START {c}\n"); fh.flush()
            rc = subprocess.run(argv(c), stdin=subprocess.DEVNULL, stdout=fh, stderr=subprocess.STDOUT,
                                creationflags=NO_WINDOW | NEW_GROUP).returncode
            fh.write(f"### {time.strftime('%H:%M:%S')} END rc={rc} {c}\n"); fh.flush()
        fh.write("QUEUE ALL DONE\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--after", type=int)
    ap.add_argument("--log", default="results/queue.log")
    ap.add_argument("--work", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("cmds", nargs="+")
    a = ap.parse_args()
    if a.work:
        work(a.after, a.cmds, a.log)
    else:
        args = [sys.executable, "-u", os.path.abspath(__file__), "--work", "--log", a.log] + \
               (["--after", str(a.after)] if a.after else []) + a.cmds
        p = subprocess.Popen(args, cwd=os.getcwd(), creationflags=DETACHED | NEW_GROUP | BREAKAWAY,
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"queue detached: pid {p.pid}, log {a.log}" + (f", after pid {a.after}" if a.after else ""))
