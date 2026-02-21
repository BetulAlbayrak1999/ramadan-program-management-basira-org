import { useState, useEffect } from 'react';
import api from '../utils/api';
import toast from 'react-hot-toast';
import { BarChart3, Users, Clock, CircleDot, Search, FileDown, X, Eye, ClipboardList } from 'lucide-react';
import Pagination, { paginate } from '../components/Pagination';

export default function AdminAnalyticsPage() {
  const [data, setData] = useState({ results: [], summary: {} });
  const [halqas, setHalqas] = useState([]);
  const [loading, setLoading] = useState(true);

  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({
    gender: '', halqa_id: '', member: '', supervisor: '',
    min_pct: '', max_pct: '',
    date_from: '', date_to: '',
    sort_by: 'score', sort_order: 'desc',
  });

  // Member cards modal
  const [cardsModal, setCardsModal] = useState(null);
  const [cardsLoading, setCardsLoading] = useState(false);
  const [cardsPage, setCardsPage] = useState(1);

  useEffect(() => {
    api.get('/admin/halqas').then((res) => setHalqas(res.data.halqas)).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([k, v]) => { if (v) params.append(k, v); });
    api.get(`/admin/analytics?${params.toString()}`)
      .then((res) => { setData(res.data); setPage(1); })
      .catch(() => toast.error('خطأ'))
      .finally(() => setLoading(false));
  }, [filters]);

  const updateFilter = (key, value) => setFilters((f) => ({ ...f, [key]: value }));

  const exportData = async (format) => {
    try {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([k, v]) => { if (v) params.append(k, v); });
      params.append('format', format);
      const res = await api.get(`/admin/export?${params.toString()}`, {
        responseType: 'blob',
      });
      const blob = new Blob([res.data], {
        type: format === 'xlsx'
          ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
          : 'text/csv;charset=utf-8-sig',
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ramadan_results.${format}`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success('تم التصدير بنجاح');
    } catch { toast.error('خطأ في التصدير'); }
  };

  const openCardsModal = async (userId, fullName) => {
    setCardsLoading(true);
    setCardsModal({ userId, fullName, cards: [] });
    setCardsPage(1);
    try {
      const params = new URLSearchParams();
      if (filters.date_from) params.append('date_from', filters.date_from);
      if (filters.date_to) params.append('date_to', filters.date_to);
      const res = await api.get(`/admin/user/${userId}/cards?${params.toString()}`);
      setCardsModal({ userId, fullName, cards: res.data.cards });
    } catch {
      toast.error('خطأ في جلب البطاقات');
      setCardsModal(null);
    } finally {
      setCardsLoading(false);
    }
  };

  return (
    <div>
      <h1 className="page-title"><BarChart3 size={22} /> التحليلات والنقاط</h1>
      <p className="page-subtitle">داشبورد النقاط والتحليلات المتقدمة</p>

      {/* Summary Stats */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon"><Users size={20} /></div>
          <div className="stat-value">{data.summary.total_active || 0}</div>
          <div className="stat-label">مشاركون نشطون</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon"><Clock size={20} /></div>
          <div className="stat-value gold">{data.summary.total_pending || 0}</div>
          <div className="stat-label">طلبات معلقة</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon"><CircleDot size={20} /></div>
          <div className="stat-value">{data.summary.total_halqas || 0}</div>
          <div className="stat-label">عدد الحلقات</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon"><Search size={20} /></div>
          <div className="stat-value gold">{data.summary.filtered_count || 0}</div>
          <div className="stat-label">نتائج الفلترة</div>
        </div>
      </div>

      {/* Filters */}
      <div className="filters-bar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
          <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>من</label>
          <input type="date" className="filter-input" value={filters.date_from}
            onChange={(e) => updateFilter('date_from', e.target.value)} dir="ltr" />
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
          <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>إلى</label>
          <input type="date" className="filter-input" value={filters.date_to}
            onChange={(e) => updateFilter('date_to', e.target.value)} dir="ltr" />
        </div>

        <select className="filter-input" value={filters.gender} onChange={(e) => updateFilter('gender', e.target.value)}>
          <option value="">كل الجنسين</option>
          <option value="male">ذكر</option>
          <option value="female">أنثى</option>
        </select>
        <select className="filter-input" value={filters.halqa_id} onChange={(e) => updateFilter('halqa_id', e.target.value)}>
          <option value="">كل الحلقات</option>
          {halqas.map((h) => <option key={h.id} value={h.id}>{h.name}</option>)}
        </select>
        <input className="filter-input" placeholder="اسم المشارك" value={filters.member}
          onChange={(e) => updateFilter('member', e.target.value)} />
        <input className="filter-input" placeholder="اسم المشرف" value={filters.supervisor}
          onChange={(e) => updateFilter('supervisor', e.target.value)} />
        <input className="filter-input" type="number" placeholder="أدنى %" style={{ width: 80 }}
          value={filters.min_pct} onChange={(e) => updateFilter('min_pct', e.target.value)} />
        <input className="filter-input" type="number" placeholder="أعلى %" style={{ width: 80 }}
          value={filters.max_pct} onChange={(e) => updateFilter('max_pct', e.target.value)} />
        <select className="filter-input" value={filters.sort_by} onChange={(e) => updateFilter('sort_by', e.target.value)}>
          <option value="score">ترتيب بالنقاط</option>
          <option value="name">ترتيب أبجدي</option>
        </select>
        <select className="filter-input" value={filters.sort_order} onChange={(e) => updateFilter('sort_order', e.target.value)}>
          <option value="desc">تنازلي</option>
          <option value="asc">تصاعدي</option>
        </select>
      </div>

      {/* Export */}
      <div className="btn-group mb-2">
        <button className="btn btn-gold btn-sm" onClick={() => exportData('xlsx')}>
          <FileDown size={14} /> تصدير XLSX
        </button>
        <button className="btn btn-secondary btn-sm" onClick={() => exportData('csv')}>
          <FileDown size={14} /> تصدير CSV
        </button>
      </div>

      {/* Results Table */}
      {loading ? (
        <div className="loading"><div className="spinner" /></div>
      ) : data.results.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon"><BarChart3 size={48} /></div>
          <div className="empty-state-text">لا توجد نتائج</div>
        </div>
      ) : (
        <div className="card">
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>#</th><th>رقم العضوية</th><th>الاسم</th><th>الجنس</th><th>الحلقة</th><th>المشرف</th>
                  <th>المجموع الحالي</th><th>المجموع العام</th><th>البطاقات</th><th>التفاصيل</th><th>النسبة</th>
                </tr>
              </thead>
              <tbody>
                {paginate(data.results, page).paged.map((r) => (
                  <tr key={r.user_id}>
                    <td style={{ fontWeight: 700, color: r.rank <= 3 ? 'var(--gold)' : 'var(--text-muted)' }}>{r.rank}</td>
                    <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{r.member_id}</td>
                    <td style={{ fontWeight: 600 }}>{r.full_name}</td>
                    <td>{['male', 'ذكر'].includes(r.gender) ? 'ذكر' : 'أنثى'}</td>
                    <td>{r.halqa_name}</td>
                    <td>{r.supervisor_name}</td>
                    <td style={{ fontWeight: 700, color: 'var(--accent)' }}>{r.total_score}</td>
                    <td>{r.max_score}</td>
                    <td>{r.cards_count}</td>
                    <td>
                      <button className="btn btn-sm btn-secondary"
                        onClick={() => openCardsModal(r.user_id, r.full_name)}
                        style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}>
                        <Eye size={13} /> عرض
                      </button>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <div className="progress-bar" style={{ width: 60, height: 6 }}>
                          <div className="progress-fill green" style={{ width: `${Math.min(r.percentage, 100)}%` }} />
                        </div>
                        <span style={{ fontWeight: 700, fontSize: '0.8rem' }}>{r.percentage}%</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination page={page} totalPages={paginate(data.results, page).totalPages}
            total={data.results.length} onPageChange={setPage} />
        </div>
      )}

      {/* Member Cards Modal */}
      {cardsModal && (
        <div className="modal-overlay" onClick={() => setCardsModal(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 700 }}>
            <button className="btn btn-secondary btn-sm" onClick={() => setCardsModal(null)}
              style={{ position: 'absolute', top: '1rem', left: '1rem', padding: '0.3rem' }}>
              <X size={16} />
            </button>
            <div className="modal-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <ClipboardList size={18} /> بطاقات {cardsModal.fullName}
            </div>

            {filters.date_from && filters.date_to && (
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: '0 0 0.75rem' }}>
                الفترة: {filters.date_from} إلى {filters.date_to}
              </p>
            )}

            {cardsLoading ? (
              <div className="loading"><div className="spinner" /></div>
            ) : cardsModal.cards.length === 0 ? (
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
                      </tr>
                    </thead>
                    <tbody>
                      {paginate(cardsModal.cards, cardsPage).paged.map((c) => (
                        <tr key={c.id}>
                          <td dir="ltr" style={{ textAlign: 'center' }}>{c.date}</td>
                          <td style={{ textAlign: 'center' }}>{c.total_score} / {c.max_score}</td>
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
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <Pagination page={cardsPage} totalPages={paginate(cardsModal.cards, cardsPage).totalPages}
                  total={cardsModal.cards.length} onPageChange={setCardsPage} />
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
