import { useState, useEffect, useCallback } from 'react';
import api from '../utils/api';
import toast from 'react-hot-toast';
import { useAuth } from '../context/AuthContext';
import {
  Eye, ClipboardList, Trophy, Save, Users,
  BookOpen, Heart, Building2, Moon, Sun, Gem, User,
  Headphones, BookMarked, Lightbulb, HeartHandshake, Star, X, Filter,
  Phone, Mail, MapPin, Calendar, FileDown, Search, Plus, Trash2,
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

function getDefaultDateRange() {
  const today = new Date();
  const weekAgo = new Date(today);
  weekAgo.setDate(today.getDate() - 6);
  return {
    from: weekAgo.toISOString().split('T')[0],
    to: today.toISOString().split('T')[0],
  };
}

export default function SupervisorPage() {
  const { user } = useAuth();
  const isSuperAdmin = user?.role === 'super_admin';

  const [tab, setTab] = useState('summary');
  const [halqas, setHalqas] = useState([]);
  const [selectedHalqaId, setSelectedHalqaId] = useState('');
  const [halqa, setHalqa] = useState(null);
  const [loading, setLoading] = useState(true);

  // Summary tab
  const [dateRange, setDateRange] = useState(getDefaultDateRange);
  const [rangeSummary, setRangeSummary] = useState(null);
  const [pageSummary, setPageSummary] = useState(1);

  // Members tab
  const [members, setMembers] = useState([]);
  const [pageMembers, setPageMembers] = useState(1);
  const [memberDetail, setMemberDetail] = useState(null);

  // Leaderboard tab
  const [leaderboard, setLeaderboard] = useState([]);
  const [pageLeaderboard, setPageLeaderboard] = useState(1);

  // Card history modal
  const [selectedMember, setSelectedMember] = useState(null);
  const [memberCards, setMemberCards] = useState([]);

  // Search filters
  const [searchName, setSearchName] = useState('');
  const [searchGender, setSearchGender] = useState('');

  // Add card for member
  const [addCardDate, setAddCardDate] = useState('');

  // Card detail/edit state
  const [cardMember, setCardMember] = useState(null);
  const [cardDetail, setCardDetail] = useState(null);
  const [cardDate, setCardDate] = useState('');
  const [editMode, setEditMode] = useState(false);
  const [editData, setEditData] = useState({});
  const [saving, setSaving] = useState(false);

  // Fetch halqas list for super_admin
  useEffect(() => {
    if (isSuperAdmin) {
      api.get('/supervisor/halqas')
        .then((res) => setHalqas(res.data.halqas))
        .catch(() => {});
    }
  }, [isSuperAdmin]);

  const halqaParam = selectedHalqaId ? `&halqa_id=${selectedHalqaId}` : '';

  useEffect(() => {
    setLoading(true);
    if (tab === 'summary') {
      api.get(`/supervisor/range-summary?date_from=${dateRange.from}&date_to=${dateRange.to}${halqaParam}`)
        .then((res) => { setRangeSummary(res.data); setHalqa(res.data.halqa); setPageSummary(1); })
        .catch((err) => toast.error(err.response?.data?.detail || 'خطأ'))
        .finally(() => setLoading(false));
    } else if (tab === 'members') {
      api.get(`/supervisor/members?_=1${halqaParam}`)
        .then((res) => { setMembers(res.data.members); setHalqa(res.data.halqa); setPageMembers(1); })
        .catch((err) => toast.error(err.response?.data?.detail || 'خطأ'))
        .finally(() => setLoading(false));
    } else if (tab === 'leaderboard') {
      api.get(`/supervisor/leaderboard?_=1${halqaParam}`)
        .then((res) => { setLeaderboard(res.data.leaderboard); setHalqa(res.data.halqa); setPageLeaderboard(1); })
        .catch((err) => toast.error(err.response?.data?.detail || 'خطأ'))
        .finally(() => setLoading(false));
    }
  }, [tab, dateRange, halqaParam]);

  const viewMemberCards = async (memberId) => {
    try {
      const res = await api.get(`/supervisor/member/${memberId}/cards`);
      setSelectedMember(res.data.member);
      setMemberCards(res.data.cards);
    } catch {
      toast.error('خطأ في تحميل البطاقات');
    }
  };

  const openCardDetail = async (memberId, dateStr) => {
    try {
      const res = await api.get(`/supervisor/member/${memberId}/card/${dateStr}`);
      setCardMember(res.data.member);
      setCardDate(dateStr);
      if (res.data.card) {
        setCardDetail(res.data.card);
        setEditData({ ...res.data.card });
      } else {
        const empty = {};
        SCORE_FIELDS.forEach((f) => { empty[f.key] = 0; });
        empty.extra_work_description = '';
        setCardDetail(null);
        setEditData(empty);
      }
      setEditMode(false);
    } catch {
      toast.error('خطأ في تحميل البطاقة');
    }
  };

  const handleSaveCard = async () => {
    setSaving(true);
    try {
      const payload = { date: cardDate };
      SCORE_FIELDS.forEach((f) => { payload[f.key] = parseFloat(editData[f.key]) || 0; });
      payload.extra_work_description = editData.extra_work_description || '';

      const res = await api.put(`/supervisor/member/${cardMember.id}/card/${cardDate}`, payload);
      toast.success(res.data.message);
      setCardDetail(res.data.card);
      setEditData({ ...res.data.card });
      setEditMode(false);
      refreshCurrentTab();
    } catch (err) {
      toast.error(err.response?.data?.error || 'خطأ في حفظ البطاقة');
    } finally {
      setSaving(false);
    }
  };

  const closeCardDetail = () => {
    setCardMember(null);
    setCardDetail(null);
    setEditMode(false);
  };

  const refreshCurrentTab = useCallback(() => {
    if (tab === 'summary') {
      api.get(`/supervisor/range-summary?date_from=${dateRange.from}&date_to=${dateRange.to}${halqaParam}`)
        .then((res) => { setRangeSummary(res.data); setHalqa(res.data.halqa); })
        .catch(() => {});
    } else if (tab === 'members') {
      api.get(`/supervisor/members?_=1${halqaParam}`)
        .then((res) => { setMembers(res.data.members); setHalqa(res.data.halqa); })
        .catch(() => {});
    } else if (tab === 'leaderboard') {
      api.get(`/supervisor/leaderboard?_=1${halqaParam}`)
        .then((res) => { setLeaderboard(res.data.leaderboard); setHalqa(res.data.halqa); })
        .catch(() => {});
    }
  }, [tab, dateRange, halqaParam]);

  const handleDeleteCard = async () => {
    if (!cardMember || !cardDate) return;
    if (!window.confirm('هل أنت متأكد من حذف هذه البطاقة؟')) return;
    try {
      const res = await api.delete(`/supervisor/member/${cardMember.id}/card/${cardDate}`);
      toast.success(res.data.message);
      closeCardDetail();
      refreshCurrentTab();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'خطأ في حذف البطاقة');
    }
  };

  const setScore = (field, value) => {
    const num = parseFloat(value);
    if (value === '' || value === '-') {
      setEditData((d) => ({ ...d, [field]: '' }));
      return;
    }
    if (!isNaN(num) && num >= 0 && num <= 10) {
      setEditData((d) => ({ ...d, [field]: num }));
    }
  };

  // Client-side filtering helper
  const applyFilters = (item) => {
    const name = item.member?.full_name || item.full_name || '';
    const gender = item.member?.gender || item.gender || '';
    if (searchName && !name.includes(searchName)) return false;
    if (searchGender) {
      const normalizedGender = ['male', 'ذكر'].includes(gender) ? 'male' : 'female';
      if (normalizedGender !== searchGender) return false;
    }
    return true;
  };

  const exportReport = async (format) => {
    try {
      const params = new URLSearchParams();
      params.append('format', format);
      if (dateRange.from) params.append('date_from', dateRange.from);
      if (dateRange.to) params.append('date_to', dateRange.to);
      if (selectedHalqaId) params.append('halqa_id', selectedHalqaId);
      if (searchName) params.append('search_name', searchName);
      if (searchGender) params.append('search_gender', searchGender);
      const res = await api.get(`/supervisor/export?${params.toString()}`, { responseType: 'blob' });
      const blob = new Blob([res.data], {
        type: format === 'xlsx'
          ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
          : 'text/csv;charset=utf-8-sig',
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `daily_cards_report.${format}`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success('تم التصدير بنجاح');
    } catch { toast.error('خطأ في التصدير'); }
  };

  return (
    <div>
      <h1 className="page-title"><Eye size={22} /> إشراف الحلقة</h1>
      <p className="page-subtitle">
        {isSuperAdmin
          ? (halqa ? `حلقة: ${halqa.name}` : 'جميع الحلقات')
          : (halqa ? `حلقة: ${halqa.name}` : 'جاري التحميل...')}
      </p>

      {isSuperAdmin && (
        <div className="filters-bar mb-2">
          <Filter size={16} />
          <select className="filter-input" value={selectedHalqaId}
            onChange={(e) => setSelectedHalqaId(e.target.value)}>
            <option value="">كل الحلقات</option>
            {halqas.map((h) => <option key={h.id} value={h.id}>{h.name}</option>)}
          </select>
        </div>
      )}

      <div className="filters-bar mb-2">
        <Search size={15} />
        <input className="filter-input" placeholder="اسم المشارك" value={searchName}
          onChange={(e) => setSearchName(e.target.value)} />
        <select className="filter-input" value={searchGender}
          onChange={(e) => setSearchGender(e.target.value)}>
          <option value="">الجنس: الكل</option>
          <option value="male">ذكر</option>
          <option value="female">أنثى</option>
        </select>
      </div>

      <div className="tabs">
        <button className={`tab ${tab === 'summary' ? 'active' : ''}`} onClick={() => setTab('summary')}>
          <ClipboardList size={14} /> ملخص الفترة
        </button>
        <button className={`tab ${tab === 'members' ? 'active' : ''}`} onClick={() => setTab('members')}>
          <Users size={14} /> المشاركون
        </button>
        <button className={`tab ${tab === 'leaderboard' ? 'active' : ''}`} onClick={() => setTab('leaderboard')}>
          <Trophy size={14} /> ترتيب الأعضاء
        </button>
      </div>

      {/* ─── Summary Tab ─── */}
      {tab === 'summary' && (
        <div>
          <div className="filters-bar mb-2">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>من</label>
              <input type="date" className="filter-input" value={dateRange.from}
                onChange={(e) => setDateRange((d) => ({ ...d, from: e.target.value }))} dir="ltr" />
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>إلى</label>
              <input type="date" className="filter-input" value={dateRange.to}
                onChange={(e) => setDateRange((d) => ({ ...d, to: e.target.value }))} dir="ltr" />
            </div>
            <div style={{ display: 'flex', gap: '0.3rem', marginRight: 'auto' }}>
              <button className="btn btn-secondary btn-sm" onClick={() => exportReport('xlsx')} title="تصدير XLSX">
                <FileDown size={14} /> XLSX
              </button>
              <button className="btn btn-secondary btn-sm" onClick={() => exportReport('csv')} title="تصدير CSV">
                <FileDown size={14} /> CSV
              </button>
            </div>
          </div>

          {loading ? (
            <div className="loading"><div className="spinner" /></div>
          ) : rangeSummary ? (
            <div>
              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-icon"><Users size={20} /></div>
                  <div className="stat-value">{rangeSummary.summary.length}</div>
                  <div className="stat-label">إجمالي المشاركين</div>
                </div>
                <div className="stat-card">
                  <div className="stat-icon"><Calendar size={20} /></div>
                  <div className="stat-value gold">{rangeSummary.total_days}</div>
                  <div className="stat-label">عدد الأيام</div>
                </div>
              </div>

              {(() => {
                const filtered = rangeSummary.summary.filter(applyFilters);
                return filtered.length === 0 ? (
                  <div className="empty-state">
                    <div className="empty-state-icon"><ClipboardList size={48} /></div>
                    <div className="empty-state-text">لا توجد بيانات</div>
                  </div>
                ) : (
                  <div className="card">
                    <div className="table-container">
                      <table>
                        <thead>
                          <tr>
                            <th>#</th><th>رقم العضوية</th><th>الاسم</th><th>البطاقات</th>
                            <th>المجموع</th><th>النسبة</th><th>التفاصيل</th>
                          </tr>
                        </thead>
                        <tbody>
                          {paginate(filtered, pageSummary).paged.map((s, i) => (
                            <tr key={s.member.id}>
                              <td>{(pageSummary - 1) * 10 + i + 1}</td>
                              <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{s.member.member_id}</td>
                              <td style={{ fontWeight: 600 }}>{s.member.full_name}</td>
                              <td>{s.cards_submitted} / {s.total_days}</td>
                              <td style={{ fontWeight: 700, color: 'var(--accent)' }}>{s.total_score}</td>
                              <td>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                  <div className="progress-bar" style={{ width: 50, height: 6 }}>
                                    <div className="progress-fill green" style={{ width: `${s.percentage}%` }} />
                                  </div>
                                  <span style={{ fontWeight: 700, fontSize: '0.8rem' }}>{s.percentage}%</span>
                                </div>
                              </td>
                              <td>
                                <button className="btn btn-secondary btn-sm" onClick={() => viewMemberCards(s.member.id)}>
                                  عرض
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    <Pagination page={pageSummary} totalPages={paginate(filtered, pageSummary).totalPages}
                      total={filtered.length} onPageChange={setPageSummary} />
                  </div>
                );
              })()}
            </div>
          ) : null}
        </div>
      )}

      {/* ─── Members Tab ─── */}
      {tab === 'members' && (
        loading ? (
          <div className="loading"><div className="spinner" /></div>
        ) : (() => {
          const filtered = members.filter(applyFilters);
          return filtered.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon"><Users size={48} /></div>
              <div className="empty-state-text">لا يوجد مشاركون</div>
            </div>
          ) : (
            <div className="card">
              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>#</th><th>رقم العضوية</th><th>الاسم</th><th>الجنس</th><th>الهاتف</th>
                      <th>البريد</th><th>الدولة</th><th>إجراء</th>
                    </tr>
                  </thead>
                  <tbody>
                    {paginate(filtered, pageMembers).paged.map((m, i) => (
                      <tr key={m.id}>
                        <td>{(pageMembers - 1) * 10 + i + 1}</td>
                        <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{m.member_id}</td>
                        <td style={{ fontWeight: 600 }}>{m.full_name}</td>
                        <td>{['male', 'ذكر'].includes(m.gender) ? 'ذكر' : 'أنثى'}</td>
                        <td dir="ltr" style={{ fontSize: '0.8rem' }}>{m.phone}</td>
                        <td dir="ltr" style={{ fontSize: '0.8rem' }}>{m.email}</td>
                        <td>{m.country}</td>
                        <td>
                          <div className="btn-group">
                            <button className="btn btn-secondary btn-sm" onClick={() => setMemberDetail(m)}>
                              <User size={13} />
                            </button>
                            <button className="btn btn-secondary btn-sm" onClick={() => viewMemberCards(m.id)}>
                              <ClipboardList size={13} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <Pagination page={pageMembers} totalPages={paginate(filtered, pageMembers).totalPages}
                total={filtered.length} onPageChange={setPageMembers} />
            </div>
          );
        })()
      )}

      {/* ─── Leaderboard Tab ─── */}
      {tab === 'leaderboard' && (
        loading ? (
          <div className="loading"><div className="spinner" /></div>
        ) : (() => {
          const filtered = leaderboard.filter(applyFilters);
          return filtered.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon"><Trophy size={48} /></div>
              <div className="empty-state-text">لا توجد بيانات بعد</div>
            </div>
          ) : (
            <div className="card">
              <div className="table-container">
                <table>
                  <thead>
                    <tr><th>#</th><th>رقم العضوية</th><th>الاسم</th><th>المجموع</th><th>البطاقات</th><th>النسبة</th></tr>
                  </thead>
                  <tbody>
                    {paginate(filtered, pageLeaderboard).paged.map((r) => (
                      <tr key={r.user_id}>
                        <td style={{ fontWeight: 800, color: r.rank <= 3 ? 'var(--gold)' : 'var(--text-muted)' }}>
                          {r.rank}
                        </td>
                        <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{r.member_id}</td>
                        <td style={{ fontWeight: 600 }}>{r.full_name}</td>
                        <td style={{ fontWeight: 700, color: 'var(--accent)' }}>{r.total_score}</td>
                        <td>{r.cards_count}</td>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <div className="progress-bar" style={{ width: 60, height: 6 }}>
                              <div className="progress-fill green" style={{ width: `${r.percentage}%` }} />
                            </div>
                            <span style={{ fontWeight: 700, fontSize: '0.8rem' }}>{r.percentage}%</span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <Pagination page={pageLeaderboard} totalPages={paginate(filtered, pageLeaderboard).totalPages}
                total={filtered.length} onPageChange={setPageLeaderboard} />
            </div>
          );
        })()
      )}

      {/* ─── Member Detail Modal ─── */}
      {memberDetail && (
        <div className="modal-overlay" onClick={() => setMemberDetail(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 450 }}>
            <div className="flex-between mb-2">
              <div className="modal-title" style={{ margin: 0 }}>
                <User size={18} /> بيانات المشارك
              </div>
              <button className="btn btn-secondary btn-sm" onClick={() => setMemberDetail(null)}>
                <X size={16} />
              </button>
            </div>

            <div style={{
              display: 'flex', flexDirection: 'column', alignItems: 'center',
              padding: '1rem 0 0.75rem', borderBottom: '1px solid var(--border)', marginBottom: '0.75rem',
            }}>
              <div style={{
                width: 56, height: 56, borderRadius: '50%', background: 'var(--primary-light)',
                color: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '1.3rem', fontWeight: 800, marginBottom: '0.5rem',
              }}>
                {memberDetail.full_name?.charAt(0)}
              </div>
              <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--text-primary)' }}>
                {memberDetail.full_name}
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>
                رقم العضوية: {memberDetail.member_id}
              </div>
              <span className={`badge ${memberDetail.gender === 'male' || memberDetail.gender === 'ذكر' ? 'badge-info' : 'badge-warning'}`}
                style={{ marginTop: '0.3rem' }}>
                {['male', 'ذكر'].includes(memberDetail.gender) ? 'ذكر' : 'أنثى'}
                {memberDetail.age ? ` — ${memberDetail.age} سنة` : ''}
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
              {[
                { icon: <Phone size={15} />, label: 'الهاتف', value: memberDetail.phone, dir: 'ltr' },
                { icon: <Mail size={15} />, label: 'البريد', value: memberDetail.email, dir: 'ltr' },
                { icon: <MapPin size={15} />, label: 'الدولة', value: memberDetail.country },
                { icon: <Calendar size={15} />, label: 'تاريخ التسجيل', value: memberDetail.created_at?.split('T')[0], dir: 'ltr' },
              ].map((item, i) => item.value ? (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }}>
                  <span style={{ color: 'var(--primary)', minWidth: 20, display: 'flex' }}>{item.icon}</span>
                  <span style={{ color: 'var(--text-muted)', minWidth: 70 }}>{item.label}:</span>
                  <span style={{ fontWeight: 600, color: 'var(--text-primary)' }} dir={item.dir}>{item.value}</span>
                </div>
              ) : null)}
              {memberDetail.referral_source && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }}>
                  <span style={{ color: 'var(--primary)', minWidth: 20, display: 'flex' }}><Star size={15} /></span>
                  <span style={{ color: 'var(--text-muted)', minWidth: 70 }}>المصدر:</span>
                  <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{memberDetail.referral_source}</span>
                </div>
              )}
            </div>

            <div className="btn-group mt-2">
              <button className="btn btn-primary btn-sm" onClick={() => { viewMemberCards(memberDetail.id); setMemberDetail(null); }}>
                <ClipboardList size={14} /> عرض البطاقات
              </button>
              <button className="btn btn-secondary btn-sm" onClick={() => setMemberDetail(null)}>إغلاق</button>
            </div>
          </div>
        </div>
      )}

      {/* ─── Member Cards History Modal ─── */}
      {selectedMember && (
        <div className="modal-overlay" onClick={() => { setSelectedMember(null); setAddCardDate(''); }}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 700 }}>
            <div className="flex-between mb-2">
              <div className="modal-title" style={{ margin: 0 }}>
                <ClipboardList size={18} /> بطاقات {selectedMember.full_name}
              </div>
              <button className="btn btn-secondary btn-sm" onClick={() => { setSelectedMember(null); setAddCardDate(''); }}>
                <X size={16} />
              </button>
            </div>

            {/* Add new card row */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <input type="date" className="filter-input" value={addCardDate}
                onChange={(e) => setAddCardDate(e.target.value)} dir="ltr"
                min="2026-02-19" max="2026-03-19"
                style={{ flex: 1 }} />
              <button className="btn btn-primary btn-sm" disabled={!addCardDate}
                onClick={() => {
                  setSelectedMember(null);
                  openCardDetail(selectedMember.id, addCardDate);
                  setAddCardDate('');
                }}>
                <Plus size={14} /> إضافة بطاقة
              </button>
            </div>

            {memberCards.length === 0 ? (
              <div className="empty-state"><div className="empty-state-text">لا توجد بطاقات</div></div>
            ) : (
              <div className="table-container">
                <table>
                  <thead><tr><th>التاريخ</th><th>المجموع</th><th>النسبة</th><th>التفاصيل</th></tr></thead>
                  <tbody>
                    {memberCards.map((c) => (
                      <tr key={c.id}>
                        <td>{c.date}</td>
                        <td>{c.total_score} / {c.max_score}</td>
                        <td><span className="badge badge-success">{c.percentage}%</span></td>
                        <td>
                          <button className="btn btn-secondary btn-sm" onClick={() => {
                            setSelectedMember(null);
                            openCardDetail(c.user_id, c.date);
                          }}>
                            عرض / تعديل
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ─── Card Detail / Edit Modal ─── */}
      {cardMember && (
        <div className="modal-overlay" onClick={closeCardDetail}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 550 }}>
            <div className="flex-between mb-2">
              <div className="modal-title" style={{ margin: 0 }}>
                بطاقة {cardMember.full_name} — {cardDate}
              </div>
              <button className="btn btn-secondary btn-sm" onClick={closeCardDetail}>
                <X size={16} />
              </button>
            </div>

            {editMode ? (
              <>
                {SCORE_FIELDS.map((f) => (
                  <div key={f.key} style={{ padding: '0.35rem 0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}>
                      {f.icon} {f.label}
                    </span>
                    <input
                      type="number" min="0" max="10" step="0.5"
                      value={editData[f.key] ?? 0}
                      onChange={(e) => setScore(f.key, e.target.value)}
                      style={{
                        width: 65, textAlign: 'center', padding: '0.3rem',
                        border: '1px solid var(--border)', borderRadius: 8,
                        fontSize: '0.9rem', fontWeight: 600, background: 'var(--background)',
                      }}
                    />
                  </div>
                ))}
                <div className="form-group mt-2">
                  <label className="form-label">وصف الأعمال الإضافية</label>
                  <textarea className="form-textarea" rows={2}
                    value={editData.extra_work_description || ''}
                    onChange={(e) => setEditData((d) => ({ ...d, extra_work_description: e.target.value }))}
                  />
                </div>
                <div className="btn-group mt-2">
                  <button className="btn btn-primary" onClick={handleSaveCard} disabled={saving}>
                    <Save size={14} /> {saving ? 'جاري الحفظ...' : 'حفظ'}
                  </button>
                  <button className="btn btn-secondary" onClick={() => setEditMode(false)}>إلغاء</button>
                </div>
              </>
            ) : (
              <>
                {cardDetail ? (
                  <>
                    <div className="flex-between mb-2">
                      <span style={{ fontWeight: 600 }}>المجموع</span>
                      <span style={{ fontWeight: 800, color: 'var(--accent)' }}>
                        {cardDetail.total_score} / {cardDetail.max_score} ({cardDetail.percentage}%)
                      </span>
                    </div>
                    <div className="progress-bar mb-2">
                      <div className="progress-fill green" style={{ width: `${cardDetail.percentage}%` }} />
                    </div>
                    {SCORE_FIELDS.map((f) => (
                      <div key={f.key} style={{ padding: '0.3rem 0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem' }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                          {f.icon} {f.label}
                        </span>
                        <span style={{ fontWeight: 700, color: 'var(--primary)', minWidth: 40, textAlign: 'center' }}>
                          {cardDetail[f.key] ?? 0}
                        </span>
                      </div>
                    ))}
                    {cardDetail.extra_work_description && (
                      <div style={{ marginTop: '0.75rem', padding: '0.5rem', background: 'var(--primary-light)', borderRadius: 8, fontSize: '0.85rem' }}>
                        <strong>وصف الأعمال الإضافية:</strong> {cardDetail.extra_work_description}
                      </div>
                    )}
                  </>
                ) : (
                  <div className="empty-state" style={{ padding: '1rem 0' }}>
                    <div className="empty-state-text">لم يتم تسجيل بطاقة لهذا اليوم</div>
                  </div>
                )}
                <div className="btn-group mt-2">
                  <button className="btn btn-primary" onClick={() => setEditMode(true)}>
                    {cardDetail ? 'تعديل البطاقة' : 'إدخال بطاقة'}
                  </button>
                  {cardDetail && (
                    <button className="btn btn-secondary" style={{ color: 'var(--danger, #e53e3e)' }} onClick={handleDeleteCard}>
                      <Trash2 size={14} /> حذف
                    </button>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
