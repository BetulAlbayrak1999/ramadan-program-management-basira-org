import React, { useState, useEffect, useCallback } from 'react';
import api from '../utils/api';
import toast from 'react-hot-toast';
import * as XLSX from 'xlsx';
import Pagination, { paginate } from '../components/Pagination';

export default function AdminUsersPage() {
  const [tab, setTab] = useState('pending');
  const [users, setUsers] = useState([]);
  const [halqas, setHalqas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedUser, setSelectedUser] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [resetPwd, setResetPwd] = useState('');
  const [rejectNote, setRejectNote] = useState('');
  const [showRejectModal, setShowRejectModal] = useState(null);
  const [importFile, setImportFile] = useState(null);
  const [importPreview, setImportPreview] = useState(null);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState(null);
  const [page, setPage] = useState(1);

  // Bulk selection
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [bulkHalqaId, setBulkHalqaId] = useState('');
  const [confirmAction, setConfirmAction] = useState(null);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const status = tab === 'all' ? '' : tab;
      const params = new URLSearchParams();
      if (status) params.append('status', status);
      if (search) params.append('search', search);
      const res = await api.get(`/admin/users?${params.toString()}`);
      setUsers(res.data.users);
      setPage(1);
    } catch { toast.error('خطأ في تحميل البيانات'); }
    finally { setLoading(false); }
  }, [tab, search]);

  useEffect(() => { fetchUsers(); }, [fetchUsers]);
  useEffect(() => {
    api.get('/admin/halqas').then((res) => setHalqas(res.data.halqas)).catch(() => {});
  }, []);

  const approve = async (id) => {
    await api.post(`/admin/registration/${id}/approve`);
    toast.success('تم قبول الطلب');
    fetchUsers();
  };

  const reject = async (id) => {
    await api.post(`/admin/registration/${id}/reject`, { note: rejectNote });
    toast.success('تم رفض الطلب');
    setShowRejectModal(null);
    setRejectNote('');
    fetchUsers();
  };

  const withdraw = async (id) => {
    await api.post(`/admin/user/${id}/withdraw`);
    toast.success('تم سحب المشارك');
    fetchUsers();
  };

  const activate = async (id) => {
    await api.post(`/admin/user/${id}/activate`);
    toast.success('تم تفعيل المشارك');
    fetchUsers();
  };

  const setRole = async (id, role) => {
    try {
      await api.post(`/admin/user/${id}/set-role`, { role });
      toast.success('تم تحديث الصلاحية');
      fetchUsers();
    } catch (err) { toast.error(err.response?.data?.error || 'خطأ'); }
  };

  const openEdit = (u) => {
    setSelectedUser(u);
    setEditForm({
      full_name: u.full_name, gender: u.gender, age: u.age,
      phone: u.phone, country: u.country, halqa_id: u.halqa_id || '',
    });
  };

  const saveUserEdit = async () => {
    try {
      await api.put(`/admin/user/${selectedUser.id}`, editForm);
      toast.success('تم تحديث البيانات');
      setSelectedUser(null);
      fetchUsers();
    } catch (err) { toast.error(err.response?.data?.error || 'خطأ'); }
  };

  const resetPassword = async (id) => {
    if (!resetPwd || resetPwd.length < 6) { toast.error('كلمة المرور يجب أن تكون 6 أحرف على الأقل'); return; }
    try {
      await api.post(`/admin/user/${id}/reset-password`, { new_password: resetPwd });
      toast.success('تم إعادة تعيين كلمة المرور');
      setResetPwd('');
    } catch (err) { toast.error(err.response?.data?.error || 'خطأ'); }
  };

  const assignHalqa = async (userId, halqaId) => {
    await api.post(`/admin/user/${userId}/assign-halqa`, { halqa_id: halqaId || null });
    toast.success('تم تعيين الحلقة');
    fetchUsers();
  };

  const handleFileSelect = (file) => {
    if (!file) return;
    setImportFile(file);
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const wb = XLSX.read(e.target.result, { type: 'array' });
        const ws = wb.Sheets[wb.SheetNames[0]];
        const rows = XLSX.utils.sheet_to_json(ws, { defval: '' });
        const validRows = rows.filter((r) => {
          const name = String(r['الاسم'] || '').trim();
          const email = String(r['البريد'] || '').trim();
          return name && email;
        });
        if (!validRows.length) { toast.error('الملف فارغ أو لا يحتوي بيانات صالحة'); setImportFile(null); return; }
        const genderCount = { male: 0, female: 0 };
        validRows.forEach((r) => {
          const g = String(r['الجنس'] || '').trim().toLowerCase();
          if (g === 'ذكر' || g === 'male') genderCount.male++;
          else if (g === 'أنثى' || g === 'female') genderCount.female++;
        });
        setImportPreview({ rows: validRows, genderCount });
      } catch { toast.error('خطأ في قراءة الملف'); setImportFile(null); }
    };
    reader.readAsArrayBuffer(file);
  };

  const confirmImport = async () => {
    if (!importFile) return;
    setImporting(true);
    const formData = new FormData();
    formData.append('file', importFile);
    try {
      const res = await api.post('/admin/import', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
      toast.success(res.data.message);
      setImportFile(null);
      setImportPreview(null);
      if (res.data.errors?.length) {
        setImportResult(res.data);
      }
      fetchUsers();
    } catch (err) { toast.error(err.response?.data?.detail || 'خطأ'); }
    finally { setImporting(false); }
  };

  const cancelImport = () => {
    setImportFile(null);
    setImportPreview(null);
  };

  const { paged, totalPages, total } = paginate(users, page);

  // Clear selection on tab change
  useEffect(() => { setSelectedIds(new Set()); }, [tab]);

  // Bulk selection helpers
  const toggleSelect = (id) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const toggleSelectAll = () => {
    if (selectedIds.size === paged.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(paged.map((u) => u.id)));
    }
  };

  const bulkAction = async (action, extra = {}) => {
    const ids = Array.from(selectedIds);
    if (!ids.length) { toast.error('اختر مشاركين أولاً'); return; }
    try {
      const res = await api.post(`/admin/bulk/${action}`, { user_ids: ids, ...extra });
      toast.success(res.data.message);
      setSelectedIds(new Set());
      fetchUsers();
    } catch (err) { toast.error(err.response?.data?.error || 'خطأ'); }
  };

  const exportUsers = async (format) => {
    try {
      const params = new URLSearchParams();
      params.append('format', format);
      const status = tab === 'all' ? '' : tab;
      if (status) params.append('status', status);
      if (search) params.append('search', search);
      const res = await api.get(`/admin/export-users?${params.toString()}`, { responseType: 'blob' });
      const blob = new Blob([res.data], {
        type: format === 'xlsx'
          ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
          : 'text/csv;charset=utf-8-sig',
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `users_report.${format}`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success('تم التصدير بنجاح');
    } catch { toast.error('خطأ في التصدير'); }
  };

  // ── Confirmation wrappers ──────────────────────────────────────────────────

  const confirmApprove = (user) => {
    setConfirmAction({
      title: 'قبول طلب التسجيل',
      message: `هل تريد قبول طلب تسجيل "${user.full_name}"؟`,
      details: 'سيتم تغيير حالة المشارك من "قيد المراجعة" إلى "نشط".',
      onConfirm: () => approve(user.id),
    });
  };

  const confirmWithdraw = (user) => {
    setConfirmAction({
      title: 'سحب المشارك',
      message: `هل تريد سحب المشارك "${user.full_name}"؟`,
      details: 'سيتم تغيير حالة المشارك من "نشط" إلى "منسحب".',
      onConfirm: () => withdraw(user.id),
    });
  };

  const confirmActivate = (user) => {
    setConfirmAction({
      title: 'تفعيل المشارك',
      message: `هل تريد تفعيل المشارك "${user.full_name}"؟`,
      details: `سيتم تغيير حالة المشارك من "${statusLabel[user.status]}" إلى "نشط".`,
      onConfirm: () => activate(user.id),
    });
  };

  const confirmSetRole = (user, newRole) => {
    if (user.role === newRole) return;
    setConfirmAction({
      title: 'تغيير الصلاحية',
      message: `هل تريد تغيير صلاحية "${user.full_name}"؟`,
      details: `سيتم تغيير الصلاحية من "${roleLabel[user.role]}" إلى "${roleLabel[newRole]}".`,
      onConfirm: () => setRole(user.id, newRole),
    });
  };

  const confirmAssignHalqa = (user, halqaId) => {
    const halqaName = halqaId ? halqas.find((h) => h.id === parseInt(halqaId))?.name : 'بدون حلقة';
    const currentName = user.halqa_id ? halqas.find((h) => h.id === user.halqa_id)?.name || 'غير معروفة' : 'بدون حلقة';
    setConfirmAction({
      title: 'تعيين الحلقة',
      message: `هل تريد تغيير حلقة "${user.full_name}"؟`,
      details: `سيتم النقل من "${currentName}" إلى "${halqaName}".`,
      onConfirm: () => assignHalqa(user.id, halqaId ? parseInt(halqaId) : null),
    });
  };

  const requestBulkAction = (action) => {
    const selected = users.filter((u) => selectedIds.has(u.id));
    if (!selected.length) { toast.error('اختر مشاركين أولاً'); return; }

    const rules = {
      approve: {
        title: 'قبول الطلبات',
        check: (u) => u.status === 'pending',
        explanation: 'يمكن قبول الطلبات ذات الحالة "قيد المراجعة" فقط. لقبول مشارك يجب أن تكون حالته "قيد المراجعة".',
      },
      reject: {
        title: 'رفض الطلبات',
        check: (u) => u.status === 'pending',
        explanation: 'يمكن رفض الطلبات ذات الحالة "قيد المراجعة" فقط. لرفض مشارك يجب أن تكون حالته "قيد المراجعة".',
      },
      activate: {
        title: 'تفعيل المشاركين',
        check: (u) => ['rejected', 'withdrawn'].includes(u.status),
        explanation: 'يمكن تفعيل المشاركين ذوي الحالة "مرفوض" أو "منسحب" فقط. المشاركون النشطون أو قيد المراجعة لا يمكن تفعيلهم.',
      },
      withdraw: {
        title: 'سحب المشاركين',
        check: (u) => u.status === 'active',
        explanation: 'يمكن سحب المشاركين ذوي الحالة "نشط" فقط. لسحب مشارك يجب أن يكون نشطاً أولاً.',
      },
    };

    const rule = rules[action];
    const eligible = selected.filter(rule.check);
    const ineligible = selected.filter((u) => !rule.check(u));

    if (eligible.length === 0) {
      setConfirmAction({
        title: `لا يمكن تنفيذ: ${rule.title}`,
        message: rule.explanation,
        warnings: ineligible.map((u) => `${u.full_name} — ${statusLabel[u.status]}`),
        canProceed: false,
      });
      return;
    }

    const warnings = ineligible.length > 0
      ? [`${ineligible.length} مشارك لا ينطبق عليهم هذا الإجراء وسيتم تجاهلهم:`,
        ...ineligible.map((u) => `• ${u.full_name} (${statusLabel[u.status]})`)]
      : [];

    setConfirmAction({
      title: rule.title,
      message: `سيتم تطبيق "${rule.title}" على ${eligible.length} مشارك`,
      details: eligible.map((u) => u.full_name).join('، '),
      warnings,
      onConfirm: () => bulkAction(action),
    });
  };

  const confirmBulkAssignHalqa = () => {
    if (!bulkHalqaId) { toast.error('اختر حلقة أولاً'); return; }
    const halqaName = halqas.find((h) => h.id === parseInt(bulkHalqaId))?.name;
    const selected = users.filter((u) => selectedIds.has(u.id));
    setConfirmAction({
      title: 'تعيين حلقة للمحددين',
      message: `سيتم تعيين ${selected.length} مشارك إلى حلقة "${halqaName}"`,
      details: selected.map((u) => u.full_name).join('، '),
      onConfirm: () => bulkAction('assign-halqa', { halqa_id: parseInt(bulkHalqaId) }),
    });
  };

  const downloadTemplate = async () => {
    const res = await api.get('/admin/import-template', { responseType: 'blob' });
    const url = URL.createObjectURL(res.data);
    const a = document.createElement('a'); a.href = url; a.download = 'import_template.xlsx'; a.click();
  };

  const statusLabel = { active: 'نشط', pending: 'قيد المراجعة', rejected: 'مرفوض', withdrawn: 'منسحب' };
  const statusBadge = { active: 'badge-success', pending: 'badge-warning', rejected: 'badge-danger', withdrawn: 'badge-info' };
  const roleLabel = { participant: 'مشارك', supervisor: 'مشرف', super_admin: 'سوبر آدمن' };

  return (
    <div>
      <h1 className="page-title">👥 إدارة المستخدمين</h1>
      <p className="page-subtitle">إدارة المشاركين وطلبات التسجيل</p>

      <div className="tabs">
        {['pending', 'active', 'rejected', 'withdrawn', 'all'].map((t) => (
          <button key={t} className={`tab ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
            {t === 'all' ? 'الكل' : statusLabel[t]}
          </button>
        ))}
      </div>

      <div className="filters-bar">
        <input className="filter-input" style={{ flex: 1, minWidth: 200 }} placeholder="🔍 بحث بالاسم أو البريد..."
          value={search} onChange={(e) => setSearch(e.target.value)} />
        <button className="btn btn-secondary btn-sm" onClick={downloadTemplate}>📥 قالب الاستيراد</button>
        <label className="btn btn-gold btn-sm" style={{ cursor: 'pointer' }}>
          📤 استيراد Excel
          <input type="file" accept=".xlsx" style={{ display: 'none' }}
            onChange={(e) => { handleFileSelect(e.target.files[0]); e.target.value = ''; }} />
        </label>
        <button className="btn btn-primary btn-sm" onClick={() => exportUsers('xlsx')}>📊 تصدير XLSX</button>
        <button className="btn btn-secondary btn-sm" onClick={() => exportUsers('csv')}>📄 تصدير CSV</button>
      </div>

      {/* Bulk Action Bar */}
      {selectedIds.size > 0 && (
        <div className="card mb-2" style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '0.5rem', padding: '0.75rem 1rem' }}>
          <span style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--primary)' }}>
            تم تحديد {selectedIds.size} مستخدم
          </span>
          <div className="btn-group" style={{ flexWrap: 'wrap' }}>
            <button className="btn btn-primary btn-sm" onClick={() => requestBulkAction('approve')}>قبول الكل</button>
            <button className="btn btn-danger btn-sm" onClick={() => requestBulkAction('reject')}>رفض الكل</button>
            <button className="btn btn-primary btn-sm" onClick={() => requestBulkAction('activate')}>تفعيل الكل</button>
            <button className="btn btn-danger btn-sm" onClick={() => requestBulkAction('withdraw')}>سحب الكل</button>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <select className="filter-input" style={{ minWidth: 120, padding: '0.3rem' }}
                value={bulkHalqaId} onChange={(e) => setBulkHalqaId(e.target.value)}>
                <option value="">اختر حلقة</option>
                {halqas.map((h) => <option key={h.id} value={h.id}>{h.name}</option>)}
              </select>
              <button className="btn btn-gold btn-sm" onClick={confirmBulkAssignHalqa}>
                تعيين حلقة
              </button>
            </div>
            <button className="btn btn-secondary btn-sm" onClick={() => setSelectedIds(new Set())}>إلغاء التحديد</button>
          </div>
        </div>
      )}

      {loading ? (
        <div className="loading"><div className="spinner" /></div>
      ) : users.length === 0 ? (
        <div className="empty-state"><div className="empty-state-icon">👥</div><div className="empty-state-text">لا يوجد مستخدمون</div></div>
      ) : (
        <div className="card">
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th style={{ width: 36 }}>
                    <input type="checkbox" checked={paged.length > 0 && selectedIds.size === paged.length}
                      onChange={toggleSelectAll} />
                  </th>
                  <th>رقم العضوية</th><th>الاسم</th><th>البريد</th><th>الجنس</th><th>الدولة</th>
                  <th>الحالة</th><th>الصلاحية</th><th>الحلقة</th><th>الإجراءات</th>
                </tr>
              </thead>
              <tbody>
                {paged.map((u) => (
                  <tr key={u.id} style={{ background: selectedIds.has(u.id) ? 'var(--primary-light)' : undefined }}>
                    <td><input type="checkbox" checked={selectedIds.has(u.id)} onChange={() => toggleSelect(u.id)} /></td>
                    <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{u.member_id}</td>
                    <td style={{ fontWeight: 600 }}>{u.full_name}</td>
                    <td dir="ltr" style={{ fontSize: '0.75rem' }}>{u.email}</td>
                    <td>{u.gender === 'male' ? 'ذكر' : 'أنثى'}</td>
                    <td>{u.country}</td>
                    <td><span className={`badge ${statusBadge[u.status]}`}>{statusLabel[u.status]}</span></td>
                    <td><span className="badge badge-info">{roleLabel[u.role]}</span></td>
                    <td>
                      <select className="filter-input" style={{ minWidth: 100, padding: '0.3rem' }}
                        value={u.halqa_id || ''} onChange={(e) => confirmAssignHalqa(u, e.target.value)}>
                        <option value="">بدون</option>
                        {halqas.map((h) => <option key={h.id} value={h.id}>{h.name}</option>)}
                      </select>
                    </td>
                    <td>
                      <div className="btn-group">
                        {u.status === 'pending' && (
                          <>
                            <button className="btn btn-primary btn-sm" onClick={() => confirmApprove(u)}>قبول</button>
                            <button className="btn btn-danger btn-sm" onClick={() => setShowRejectModal(u.id)}>رفض</button>
                          </>
                        )}
                        {(u.status === 'rejected' || u.status === 'withdrawn') && (
                          <button className="btn btn-primary btn-sm" onClick={() => confirmActivate(u)}>تفعيل</button>
                        )}
                        {u.status === 'active' && (
                          <button className="btn btn-danger btn-sm" onClick={() => confirmWithdraw(u)}>سحب</button>
                        )}
                        <button className="btn btn-secondary btn-sm" onClick={() => openEdit(u)}>✏️</button>
                        <select className="filter-input" style={{ minWidth: 80, padding: '0.3rem', fontSize: '0.7rem' }}
                          value={u.role} onChange={(e) => confirmSetRole(u, e.target.value)}>
                          <option value="participant">مشارك</option>
                          <option value="supervisor">مشرف</option>
                          <option value="super_admin">سوبر آدمن</option>
                        </select>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination page={page} totalPages={totalPages} total={total} onPageChange={setPage} />
        </div>
      )}

      {/* Reject Modal */}
      {showRejectModal && (
        <div className="modal-overlay" onClick={() => setShowRejectModal(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-title">رفض طلب التسجيل</div>
            <div className="form-group">
              <label className="form-label">ملاحظة الرفض (اختياري)</label>
              <textarea className="form-textarea" value={rejectNote}
                onChange={(e) => setRejectNote(e.target.value)} placeholder="سبب الرفض..." />
            </div>
            <div className="btn-group">
              <button className="btn btn-danger" onClick={() => reject(showRejectModal)}>تأكيد الرفض</button>
              <button className="btn btn-secondary" onClick={() => setShowRejectModal(null)}>إلغاء</button>
            </div>
          </div>
        </div>
      )}

      {/* Edit User Modal */}
      {selectedUser && (
        <div className="modal-overlay" onClick={() => setSelectedUser(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-title">تعديل بيانات {selectedUser.full_name}</div>

            <div className="form-group">
              <label className="form-label">الاسم</label>
              <input className="form-input" value={editForm.full_name || ''}
                onChange={(e) => setEditForm((f) => ({ ...f, full_name: e.target.value }))} />
            </div>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">الجنس</label>
                <select className="form-select" value={editForm.gender}
                  onChange={(e) => setEditForm((f) => ({ ...f, gender: e.target.value }))}>
                  <option value="male">ذكر</option>
                  <option value="female">أنثى</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">العمر</label>
                <input type="number" className="form-input" value={editForm.age || ''}
                  onChange={(e) => setEditForm((f) => ({ ...f, age: parseInt(e.target.value) }))} />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">الهاتف</label>
              <input className="form-input" dir="ltr" value={editForm.phone || ''}
                onChange={(e) => setEditForm((f) => ({ ...f, phone: e.target.value }))} />
            </div>
            <div className="form-group">
              <label className="form-label">الدولة</label>
              <input className="form-input" value={editForm.country || ''}
                onChange={(e) => setEditForm((f) => ({ ...f, country: e.target.value }))} />
            </div>

            {/* Reset Password */}
            <div style={{ borderTop: '1px solid var(--border)', paddingTop: '1rem', marginTop: '1rem' }}>
              <label className="form-label">إعادة تعيين كلمة المرور</label>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <input type="text" className="form-input" dir="ltr" placeholder="كلمة المرور الجديدة"
                  value={resetPwd} onChange={(e) => setResetPwd(e.target.value)} />
                <button className="btn btn-gold btn-sm" onClick={() => resetPassword(selectedUser.id)}>تعيين</button>
              </div>
            </div>

            <div className="btn-group mt-2">
              <button className="btn btn-primary" onClick={saveUserEdit}>💾 حفظ التعديلات</button>
              <button className="btn btn-secondary" onClick={() => setSelectedUser(null)}>إلغاء</button>
            </div>
          </div>
        </div>
      )}

      {/* Import Preview Modal */}
      {importPreview && (
        <div className="modal-overlay" onClick={cancelImport}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 700 }}>
            <div className="modal-title">معاينة ملف الاستيراد</div>

            <div className="stats-grid" style={{ marginBottom: '1rem' }}>
              <div className="stat-card">
                <div className="stat-value">{importPreview.rows.length}</div>
                <div className="stat-label">إجمالي المشاركين</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{importPreview.genderCount.male}</div>
                <div className="stat-label">ذكور</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{importPreview.genderCount.female}</div>
                <div className="stat-label">إناث</div>
              </div>
            </div>

            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
              سيتم إضافة المشاركين في قائمة "قيد المراجعة" بكلمة مرور افتراضية (123456)
            </p>

            <div className="table-container" style={{ maxHeight: 300, overflowY: 'auto' }}>
              <table>
                <thead>
                  <tr>
                    <th>#</th><th>الاسم</th><th>البريد</th><th>الجنس</th><th>الهاتف</th><th>الدولة</th>
                  </tr>
                </thead>
                <tbody>
                  {importPreview.rows.map((r, i) => (
                    <tr key={i}>
                      <td>{i + 1}</td>
                      <td>{r['الاسم'] || '-'}</td>
                      <td dir="ltr" style={{ fontSize: '0.75rem' }}>{r['البريد'] || '-'}</td>
                      <td>{r['الجنس'] || '-'}</td>
                      <td dir="ltr">{r['الهاتف'] || '-'}</td>
                      <td>{r['الدولة'] || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="btn-group mt-2">
              <button className="btn btn-primary" onClick={confirmImport} disabled={importing}>
                {importing ? 'جاري الاستيراد...' : `تأكيد استيراد ${importPreview.rows.length} مشارك`}
              </button>
              <button className="btn btn-secondary" onClick={cancelImport} disabled={importing}>إلغاء</button>
            </div>
          </div>
        </div>
      )}

      {/* Import Result Modal (errors) */}
      {importResult && (
        <div className="modal-overlay" onClick={() => setImportResult(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 500 }}>
            <div className="modal-title">نتيجة الاستيراد</div>
            <p style={{ fontWeight: 600, color: 'var(--accent)', marginBottom: '0.5rem' }}>{importResult.message}</p>
            {importResult.errors?.length > 0 && (
              <>
                <p style={{ fontSize: '0.85rem', color: 'var(--danger)', fontWeight: 600, marginBottom: '0.5rem' }}>
                  أخطاء ({importResult.errors.length}):
                </p>
                <div style={{ maxHeight: 200, overflowY: 'auto', background: 'var(--background)', borderRadius: 8, padding: '0.5rem' }}>
                  {importResult.errors.map((err, i) => (
                    <div key={i} style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', padding: '0.2rem 0', borderBottom: '1px solid var(--border)' }}>
                      {err}
                    </div>
                  ))}
                </div>
              </>
            )}
            <div className="btn-group mt-2">
              <button className="btn btn-primary" onClick={() => setImportResult(null)}>حسناً</button>
            </div>
          </div>
        </div>
      )}
      {/* Confirmation Modal */}
      {confirmAction && (
        <div className="modal-overlay" onClick={() => setConfirmAction(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 500 }}>
            <div className="modal-title">{confirmAction.title}</div>
            <p style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: '0.5rem' }}>
              {confirmAction.message}
            </p>
            {confirmAction.details && (
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                {confirmAction.details}
              </p>
            )}
            {confirmAction.warnings?.length > 0 && (
              <div style={{
                background: 'var(--gold-light)', borderRadius: 8, padding: '0.5rem 0.75rem',
                marginBottom: '0.75rem', borderRight: '3px solid var(--gold)',
                maxHeight: 150, overflowY: 'auto',
              }}>
                {confirmAction.warnings.map((w, i) => (
                  <div key={i} style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', padding: '0.15rem 0' }}>{w}</div>
                ))}
              </div>
            )}
            <div className="btn-group">
              {confirmAction.canProceed !== false && (
                <button className="btn btn-primary" onClick={() => { confirmAction.onConfirm(); setConfirmAction(null); }}>
                  تأكيد
                </button>
              )}
              <button className="btn btn-secondary" onClick={() => setConfirmAction(null)}>
                {confirmAction.canProceed === false ? 'حسناً' : 'إلغاء'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
