import { useEffect, useState } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { api } from './api/client';
import { AppShell } from './components/layout/AppShell';
import { DiscountBands } from './pages/DiscountBands';
import { Executive } from './pages/Executive';
import { NotFound } from './pages/NotFound';
import { Orders } from './pages/Orders';
import { Quality } from './pages/Quality';
import { Scenarios } from './pages/Scenarios';
import { Variance } from './pages/Variance';

export function App() {
  const [apiUp, setApiUp] = useState<boolean | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .health()
      .then((h) => {
        if (!cancelled) setApiUp(h.status === 'ok');
      })
      .catch(() => {
        if (!cancelled) setApiUp(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <AppShell apiUp={apiUp}>
      <Routes>
        <Route path="/" element={<Navigate to="/executive" replace />} />
        <Route path="/executive" element={<Executive />} />
        <Route path="/discount-bands" element={<DiscountBands />} />
        <Route path="/scenarios" element={<Scenarios />} />
        <Route path="/variance" element={<Variance />} />
        <Route path="/orders" element={<Orders />} />
        <Route path="/quality" element={<Quality />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </AppShell>
  );
}
