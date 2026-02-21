import React, { useState, useEffect, useCallback } from 'react';
import api from '../utils/api';
import toast from 'react-hot-toast';
import {
  BookOpen, Heart, Building2, Moon, Sun, Gem,
  Headphones, BookMarked, Lightbulb, HeartHandshake, Star, Save, X, CheckCircle, MessageCircle,
} from 'lucide-react';

const FIELDS = [
  { key: 'quran', label: 'وِرد القرآن', icon: <BookOpen size={16} /> },
  { key: 'duas', label: 'الأدعية', icon: <Heart size={16} /> },
  { key: 'taraweeh', label: 'صلاة التراويح', icon: <Building2 size={16} /> },
  { key: 'tahajjud', label: 'التهجد والوتر', icon: <Moon size={16} /> },
  { key: 'duha', label: 'صلاة الضحى', icon: <Sun size={16} /> },
  { key: 'rawatib', label: 'السنن الرواتب', icon: <Gem size={16} /> },
  { key: 'main_lesson', label: 'المقطع الأساسي', icon: <Headphones size={16} /> },
  { key: 'required_lesson', label: 'المقطع الواجب', icon: <BookMarked size={16} /> },
  { key: 'enrichment_lesson', label: 'المقطع الإثرائي', icon: <Lightbulb size={16} /> },
  { key: 'charity_worship', label: 'عبادة متعدية للغير', icon: <HeartHandshake size={16} /> },
  { key: 'extra_work', label: 'أعمال إضافية', icon: <Star size={16} /> },
];

const RAMADAN_START = '2026-02-19';
const RAMADAN_END = '2026-03-19';

