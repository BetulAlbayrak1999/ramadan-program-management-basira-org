import { useState, useEffect } from 'react';
import api from '../utils/api';
import toast from 'react-hot-toast';
import { CircleDot, Pin, Pencil, Users, Save, Search, X, UserPlus, UserMinus, ArrowLeftRight, CheckCircle } from 'lucide-react';
import Pagination, { paginate } from '../components/Pagination';

export default function AdminHalqasPage() {
  const [halqas, setHalqas] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [editHalqa, setEditHalqa] = useState(null);
  const [newName, setNewName] = useState('');
  const [newSupervisor, setNewSupervisor] = useState('');
  const [assignModal, setAssignModal] = useState(null);
  const [selectedMembers, setSelectedMembers] = useState([]);

  // Assign modal filters
  const [assignSearch, setAssignSearch] = useState('');
  const [assignGender, setAssignGender] = useState('');
  const [assignSort, setAssignSort] = useState('asc');
  const [assignHalqaFilter, setAssignHalqaFilter] = useState('');
  const [assignPage, setAssignPage] = useState(1);
  const [confirmAssign, setConfirmAssign] = useState(null);

  // Supervisor picker filters (shared for create & edit modals)
  const [supSearch, setSupSearch] = useState('');
  const [supGender, setSupGender] = useState('');

  // Main page filters
  const [halqaSearch, setHalqaSearch] = useState('');
  const [memberFilter, setMemberFilter] = useState('all');
  const [memberHalqaFilter, setMemberHalqaFilter] = useState('');
  const [memberPage, setMemberPage] = useState(1);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [hRes, uRes] = await Promise.all([
        api.get('/admin/halqas'),
        api.get('/admin/users?status=active'),
      ]);
      setHalqas(hRes.data.halqas);
      setUsers(uRes.data.users);
    } catch { toast.error('خطأ'); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchData(); }, []);

  const createHalqa = async () => {
    if (!newName.trim()) { toast.error('اسم الحلقة مطلوب'); return; }
    try {
      await api.post('/admin/halqa', { name: newName, supervisor_id: newSupervisor || null });
      toast.success('تم إنشاء الحلقة');
      setShowCreate(false); setNewName(''); setNewSupervisor('');
      fetchData();
    } catch (err) { toast.error(err.response?.data?.error || 'خطأ'); }
  };

  const updateHalqa = async () => {
    try {
      await api.put(`/admin/halqa/${editHalqa.id}`, {
        name: editHalqa.name,
        supervisor_id: editHalqa.supervisor_id || null,
      });
      toast.success('تم تحديث الحلقة');
      setEditHalqa(null);
      fetchData();
    } catch (err) { toast.error(err.response?.data?.error || 'خطأ'); }
  };

  const openAssign = (halqa) => {
    const currentMembers = users.filter((u) => u.halqa_id === halqa.id).map((u) => u.id);
    setSelectedMembers(currentMembers);
    setAssignSearch('');
    setAssignGender('');
    setAssignHalqaFilter('');
    setAssignSort('asc');
    setAssignPage(1);
    setAssignModal(halqa);
  };

  const prepareConfirm = () => {
    const currentIds = users.filter((u) => u.halqa_id === assignModal.id).map((u) => u.id);
    const added = selectedMembers.filter((id) => !currentIds.includes(id));
    const removed = currentIds.filter((id) => !selectedMembers.includes(id));
    const movedFromOther = added.filter((id) => {
      const u = users.find((x) => x.id === id);
      return u && u.halqa_id && u.halqa_id !== assignModal.id;
    });
    const addedNew = added.filter((id) => !movedFromOther.includes(id));

    const getName = (id) => users.find((u) => u.id === id)?.full_name || '';
    const getHalqa = (id) => users.find((u) => u.id === id)?.halqa_name || '';

    setConfirmAssign({
      added: addedNew.map((id) => getName(id)),
      moved: movedFromOther.map((id) => ({ name: getName(id), from: getHalqa(id) })),
      removed: removed.map((id) => getName(id)),
      unchanged: selectedMembers.length - addedNew.length - movedFromOther.length,
    });
  };

  const saveAssign = async () => {
    try {
      await api.post(`/admin/halqa/${assignModal.id}/assign-members`, { user_ids: selectedMembers });
      const otherUsers = users.filter((u) => u.halqa_id === assignModal.id && !selectedMembers.includes(u.id));
      for (const u of otherUsers) {
        await api.post(`/admin/user/${u.id}/assign-halqa`, { halqa_id: null });
      }
      toast.success('تم تعيين المشاركين');
      setConfirmAssign(null);
      setAssignModal(null);
      fetchData();
    } catch { toast.error('خطأ'); }
  };

  const toggleMember = (id) => {
    setSelectedMembers((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const supervisors = users.filter((u) => u.role === 'supervisor' || u.role === 'super_admin');

  const genderMatches = (userGender, filterGender) => {
    if (filterGender === 'male') return ['male', 'ذكر'].includes(userGender);
    if (filterGender === 'female') return ['female', 'أنثى'].includes(userGender);
    return true;
  };

  // Filtered supervisors for create/edit modals
  const filteredSupervisors = supervisors.filter((s) => {
    if (supSearch && !s.full_name.includes(supSearch)) return false;
    if (supGender && !genderMatches(s.gender, supGender)) return false;
    return true;
  });
  const genderLabel = (g) => ['male', 'ذكر'].includes(g) ? 'ذكر' : 'أنثى';

  // Filter, sort, and paginate users for assign modal

  const filteredAssignUsers = users
    .filter((u) => {
      if (assignSearch && !u.full_name.includes(assignSearch)) return false;
      if (assignGender && !genderMatches(u.gender, assignGender)) return false;
      if (assignHalqaFilter === 'this' && u.halqa_id !== assignModal?.id) return false;
      if (assignHalqaFilter === 'assigned' && !u.halqa_id) return false;
      if (assignHalqaFilter === 'unassigned' && u.halqa_id) return false;
      return true;
    })
    .sort((a, b) => {
      const cmp = (a.full_name || '').localeCompare(b.full_name || '', 'ar');
      return assignSort === 'asc' ? cmp : -cmp;
    });

  const assignPaginated = paginate(filteredAssignUsers, assignPage);

  // Main page: halqa grid filtering
  const filteredHalqas = halqas.filter((h) => !halqaSearch || h.name.includes(halqaSearch));
  const unassignedCount = users.filter((u) => !u.halqa_id).length;

  // Main page: participants list filtering
  const filteredMembers = users
    .filter((u) => {
      if (memberFilter === 'assigned' && !u.halqa_id) return false;
      if (memberFilter === 'unassigned' && u.halqa_id) return false;
      if (memberHalqaFilter && String(u.halqa_id) !== memberHalqaFilter) return false;
      return true;
    })
    .sort((a, b) => (a.full_name || '').localeCompare(b.full_name || '', 'ar'));
  const membersPaginated = paginate(filteredMembers, memberPage);

  if (loading) return <div className="loading"><div className="spinner" /></div>;

  return (
    <div>
      <h1 className="page-title"><CircleDot size={22} /> إدارة الحلقات</h1>
      <p className="page-subtitle">إنشاء وإدارة الحلقات وتعيين المشاركين والمشرفين</p>

      {/* Summary Stats */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon"><CircleDot size={20} /></div>
          <div className="stat-value">{halqas.length}</div>
          <div className="stat-label">عدد الحلقات</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon"><Users size={20} /></div>
          <div className="stat-value">{users.length}</div>
          <div className="stat-label">إجمالي المشاركين</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon"><UserPlus size={20} /></div>
          <div className="stat-value">{users.length - unassignedCount}</div>
          <div className="stat-label">معيّنون في حلقات</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon"><UserMinus size={20} /></div>
          <div className="stat-value gold">{unassignedCount}</div>
          <div className="stat-label">غير معيّنين</div>
        </div>
      </div>

      {/* Search & Create */}
      <div className="filters-bar mb-2">
        <div style={{ position: 'relative', flex: '1 1 200px' }}>
          <Search size={14} style={{ position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input className="filter-input" placeholder="بحث باسم الحلقة..."
            value={halqaSearch} onChange={(e) => setHalqaSearch(e.target.value)}
            style={{ paddingRight: 32, width: '100%' }} />
        </div>
        <button className="btn btn-primary btn-sm" onClick={() => { setSupSearch(''); setSupGender(''); setShowCreate(true); }}>+ إنشاء حلقة جديدة</button>
      </div>

      {/* Halqa Grid */}
      {filteredHalqas.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon"><CircleDot size={48} /></div>
          <div className="empty-state-text">{halqaSearch ? 'لا توجد حلقات تطابق البحث' : 'لا توجد حلقات بعد'}</div>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
          {filteredHalqas.map((h) => (
            <div className="card" key={h.id}>
              <div className="card-header">
                <div className="card-title"><Pin size={16} /> {h.name}</div>
                <div className="btn-group">
                  <button className="btn btn-secondary btn-sm" onClick={() => { setSupSearch(''); setSupGender(''); setEditHalqa({ ...h, original_supervisor_id: h.supervisor_id }); }}><Pencil size={14} /></button>
                  <button className="btn btn-gold btn-sm" onClick={() => openAssign(h)}><Users size={14} /> تعيين</button>
                </div>
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                المشرف: <strong>{h.supervisor_name || 'غير محدد'}</strong>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <div style={{ flex: 1, textAlign: 'center', padding: '0.4rem', background: 'var(--primary-light)', borderRadius: 8 }}>
                  <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--primary)' }}>{h.member_count}</div>
                  <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>إجمالي</div>
                </div>
                <div style={{ flex: 1, textAlign: 'center', padding: '0.4rem', background: '#eff6ff', borderRadius: 8 }}>
                  <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#2563eb' }}>{h.male_count || 0}</div>
                  <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>ذكور</div>
                </div>
                <div style={{ flex: 1, textAlign: 'center', padding: '0.4rem', background: '#fdf2f8', borderRadius: 8 }}>
                  <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#db2777' }}>{h.female_count || 0}</div>
                  <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>إناث</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Participants Section */}
      <div className="card" style={{ marginTop: '1.5rem' }}>
        <div className="card-title mb-2" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Users size={18} /> المشاركون
        </div>

        <div className="filters-bar mb-2">
          <select className="filter-input" value={memberFilter}
            onChange={(e) => { setMemberFilter(e.target.value); setMemberPage(1); }}>
            <option value="all">الكل ({users.length})</option>
            <option value="assigned">معيّنون في حلقات ({users.length - unassignedCount})</option>
            <option value="unassigned">غير معيّنين ({unassignedCount})</option>
          </select>
          <select className="filter-input" value={memberHalqaFilter}
            onChange={(e) => { setMemberHalqaFilter(e.target.value); setMemberPage(1); }}>
            <option value="">كل الحلقات</option>
            {halqas.map((h) => <option key={h.id} value={h.id}>{h.name}</option>)}
          </select>
        </div>

        {filteredMembers.length === 0 ? (
          <div className="empty-state" style={{ padding: '2rem 0' }}>
            <div className="empty-state-icon"><Users size={36} /></div>
            <div className="empty-state-text">لا يوجد مشاركون</div>
          </div>
        ) : (
          <>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>رقم العضوية</th><th>الاسم</th><th>الجنس</th><th>الحلقة</th>
                  </tr>
                </thead>
                <tbody>
                  {membersPaginated.paged.map((u) => (
                    <tr key={u.id}>
                      <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{u.member_id}</td>
                      <td style={{ fontWeight: 600 }}>
                        {u.full_name}
                        {u.supervised_halqa_name && (
                          <span className="badge badge-info" style={{ marginRight: '0.4rem', fontSize: '0.65rem' }}>
                            مشرف: {u.supervised_halqa_name}
                          </span>
                        )}
                      </td>
                      <td>{['male', 'ذكر'].includes(u.gender) ? 'ذكر' : 'أنثى'}</td>
                      <td>
                        {u.halqa_name ? (
                          <span className="badge badge-success">{u.halqa_name}</span>
                        ) : (
                          <span className="badge badge-warning">غير معيّن</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination page={memberPage} totalPages={membersPaginated.totalPages}
              total={filteredMembers.length} onPageChange={setMemberPage} />
          </>
        )}
      </div>

      {/* Create Modal */}
      {showCreate && (
        <div className="modal-overlay" onClick={() => setShowCreate(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-title">إنشاء حلقة جديدة</div>
            <div className="form-group">
              <label className="form-label">اسم الحلقة</label>
              <input className="form-input" value={newName} onChange={(e) => setNewName(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">المشرف</label>
              <div className="filters-bar mb-1" style={{ gap: '0.4rem' }}>
                <div style={{ position: 'relative', flex: '1 1 140px' }}>
                  <Search size={13} style={{ position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                  <input className="filter-input" placeholder="بحث باسم المشرف..."
                    value={supSearch} onChange={(e) => setSupSearch(e.target.value)}
                    style={{ paddingRight: 28, width: '100%', fontSize: '0.78rem' }} />
                </div>
                <select className="filter-input" value={supGender}
                  onChange={(e) => setSupGender(e.target.value)} style={{ fontSize: '0.78rem', minWidth: 80 }}>
                  <option value="">كل الجنسين</option>
                  <option value="male">ذكر</option>
                  <option value="female">أنثى</option>
                </select>
              </div>
              <div style={{ border: '1px solid var(--border)', borderRadius: 8, maxHeight: 180, overflowY: 'auto' }}>
                <div
                  onClick={() => setNewSupervisor('')}
                  style={{
                    padding: '0.5rem 0.75rem', cursor: 'pointer', fontSize: '0.82rem',
                    background: !newSupervisor ? 'var(--primary)' : 'transparent',
                    color: !newSupervisor ? '#fff' : 'var(--text-primary)',
                    borderBottom: '1px solid var(--border)',
                  }}>
                  بدون مشرف
                </div>
                {filteredSupervisors.map((s) => (
                  <div key={s.id}
                    onClick={() => setNewSupervisor(String(s.id))}
                    style={{
                      padding: '0.5rem 0.75rem', cursor: 'pointer', fontSize: '0.82rem',
                      background: String(s.id) === newSupervisor ? 'var(--primary)' : 'transparent',
                      color: String(s.id) === newSupervisor ? '#fff' : 'var(--text-primary)',
                      borderBottom: '1px solid var(--border)',
                    }}>
                    {s.full_name} — {genderLabel(s.gender)}
                  </div>
                ))}
                {filteredSupervisors.length === 0 && (
                  <div style={{ padding: '0.75rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                    لا توجد نتائج
                  </div>
                )}
              </div>
            </div>
            <div className="btn-group">
              <button className="btn btn-primary" onClick={createHalqa}>إنشاء</button>
              <button className="btn btn-secondary" onClick={() => setShowCreate(false)}>إلغاء</button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {editHalqa && (
        <div className="modal-overlay" onClick={() => setEditHalqa(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-title">تعديل الحلقة</div>
            {/* Current supervisor info */}
            <div style={{
              background: 'var(--primary-light)', borderRadius: 8, padding: '0.5rem 0.75rem',
              marginBottom: '0.75rem', fontSize: '0.82rem', display: 'flex', alignItems: 'center', gap: '0.4rem',
            }}>
              <span style={{ color: 'var(--text-muted)' }}>المشرف الحالي:</span>
              <strong style={{ color: 'var(--primary)' }}>
                {editHalqa.supervisor_name || 'بدون مشرف'}
              </strong>
            </div>
            <div className="form-group">
              <label className="form-label">اسم الحلقة</label>
              <input className="form-input" value={editHalqa.name}
                onChange={(e) => setEditHalqa((h) => ({ ...h, name: e.target.value }))} />
            </div>
            <div className="form-group">
              <label className="form-label">المشرف</label>
              <div className="filters-bar mb-1" style={{ gap: '0.4rem' }}>
                <div style={{ position: 'relative', flex: '1 1 140px' }}>
                  <Search size={13} style={{ position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                  <input className="filter-input" placeholder="بحث باسم المشرف..."
                    value={supSearch} onChange={(e) => setSupSearch(e.target.value)}
                    style={{ paddingRight: 28, width: '100%', fontSize: '0.78rem' }} />
                </div>
                <select className="filter-input" value={supGender}
                  onChange={(e) => setSupGender(e.target.value)} style={{ fontSize: '0.78rem', minWidth: 80 }}>
                  <option value="">كل الجنسين</option>
                  <option value="male">ذكر</option>
                  <option value="female">أنثى</option>
                </select>
              </div>
              <div style={{ border: '1px solid var(--border)', borderRadius: 8, maxHeight: 180, overflowY: 'auto' }}>
                <div
                  onClick={() => setEditHalqa((h) => ({ ...h, supervisor_id: null }))}
                  style={{
                    padding: '0.5rem 0.75rem', cursor: 'pointer', fontSize: '0.82rem',
                    background: !editHalqa.supervisor_id ? 'var(--primary)' : 'transparent',
                    color: !editHalqa.supervisor_id ? '#fff' : 'var(--text-primary)',
                    borderBottom: '1px solid var(--border)',
                  }}>
                  بدون مشرف
                </div>
                {filteredSupervisors.map((s) => {
                  const isSelected = s.id === editHalqa.supervisor_id;
                  const isOriginal = s.id === editHalqa.original_supervisor_id;
                  return (
                    <div key={s.id}
                      onClick={() => setEditHalqa((h) => ({ ...h, supervisor_id: s.id }))}
                      style={{
                        padding: '0.5rem 0.75rem', cursor: 'pointer', fontSize: '0.82rem',
                        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                        background: isSelected ? 'var(--primary)' : isOriginal ? '#e0f2fe' : 'transparent',
                        color: isSelected ? '#fff' : 'var(--text-primary)',
                        borderBottom: '1px solid var(--border)',
                        borderRight: isOriginal && !isSelected ? '3px solid var(--gold)' : 'none',
                      }}>
                      <span>{s.full_name} — {genderLabel(s.gender)}</span>
                      {isOriginal && !isSelected && (
                        <span style={{ fontSize: '0.68rem', color: 'var(--gold)', fontWeight: 700 }}>الحالي</span>
                      )}
                    </div>
                  );
                })}
                {filteredSupervisors.length === 0 && (
                  <div style={{ padding: '0.75rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                    لا توجد نتائج
                  </div>
                )}
              </div>
            </div>
            <div className="btn-group">
              <button className="btn btn-primary" onClick={updateHalqa}>حفظ</button>
              <button className="btn btn-secondary" onClick={() => setEditHalqa(null)}>إلغاء</button>
            </div>
          </div>
        </div>
      )}

      {/* Assign Members Modal */}
      {assignModal && (
        <div className="modal-overlay" onClick={() => setAssignModal(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 750, width: '95vw' }}>
            <div className="flex-between mb-2">
              <div className="modal-title" style={{ margin: 0 }}>
                <Users size={18} /> تعيين مشاركين لحلقة: {assignModal.name}
              </div>
              <button className="btn btn-secondary btn-sm" onClick={() => setAssignModal(null)}>
                <X size={16} />
              </button>
            </div>

            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
              اختر المشاركين ({selectedMembers.length} محدد)
            </p>

            {/* Filters */}
            <div className="filters-bar mb-2" style={{ flexWrap: 'wrap' }}>
              <div style={{ position: 'relative', flex: '1 1 180px' }}>
                <Search size={14} style={{ position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                <input className="filter-input" placeholder="بحث بالاسم..."
                  value={assignSearch} onChange={(e) => { setAssignSearch(e.target.value); setAssignPage(1); }}
                  style={{ paddingRight: 32, width: '100%' }} />
              </div>
              <select className="filter-input" value={assignGender}
                onChange={(e) => { setAssignGender(e.target.value); setAssignPage(1); }}>
                <option value="">كل الجنسين</option>
                <option value="male">ذكر</option>
                <option value="female">أنثى</option>
              </select>
              <select className="filter-input" value={assignHalqaFilter}
                onChange={(e) => { setAssignHalqaFilter(e.target.value); setAssignPage(1); }}>
                <option value="">الكل</option>
                <option value="this">أعضاء هذه الحلقة</option>
                <option value="assigned">معيّنون في حلقات</option>
                <option value="unassigned">غير معيّنين</option>
              </select>
              <select className="filter-input" value={assignSort}
                onChange={(e) => { setAssignSort(e.target.value); setAssignPage(1); }}>
                <option value="asc">الاسم تصاعدي</option>
                <option value="desc">الاسم تنازلي</option>
              </select>
            </div>

            {/* Users Table */}
            <div className="table-container" style={{ maxHeight: 420, overflowY: 'auto' }}>
              <table>
                <thead>
                  <tr>
                    <th style={{ width: 40 }}></th>
                    <th>الاسم</th>
                    <th>الجنس</th>
                    <th>الحلقة الحالية</th>
                  </tr>
                </thead>
                <tbody>
                  {assignPaginated.paged.map((u) => (
                    <tr key={u.id}
                      onClick={() => toggleMember(u.id)}
                      style={{
                        cursor: 'pointer',
                        background: selectedMembers.includes(u.id) ? 'var(--primary-light)' : 'transparent',
                      }}>
                      <td>
                        <input type="checkbox" checked={selectedMembers.includes(u.id)}
                          onChange={() => toggleMember(u.id)}
                          onClick={(e) => e.stopPropagation()} />
                      </td>
                      <td style={{ fontWeight: 600 }}>
                        {u.full_name}
                        {u.supervised_halqa_name && (
                          <span className="badge badge-info" style={{ marginRight: '0.4rem', fontSize: '0.65rem' }}>
                            مشرف: {u.supervised_halqa_name}
                          </span>
                        )}
                      </td>
                      <td>{['male', 'ذكر'].includes(u.gender) ? 'ذكر' : 'أنثى'}</td>
                      <td>
                        {u.halqa_id === assignModal.id ? (
                          <span className="badge badge-success">هذه الحلقة</span>
                        ) : u.halqa_name ? (
                          <span className="badge badge-warning">{u.halqa_name}</span>
                        ) : (
                          <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>غير معيّن</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <Pagination page={assignPage} totalPages={assignPaginated.totalPages}
              total={assignPaginated.total} onPageChange={setAssignPage} />

            <div className="btn-group mt-2">
              <button className="btn btn-primary" onClick={prepareConfirm}>
                <Save size={14} /> حفظ التعيين
              </button>
              <button className="btn btn-secondary" onClick={() => setAssignModal(null)}>إلغاء</button>
            </div>
          </div>
        </div>
      )}

      {/* Confirm Assign Modal */}
      {confirmAssign && (
        <div className="modal-overlay" onClick={() => setConfirmAssign(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 500 }}>
            <div className="modal-title">
              <CheckCircle size={18} /> تأكيد تعيين المشاركين — {assignModal?.name}
            </div>

            {confirmAssign.added.length === 0 && confirmAssign.moved.length === 0 && confirmAssign.removed.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textAlign: 'center', padding: '1rem 0' }}>
                لا توجد تغييرات
              </p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {confirmAssign.added.length > 0 && (
                  <div style={{ background: 'var(--primary-light)', borderRadius: 10, padding: '0.75rem' }}>
                    <div style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--primary)', marginBottom: '0.4rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      <UserPlus size={15} /> إضافة ({confirmAssign.added.length})
                    </div>
                    {confirmAssign.added.map((name, i) => (
                      <div key={i} style={{ fontSize: '0.8rem', padding: '0.15rem 0', color: 'var(--text-primary)' }}>• {name}</div>
                    ))}
                  </div>
                )}

                {confirmAssign.moved.length > 0 && (
                  <div style={{ background: 'var(--gold-light)', borderRadius: 10, padding: '0.75rem' }}>
                    <div style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--gold)', marginBottom: '0.4rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      <ArrowLeftRight size={15} /> نقل من حلقة أخرى ({confirmAssign.moved.length})
                    </div>
                    {confirmAssign.moved.map((m, i) => (
                      <div key={i} style={{ fontSize: '0.8rem', padding: '0.15rem 0', color: 'var(--text-primary)' }}>
                        • {m.name} <span style={{ color: 'var(--text-muted)' }}>(من: {m.from})</span>
                      </div>
                    ))}
                  </div>
                )}

                {confirmAssign.removed.length > 0 && (
                  <div style={{ background: '#fef2f2', borderRadius: 10, padding: '0.75rem' }}>
                    <div style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--danger)', marginBottom: '0.4rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      <UserMinus size={15} /> إزالة ({confirmAssign.removed.length})
                    </div>
                    {confirmAssign.removed.map((name, i) => (
                      <div key={i} style={{ fontSize: '0.8rem', padding: '0.15rem 0', color: 'var(--text-primary)' }}>• {name}</div>
                    ))}
                  </div>
                )}

                {confirmAssign.unchanged > 0 && (
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: 0 }}>
                    بالإضافة إلى {confirmAssign.unchanged} مشارك بدون تغيير
                  </p>
                )}
              </div>
            )}

            <div className="btn-group mt-2">
              <button className="btn btn-primary" onClick={saveAssign}
                disabled={confirmAssign.added.length === 0 && confirmAssign.moved.length === 0 && confirmAssign.removed.length === 0}>
                <CheckCircle size={14} /> تأكيد
              </button>
              <button className="btn btn-secondary" onClick={() => setConfirmAssign(null)}>رجوع</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
