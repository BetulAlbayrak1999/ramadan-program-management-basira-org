import { Link } from 'react-router-dom';
import { Moon, BookOpen, Users, Trophy, Star, ArrowLeft } from 'lucide-react';

export default function HomePage() {
  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #e6f5f3 0%, #f0edf7 50%, #fdf6e9 100%)',
      fontFamily: 'Noto Kufi Arabic, sans-serif',
      direction: 'rtl',
    }}>
      {/* Header */}
      <header style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        padding: '1.2rem 2rem', maxWidth: 1100, margin: '0 auto',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 800, fontSize: '1.1rem', color: '#1a7a6d' }}>
          <Moon size={22} /> بصيرة
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <Link to="/login" className="btn btn-secondary btn-sm">تسجيل الدخول</Link>
          <Link to="/register" className="btn btn-primary btn-sm">إنشاء حساب</Link>
        </div>
      </header>

      {/* Hero */}
      <section style={{
        textAlign: 'center', padding: '4rem 1.5rem 3rem',
        maxWidth: 750, margin: '0 auto',
      }}>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: '0.5rem',
          background: 'rgba(196, 151, 59, 0.12)', color: '#c4973b',
          padding: '0.4rem 1rem', borderRadius: 50, fontSize: '0.8rem', fontWeight: 600,
          marginBottom: '1.5rem',
        }}>
          <Star size={14} /> رمضان كريم
        </div>

        <h1 style={{
          fontSize: 'clamp(1.8rem, 5vw, 2.8rem)', fontWeight: 900,
          color: '#2c3e50', lineHeight: 1.4, marginBottom: '1rem',
          fontFamily: 'Amiri, serif',
        }}>
          المنصة الرمضانية
          <span style={{ display: 'block', color: '#1a7a6d', fontSize: '0.85em' }}>بصيرة</span>
        </h1>

        <p style={{
          fontSize: '1.05rem', color: '#5a6c7d', lineHeight: 1.8,
          maxWidth: 550, margin: '0 auto 2rem',
        }}>
          منصة متكاملة لمتابعة الإنجاز الرمضاني اليومي،
          تتبع أعمالك من قرآن وأذكار وصلوات، وتنافس مع حلقتك نحو رمضان مثمر
        </p>

        <div style={{ display: 'flex', justifyContent: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          <Link to="/register" className="btn btn-primary" style={{ padding: '0.7rem 2rem', fontSize: '1rem' }}>
            ابدأ الآن <ArrowLeft size={18} />
          </Link>
          <Link to="/login" className="btn btn-secondary" style={{ padding: '0.7rem 2rem', fontSize: '1rem' }}>
            لديّ حساب
          </Link>
        </div>
      </section>

      {/* Features */}
      <section style={{
        maxWidth: 900, margin: '0 auto', padding: '2rem 1.5rem 4rem',
        display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.25rem',
      }}>
        {[
          { icon: <BookOpen size={28} />, title: 'البطاقة اليومية', desc: 'سجّل أعمالك اليومية من قرآن وأذكار وصلوات وغيرها بسهولة', color: '#1a7a6d' },
          { icon: <Users size={28} />, title: 'حلقات ومجموعات', desc: 'انضم إلى حلقة بإشراف مشرف يتابع تقدمك ويشجعك', color: '#8b7cb8' },
          { icon: <Trophy size={28} />, title: 'ترتيب وتنافس', desc: 'تابع ترتيبك بين أعضاء حلقتك وحفّز نفسك للمزيد', color: '#c4973b' },
        ].map((f, i) => (
          <div key={i} style={{
            background: '#fff', borderRadius: 16, padding: '2rem 1.5rem',
            boxShadow: '0 2px 12px rgba(0,0,0,0.05)',
            textAlign: 'center', transition: 'transform 0.2s',
          }}
          onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-4px)'}
          onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
          >
            <div style={{
              width: 56, height: 56, borderRadius: 14,
              background: `${f.color}14`, color: f.color,
              display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
              marginBottom: '1rem',
            }}>
              {f.icon}
            </div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#2c3e50', marginBottom: '0.5rem' }}>{f.title}</h3>
            <p style={{ fontSize: '0.88rem', color: '#5a6c7d', lineHeight: 1.7, margin: 0 }}>{f.desc}</p>
          </div>
        ))}
      </section>

      {/* Footer */}
      <footer style={{
        textAlign: 'center', padding: '1.5rem', color: '#8e9baa',
        fontSize: '0.8rem', borderTop: '1px solid #e8e5e0',
      }}>
        بصيرة — المنصة الرمضانية &copy; {new Date().getFullYear()}
      </footer>
    </div>
  );
}
