import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../utils/api';
import toast from 'react-hot-toast';

export default function ProfilePage() {
  const { user, updateUser } = useAuth();
  const [editing, setEditing] = useState(false);
  const [changingPwd, setChangingPwd] = useState(false);
  const [form, setForm] = useState({ full_name: user?.full_name, phone: user?.phone, country: user?.country, age: user?.age });
  const [pwdForm, setPwdForm] = useState({ current_password: '', new_password: '', confirm_password: '' });
  const [loading, setLoading] = useState(false);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const saveProfile = async () => {
    setLoading(true);
    try {
      const res = await api.put('/auth/profile', form);
      updateUser(res.data.user);
      toast.success('تم تحديث الملف الشخصي');
      setEditing(false);
    } catch (err) {
      toast.error(err.response?.data?.error || 'خطأ');
    } finally { setLoading(false); }
  };

  const changePassword = async () => {
    if (pwdForm.new_password !== pwdForm.confirm_password) {
      toast.error('كلمتا المرور غير متطابقتين');
      return;
    }
    setLoading(true);
    try {
      await api.post('/auth/change-password', pwdForm);
      toast.success('تم تغيير كلمة المرور');
      setChangingPwd(false);
      setPwdForm({ current_password: '', new_password: '', confirm_password: '' });
    } catch (err) {
      toast.error(err.response?.data?.error || 'خطأ');
    } finally { setLoading(false); }
  };

  const roleLabel = { participant: 'مشارك', supervisor: 'مشرف', super_admin: 'سوبر آدمن' };
  const genderLabel = { male: 'ذكر', female: 'أنثى' };
  const statusLabel = { active: 'نشط', pending: 'قيد المراجعة', rejected: 'مرفوض', withdrawn: 'منسحب' };

  return (
    <div>
      <h1 className="page-title">👤 الملف الشخصي</h1>
      <p className="page-subtitle">عرض وتعديل بياناتك الشخصية</p>

      <div className="card mb-2">
        <div className="card-header">
          <div className="card-title">البيانات الشخصية</div>
          {!editing && (
            <button className="btn btn-secondary btn-sm" onClick={() => setEditing(true)}>✏️ تعديل</button>
          )}
        </div>

        {editing ? (
          <div>
            <div className="form-group">
              <label className="form-label">الاسم الثلاثي</label>
              <input className="form-input" value={form.full_name} onChange={(e) => set('full_name', e.target.value)} />
            </div>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">الهاتف</label>
                <input className="form-input" value={form.phone} onChange={(e) => set('phone', e.target.value)} dir="ltr" />
              </div>
              <div className="form-group">
                <label className="form-label">العمر</label>
                <input type="number" className="form-input" value={form.age} onChange={(e) => set('age', e.target.value)} />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">الدولة</label>
              <input className="form-input" value={form.country} onChange={(e) => set('country', e.target.value)} />
            </div>
            <div className="btn-group">
              <button className="btn btn-primary" onClick={saveProfile} disabled={loading}>
                {loading ? 'جاري الحفظ...' : 'حفظ التعديلات'}
              </button>
              <button className="btn btn-secondary" onClick={() => setEditing(false)}>إلغاء</button>
            </div>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
            {[
              ['رقم العضوية', user?.member_id],
              ['الاسم', user?.full_name],
              ['البريد', user?.email],
              ['الهاتف', user?.phone],
              ['الجنس', genderLabel[user?.gender]],
              ['العمر', user?.age],
              ['الدولة', user?.country],
              ['الحالة', statusLabel[user?.status]],
              ['الصلاحية', roleLabel[user?.role]],
              ['الحلقة', user?.halqa_name || 'غير محدد'],
            ].map(([label, val]) => (
              <div key={label}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>{label}</div>
                <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>{val || '-'}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Change Password */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">🔒 كلمة المرور</div>
          {!changingPwd && (
            <button className="btn btn-secondary btn-sm" onClick={() => setChangingPwd(true)}>تغيير</button>
          )}
        </div>

        {changingPwd && (
          <div>
            <div className="form-group">
              <label className="form-label">كلمة المرور الحالية</label>
              <input type="password" className="form-input" dir="ltr"
                value={pwdForm.current_password}
                onChange={(e) => setPwdForm((f) => ({ ...f, current_password: e.target.value }))} />
            </div>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">كلمة المرور الجديدة</label>
                <input type="password" className="form-input" dir="ltr"
                  value={pwdForm.new_password}
                  onChange={(e) => setPwdForm((f) => ({ ...f, new_password: e.target.value }))} />
              </div>
              <div className="form-group">
                <label className="form-label">تأكيد كلمة المرور</label>
                <input type="password" className="form-input" dir="ltr"
                  value={pwdForm.confirm_password}
                  onChange={(e) => setPwdForm((f) => ({ ...f, confirm_password: e.target.value }))} />
              </div>
            </div>
            <div className="btn-group">
              <button className="btn btn-primary" onClick={changePassword} disabled={loading}>
                {loading ? 'جاري التغيير...' : 'تغيير كلمة المرور'}
              </button>
              <button className="btn btn-secondary" onClick={() => setChangingPwd(false)}>إلغاء</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
