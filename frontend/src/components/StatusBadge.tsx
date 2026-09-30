import type { VerificationStatus } from '@/api/types';
import { statusStyle } from '@/lib/status';

export function StatusDot({
  status,
  size = 8,
}: {
  status: VerificationStatus | null;
  size?: number;
}) {
  const s = statusStyle(status);
  return (
    <span
      title={s.label}
      style={{
        width: size,
        height: size,
        borderRadius: '50%',
        background: s.dot,
        display: 'inline-block',
        flex: 'none',
      }}
    />
  );
}

export function StatusBadge({ status }: { status: VerificationStatus | null }) {
  const s = statusStyle(status);
  return (
    <span
      className="inline-flex items-center gap-1.5 px-1.5 py-0.5 text-[11.5px]"
      style={{ background: s.bg, color: s.ink }}
    >
      <span style={{ width: 7, height: 7, borderRadius: '50%', background: s.dot }} />
      {s.label}
    </span>
  );
}
