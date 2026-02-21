import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import api from '../utils/api';
import { useAuth } from '../context/AuthContext';
import {
  BarChart3, Star, TrendingUp, FileEdit, User, ClipboardList, Eye, X,
  BookOpen, Heart, Building2, Moon, Sun, Gem, Headphones, BookMarked, Lightbulb, HeartHandshake,
  Phone, Mail, Users,
} from 'lucide-react';
import Pagination, { paginate } from '../components/Pagination';

const SCORE_FIELDS = [
  { key: 'quran', label: 'وِرد القرآن', icon: <BookOpen size={14} /> },
  { key: 'duas', label: 'الأدعية', icon: <Heart size={14} /> },
  { key: 'taraweeh', label: 'صلاة التراويح', icon: <Building2 size={14} /> },
  { key: 'tahajjud', label: 'التهجد والوتر', icon: <Moon size={14} /> },
  { key: 'duha', label: 'صلاة الضحى', icon: <Sun size={14} /> },
  { key: 'rawatib', label: 'السنن الرواتب', icon: <Gem size={14} /> },
  { key: 'main_lesson', label: 'المقطع الأساسي', icon: <Headphones size={14} /> },
  { key: 'required_lesson', label: 'المقطع الواجب', icon: <BookMarked size={14} /> },
  { key: 'enrichment_lesson', label: 'المقطع الإثرائي', icon: <Lightbulb size={14} /> },
  { key: 'charity_worship', label: 'عبادة متعدية للغير', icon: <HeartHandshake size={14} /> },
  { key: 'extra_work', label: 'أعمال إضافية', icon: <Star size={14} /> },
];

