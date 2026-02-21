import React, { useState, useEffect } from 'react';
import api from '../utils/api';
import toast from 'react-hot-toast';

export default function AdminSettingsPage() {
  const [settings, setSettings] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/settings/')
      .then((res) => setSettings(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const toggleNotifications = async () => {
    try {
      const newVal = !settings.enable_email_notifications;
      const res = await api.put('/settings/', { enable_email_notifications: newVal });
      setSettings(res.data.settings);
      toast.success(`تم ${newVal ? 'تفعيل' : 'تعطيل'} إشعارات البريد`);
    } catch { toast.error('خطأ'); }
  };

  if (loading) return <div className="loading"><div className="spinner" /></div>;

  return (
    <div>
      <h1 className="page-title">⚙️ إعدادات الموقع</h1>
      <p className="page-subtitle">إدارة إعدادات المنصة</p>

      <div className="card">
        <div className="card-title mb-2">📧 إشعارات البريد الإلكتروني</div>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
          عند تفعيل هذا الخيار، سيتم إرسال إشعار إلى بريد السوبر آدمن عند كل طلب تسجيل جديد.
        </p>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <button
            className={`btn ${settings.enable_email_notifications ? 'btn-primary' : 'btn-secondary'}`}
            onClick={toggleNotifications}
            style={{ minWidth: 120 }}
          >
            {settings.enable_email_notifications ? '✅ مُفعّل' : '❌ مُعطّل'}
          </button>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            الحالة الحالية: {settings.enable_email_notifications ? 'الإشعارات مفعلة' : 'الإشعارات معطلة'}
          </span>
        </div>
      </div>

      <div className="card mt-2">
        <div className="card-title mb-2">ℹ️ معلومات النظام</div>
        <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          <p style={{ marginBottom: '0.5rem' }}>
            <strong>السوبر آدمن الأساسي:</strong> يتم تحديده من ملف البيئة (.env) عبر المتغير SUPER_ADMIN_EMAIL.
            فقط من يدخل بهذا البريد يكون السوبر آدمن الأساسي ويملك صلاحية إضافة أو حذف سوبر آدمن آخرين.
          </p>
          <p style={{ marginBottom: '0.5rem' }}>
            <strong>كلمة المرور الافتراضية للمستوردين:</strong> 123456 (يُنصح بتغييرها فوراً)
          </p>
        </div>
      </div>
    </div>
  );
}
