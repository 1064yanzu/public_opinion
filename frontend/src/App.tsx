import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import { Dashboard } from './pages/Dashboard';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Analysis } from './pages/Analysis';
import { Advanced } from './pages/Advanced';
import { Monitor } from './pages/Monitor';
import { AiAssistant } from './pages/AiAssistant';
import { Reports } from './pages/Reports';
import { Settings } from './pages/Settings';
import { Spider } from './pages/Spider';
import { BigData } from './pages/BigData';
import { Cases } from './pages/Cases';
import { Manual } from './pages/Manual';

// Protected Route Wrapper
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <div className="loading-screen">Loading...</div>; // Could be a nice spinner
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />

      <Route
        path="/analysis"
        element={
          <ProtectedRoute>
            <Analysis />
          </ProtectedRoute>
        }
      />

      <Route
        path="/advanced"
        element={
          <ProtectedRoute>
            <Advanced />
          </ProtectedRoute>
        }
      />

      <Route
        path="/monitor"
        element={
          <ProtectedRoute>
            <Monitor />
          </ProtectedRoute>
        }
      />

      <Route
        path="/ai-assistant"
        element={
          <ProtectedRoute>
            <AiAssistant />
          </ProtectedRoute>
        }
      />

      <Route
        path="/spider"
        element={
          <ProtectedRoute>
            <Spider />
          </ProtectedRoute>
        }
      />

      <Route
        path="/bigdata"
        element={
          <ProtectedRoute>
            <BigData />
          </ProtectedRoute>
        }
      />

      <Route
        path="/cases"
        element={
          <ProtectedRoute>
            <Cases />
          </ProtectedRoute>
        }
      />

      <Route
        path="/manual"
        element={
          <ProtectedRoute>
            <Manual />
          </ProtectedRoute>
        }
      />

      <Route
        path="/reports"
        element={
          <ProtectedRoute>
            <Reports />
          </ProtectedRoute>
        }
      />

      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <Settings />
          </ProtectedRoute>
        }
      />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
