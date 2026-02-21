import { useState, useEffect } from 'react';
import { Trophy, Medal, Filter } from 'lucide-react';
import api from '../utils/api';
import { useAuth } from '../context/AuthContext';
import Pagination, { paginate } from '../components/Pagination';

export default function LeaderboardPage() {
  const { user } = useAuth();
  const isSuperAdmin = user?.role === 'super_admin';
  const [data, setData] = useState([]);
  const [halqa, setHalqa] = useState(null);
  const [halqas, setHalqas] = useState([]);
  const [selectedHalqaId, setSelectedHalqaId] = useState('');
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);

  useEffect(() => {
    if (isSuperAdmin) {
      api.get('/supervisor/halqas')
        .then((res) => setHalqas(res.data.halqas))
        .catch(() => {});
    }
  }, [isSuperAdmin]);

  useEffect(() => {
    setLoading(true);
    const params = selectedHalqaId ? `?halqa_id=${selectedHalqaId}` : '';
    api.get(`/supervisor/leaderboard${params}`)
      .then((res) => {
        setData(res.data.leaderboard);
        setHalqa(res.data.halqa);
        setPage(1);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [selectedHalqaId]);

  return (
    <div>
      <h1 className="page-title"><Trophy size={24} /> ترتيب الحلقة</h1>
      <p className="page-subtitle">
        {isSuperAdmin
          ? (halqa ? `ترتيب مشاركي حلقة: ${halqa.name}` : 'ترتيب جميع المشاركين')
          : (halqa ? `ترتيب مشاركي حلقة: ${halqa.name}` : 'ترتيب المشاركين حسب مجموع النقاط')}
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

      {loading ? (
        <div className="loading"><div className="spinner" /></div>
      ) : data.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon"><Trophy size={48} /></div>
          <div className="empty-state-text">لا توجد بيانات بعد</div>
        </div>
      ) : (
        <div className="card">
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>الاسم</th>
                  <th>المجموع</th>
                  <th>البطاقات</th>
                  <th>النسبة</th>
                </tr>
              </thead>
              <tbody>
                {paginate(data, page).paged.map((r) => (
                  <tr key={r.user_id} style={r.user_id === user?.id ? { background: 'var(--primary-light)' } : {}}>
                    <td style={{ fontWeight: 800, color: r.rank <= 3 ? 'var(--gold)' : 'var(--text-muted)' }}>
                      {r.rank <= 3 ? <Medal size={16} style={{ color: 'var(--gold)', verticalAlign: 'middle' }} /> : r.rank}
                    </td>
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
          <Pagination page={page} totalPages={paginate(data, page).totalPages}
            total={data.length} onPageChange={setPage} />
        </div>
      )}
    </div>
  );
}
