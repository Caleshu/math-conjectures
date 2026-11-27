"""Job worker. Run standalone with `python -m app.jobs.worker`, or embedded in the API process
(RUN_EMBEDDED_WORKER=true, the default for local development).

Experiment jobs never execute user/agent code in this process: they spawn a sandboxed child
process (see app.sandbox.runner)."""
from __future__ import annotations

import logging
import os
import socket
import threading
import time
import traceback

from app.config import get_settings
from app.jobs import queue
from app.jobs.handlers import HANDLERS, NonRetryable

log = logging.getLogger("mrl.worker")


class Worker:
    def __init__(self, name: str | None = None, job_types: list[str] | None = None):
        self.job_types = job_types
        self.prefix = f"{socket.gethostname()}:{name or 'worker'}"
        self.worker_id = f"{self.prefix}:{os.getpid()}"
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def run_one(self) -> bool:
        jid = queue.claim_next(self.worker_id, self.job_types or list(HANDLERS))
        if not jid:
            return False
        from app.db import session_scope
        from app.models import Job

        with session_scope() as db:
            job = db.get(Job, jid)
            jtype, payload = job.job_type, dict(job.payload or {})
        log.info("job %s (%s) started", jid, jtype)

        stop_beat = threading.Event()

        def beat():
            while not stop_beat.wait(20):
                queue.heartbeat(jid)

        t = threading.Thread(target=beat, daemon=True)
        t.start()
        try:
            def progress(stage: str, info: dict | None = None):
                queue.heartbeat(jid, stage, info)

            result = HANDLERS[jtype](jid, payload, progress)
            queue.complete(jid, result or {})
            log.info("job %s succeeded", jid)
        except NonRetryable as e:
            queue.fail(jid, str(e), retryable=False)
            log.warning("job %s failed (non-retryable): %s", jid, e)
        except Exception as e:
            queue.fail(jid, f"{type(e).__name__}: {e}\n{traceback.format_exc(limit=6)}", retryable=True)
            log.exception("job %s failed", jid)
        finally:
            stop_beat.set()
        return True

    def loop(self) -> None:
        n = queue.requeue_interrupted_on_startup(self.prefix)
        if n:
            log.info("requeued %d interrupted job(s)", n)
        poll = get_settings().worker_poll_seconds
        last_stale_check = 0.0
        while not self._stop.is_set():
            try:
                if time.monotonic() - last_stale_check > 60:
                    queue.requeue_stale()
                    last_stale_check = time.monotonic()
                if not self.run_one():
                    self._stop.wait(poll)
            except Exception:
                log.exception("worker loop error")
                self._stop.wait(5)

    def start_background(self) -> None:
        self._thread = threading.Thread(target=self.loop, name="mrl-worker", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    Worker("standalone").loop()


if __name__ == "__main__":
    main()
