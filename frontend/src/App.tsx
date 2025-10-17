import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, theme } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { useAuthStore } from './store/authStore';
import LoginPage from './pages/LoginPage';
import Dashboard from './pages/Dashboard';
import DatasetsPage from './pages/DatasetsPage';
import DatasetDetail from './pages/DatasetDetail';
import AnalyticsPage from './pages/AnalyticsPage';
import SpiderPage from './pages/SpiderPage';
import WordCloudPage from './pages/WordCloudPage';
import AIAssistantPage from './pages/AIAssistantPage';
import Layout from './components/Layout';

const App: React.FC = () => {
  const token = useAuthStore((state) => state.token);

  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: theme.defaultAlgorithm,
        token: {
          colorPrimary: '#6366f1',
          borderRadius: 12,
          fontSize: 14,
        },
      }}
    >
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          {token ? (
            <Route path="/" element={<Layout />}>
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="datasets" element={<DatasetsPage />} />
              <Route path="datasets/:id" element={<DatasetDetail />} />
              <Route path="analytics/:id" element={<AnalyticsPage />} />
              <Route path="spider" element={<SpiderPage />} />
              <Route path="wordcloud" element={<WordCloudPage />} />
              <Route path="ai" element={<AIAssistantPage />} />
            </Route>
          ) : (
            <Route path="*" element={<Navigate to="/login" replace />} />
          )}
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
};

export default App;
