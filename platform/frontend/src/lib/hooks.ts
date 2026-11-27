"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";
import type { Job } from "./types";

/** Fetch `path`; optionally re-poll every `pollMs` while `shouldPoll(data)` is true. */
export function useApi<T>(path: string | null, opts: { pollMs?: number; shouldPoll?: (d: T) => boolean } = {}) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState<boolean>(Boolean(path));
  const optsRef = useRef(opts);
  optsRef.current = opts;

  const load = useCallback(async (quiet = false) => {
    if (!path) return;
    if (!quiet) setLoading(true);
    try {
      const d = await api.get<T>(path);
      setData(d);
      setError(null);
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }, [path]);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    const { pollMs, shouldPoll } = optsRef.current;
    if (!pollMs || !data) return;
    if (shouldPoll && !shouldPoll(data)) return;
    const t = setTimeout(() => load(true), pollMs);
    return () => clearTimeout(t);
  }, [data, load]);

  return { data, error, loading, reload: load, setData };
}

/** Poll a job until it reaches a terminal state. */
export function useJob(jobId: string | null, onDone?: (j: Job) => void) {
  const done = useRef(onDone);
  done.current = onDone;
  const { data, error } = useApi<Job>(jobId ? `/api/jobs/${jobId}` : null, {
    pollMs: 1500,
    shouldPoll: (j) => j.status === "queued" || j.status === "running",
  });
  const fired = useRef<string | null>(null);
  useEffect(() => {
    if (data && (data.status === "succeeded" || data.status === "failed") && fired.current !== data.id) {
      fired.current = data.id;
      done.current?.(data);
    }
  }, [data]);
  return { job: data, error };
}