function formatDate(d) {
  return d.toLocaleDateString('ar-EG', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
}

// Anchor: 19 Feb 2026 = 1 Ramadan 1447 (Turkey observation)
const SHABAN_START = new Date(2026, 0, 21);  // 1 Sha'ban 1447
const RAMADAN_START_DATE = new Date(2026, 1, 19); // 1 Ramadan 1447
const SHAWWAL_START = new Date(2026, 2, 20); // 1 Shawwal 1447

function getHijriInfo(d) {
  const ts = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  if (ts >= RAMADAN_START_DATE && ts < SHAWWAL_START) {
    const day = Math.floor((ts - RAMADAN_START_DATE) / 86400000) + 1;
    return { day, month: 'رمضان', monthIndex: 9, year: 1447, isRamadan: true };
  }
  if (ts >= SHABAN_START && ts < RAMADAN_START_DATE) {
    const day = Math.floor((ts - SHABAN_START) / 86400000) + 1;
    return { day, month: 'شعبان', monthIndex: 8, year: 1447, isRamadan: false };
  }
  if (ts >= SHAWWAL_START) {
    const day = Math.floor((ts - SHAWWAL_START) / 86400000) + 1;
    return { day, month: 'شوال', monthIndex: 10, year: 1447, isRamadan: false };
  }
  // Fallback for dates far outside — use Intl API
  const str = ts.toLocaleDateString('ar-SA-u-ca-islamic-umalqura', { day: 'numeric', month: 'long', year: 'numeric' });
  return { formatted: str, isRamadan: false };
}

function formatHijriDate(d) {
  const h = getHijriInfo(d);
  if (h.formatted) return h.formatted;
  return `${h.day} ${h.month} ${h.year}`;
}

function getRamadanDay(d) {
  const h = getHijriInfo(d);
  return h.isRamadan ? h.day : null;
}

function toISODate(d) {
  return d.toISOString().split('T')[0];
}

export default function DailyCardPage() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [card, setCard] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [justSubmitted, setJustSubmitted] = useState(false);
  const [supervisor, setSupervisor] = useState(null);

  useEffect(() => {
    api.get('/participant/stats')
      .then((res) => setSupervisor(res.data.supervisor))
      .catch(() => {});
  }, []);

  const fetchCard = useCallback(async () => {
    setLoading(true);
    setJustSubmitted(false);
    try {
      const res = await api.get(`/participant/card/${toISODate(currentDate)}`);
      if (res.data.card) {
        setCard(res.data.card);
        setSubmitted(true);
      } else {
        const empty = {};
        FIELDS.forEach((f) => { empty[f.key] = 0; });
        empty.extra_work_description = '';
        setCard(empty);
        setSubmitted(false);
      }
    } catch {
      toast.error('خطأ في تحميل البطاقة');
    } finally {
      setLoading(false);
    }
  }, [currentDate]);

  useEffect(() => { fetchCard(); }, [fetchCard]);

  const prevDay = () => {
    const d = new Date(currentDate);
    d.setDate(d.getDate() - 1);
    setCurrentDate(d);
  };

  const nextDay = () => {
    const d = new Date(currentDate);
    d.setDate(d.getDate() + 1);
    if (d <= new Date()) setCurrentDate(d);
  };

  const setScore = (field, value) => {
    const num = parseFloat(value);
    if (value === '' || value === '-') {
      setCard((c) => ({ ...c, [field]: '' }));
      return;
    }
    if (!isNaN(num) && num >= 0 && num <= 10) {
      setCard((c) => ({ ...c, [field]: num }));
    }
  };

  const totalScore = FIELDS.reduce((sum, f) => sum + (parseFloat(card[f.key]) || 0), 0);
  const maxScore = FIELDS.length * 10;
  const percentage = maxScore > 0 ? Math.round((totalScore / maxScore) * 1000) / 10 : 0;

  const handleSave = async () => {
    setSaving(true);
    try {
      const payload = { date: toISODate(currentDate) };
      FIELDS.forEach((f) => { payload[f.key] = parseFloat(card[f.key]) || 0; });
      payload.extra_work_description = card.extra_work_description || '';

      const res = await api.post('/participant/card', payload);
      setCard(res.data.card);
      toast.success('تم حفظ البطاقة بنجاح');
      setSubmitted(true);
      setShowConfirm(false);
      setJustSubmitted(true);
    } catch (err) {
      const detail = err.response?.data?.detail;
      toast.error(typeof detail === 'string' ? detail : 'خطأ في حفظ البطاقة');
    } finally {
      setSaving(false);
    }
  };

  const isToday = toISODate(currentDate) === toISODate(new Date());
  const isFuture = currentDate > new Date();
  const dateStr = toISODate(currentDate);
  const isOutsideRamadan = dateStr < RAMADAN_START || dateStr > RAMADAN_END;

  const supervisorWhatsappLink = supervisor?.phone
    ? `https://wa.me/${supervisor.phone.replace(/[^0-9]/g, '')}`
    : null;

  return (
    <div>
      <h1 className="page-title">البطاقة الرمضانية</h1>
      <p className="page-subtitle">سجّل إنجازك اليومي</p>

      {/* Date Navigator */}
      <div className="date-nav">
        <button className="date-nav-btn" onClick={prevDay}>&rarr;</button>
        <span className="date-nav-current">
          <span>{formatDate(currentDate)} {isToday && <span className="badge badge-success" style={{ marginRight: 8 }}>اليوم</span>}</span>
          <span style={{
            display: 'block', marginTop: 6, padding: '0.3rem 0.8rem',
            background: 'linear-gradient(135deg, var(--gold-light), var(--primary-light))',
            borderRadius: 10, fontSize: '0.92rem', fontWeight: 700,
            color: 'var(--primary-dark)', letterSpacing: '0.02em',
          }}>
            <Moon size={14} style={{ verticalAlign: 'middle', marginLeft: 4, color: 'var(--gold)' }} />
            {formatHijriDate(currentDate)}
            {getRamadanDay(currentDate) && (
              <span style={{ marginRight: 8, color: 'var(--gold)', fontWeight: 800 }}>
                — اليوم {getRamadanDay(currentDate)} من رمضان
              </span>
            )}
          </span>
        </span>
        <button className="date-nav-btn" onClick={nextDay} disabled={isFuture}>&larr;</button>
      </div>

      {loading ? (
        <div className="loading"><div className="spinner" /></div>
      ) : isOutsideRamadan ? (
        /* Outside Ramadan date range */
        <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>
          <Moon size={48} style={{ color: 'var(--gold)', marginBottom: '1rem' }} />
          <p style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
            لا يمكن تعبئة بطاقة لهذا التاريخ
          </p>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            فترة البرنامج الرمضاني: {RAMADAN_START} إلى {RAMADAN_END}
          </p>
        </div>
      ) : submitted ? (
        /* Read-only view for already submitted cards */
        <>
          {/* WhatsApp reminder after fresh submit */}
          {justSubmitted && supervisor && (
            <div className="card mb-2" style={{ background: 'var(--primary-light)', borderRight: '4px solid var(--success)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <CheckCircle size={18} style={{ color: 'var(--success)' }} />
                <span style={{ fontWeight: 700, color: 'var(--primary-dark)' }}>تم حفظ البطاقة بنجاح</span>
              </div>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                لا تنسَ إرسال "تم تسليم البطاقة" إلى المشرف عبر واتساب
              </p>
              {supervisorWhatsappLink && (
                <a href={supervisorWhatsappLink} target="_blank" rel="noopener noreferrer"
                  className="btn btn-primary btn-sm" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}>
                  <MessageCircle size={16} /> تواصل مع المشرف ({supervisor.full_name})
                </a>
              )}
            </div>
          )}

          <div className="card mb-2">
            <div className="flex-between">
              <span style={{ fontSize: '0.9rem', fontWeight: 600 }}>المجموع</span>
              <span style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--accent)' }}>
                {card.total_score ?? totalScore} / {card.max_score ?? maxScore}
              </span>
            </div>
            <div className="progress-bar mt-1">
              <div className="progress-fill green" style={{ width: `${card.percentage ?? percentage}%` }} />
            </div>
            <div style={{ textAlign: 'center', marginTop: '0.5rem', fontSize: '1.5rem', fontWeight: 800, color: 'var(--gold)' }}>
              {card.percentage ?? percentage}%
            </div>
          </div>

          <div className="card mb-2">
            <div style={{ textAlign: 'center', color: 'var(--text-muted)', marginBottom: '0.75rem', fontSize: '0.85rem' }}>
              تم تسجيل بطاقة هذا اليوم مسبقاً (للعرض فقط)
            </div>
            {FIELDS.map((f) => (
              <div key={f.key} className="score-field" style={{ padding: '0.4rem 0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}>
                  {f.icon} {f.label}
                </span>
                <span style={{ fontWeight: 700, color: 'var(--primary)', minWidth: 40, textAlign: 'center' }}>
                  {card[f.key] ?? 0}
                </span>
              </div>
            ))}
            {card.extra_work_description && (
              <div style={{ marginTop: '0.75rem', padding: '0.5rem', background: 'var(--primary-light)', borderRadius: 8, fontSize: '0.85rem' }}>
                <strong>وصف الأعمال الإضافية:</strong> {card.extra_work_description}
              </div>
            )}
          </div>
        </>
      ) : (
        /* Editable form for new cards */
        <>
          <div className="card mb-2">
            <div className="flex-between">
              <span style={{ fontSize: '0.9rem', fontWeight: 600 }}>المجموع أعمال اليوم</span>
              <span style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--accent)' }}>{totalScore} / {maxScore}</span>
            </div>
            <div className="progress-bar mt-1">
              <div className="progress-fill green" style={{ width: `${percentage}%` }} />
            </div>
            <div style={{ textAlign: 'center', marginTop: '0.5rem', fontSize: '1.5rem', fontWeight: 800, color: 'var(--gold)' }}>
              {percentage}%
            </div>
          </div>

          <div className="card mb-2">
            {FIELDS.map((f) => {
              const val = parseFloat(card[f.key]) || 0;
              const filled = val > 0;
              return (
                <div key={f.key} className="score-field" style={{
                  padding: '0.5rem 0.75rem',
                  margin: '0.25rem 0',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  borderRadius: 10,
                  background: filled ? 'var(--primary-light)' : 'var(--gold-light)',
                  borderRight: `3px solid ${filled ? 'var(--success)' : 'var(--gold)'}`,
                  transition: 'background 0.3s, border-color 0.3s',
                }}>
                  <span style={{
                    display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem',
                    color: filled ? 'var(--primary-dark)' : 'var(--text-secondary)',
                  }}>
                    {f.icon} {f.label}
                  </span>
                  <input
                    type="number"
                    min="0"
                    max="10"
                    step="0.5"
                    value={card[f.key] ?? 0}
                    onChange={(e) => setScore(f.key, e.target.value)}
                    style={{
                      width: 65,
                      textAlign: 'center',
                      padding: '0.3rem',
                      border: `1.5px solid ${filled ? 'var(--success)' : 'var(--gold)'}`,
                      borderRadius: 8,
                      fontSize: '0.9rem',
                      fontWeight: 600,
                      background: 'var(--surface)',
                      transition: 'border-color 0.3s',
                    }}
                  />
                </div>
              );
            })}

            <div className="form-group mt-2">
              <label className="form-label">وصف الأعمال الإضافية (اختياري)</label>
              <textarea className="form-textarea"
                value={card.extra_work_description || ''}
                onChange={(e) => setCard((c) => ({ ...c, extra_work_description: e.target.value }))}
                placeholder="اكتب وصفاً للأعمال الإضافية..."
                rows={2}
              />
            </div>
          </div>

          <button className="btn btn-primary btn-full" onClick={() => setShowConfirm(true)}>
            <Save size={16} style={{ marginLeft: 6 }} />
            حفظ البطاقة
          </button>
        </>
      )}

      {/* Confirmation Modal */}
      {showConfirm && (
        <div className="modal-overlay" onClick={() => setShowConfirm(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 550 }}>
            <button className="btn btn-secondary btn-sm" onClick={() => setShowConfirm(false)}
              style={{ position: 'absolute', top: '1rem', left: '1rem', padding: '0.3rem' }}>
              <X size={16} />
            </button>
            <div className="modal-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <CheckCircle size={18} /> تأكيد حفظ البطاقة
            </div>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
              يرجى مراجعة البطاقة قبل الحفظ — لا يمكن التعديل بعد الإرسال
            </p>

            <div className="flex-between mb-2">
              <span style={{ fontSize: '0.9rem', fontWeight: 600 }}>المجموع</span>
              <span style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--accent)' }}>
                {totalScore} / {maxScore} ({percentage}%)
              </span>
            </div>
            <div className="progress-bar mb-2">
              <div className="progress-fill green" style={{ width: `${percentage}%` }} />
            </div>

            {FIELDS.map((f) => {
              const val = parseFloat(card[f.key]) || 0;
              const filled = val > 0;
              return (
                <div key={f.key} style={{
                  padding: '0.35rem 0.75rem',
                  margin: '0.15rem 0',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  borderRadius: 8,
                  background: filled ? 'var(--primary-light)' : 'var(--gold-light)',
                  borderRight: `3px solid ${filled ? 'var(--success)' : 'var(--gold)'}`,
                }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8rem', color: filled ? 'var(--primary-dark)' : 'var(--text-secondary)' }}>
                    {f.icon} {f.label}
                  </span>
                  <span style={{ fontWeight: 700, fontSize: '0.85rem', color: filled ? 'var(--primary)' : 'var(--text-muted)', minWidth: 30, textAlign: 'center' }}>
                    {val}
                  </span>
                </div>
              );
            })}

            {card.extra_work_description && (
              <div style={{ marginTop: '0.5rem', padding: '0.4rem', background: 'var(--primary-light)', borderRadius: 8, fontSize: '0.8rem' }}>
                <strong>وصف الأعمال الإضافية:</strong> {card.extra_work_description}
              </div>
            )}

            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
              <button className="btn btn-primary" onClick={handleSave} disabled={saving} style={{ flex: 1 }}>
                <CheckCircle size={15} /> {saving ? 'جاري الحفظ...' : 'تأكيد الحفظ'}
              </button>
              <button className="btn btn-secondary" onClick={() => setShowConfirm(false)} style={{ flex: 1 }}>
                رجوع
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