export default function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  // Cards history
  const [cards, setCards] = useState([]);
  const [cardsLoading, setCardsLoading] = useState(false);
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [cardsPage, setCardsPage] = useState(1);

  // Card detail modal
  const [detailCard, setDetailCard] = useState(null);

  useEffect(() => {
    api.get('/participant/stats')
      .then((res) => setStats(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const fetchCards = useCallback(async () => {
    setCardsLoading(true);
    try {
      const params = new URLSearchParams();
      if (dateFrom) params.append('date_from', dateFrom);
      if (dateTo) params.append('date_to', dateTo);
      const res = await api.get(`/participant/cards?${params.toString()}`);
      setCards(res.data.cards);
      setCardsPage(1);
    } catch {
      setCards([]);
    } finally {
      setCardsLoading(false);
    }
  }, [dateFrom, dateTo]);

  useEffect(() => { fetchCards(); }, [fetchCards]);

  if (loading) return <div className="loading"><div className="spinner" /></div>;

  return (
    <div>
      <h1 className="page-title">
        {user?.full_name ? `أهلاً ${user.full_name}` : 'أهلاً بك'}
      </h1>
      <p className="page-subtitle">
        مرحباً بك في البرنامج الرمضاني — واصل إنجازك اليومي
        {user?.member_id && <span style={{ marginRight: 8, color: 'var(--text-muted)' }}>(رقم العضوية: {user.member_id})</span>}
      </p>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon"><BarChart3 size={22} /></div>
          <div className="stat-value">{stats?.today_percentage || 0}%</div>
          <div className="stat-label">إنجاز اليوم</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon"><Star size={22} /></div>
          <div className="stat-value gold">{stats?.overall_total || 0}</div>
          <div className="stat-label">مجموع نقاطك</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon"><TrendingUp size={22} /></div>
          <div className="stat-value">{stats?.overall_percentage || 0}%</div>
          <div className="stat-label">الإنجاز الكلي</div>
        </div>
      </div>

      {/* Supervisor Info */}
      {stats?.supervisor && (
        <div className="card mb-2">
          <div className="card-title mb-2" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Users size={18} /> المشرف
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}>
              <User size={14} style={{ color: 'var(--primary)' }} />
              <span style={{ color: 'var(--text-muted)' }}>الاسم:</span>
              <span style={{ fontWeight: 600 }}>{stats.supervisor.full_name}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}>
              <Mail size={14} style={{ color: 'var(--primary)' }} />
              <span style={{ color: 'var(--text-muted)' }}>البريد:</span>
              <span style={{ fontWeight: 600 }} dir="ltr">{stats.supervisor.email}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}>
              <Phone size={14} style={{ color: 'var(--primary)' }} />
              <span style={{ color: 'var(--text-muted)' }}>الهاتف:</span>
              <span style={{ fontWeight: 600 }} dir="ltr">{stats.supervisor.phone}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}>
              <User size={14} style={{ color: 'var(--primary)' }} />
              <span style={{ color: 'var(--text-muted)' }}>الجنس:</span>
              <span style={{ fontWeight: 600 }}>
                {['male', 'ذكر'].includes(stats.supervisor.gender) ? 'ذكر' : 'أنثى'}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Overall Progress */}
      <div className="card mb-2">
        <div className="card-header">
          <div className="card-title">نسبة الإنجاز الكلية</div>
          <span style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--accent)' }}>
            {stats?.overall_percentage || 0}%
          </span>
        </div>
        <div className="progress-bar">
          <div className="progress-fill green" style={{ width: `${stats?.overall_percentage || 0}%` }} />
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.5rem' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>عدد البطاقات: {stats?.cards_count || 0}</span>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card mb-2">
        <div className="card-title mb-2">إجراءات سريعة</div>
        <div className="btn-group">
          <Link to="/daily-card" className="btn btn-primary">
            <FileEdit size={16} style={{ marginLeft: 6 }} /> تعبئة بطاقة اليوم
          </Link>
          <Link to="/profile" className="btn btn-secondary">
            <User size={16} style={{ marginLeft: 6 }} /> الملف الشخصي
          </Link>
        </div>
      </div>

      {/* Cards History */}
      <div className="card">
        <div className="card-title mb-2" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <ClipboardList size={18} /> سجل البطاقات اليومية
        </div>

        <div className="filters-bar mb-2">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>من</label>
            <input type="date" className="filter-input" value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)} dir="ltr" />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>إلى</label>
            <input type="date" className="filter-input" value={dateTo}
              onChange={(e) => setDateTo(e.target.value)} dir="ltr" />
          </div>
        </div>

        {cardsLoading ? (
          <div className="loading"><div className="spinner" /></div>
        ) : cards.length === 0 ? (
          <div className="empty-state" style={{ padding: '2rem 0' }}>
            <div className="empty-state-icon"><ClipboardList size={36} /></div>
            <div className="empty-state-text">لا توجد بطاقات</div>
          </div>
        ) : (
          <>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>التاريخ</th>
                    <th>المجموع</th>
                    <th>النسبة</th>
                    <th>التفاصيل</th>
                  </tr>
                </thead>
                <tbody>
                  {paginate(cards, cardsPage).paged.map((c) => (
                    <tr key={c.id}>
                      <td dir="ltr" style={{ textAlign: 'center' }}>{c.date}</td>
                      <td style={{ textAlign: 'center', fontWeight: 600 }}>{c.total_score} / {c.max_score}</td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.4rem' }}>
                          <span style={{
                            fontWeight: 700, fontSize: '0.85rem',
                            color: c.percentage >= 80 ? 'var(--success)' : c.percentage >= 50 ? 'var(--gold)' : 'var(--danger)',
                          }}>
                            {c.percentage}%
                          </span>
                        </div>
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        <button className="btn btn-sm btn-secondary"
                          onClick={() => setDetailCard(c)}
                          style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}>
                          <Eye size={13} /> عرض
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination page={cardsPage} totalPages={paginate(cards, cardsPage).totalPages}
              total={cards.length} onPageChange={setCardsPage} />
          </>
        )}
      </div>

      {/* Card Detail Modal */}
      {detailCard && (
        <div className="modal-overlay" onClick={() => setDetailCard(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 550 }}>
            <button className="btn btn-secondary btn-sm" onClick={() => setDetailCard(null)}
              style={{ position: 'absolute', top: '1rem', left: '1rem', padding: '0.3rem' }}>
              <X size={16} />
            </button>
            <div className="modal-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <ClipboardList size={18} /> بطاقة يوم {detailCard.date}
            </div>

            <div className="flex-between mb-2">
              <span style={{ fontSize: '0.9rem', fontWeight: 600 }}>المجموع</span>
              <span style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--accent)' }}>
                {detailCard.total_score} / {detailCard.max_score}
              </span>
            </div>
            <div className="progress-bar mb-2">
              <div className="progress-fill green" style={{ width: `${detailCard.percentage}%` }} />
            </div>
            <div style={{ textAlign: 'center', marginBottom: '1rem', fontSize: '1.3rem', fontWeight: 800, color: 'var(--gold)' }}>
              {detailCard.percentage}%
            </div>

            {SCORE_FIELDS.map((f) => {
              const val = detailCard[f.key] || 0;
              const filled = val > 0;
              return (
                <div key={f.key} style={{
                  padding: '0.4rem 0.75rem',
                  margin: '0.2rem 0',
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

            {detailCard.extra_work_description && (
              <div style={{ marginTop: '0.75rem', padding: '0.5rem', background: 'var(--primary-light)', borderRadius: 8, fontSize: '0.8rem' }}>
                <strong>وصف الأعمال الإضافية:</strong> {detailCard.extra_work_description}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
