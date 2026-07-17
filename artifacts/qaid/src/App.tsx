import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from '@/components/ui/toaster';
import { TooltipProvider } from '@/components/ui/tooltip';
import NotFound from '@/pages/not-found';
import { Route, Switch, Router as WouterRouter } from 'wouter';
import { ThemeProvider } from './components/theme-provider';
import { AnalysisProvider } from './contexts/AnalysisContext';
import { Header } from './components/layout/Header';
import { Landing } from './pages/Landing';
import { Dashboard } from './pages/Dashboard';

const queryClient = new QueryClient();

function Router() {
  return (
    <Switch>
      <Route path="/" component={Landing} />
      <Route path="/dashboard" component={Dashboard} />
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <ThemeProvider defaultTheme="system" storageKey="qaid-theme">
      <QueryClientProvider client={queryClient}>
        <AnalysisProvider>
          <TooltipProvider>
            <WouterRouter base={import.meta.env.BASE_URL.replace(/\/$/, '')}>
              <div className="min-h-screen flex flex-col font-sans">
                <Header />
                <main className="flex-1">
                  <Router />
                </main>
              </div>
            </WouterRouter>
            <Toaster />
          </TooltipProvider>
        </AnalysisProvider>
      </QueryClientProvider>
    </ThemeProvider>
  );
}

export default App;
