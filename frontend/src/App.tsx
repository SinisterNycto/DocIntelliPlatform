import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ClerkProvider, SignedIn, SignedOut, RedirectToSignIn } from '@clerk/clerk-react';
import { dark } from '@clerk/themes';
import Dashboard from './pages/Dashboard';
import ProjectView from './pages/ProjectView';
import LandingPage from './pages/LandingPage';
import { useTheme } from './components/ThemeProvider';

const PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

if (!PUBLISHABLE_KEY) {
  console.error("Missing VITE_CLERK_PUBLISHABLE_KEY in .env");
}

function App() {
  const { theme } = useTheme();

  // Determine if we should use the dark baseTheme for Clerk
  const isDark = theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);

  if (!PUBLISHABLE_KEY) {
    return (
      <div className="min-h-screen bg-[#111316] text-[#E4E7EB] flex items-center justify-center p-4">
        <div className="text-center space-y-4 max-w-md border border-[#2D3139] p-8 rounded-lg shadow-xl">
          <h1 className="text-xl font-semibold">Missing API Key</h1>
          <p className="text-[#8B949E]">
            Please restart your Vite development server so it can load the new <code className="text-[#6B8E85]">.env</code> file.
          </p>
          <p className="text-[#8B949E] text-sm">
            Also ensure you have pasted your Clerk Publishable Key into the <code className="text-[#6B8E85]">frontend/.env</code> file!
          </p>
        </div>
      </div>
    );
  }

  return (
    <ClerkProvider 
      publishableKey={PUBLISHABLE_KEY}
      appearance={{
        baseTheme: isDark ? dark : undefined,
        variables: {
          colorPrimary: '#6B8E85',
        },
        elements: {
          card: 'shadow-xl',
          formButtonPrimary: 'font-bold uppercase tracking-widest',
        }
      }}
    >
      <Router>
        <div className="min-h-screen bg-void font-sans text-text-data transition-colors duration-300">
          <Routes>
            <Route path="/" element={<LandingPage />} />
            

            <Route 
              path="/dashboard" 
              element={
                <>
                  <SignedIn>
                    <Dashboard />
                  </SignedIn>
                  <SignedOut>
                    <RedirectToSignIn />
                  </SignedOut>
                </>
              } 
            />
            
            <Route 
              path="/project/:id" 
              element={
                <>
                  <SignedIn>
                    <ProjectView />
                  </SignedIn>
                  <SignedOut>
                    <RedirectToSignIn />
                  </SignedOut>
                </>
              } 
            />
            
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </div>
      </Router>
    </ClerkProvider>
  );
}

export default App;
