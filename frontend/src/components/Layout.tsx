import { Outlet, Link } from "react-router-dom";

export default function Layout() {
  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <header
        style={{
          padding: "0.75rem 1.5rem",
          borderBottom: "1px solid var(--border)",
          display: "flex",
          alignItems: "center",
          gap: "1.5rem",
          background: "var(--bg-card)",
        }}
      >
        <Link
          to="/"
          style={{
            color: "var(--accent)",
            textDecoration: "none",
            fontWeight: 700,
            fontSize: "1.25rem",
          }}
        >
          Pax Nebulus
        </Link>
        <nav style={{ display: "flex", gap: "1rem" }}>
          <Link to="/" style={{ color: "var(--text-muted)", textDecoration: "none" }}>
            Dashboard
          </Link>
          <Link to="/settings" style={{ color: "var(--text-muted)", textDecoration: "none" }}>
            Settings
          </Link>
        </nav>
      </header>
      <main style={{ flex: 1, padding: "1.5rem" }}>
        <Outlet />
      </main>
    </div>
  );
}
