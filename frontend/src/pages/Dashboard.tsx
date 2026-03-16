import { useEffect, useState } from "react";
import { useLiveData } from "../hooks/useLiveData";
import EnergyScene from "../components/EnergyScene";
import type { SceneBuildingType } from "../types";

function Card({
  title,
  value,
  unit,
  sub,
  color,
}: {
  title: string;
  value: number | string;
  unit: string;
  sub?: string;
  color: string;
}) {
  return (
    <div
      style={{
        background: "var(--bg-card)",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius)",
        padding: "1.25rem",
        minWidth: "140px",
      }}
    >
      <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: "0.25rem" }}>
        {title}
      </div>
      <div style={{ fontSize: "1.75rem", fontWeight: 700, fontFamily: "var(--font-mono)", color }}>
        {typeof value === "number" ? value.toFixed(1) : value} {unit}
      </div>
      {sub && (
        <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
          {sub}
        </div>
      )}
    </div>
  );
}

export default function Dashboard() {
  const { data, connected } = useLiveData();
  const [buildingType, setBuildingType] = useState<SceneBuildingType>("house");
  const [offGrid, setOffGrid] = useState(false);

  useEffect(() => {
    fetch("/api/config")
      .then((r) => (r.ok ? r.json() : null))
      .then((cfg: { scene_building_type?: SceneBuildingType; scene_off_grid?: boolean } | null) => {
        if (cfg?.scene_building_type) setBuildingType(cfg.scene_building_type);
        if (cfg?.scene_off_grid != null) setOffGrid(cfg.scene_off_grid);
      })
      .catch(() => {});
  }, []);

  return (
    <div>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "1.5rem",
        }}
      >
        <h1 style={{ margin: 0, fontSize: "1.5rem", fontWeight: 500 }}>Live dashboard</h1>
        <span
          style={{
            fontSize: "0.8rem",
            color: connected ? "var(--accent)" : "var(--text-muted)",
          }}
        >
          {connected ? "● Live" : "○ Connecting…"}
        </span>
      </div>

      {!data && !connected && (
        <p style={{ color: "var(--text-muted)" }}>
          Waiting for inverter data. Check connection and settings.
        </p>
      )}

      <div style={{ marginBottom: "1rem" }}>
        <EnergyScene
          data={data}
          buildingType={buildingType}
          offGrid={offGrid}
        />
      </div>

      {data && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))",
            gap: "1rem",
          }}
        >
          <Card
            title="PV power"
            value={data.pv_power_w}
            unit="W"
            sub={`${data.pv_voltage_v.toFixed(1)} V · ${data.pv_current_a.toFixed(1)} A`}
            color="var(--pv)"
          />
          <Card
            title="Battery SoC"
            value={data.battery_soc_percent}
            unit="%"
            sub={`${data.battery_power_w >= 0 ? "Charging" : "Discharging"} ${Math.abs(data.battery_power_w).toFixed(0)} W`}
            color="var(--battery)"
          />
          <Card
            title="Grid"
            value={data.grid_power_w}
            unit="W"
            sub={`${data.grid_voltage_v.toFixed(0)} V · ${data.grid_frequency_hz.toFixed(2)} Hz`}
            color="var(--grid)"
          />
          <Card
            title="Load"
            value={data.load_power_w}
            unit="W"
            color="var(--load)"
          />
          {(data.inverter_temperature_c != null || data.battery_temperature_c != null) && (
            <Card
              title="Temperature"
              value={
                data.inverter_temperature_c != null
                  ? data.inverter_temperature_c
                  : data.battery_temperature_c ?? 0
              }
              unit="°C"
              sub={data.battery_temperature_c != null ? `Batt: ${data.battery_temperature_c}°C` : undefined}
              color="var(--text-muted)"
            />
          )}
        </div>
      )}

      {data?.status_message && (
        <p style={{ marginTop: "1.5rem", fontSize: "0.85rem", color: "var(--text-muted)" }}>
          {data.status_message} · Mode: {data.mode || "—"}
        </p>
      )}
    </div>
  );
}
