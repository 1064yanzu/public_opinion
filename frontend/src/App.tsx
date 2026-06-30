import React, { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import { Loading } from '@/components/common/Loading';

// 代码分割：按路由懒加载页面组件
const Dashboard = lazy(() => import('./pages/Dashboard').then(m => ({ default: m.Dashboard })));
const Login = lazy(() => import('./pages/Login').then(m => ({ default: m.Login })));
const Register = lazy(() => import('./pages/Register').then(m => ({ default: m.Register })));
const Monitor = lazy(() => import('./pages/Monitor').then(m => ({ default: m.Monitor })));
const AiAssistant = lazy(() => import('./pages/AiAssistant').then(m => ({ default: m.AiAssistant })));
const Reports = lazy(() => import('./pages/Reports').then(m => ({ default: m.Reports })));
const Settings = lazy(() => import('./pages/Settings').then(m => ({ default: m.Settings })));
const Spider = lazy(() => import('./pages/Spider').then(m => ({ default: m.Spider })));
const BigData = lazy(() => import('./pages/BigData').then(m => ({ default: m.BigData })));
const Manual = lazy(() => import('./pages/Manual').then(m => ({ default: m.Manual })));

// Protected Route Wrapper
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <Loading fullScreen text="正在校验登录状态..." />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

function App() {
  return (
    <Suspense fallback={<Loading fullScreen text="正在加载页面..." />}>
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
    </Suspense>
  );
}

export default App;
