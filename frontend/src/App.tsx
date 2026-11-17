import React from 'react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { AuthProvider } from './lib/authContext';
import { ThemeProvider } from './lib/themeContext';
import { Shell } from './components/layout/Shell';

import { CommandCenter } from './pages/CommandCenter';
import { TriageQueue } from './pages/TriageQueue';
import { TicketDetailPage } from './pages/TicketDetail';
import { SLARiskForecast } from './pages/SLARiskForecast';
import { FrictionMonitor } from './pages/FrictionMonitor';
import { ThemeExplorer } from './pages/ThemeExplorer';
import { Playground } from './pages/Playground';
import { ModelLab } from './pages/ModelLab';
import { Settings } from './pages/Settings';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 10000,
      retry: 1,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<Shell />}>
                <Route index element={<CommandCenter />} />
                <Route path="triage" element={<TriageQueue />} />
                <Route path="tickets/:id" element={<TicketDetailPage />} />
                <Route path="sla-risk" element={<SLARiskForecast />} />
                <Route path="friction" element={<FrictionMonitor />} />
                <Route path="themes" element={<ThemeExplorer />} />
                <Route path="playground" element={<Playground />} />
                <Route path="models" element={<ModelLab />} />
                <Route path="settings" element={<Settings />} />
              </Route>
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

export default App;
