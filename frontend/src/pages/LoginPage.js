import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Moon, Eye, EyeOff } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
      toast.success('تم تسجيل الدخول بنجاح');
      navigate('/dashboard');
    } catch (err) {
      const detail = err.response?.data?.detail;
      toast.error(typeof detail === 'string' ? detail : 'حدث خطأ في تسجيل الدخول');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1 className="auth-title">🌙 المنصة الرمضانية</h1>
        <p className="auth-subtitle">تسجيل الدخول إلى حسابك</p>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">البريد الإلكتروني</label>
            <input type="email" className="form-input" name="email" autoComplete="email"
              value={email} onChange={(e) => setEmail(e.target.value)}
              required placeholder="example@email.com" dir="ltr" />
          </div>

          <div className="form-group">
            <label className="form-label">كلمة المرور</label>
            <div style={{ position: 'relative' }}>
              <input type={showPassword ? 'text' : 'password'} className="form-input"
                name="password" autoComplete="current-password"
                value={password} onChange={(e) => setPassword(e.target.value)}
                required placeholder="••••••••" dir="ltr"
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

          <div style={{ textAlign: 'left', marginBottom: '1.5rem' }}>
            <Link to="/forgot-password" className="auth-link">نسيت كلمة المرور؟</Link>
          </div>

          <button type="submit" className="btn btn-primary btn-full" disabled={loading}>
            {loading ? 'جاري الدخول...' : 'تسجيل الدخول'}
          </button>
        </form>

        <div className="auth-footer">
          ليس لديك حساب؟ <Link to="/register" className="auth-link">سجل الآن</Link>
        </div>
      </div>
    </div>
  );
}
