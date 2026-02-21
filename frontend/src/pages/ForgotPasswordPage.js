import { useState } from 'react';
import { KeyRound, Eye, EyeOff } from 'lucide-react';
import { Link } from 'react-router-dom';
import api from '../utils/api';
import toast from 'react-hot-toast';

export default function ForgotPasswordPage() {
  const [step, setStep] = useState(1);
  const [email, setEmail] = useState('');
  const [token, setToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  const requestReset = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post('/auth/forgot-password', { email });
      toast.success('تم إرسال رمز إعادة التعيين إلى بريدك');
      setStep(2);
    } catch (err) {
      if (err.response?.status === 404) {
        toast.error('هذا البريد الإلكتروني غير مسجل في النظام');
      } else {
        toast.error('حدث خطأ');
      }
    } finally {
      setLoading(false);
    }
  };

  const resetPassword = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post('/auth/reset-password', { email, token, new_password: newPassword });
      toast.success('تم إعادة تعيين كلمة المرور بنجاح');
      setStep(3);
    } catch (err) {
      const detail = err.response?.data?.detail;
      toast.error(typeof detail === 'string' ? detail : 'حدث خطأ');
    } finally {
      setLoading(false);
    }
  };

  const passwordToggleBtn = (
    <button type="button" onClick={() => setShowPassword((v) => !v)}
      style={{
        position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)',
        background: 'none', border: 'none', cursor: 'pointer',
        color: 'var(--text-muted)', padding: 0, display: 'flex', alignItems: 'center',
      }}>
      {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
    </button>
  );

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1 className="auth-title">🔑 إعادة تعيين كلمة المرور</h1>

        {step === 1 && (
          <form onSubmit={requestReset}>
            <p className="auth-subtitle">أدخل بريدك الإلكتروني لإرسال رمز إعادة التعيين</p>
            <div className="form-group">
              <label className="form-label">البريد الإلكتروني</label>
              <input type="email" className="form-input" value={email}
                onChange={(e) => setEmail(e.target.value)} required dir="ltr" />
            </div>
            <button type="submit" className="btn btn-primary btn-full" disabled={loading}>
              {loading ? 'جاري الإرسال...' : 'إرسال الرمز'}
            </button>
          </form>
        )}

        {step === 2 && (
          <form onSubmit={resetPassword}>
            <p className="auth-subtitle">أدخل الرمز المرسل إلى بريدك وكلمة المرور الجديدة</p>
            <div className="form-group">
              <label className="form-label">رمز التحقق</label>
              <input className="form-input" value={token}
                onChange={(e) => setToken(e.target.value)} required dir="ltr" placeholder="الرمز المكون من 6 أرقام" />
            </div>
            <div className="form-group">
              <label className="form-label">كلمة المرور الجديدة</label>
              <div style={{ position: 'relative' }}>
                <input type={showPassword ? 'text' : 'password'} className="form-input" value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)} required dir="ltr" minLength={6}
                  style={{ paddingLeft: 40 }} />
                {passwordToggleBtn}
              </div>
            </div>
            <button type="submit" className="btn btn-primary btn-full" disabled={loading}>
              {loading ? 'جاري التعيين...' : 'تعيين كلمة المرور'}
            </button>
          </form>
        )}

        {step === 3 && (
          <div className="text-center">
            <p className="auth-subtitle" style={{ fontSize: '1.1rem', color: 'var(--accent)' }}>✅ تم إعادة تعيين كلمة المرور بنجاح</p>
            <Link to="/login" className="btn btn-primary mt-2">العودة لتسجيل الدخول</Link>
          </div>
        )}

        <div className="auth-footer">
          <Link to="/login" className="auth-link">العودة لتسجيل الدخول</Link>
        </div>
      </div>
    </div>
  );
}
