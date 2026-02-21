import { ChevronRight, ChevronLeft } from 'lucide-react';

const PAGE_SIZE = 10;

export function paginate(items, page) {
  const total = items.length;
  const totalPages = Math.ceil(total / PAGE_SIZE) || 1;
  const safePage = Math.min(Math.max(1, page), totalPages);
  const start = (safePage - 1) * PAGE_SIZE;
  const paged = items.slice(start, start + PAGE_SIZE);
  return { paged, totalPages, safePage, total };
}

export default function Pagination({ page, totalPages, total, onPageChange }) {
  if (totalPages <= 1) return null;
  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      gap: '0.5rem', padding: '0.75rem 0', fontSize: '0.85rem',
    }}>
      <button className="btn btn-secondary btn-sm" disabled={page <= 1}
        onClick={() => onPageChange(page - 1)} style={{ padding: '0.3rem 0.5rem' }}>
        <ChevronRight size={16} />
      </button>
      <span style={{ color: 'var(--text-secondary)' }}>
        صفحة {page} من {totalPages} — ({total} سجل)
      </span>
      <button className="btn btn-secondary btn-sm" disabled={page >= totalPages}
        onClick={() => onPageChange(page + 1)} style={{ padding: '0.3rem 0.5rem' }}>
        <ChevronLeft size={16} />
      </button>
    </div>
  );
}
