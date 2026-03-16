import { Canvas, useFrame } from "@react-three/fiber";
import { Environment, Html, OrbitControls } from "@react-three/drei";
import * as THREE from "three";
import { useMemo, useRef } from "react";

import type { LiveData } from "../types";
import type { SceneBuildingType } from "../types";

type Vec3 = [number, number, number];

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

function FlowParticles({
  from,
  to,
  color,
  strength,
}: {
  from: Vec3;
  to: Vec3;
  color: string;
  strength: number;
}) {
  const group = useRef<THREE.Group>(null);
  const curve = useMemo(() => {
    const a = new THREE.Vector3(...from);
    const b = new THREE.Vector3(...to);
    const mid = a.clone().lerp(b, 0.5);
    mid.y += 0.6;
    return new THREE.CatmullRomCurve3([a, mid, b]);
  }, [from, to]);

  const particleCount = clamp(Math.round(4 + strength * 12), 4, 16);
  const phases = useMemo(
    () => new Array(particleCount).fill(0).map((_, i) => i / particleCount),
    [particleCount]
  );

  useFrame((state) => {
    if (!group.current) return;
    const speed = 0.35 + strength * 0.9;
    group.current.children.forEach((child, idx) => {
      const t = (phases[idx] + state.clock.elapsedTime * speed) % 1;
      child.position.copy(curve.getPoint(t));
    });
  });

  return (
    <group ref={group}>
      {phases.map((_, i) => (
        <mesh key={i}>
          <sphereGeometry args={[0.06, 12, 12]} />
          <meshStandardMaterial color={color} emissive={color} emissiveIntensity={1.2} />
        </mesh>
      ))}
    </group>
  );
}

function ValueLabel({ text, color }: { text: string; color: string }) {
  return (
    <Html
      center
      position={[0, 0.5, 0]}
      style={{
        pointerEvents: "none",
        userSelect: "none",
        whiteSpace: "nowrap",
        fontFamily: "var(--font-mono), monospace",
        fontSize: "11px",
        fontWeight: 600,
        color,
        textShadow: "0 0 8px rgba(0,0,0,0.8)",
      }}
    >
      {text}
    </Html>
  );
}

function SolarNode({
  position,
  powerW,
  buildingType,
}: {
  position: Vec3;
  powerW: number;
  buildingType: SceneBuildingType;
}) {
  const isGroundArray = buildingType === "farm";
  const geometry = useMemo(
    () =>
      isGroundArray
        ? new THREE.BoxGeometry(0.7, 0.12, 0.5)
        : new THREE.BoxGeometry(0.5, 0.06, 0.3),
    [isGroundArray]
  );
  return (
    <group position={position}>
      <mesh geometry={geometry} castShadow receiveShadow>
        <meshStandardMaterial color="#fbbf24" emissive="#fbbf24" emissiveIntensity={0.4} />
      </mesh>
      <ValueLabel color="#fbbf24" text={`Solar ${Math.round(powerW)} W`} />
    </group>
  );
}

function BatteryNode({ position, soc }: { position: Vec3; soc: number }) {
  const geometry = useMemo(() => new THREE.CapsuleGeometry(0.18, 0.35, 6, 10), []);
  return (
    <group position={position}>
      <mesh geometry={geometry} castShadow receiveShadow>
        <meshStandardMaterial color="#22d3a0" emissive="#22d3a0" emissiveIntensity={0.35} />
      </mesh>
      <ValueLabel color="#22d3a0" text={`Battery ${Math.round(soc)}%`} />
    </group>
  );
}

function GridPoles({ position }: { position: Vec3 }) {
  const poleH = 0.8;
  const crossY = 0.5;
  return (
    <group position={position}>
      <mesh position={[0, poleH / 2, 0]} castShadow>
        <cylinderGeometry args={[0.04, 0.05, poleH, 8]} />
        <meshStandardMaterial color="#475569" />
      </mesh>
      <mesh position={[0.25, crossY, 0]} rotation={[0, 0, Math.PI / 2]} castShadow>
        <cylinderGeometry args={[0.02, 0.02, 0.5, 6]} />
        <meshStandardMaterial color="#64748b" />
      </mesh>
      <mesh position={[-0.25, crossY, 0]} rotation={[0, 0, Math.PI / 2]} castShadow>
        <cylinderGeometry args={[0.02, 0.02, 0.5, 6]} />
        <meshStandardMaterial color="#64748b" />
      </mesh>
    </group>
  );
}

