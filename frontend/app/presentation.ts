export const statusStyle: Record<string, string> = {
  APPROVED: 'bg-emerald-100 text-emerald-800',
  CHANGES_REQUESTED: 'bg-amber-100 text-amber-800',
  UNDER_REVIEW: 'bg-sky-100 text-sky-800',
  SUBMITTED: 'bg-indigo-100 text-indigo-800',
  DRAFT: 'bg-slate-200 text-slate-700',
  MISSING: 'bg-rose-100 text-rose-700',
};

export const pretty = (value: string) =>
  value
    .replaceAll('_', ' ')
    .toLowerCase()
    .replace(/^./, (character) => character.toUpperCase());
