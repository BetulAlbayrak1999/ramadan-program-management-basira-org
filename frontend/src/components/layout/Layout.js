import { useState } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  LayoutDashboard, FileEdit, Trophy, User, Eye, Users,
  CircleDot, BarChart3, Settings, LogOut, Menu, X, Moon,
} from 'lucide-react';

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = () => { logout(); navigate('/login'); };
  const closeSidebar = () => setSidebarOpen(false);

  const navItems = [
    { to: '/dashboard', icon: <LayoutDashboard size={18} />, label: 'لوحة القيادة' },
    { to: '/daily-card', icon: <FileEdit size={18} />, label: 'البطاقة الرمضانية' },
    { to: '/profile', icon: <User size={18} />, label: 'الملف الشخصي' },
  ];

  const supervisorNavItems = [
    { to: '/leaderboard', icon: <Trophy size={18} />, label: 'الترتيب العام' },
  ];

  const supervisorItems = [
    { to: '/supervisor', icon: <Eye size={18} />, label: 'إشراف الحلقة' },
  ];

  const adminItems = [
    { to: '/admin/users', icon: <Users size={18} />, label: 'إدارة المستخدمين' },
    { to: '/admin/halqas', icon: <CircleDot size={18} />, label: 'إدارة الحلقات' },
    { to: '/admin/analytics', icon: <BarChart3 size={18} />, label: 'التحليلات والنقاط' },
    { to: '/admin/settings', icon: <Settings size={18} />, label: 'الإعدادات' },
  ];

  const roleLabel = {
    participant: 'مشارك',
    supervisor: 'مشرف',
    super_admin: 'سوبر آدمن',
  };

  return (
    <div className="app-layout">
      {/* Mobile Header */}
      <div className="mobile-header">
        <button className="hamburger" onClick={() => setSidebarOpen(true)}><Menu size={22} /></button>
        <span className="mobile-logo">المنصة الرمضانية</span>
        <span style={{ width: 40 }} />
      </div>

      {/* Overlay */}
      <div className={`overlay ${sidebarOpen ? 'show' : ''}`} onClick={closeSidebar} />

      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <button className="hamburger" onClick={closeSidebar}
            style={{ display: sidebarOpen ? 'flex' : 'none', position: 'absolute', left: '1rem', top: '1rem' }}>
            <X size={20} />
          </button>
          <div className="sidebar-logo"><Moon size={20} /> المنصة الرمضانية</div>
          <div className="sidebar-subtitle">متابعة الإنجاز اليومي</div>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section-title">القائمة الرئيسية</div>
          {navItems.map((item) => (
            <NavLink key={item.to} to={item.to} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
              onClick={closeSidebar}>
              {item.icon} {item.label}
            </NavLink>
          ))}

          {(user?.role === 'supervisor' || user?.role === 'super_admin') && (
            <>
              <div className="nav-section-title">الإشراف</div>
              {supervisorNavItems.map((item) => (
                <NavLink key={item.to} to={item.to} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                  onClick={closeSidebar}>
                  {item.icon} {item.label}
                </NavLink>
              ))}
              {supervisorItems.map((item) => (
                <NavLink key={item.to} to={item.to} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                  onClick={closeSidebar}>
                  {item.icon} {item.label}
                </NavLink>
              ))}
            </>
          )}

          {user?.role === 'super_admin' && (
            <>
              <div className="nav-section-title">الإدارة</div>
              {adminItems.map((item) => (
                <NavLink key={item.to} to={item.to} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                  onClick={closeSidebar}>
                  {item.icon} {item.label}
                </NavLink>
              ))}
            </>
          )}
        </nav>

        <div className="sidebar-footer">
          <div className="user-info">
            <div className="user-avatar">{user?.full_name?.charAt(0)}</div>
            <div>
              <div className="user-name">{user?.full_name}</div>
              <div className="user-role">{roleLabel[user?.role] || user?.role}</div>
            </div>
          </div>
          <button className="nav-item" onClick={handleLogout}>
            <LogOut size={18} /> تسجيل الخروج
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