function GeneratorNode({ position, powerW }: { position: Vec3; powerW: number }) {
  return (
    <group position={position}>
      <mesh position={[0, 0.2, 0]} castShadow>
        <boxGeometry args={[0.4, 0.25, 0.35]} />
        <meshStandardMaterial color="#374151" emissive="#1f2937" />
      </mesh>
      <mesh position={[0.15, 0.38, 0]} castShadow>
        <cylinderGeometry args={[0.08, 0.08, 0.12, 12]} />
        <meshStandardMaterial color="#6b7280" />
      </mesh>
      <ValueLabel color="#94a3b8" text={`Gen ${Math.round(powerW)} W`} />
    </group>
  );
}

function LoadNode({ position, powerW }: { position: Vec3; powerW: number }) {
  return (
    <group position={position}>
      <mesh castShadow>
        <boxGeometry args={[0.35, 0.35, 0.35]} />
        <meshStandardMaterial color="#f472b6" emissive="#f472b6" emissiveIntensity={0.3} />
      </mesh>
      <ValueLabel color="#f472b6" text={`Load ${Math.round(powerW)} W`} />
    </group>
  );
}

function BuildingHouse() {
  return (
    <group>
      <mesh castShadow receiveShadow>
        <boxGeometry args={[1.0, 0.55, 0.95]} />
        <meshStandardMaterial color="#374151" emissive="#1e293b" emissiveIntensity={0.5} />
      </mesh>
      <mesh position={[0, 0.5, 0]} rotation={[0, 0, 0]} castShadow receiveShadow>
        <coneGeometry args={[0.78, 0.5, 4]} />
        <meshStandardMaterial color="#1f2937" />
      </mesh>
      <group position={[0, 0.72, 0.2]}>
        <mesh>
          <boxGeometry args={[0.9, 0.06, 0.5]} />
          <meshStandardMaterial color="#fbbf24" emissive="#fbbf24" emissiveIntensity={0.25} />
        </mesh>
      </group>
      <mesh position={[-0.28, 0.02, 0.48]}>
        <boxGeometry args={[0.18, 0.22, 0.02]} />
        <meshStandardMaterial color="#22d3a0" emissive="#22d3a0" emissiveIntensity={1.2} />
      </mesh>
      <mesh position={[0.28, 0.02, 0.48]}>
        <boxGeometry args={[0.18, 0.22, 0.02]} />
        <meshStandardMaterial color="#60a5fa" emissive="#60a5fa" emissiveIntensity={1.2} />
      </mesh>
      <mesh position={[0, 0.02, 0.48]}>
        <boxGeometry args={[0.2, 0.15, 0.02]} />
        <meshStandardMaterial color="#fcd34d" emissive="#fcd34d" emissiveIntensity={0.8} />
      </mesh>
    </group>
  );
}

function BuildingCommercial() {
  return (
    <group>
      <mesh castShadow receiveShadow>
        <boxGeometry args={[1.4, 0.9, 1.2]} />
        <meshStandardMaterial color="#4b5563" emissive="#374151" emissiveIntensity={0.4} />
      </mesh>
      <mesh position={[0, 0.95, 0]}>
        <boxGeometry args={[1.5, 0.08, 1.35]} />
        <meshStandardMaterial color="#fbbf24" emissive="#fbbf24" emissiveIntensity={0.3} />
      </mesh>
      {[0, 1, 2].map((i) => (
        <mesh key={i} position={[-0.4 + i * 0.4, 0.1, 0.61]}>
          <boxGeometry args={[0.25, 0.35, 0.02]} />
          <meshStandardMaterial color="#93c5fd" emissive="#60a5fa" emissiveIntensity={0.6} />
        </mesh>
      ))}
    </group>
  );
}

function BuildingFarm() {
  return (
    <group>
      <mesh castShadow receiveShadow>
        <boxGeometry args={[1.1, 0.65, 1.0]} />
        <meshStandardMaterial color="#6b4423" emissive="#4a3520" emissiveIntensity={0.4} />
      </mesh>
      <mesh position={[0, 0.6, 0]} castShadow receiveShadow>
        <coneGeometry args={[0.82, 0.45, 4]} />
        <meshStandardMaterial color="#78350f" />
      </mesh>
      <mesh position={[0.35, 0.02, 0.55]}>
        <boxGeometry args={[0.12, 0.1, 0.08]} />
        <meshStandardMaterial color="#854d0e" />
      </mesh>
      <mesh position={[-0.32, 0.02, 0.5]}>
        <sphereGeometry args={[0.08, 8, 8]} />
        <meshStandardMaterial color="#a16207" />
      </mesh>
      <mesh position={[-0.38, 0.02, 0.58]}>
        <sphereGeometry args={[0.06, 6, 6]} />
        <meshStandardMaterial color="#ca8a04" />
      </mesh>
    </group>
  );
}

