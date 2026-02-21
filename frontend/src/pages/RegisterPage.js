import { useState } from 'react';
import { Moon, Eye, EyeOff } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../utils/api';
import toast from 'react-hot-toast';

export default function RegisterPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [form, setForm] = useState({
    full_name: '', gender: 'male', age: '', phone: '',
    email: '', password: '', confirm_password: '', country: '', referral_source: '',
  });

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (form.password !== form.confirm_password) {
      toast.error('كلمتا المرور غير متطابقتين');
      return;
    }
    setLoading(true);
    try {
      const res = await api.post('/auth/register', form);
      toast.success(res.data.message);
      navigate('/login');
    } catch (err) {
      const detail = err.response?.data?.detail;
      toast.error(typeof detail === 'string' ? detail : 'حدث خطأ');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card" style={{ maxWidth: 560 }}>
        <h1 className="auth-title">🌙 التسجيل في البرنامج</h1>
        <p className="auth-subtitle">أنشئ حساباً جديداً للمشاركة في البرنامج الرمضاني</p>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">الاسم الثلاثي *</label>
            <input className="form-input" value={form.full_name}
              onChange={(e) => set('full_name', e.target.value)} required placeholder="الاسم الثلاثي باللغة العربية" />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">الجنس *</label>
              <select className="form-select" value={form.gender} onChange={(e) => set('gender', e.target.value)}>
                <option value="male">ذكر</option>
                <option value="female">أنثى</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">العمر *</label>
              <input type="number" className="form-input" value={form.age}
                onChange={(e) => set('age', e.target.value)} required min="5" max="100" />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">رقم الهاتف (مع الرمز الدولي) *</label>
            <input className="form-input" value={form.phone} dir="ltr"
              onChange={(e) => set('phone', e.target.value)} required placeholder="+966500000000" />
          </div>

          <div className="form-group">
            <label className="form-label">البريد الإلكتروني *</label>
            <input type="email" className="form-input" value={form.email} dir="ltr"
              onChange={(e) => set('email', e.target.value)} required placeholder="example@email.com" />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">كلمة المرور *</label>
              <div style={{ position: 'relative' }}>
                <input type={showPassword ? 'text' : 'password'} className="form-input" value={form.password} dir="ltr"
                  onChange={(e) => set('password', e.target.value)} required minLength={6} placeholder="6 أحرف على الأقل"
                  style={{ paddingLeft: 40 }} />
                <button type="button" onClick={() => setShowPassword((v) => !v)}
                  style={{
                    position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)',
                    background: 'none', border: 'none', cursor: 'pointer',
                    color: 'var(--text-muted)', padding: 0, display: 'flex', alignItems: 'center',
                  }}>
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">تأكيد كلمة المرور *</label>
              <div style={{ position: 'relative' }}>
                <input type={showConfirm ? 'text' : 'password'} className="form-input" value={form.confirm_password} dir="ltr"
                  onChange={(e) => set('confirm_password', e.target.value)} required placeholder="أعد كتابة كلمة المرور"
                  style={{ paddingLeft: 40 }} />
                <button type="button" onClick={() => setShowConfirm((v) => !v)}
                  style={{
                    position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)',
                    background: 'none', border: 'none', cursor: 'pointer',
                    color: 'var(--text-muted)', padding: 0, display: 'flex', alignItems: 'center',
                  }}>
                  {showConfirm ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">الدولة *</label>
            <input className="form-input" value={form.country}
              onChange={(e) => set('country', e.target.value)} required placeholder="اسم الدولة" />
          </div>

          <div className="form-group">
            <label className="form-label">عن طريق من عرفت بالموقع؟</label>
            <input className="form-input" value={form.referral_source}
              onChange={(e) => set('referral_source', e.target.value)} placeholder="اختياري" />
          </div>

          <button type="submit" className="btn btn-primary btn-full" disabled={loading}>
            {loading ? 'جاري التسجيل...' : 'إرسال طلب التسجيل'}
          </button>
        </form>

        <div className="auth-footer">
          لديك حساب بالفعل؟ <Link to="/login" className="auth-link">تسجيل الدخول</Link>
        </div>
      </div>
    </div>
  );
}
