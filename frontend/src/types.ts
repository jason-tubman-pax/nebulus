export interface LiveData {
  timestamp: string;
  pv_power_w: number;
  pv_voltage_v: number;
  pv_current_a: number;
  battery_soc_percent: number;
  battery_power_w: number;
  battery_voltage_v: number;
  battery_current_a: number;
  battery_temperature_c?: number;
  grid_power_w: number;
  grid_voltage_v: number;
  grid_frequency_hz: number;
  load_power_w: number;
  inverter_temperature_c?: number;
  status_message: string;
  mode: string;
}

export interface InverterConnectionConfig {
  driver: string;
  connection_type: "tcp" | "rtu";
  host?: string;
  port: number;
  serial_port?: string;
  baudrate: number;
  slave_id: number;
  timeout_seconds: number;
}

export interface PersistenceConfig {
  enabled: boolean;
  max_storage_mb: number;
  sample_interval_seconds: number;
  rollover_strategy: "delete_oldest" | "keep_days";
  keep_days?: number;
}

export interface SystemConfig {
  inverter: InverterConnectionConfig;
  persistence?: PersistenceConfig;
  share_token?: string;
  hostname?: string;
}

export interface StorageInfo {
  disk_available_mb: number | null;
  db_size_mb: number;
  row_count: number;
  config: PersistenceConfig;
}

export interface TunnelState {
  enabled: boolean;
  share_url?: string;
  tunnel_type: string;
  error?: string;
}

export interface WifiNetwork {
  ssid: string;
  signal_strength: number;
  secured: boolean;
  connected: boolean;
}
