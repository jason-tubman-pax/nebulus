import { useEffect, useState } from "react";
import type { LiveData } from "../types";

const WS_BASE = (() => {
  const { protocol, host } = window.location;
  const wsProtocol = protocol === "https:" ? "wss:" : "ws:";
  return `${wsProtocol}//${host}`;
})();

export function useLiveData() {
  const [data, setData] = useState<LiveData | null>(null);
  const [connected, setConnected] = useState(false);

  // Fetch latest on mount (works with seeded history when no inverter is connected)
  useEffect(() => {
    fetch("/api/live")
      .then((r) => (r.ok ? r.json() : null))
      .then((payload: LiveData | null) => {
        if (payload) setData(payload);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    const ws = new WebSocket(`${WS_BASE}/api/live/ws`);
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (ev) => {
      try {
        const payload = JSON.parse(ev.data) as LiveData;
        setData(payload);
      } catch {
        // ignore
      }
    };
    return () => ws.close();
  }, []);

  return { data, connected };
}
