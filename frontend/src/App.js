import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './context/AuthContext';
import Layout from './components/layout/Layout';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ForgotPasswordPage from './pages/ForgotPasswordPage';
import DashboardPage from './pages/DashboardPage';
import DailyCardPage from './pages/DailyCardPage';
import LeaderboardPage from './pages/LeaderboardPage';
import ProfilePage from './pages/ProfilePage';
import SupervisorPage from './pages/SupervisorPage';
import AdminUsersPage from './pages/AdminUsersPage';
import AdminHalqasPage from './pages/AdminHalqasPage';
import AdminAnalyticsPage from './pages/AdminAnalyticsPage';
import AdminSettingsPage from './pages/AdminSettingsPage';
import HomePage from './pages/HomePage';
import './styles/global.css';

function ProtectedRoute({ children, roles }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="loading"><div className="spinner" /></div>;
  if (!user) return <Navigate to="/login" />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/dashboard" />;
  return children;
}

function PublicRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="loading"><div className="spinner" /></div>;
  if (user) return <Navigate to="/dashboard" />;
  return children;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<PublicRoute><HomePage /></PublicRoute>} />
      <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
      <Route path="/register" element={<PublicRoute><RegisterPage /></PublicRoute>} />
      <Route path="/forgot-password" element={<PublicRoute><ForgotPasswordPage /></PublicRoute>} />

      <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/daily-card" element={<DailyCardPage />} />
        <Route path="/leaderboard" element={
          <ProtectedRoute roles={['supervisor', 'super_admin']}><LeaderboardPage /></ProtectedRoute>
        } />
        <Route path="/profile" element={<ProfilePage />} />

        <Route path="/supervisor" element={
          <ProtectedRoute roles={['supervisor', 'super_admin']}><SupervisorPage /></ProtectedRoute>
        } />

        <Route path="/admin/users" element={
          <ProtectedRoute roles={['super_admin']}><AdminUsersPage /></ProtectedRoute>
        } />
        <Route path="/admin/halqas" element={
          <ProtectedRoute roles={['super_admin']}><AdminHalqasPage /></ProtectedRoute>
        } />
        <Route path="/admin/analytics" element={
          <ProtectedRoute roles={['super_admin']}><AdminAnalyticsPage /></ProtectedRoute>
        } />
        <Route path="/admin/settings" element={
          <ProtectedRoute roles={['super_admin']}><AdminSettingsPage /></ProtectedRoute>
        } />
      </Route>

      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Toaster position="top-center" toastOptions={{
          style: { background: '#1a3a3a', color: '#e8f5f0', border: '1px solid #2d5a5a', fontFamily: 'Noto Kufi Arabic' },
          success: { iconTheme: { primary: '#27ae60', secondary: '#1a3a3a' } },
          error: { iconTheme: { primary: '#e74c3c', secondary: '#1a3a3a' } },
        }} />
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
