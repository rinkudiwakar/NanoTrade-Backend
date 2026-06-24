import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Auth } from '@/pages/Auth';
import { Dashboard } from '@/pages/Dashboard';
import { LandingPage } from '@/pages/LandingPage';
import { useUserStore } from '@/store/userStore';

export default function App() {
  const { session, isInitialized, initializeAuth } = useUserStore();

  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  if (!isInitialized) {
    return <div className="flex h-screen items-center justify-center bg-background text-foreground">Loading...</div>;
  }

  return (
    <BrowserRouter>
      <div className="dark">
        <Routes>
          <Route 
            path="/" 
            element={<LandingPage />} 
          />
          <Route 
            path="/dashboard" 
            element={session ? <Dashboard /> : <Navigate to="/auth" />} 
          />
          <Route 
            path="/auth" 
            element={!session ? <Auth /> : <Navigate to="/dashboard" />} 
          />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
