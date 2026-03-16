import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useLiveData } from "../hooks/useLiveData";

export default function ShareDashboard() {
  const { token } = useParams<{ token: string }>();
  const [valid, setValid] = useState<boolean | null>(null);
  const { data, connected } = useLiveData();

  useEffect(() => {
    if (!token) {
      setValid(false);
      return;
    }
    fetch(`/api/share/verify/${token}`)
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((body) => setValid(body.valid === true))
      .catch(() => setValid(false));
  }, [token]);

  if (valid === null) return <p style={{ color: "var(--text-muted)" }}>Checking…</p>;
  if (!valid) {
    return (
      <div style={{ textAlign: "center", padding: "2rem" }}>
        <p style={{ color: "var(--danger)" }}>Invalid or expired share link.</p>
      </div>
    );
  }

  return (
    <div style={{ padding: "1.5rem", maxWidth: "900px", margin: "0 auto" }}>
      <div style={{ marginBottom: "1rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1 style={{ margin: 0, fontSize: "1.25rem", color: "var(--accent)" }}>Pax Nebulus · Shared view</h1>
        <span style={{ fontSize: "0.8rem", color: connected ? "var(--accent)" : "var(--text-muted)" }}>
          {connected ? "● Live" : "○ Connecting…"}
        </span>
      </div>
      {!data && (
        <p style={{ color: "var(--text-muted)" }}>Waiting for data…</p>
      )}
      {data && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))",
            gap: "1rem",
          }}
        >
          <div
            style={{
              background: "var(--bg-card)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius)",
              padding: "1rem",
            }}
          >
            <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>PV</div>
            <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--pv)" }}>
              {data.pv_power_w.toFixed(0)} W
            </div>
          </div>
          <div
            style={{
              background: "var(--bg-card)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius)",
              padding: "1rem",
            }}
          >
            <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>Battery</div>
            <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--battery)" }}>
              {data.battery_soc_percent.toFixed(0)}%
            </div>
          </div>
          <div
            style={{
              background: "var(--bg-card)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius)",
              padding: "1rem",
            }}
          >
            <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>Grid</div>
            <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--grid)" }}>
              {data.grid_power_w.toFixed(0)} W
            </div>
          </div>
          <div
            style={{
              background: "var(--bg-card)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius)",
              padding: "1rem",
            }}
          >
            <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>Load</div>
            <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--load)" }}>
              {data.load_power_w.toFixed(0)} W
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
