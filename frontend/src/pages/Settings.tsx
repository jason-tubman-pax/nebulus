import { useEffect, useState } from "react";
import type { SystemConfig, TunnelState, WifiNetwork, StorageInfo, PersistenceConfig } from "../types";

const API = "/api";

export default function Settings() {
  const [config, setConfig] = useState<SystemConfig | null>(null);
  const [tunnel, setTunnel] = useState<TunnelState | null>(null);
  const [storageInfo, setStorageInfo] = useState<StorageInfo | null>(null);
  const [wifiNetworks, setWifiNetworks] = useState<WifiNetwork[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch(`${API}/config`).then((r) => r.json()),
      fetch(`${API}/tunnel`).then((r) => r.json()),
      fetch(`${API}/storage`).then((r) => r.json()),
    ]).then(([cfg, tun, stor]) => {
      setConfig(cfg);
      setTunnel(tun);
      setStorageInfo(stor);
      setLoading(false);
    });
  }, []);

  const refreshStorage = () => {
    fetch(`${API}/storage`).then((r) => r.json()).then(setStorageInfo);
  };

  const loadWifi = () => {
    fetch(`${API}/wifi/scan`)
      .then((r) => r.json())
      .then(setWifiNetworks)
      .catch(() => setWifiNetworks([]));
  };

  const startTunnel = () => {
    fetch(`${API}/tunnel/start`, { method: "POST" })
      .then((r) => r.json())
      .then(setTunnel);
  };

  const stopTunnel = () => {
    fetch(`${API}/tunnel/stop`, { method: "POST" })
      .then((r) => r.json())
      .then(setTunnel);
  };

  const regenerateToken = () => {
    fetch(`${API}/tunnel/share-token`, { method: "POST" })
      .then((r) => r.json())
      .then((body: { share_token: string }) => {
        if (config) setConfig({ ...config, share_token: body.share_token });
      });
  };

  if (loading || !config) return <p style={{ color: "var(--text-muted)" }}>Loading…</p>;

  return (
    <div>
      <h1 style={{ margin: "0 0 1.5rem", fontSize: "1.5rem", fontWeight: 500 }}>Settings</h1>

      <section
        style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius)",
          padding: "1.25rem",
          marginBottom: "1rem",
        }}
      >
        <h2 style={{ margin: "0 0 0.75rem", fontSize: "1rem" }}>Inverter connection</h2>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem", alignItems: "center" }}>
          <label>
            Driver:{" "}
            <select
              value={config.inverter.driver}
              onChange={(e) =>
                setConfig({
                  ...config,
                  inverter: { ...config.inverter, driver: e.target.value },
                })
              }
            >
              <option value="deye">Deye</option>
              <option value="sofar">Sofar</option>
              <option value="generic">Generic Modbus</option>
            </select>
          </label>
          <label>
            Type:{" "}
            <select
              value={config.inverter.connection_type}
              onChange={(e) =>
                setConfig({
                  ...config,
                  inverter: {
                    ...config.inverter,
                    connection_type: e.target.value as "tcp" | "rtu",
                  },
                })
              }
            >
              <option value="tcp">TCP</option>
              <option value="rtu">RTU (serial)</option>
            </select>
          </label>
          {config.inverter.connection_type === "tcp" && (
            <>
              <input
                type="text"
                placeholder="Host"
                value={config.inverter.host ?? ""}
                onChange={(e) =>
                  setConfig({
                    ...config,
                    inverter: { ...config.inverter, host: e.target.value || undefined },
                  })
                }
              />
              <input
                type="number"
                placeholder="Port"
                value={config.inverter.port}
                onChange={(e) =>
                  setConfig({
                    ...config,
                    inverter: { ...config.inverter, port: parseInt(e.target.value, 10) || 502 },
                  })
                }
              />
            </>
          )}
          {config.inverter.connection_type === "rtu" && (
            <input
              type="text"
              placeholder="Serial port (e.g. /dev/ttyUSB0)"
              value={config.inverter.serial_port ?? ""}
              onChange={(e) =>
                setConfig({
                  ...config,
                  inverter: { ...config.inverter, serial_port: e.target.value || undefined },
                })
              }
            />
          )}
        </div>
        <button
          type="button"
          onClick={() =>
            fetch(`${API}/config`, {
              method: "PUT",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(config),
            })
          }
          style={{ marginTop: "0.75rem" }}
        >
          Save
        </button>
      </section>

      <section
        style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius)",
          padding: "1.25rem",
          marginBottom: "1rem",
        }}
      >
        <h2 style={{ margin: "0 0 0.75rem", fontSize: "1rem" }}>Public share link</h2>
        <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginBottom: "0.75rem" }}>
          Expose the dashboard via a free tunnel (Cloudflare). Generate a token, then start the
          tunnel. Anyone with the link can view the read-only dashboard.
        </p>
        <div style={{ marginBottom: "0.75rem" }}>
          Share token: <code style={{ background: "var(--bg-elevated)", padding: "0.2rem 0.5rem" }}>{config.share_token || "—"}</code>
          <button type="button" onClick={regenerateToken} style={{ marginLeft: "0.5rem" }}>
            Regenerate
          </button>
        </div>
        {config.share_token && (
          <div style={{ marginBottom: "0.75rem", fontSize: "0.9rem" }}>
            Share URL (after starting tunnel):{" "}
            <code style={{ background: "var(--bg-elevated)", padding: "0.2rem 0.5rem" }}>
              {typeof window !== "undefined" ? `${window.location.origin}/share/${config.share_token}` : ""}
            </code>
          </div>
        )}
        {tunnel && (
          <div style={{ marginBottom: "0.75rem" }}>
            Tunnel: {tunnel.enabled ? "Running" : "Stopped"}
            {tunnel.share_url && <span> · {tunnel.share_url}</span>}
            {tunnel.error && <span style={{ color: "var(--danger)" }}> · {tunnel.error}</span>}
          </div>
        )}
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <button type="button" onClick={startTunnel} disabled={tunnel?.enabled}>
            Start tunnel
          </button>
          <button type="button" onClick={stopTunnel} disabled={!tunnel?.enabled}>
            Stop tunnel
          </button>
        </div>
      </section>

      <section
        style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius)",
          padding: "1.25rem",
          marginBottom: "1rem",
        }}
      >
        <h2 style={{ margin: "0 0 0.75rem", fontSize: "1rem" }}>Dashboard history & storage</h2>
        <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginBottom: "0.75rem" }}>
          Persist live data for charts. Limits and rollover keep usage within available disk.
        </p>
        {storageInfo && (
          <>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))", gap: "0.75rem", marginBottom: "1rem" }}>
              <div style={{ padding: "0.5rem", background: "var(--bg-elevated)", borderRadius: "var(--radius)" }}>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Disk available</div>
                <div style={{ fontFamily: "var(--font-mono)", fontWeight: 600 }}>
                  {storageInfo.disk_available_mb != null ? `${storageInfo.disk_available_mb.toFixed(0)} MB` : "—"}
                </div>
              </div>
              <div style={{ padding: "0.5rem", background: "var(--bg-elevated)", borderRadius: "var(--radius)" }}>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>History DB size</div>
                <div style={{ fontFamily: "var(--font-mono)", fontWeight: 600 }}>{storageInfo.db_size_mb.toFixed(2)} MB</div>
              </div>
              <div style={{ padding: "0.5rem", background: "var(--bg-elevated)", borderRadius: "var(--radius)" }}>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Samples stored</div>
                <div style={{ fontFamily: "var(--font-mono)", fontWeight: 600 }}>{storageInfo.row_count.toLocaleString()}</div>
              </div>
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "1rem", alignItems: "flex-start" }}>
              <label style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <input
                  type="checkbox"
                  checked={storageInfo.config.enabled}
                  onChange={(e) =>
                    setStorageInfo({
                      ...storageInfo,
                      config: { ...storageInfo.config, enabled: e.target.checked },
                    })
                  }
                />
                Enable history
              </label>
              <label>
                Max storage (MB):{" "}
                <input
                  type="number"
                  min={1}
                  max={storageInfo.disk_available_mb != null ? Math.floor(storageInfo.disk_available_mb) : 10000}
                  step={10}
                  value={storageInfo.config.max_storage_mb}
                  onChange={(e) =>
                    setStorageInfo({
                      ...storageInfo,
                      config: {
                        ...storageInfo.config,
                        max_storage_mb: Math.max(1, parseFloat(e.target.value) || 100),
                      },
                    })
                  }
                />
                {storageInfo.disk_available_mb != null && (
                  <span style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginLeft: "0.25rem" }}>
                    (max {Math.floor(storageInfo.disk_available_mb)})
                  </span>
                )}
              </label>
              <label>
                Sample every (sec):{" "}
                <input
                  type="number"
                  min={10}
                  max={3600}
                  value={storageInfo.config.sample_interval_seconds}
                  onChange={(e) =>
                    setStorageInfo({
                      ...storageInfo,
                      config: {
                        ...storageInfo.config,
                        sample_interval_seconds: Math.max(10, parseInt(e.target.value, 10) || 60),
                      },
                    })
                  }
                />
              </label>
              <label>
                Rollover:{" "}
                <select
                  value={storageInfo.config.rollover_strategy}
                  onChange={(e) =>
                    setStorageInfo({
                      ...storageInfo,
                      config: {
                        ...storageInfo.config,
                        rollover_strategy: e.target.value as "delete_oldest" | "keep_days",
                      },
                    })
                  }
                >
                  <option value="delete_oldest">Delete oldest when full</option>
                  <option value="keep_days">Keep last N days</option>
                </select>
              </label>
              {storageInfo.config.rollover_strategy === "keep_days" && (
                <label>
                  Keep days:{" "}
                  <input
                    type="number"
                    min={1}
                    max={365}
                    value={storageInfo.config.keep_days ?? 30}
                    onChange={(e) =>
                      setStorageInfo({
                        ...storageInfo,
                        config: {
                          ...storageInfo.config,
                          keep_days: Math.max(1, parseInt(e.target.value, 10) || 30),
                        },
                      })
                    }
                  />
                </label>
              )}
            </div>
            <button
              type="button"
              onClick={() => {
                fetch(`${API}/storage/config`, {
                  method: "PUT",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify(storageInfo.config),
                }).then(() => {
                  if (config) setConfig({ ...config, persistence: storageInfo.config });
                  refreshStorage();
                });
              }}
              style={{ marginTop: "0.75rem" }}
            >
              Save storage settings
            </button>
          </>
        )}
      </section>

      <section
        style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius)",
          padding: "1.25rem",
        }}
      >
        <h2 style={{ margin: "0 0 0.75rem", fontSize: "1rem" }}>WiFi</h2>
        <button type="button" onClick={loadWifi} style={{ marginBottom: "0.75rem" }}>
          Scan networks
        </button>
        {wifiNetworks.length > 0 && (
          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            {wifiNetworks.slice(0, 10).map((n) => (
              <li
                key={n.ssid}
                style={{
                  padding: "0.5rem 0",
                  borderBottom: "1px solid var(--border)",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <span>{n.ssid}</span>
                <span style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
                  {n.signal_strength}% {n.secured ? "· Secured" : ""}
                </span>
              </li>
            ))}
          </ul>
        )}
        <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginTop: "0.75rem" }}>
          To connect, use nmcli on the device or connect via system settings. API connect can be
          added for headless setup.
        </p>
      </section>
    </div>
  );
}
