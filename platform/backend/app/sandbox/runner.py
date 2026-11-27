"""Restricted execution of experiment code.

Code always runs in a *separate process*, never inside the API/worker interpreter:
- fresh working directory per experiment; the script sees only its parameters file
- empty environment (no API keys or DATABASE_URL are inherited), `python -I -B`
- POSIX rlimits: CPU seconds, address space (where the OS enforces it), file size, open files
- wall-clock timeout; the whole process group is killed on expiry
- OS isolation when available:
    macOS  -> sandbox-exec profile: no network, writes only inside the working directory
    Linux  -> bubblewrap (bwrap) if installed: no network, read-only root, private /tmp
    other  -> rlimits only, and the experiment record says so

For a multi-user deployment run workers in a container/VM (gVisor, Firecracker) as well; the
isolation level actually applied is stored with every experiment so results stay honest.

Contract for experiment scripts: read parameters from the JSON file named by $MRL_PARAMS (also
`params.json` in the cwd); write a JSON object to `result.json` in the cwd; print logs freely.
"""
from __future__ import annotations

import json
import os
import platform
import resource
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from app.config import get_settings

MAX_OUTPUT_BYTES = 1_000_000


@dataclass
class SandboxResult:
    status: str  # succeeded | failed | timeout
    exit_code: int | None
    stdout: str
    stderr: str
    result: dict | None
    runtime_seconds: float
    environment: dict = field(default_factory=dict)


def _versions(python: str) -> dict:
    code = ("import json,sys,platform\nout={'python':sys.version.split()[0],'platform':platform.platform()}\n"
            "for m in ('networkx','sympy','ortools','numpy','pysat'):\n"
            "  try:\n    mod=__import__(m); out[m]=getattr(mod,'__version__','?')\n"
            "  except Exception: out[m]=None\nprint(json.dumps(out))")
    try:
        r = subprocess.run([python, "-I", "-c", code], capture_output=True, text=True, timeout=60, env={})
        return json.loads(r.stdout)
    except Exception as e:
        return {"error": f"could not determine versions: {e}"}


_version_cache: dict[str, dict] = {}


def software_versions(python: str) -> dict:
    if python not in _version_cache:
        _version_cache[python] = _versions(python)
    return dict(_version_cache[python])


def _macos_profile(workdir: Path) -> str:
    w = str(workdir).replace('"', '\\"')
    return ("(version 1)(allow default)(deny network*)(deny file-write*)"
            f'(allow file-write* (subpath "{w}") (literal "/dev/null") (literal "/dev/stdout") '
            '(literal "/dev/stderr") (regex #"^/dev/tty"))')


def isolation_command(workdir: Path, argv: list[str]) -> tuple[list[str], str]:
    system = platform.system()
    if system == "Darwin" and shutil.which("sandbox-exec"):
        return ["sandbox-exec", "-p", _macos_profile(workdir), *argv], "macos-sandbox-exec(no-network,write-confined)+rlimits"
    if system == "Linux" and shutil.which("bwrap"):
        py_root = str(Path(sys.prefix).resolve())
        return ["bwrap", "--ro-bind", "/", "/", "--dev", "/dev", "--proc", "/proc", "--tmpfs", "/tmp",
                "--bind", str(workdir), str(workdir), "--ro-bind", py_root, py_root, "--unshare-all",
                "--die-with-parent", "--chdir", str(workdir), *argv], "bubblewrap(no-network,ro-root)+rlimits"
    return argv, "rlimits-only (WARNING: no network/filesystem isolation available on this host)"


def run_python(code: str, params: dict, workdir: Path, *, timeout_s: int, memory_mb: int) -> SandboxResult:
    s = get_settings()
    timeout_s = max(1, min(int(timeout_s), s.sandbox_max_timeout_s))
    python = s.sandbox_python or sys.executable
    workdir = workdir.resolve()
    workdir.mkdir(parents=True, exist_ok=True)
    (workdir / "tmp").mkdir(exist_ok=True)
    (workdir / "main.py").write_text(code)
    (workdir / "params.json").write_text(json.dumps(params, indent=2, sort_keys=True))
    res_file = workdir / "result.json"
    if res_file.exists():
        res_file.unlink()

    env = {"PATH": "/usr/bin:/bin", "HOME": str(workdir), "TMPDIR": str(workdir / "tmp"),
           "MRL_PARAMS": str(workdir / "params.json"), "PYTHONHASHSEED": "0", "OMP_NUM_THREADS": "4",
           "LANG": "C.UTF-8"}
    argv, isolation = isolation_command(workdir, [python, "-I", "-B", "main.py"])
    mem_bytes = memory_mb * 1024 * 1024

    def limits():  # runs in the child before exec
        os.setsid()
        resource.setrlimit(resource.RLIMIT_CPU, (timeout_s * 8 + 5, timeout_s * 8 + 10))  # multi-threaded solvers
        resource.setrlimit(resource.RLIMIT_FSIZE, (200 * 1024 * 1024, 200 * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_NOFILE, (256, 256))
        try:
            resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
        except (ValueError, OSError):
            pass  # macOS does not enforce RLIMIT_AS; recorded below

    t0 = time.monotonic()
    proc = subprocess.Popen(argv, cwd=workdir, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            preexec_fn=limits)
    status = "succeeded"
    try:
        out, err = proc.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        out, err = proc.communicate()
        status = "timeout"
    runtime = time.monotonic() - t0
    if status != "timeout" and proc.returncode != 0:
        status = "failed"
    result = None
    if res_file.exists():
        try:
            result = json.loads(res_file.read_text()[:20_000_000])
        except json.JSONDecodeError as e:
            result = {"_error": f"result.json was not valid JSON: {e}"}

    env_info = software_versions(python)
    env_info.update({
        "isolation": isolation,
        "limits": {"wall_timeout_s": timeout_s, "memory_mb": memory_mb,
                   "memory_enforced": platform.system() != "Darwin", "cpu_seconds": timeout_s * 8 + 5,
                   "max_file_mb": 200, "max_open_files": 256},
        "interpreter": python, "host": platform.node() and "local", "cwd_isolated": True,
    })
    return SandboxResult(status=status, exit_code=proc.returncode, stdout=out.decode(errors="replace")[-MAX_OUTPUT_BYTES:],
                         stderr=err.decode(errors="replace")[-MAX_OUTPUT_BYTES:], result=result,
                         runtime_seconds=round(runtime, 3), environment=env_info)
