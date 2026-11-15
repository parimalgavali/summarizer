import { useEffect, useState, type FormEvent } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { setApiKey, UNAUTHORIZED_EVENT } from "../lib/api";

/** Asks for the backend access key whenever the API answers 401. */
export default function AccessKeyGate() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [key, setKey] = useState("");

  useEffect(() => {
    const show = () => setOpen(true);
    window.addEventListener(UNAUTHORIZED_EVENT, show);
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, show);
  }, []);

  if (!open) return null;

  const submit = (event: FormEvent) => {
    event.preventDefault();
    const trimmed = key.trim();
    if (!trimmed) return;
    setApiKey(trimmed);
    setKey("");
    setOpen(false);
    queryClient.resetQueries();
  };

  return (
    <div className="access-gate" role="dialog" aria-modal="true" aria-labelledby="access-gate-title">
      <form className="access-gate-card" onSubmit={submit}>
        <h2 id="access-gate-title">Access key required</h2>
        <p>Enter the API key for this workbench. It is saved in this browser.</p>
        <input
          type="password"
          value={key}
          onChange={(e) => setKey(e.target.value)}
          placeholder="API key"
          aria-label="API key"
          autoComplete="current-password"
          autoFocus
        />
        <button type="submit" className="primary-action" disabled={!key.trim()}>
          Unlock
        </button>
      </form>
    </div>
  );
}
