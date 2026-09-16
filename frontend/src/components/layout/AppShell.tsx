import { useState } from 'react';
import { NavLink } from 'react-router-dom';

const NAV = [
  { to: '/executive', label: 'Executive', index: '01' },
  { to: '/discount-bands', label: 'Discount Bands', index: '02' },
  { to: '/scenarios', label: 'Scenarios', index: '03' },
  { to: '/variance', label: 'Variance', index: '04' },
  { to: '/orders', label: 'Orders', index: '05' },
  { to: '/quality', label: 'Data Quality', index: '06' },
];

interface AppShellProps {
  children: React.ReactNode;
  apiUp: boolean | null;
}

export function AppShell({ children, apiUp }: AppShellProps) {
  const [open, setOpen] = useState(false);

  return (
    <div className="app-shell">
      <div
        className={`scrim${open ? ' visible' : ''}`}
        onClick={() => setOpen(false)}
        aria-hidden="true"
      />
      <aside className={`sidebar${open ? ' open' : ''}`} aria-label="Primary">
        <div className="sidebar-brand">
          <h1>Margin Map</h1>
          <p>Profitability Intelligence</p>
        </div>
        <div className="sidebar-status" role="status">
          <span className={`dot${apiUp === false ? ' down' : ''}`} aria-hidden="true" />
          {apiUp === null ? 'Checking API…' : apiUp ? 'API connected · read-only' : 'API unreachable'}
        </div>
        <nav className="sidebar-nav" aria-label="Analytical sections">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => (isActive ? 'active' : '')}
              onClick={() => setOpen(false)}
            >
              <span className="nav-index">{item.index}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-foot">
          Frozen analytical outputs
          <br />
          AO-01 – AO-06 · read-only
        </div>
      </aside>
      <div className="main-column">
        <div className="mobile-bar">
          <button
            type="button"
            className="menu-toggle"
            aria-label="Toggle navigation"
            onClick={() => setOpen((o) => !o)}
          >
            ☰
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