function Scene({
  data,
  buildingType,
  offGrid,
}: {
  data: LiveData | null;
  buildingType: SceneBuildingType;
  offGrid: boolean;
}) {
  const home: Vec3 = [0, 0, 0];
  const solar: Vec3 = buildingType === "farm" ? [-2.0, 0.15, -1.0] : [-2.2, 0.85, -0.5];
  const battery: Vec3 = [-1.8, -0.6, 1.3];
  const gridOrGen: Vec3 = [2.2, 0.5, -0.2];
  const load: Vec3 = [2.0, -0.7, 1.2];

  const pvW = data?.pv_power_w ?? 0;
  const loadW = data?.load_power_w ?? 0;
  const batteryW = data?.battery_power_w ?? 0;
  const gridW = data?.grid_power_w ?? 0;
  const soc = data?.battery_soc_percent ?? 0;

  const pvToHome = clamp(pvW / 4000, 0, 1);
  const gridToHome = clamp(Math.max(gridW, 0) / 4000, 0, 1);
  const homeToGrid = clamp(Math.max(-gridW, 0) / 4000, 0, 1);
  const homeToLoad = clamp(loadW / 4000, 0, 1);
  const homeToBattery = clamp(Math.max(batteryW, 0) / 4000, 0, 1);
  const batteryToHome = clamp(Math.max(-batteryW, 0) / 4000, 0, 1);

  return (
    <>
      <ambientLight intensity={0.55} />
      <directionalLight position={[4, 6, 2]} intensity={1.1} castShadow />

      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -1.1, 0]} receiveShadow>
        <planeGeometry args={[30, 30]} />
        <meshStandardMaterial color="#0f172a" />
      </mesh>

      <group position={home}>
        {buildingType === "house" && <BuildingHouse />}
        {buildingType === "commercial" && <BuildingCommercial />}
        {buildingType === "farm" && <BuildingFarm />}
      </group>

      <SolarNode position={solar} powerW={pvW} buildingType={buildingType} />
      <BatteryNode position={battery} soc={soc} />
      {offGrid ? (
        <GeneratorNode position={gridOrGen} powerW={gridW} />
      ) : (
        <group position={gridOrGen}>
          <GridPoles position={[0, 0, 0]} />
          <ValueLabel color="#60a5fa" text={`Grid ${Math.round(gridW)} W`} />
        </group>
      )}
      <LoadNode position={load} powerW={loadW} />

      <FlowParticles from={solar} to={home} color="#fbbf24" strength={pvToHome} />
      <FlowParticles from={home} to={load} color="#f472b6" strength={homeToLoad} />
      <FlowParticles from={gridOrGen} to={home} color="#60a5fa" strength={gridToHome} />
      <FlowParticles from={home} to={gridOrGen} color="#93c5fd" strength={homeToGrid} />
      <FlowParticles from={home} to={battery} color="#22d3a0" strength={homeToBattery} />
      <FlowParticles from={battery} to={home} color="#34d399" strength={batteryToHome} />

      <Environment preset="city" />
    </>
  );
}

export default function EnergyScene({
  data,
  buildingType = "house",
  offGrid = false,
}: {
  data: LiveData | null;
  buildingType?: SceneBuildingType;
  offGrid?: boolean;
}) {
  return (
    <div
      style={{
        height: 380,
        borderRadius: "var(--radius)",
        border: "1px solid var(--border)",
        overflow: "hidden",
        background: "radial-gradient(1200px 400px at 50% 0%, #111827 0%, #0b0f14 60%)",
      }}
    >
      <Canvas
        shadows
        camera={{ position: [0, 2.6, 5.2], fov: 45 }}
        gl={{ antialias: true, alpha: true, powerPreference: "high-performance" }}
      >
        <OrbitControls
          enablePan
          enableZoom
          enableRotate
          minDistance={4}
          maxDistance={12}
          maxPolarAngle={Math.PI / 2 - 0.2}
        />
        <Scene data={data} buildingType={buildingType} offGrid={offGrid} />
      </Canvas>
    </div>
  );
}
