'use client';
import { useEffect, useId, useRef, useState } from 'react';
import { X } from 'lucide-react';

export type Field = {
  name: string;
  label: string;
  type?: string;
  required?: boolean;
  value?: string | number;
  options?: { value: string | number; label: string }[];
  hint?: string;
};
export type FormSpec = {
  title: string;
  description?: string;
  fields: Field[];
  submit?: string;
  save: (data: FormData) => Promise<void>;
};
export function FormDialog({
  spec,
  close,
}: {
  spec: FormSpec;
  close: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const formId = useId();
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    ref.current?.showModal();
  }, []);
  return (
    <dialog
      ref={ref}
      className="form-dialog"
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) close();
      }}
    >
      <div className="dialog-heading">
        <h2>{spec.title}</h2>
        <button disabled={busy} onClick={close} aria-label="Close dialog">
          <X size={20} />
        </button>
      </div>
      {spec.description && <p className="muted">{spec.description}</p>}
      <form
        method="post"
        onSubmit={(event) => {
          event.preventDefault();
          const data = new FormData(event.currentTarget);
          setBusy(true);
          setError('');
          void spec
            .save(data)
            .then(close)
            .catch((reason: unknown) =>
              setError(
                reason instanceof Error ? reason.message : 'Unable to save',
              ),
            )
            .finally(() => setBusy(false));
        }}
      >
        {spec.fields.map((field) => (
          <div key={field.name} className="field">
            <label htmlFor={formId + field.name}>{field.label}</label>
            {field.options ? (
              <select
                id={formId + field.name}
                name={field.name}
                required={field.required}
                defaultValue={field.value ?? ''}
              >
                <option value="">Choose…</option>
                {field.options.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            ) : field.type === 'textarea' ? (
              <textarea
                id={formId + field.name}
                name={field.name}
                required={field.required}
                defaultValue={field.value}
                rows={3}
              />
            ) : (
              <input
                id={formId + field.name}
                name={field.name}
                type={field.type || 'text'}
                required={field.required}
                defaultValue={field.type === 'file' ? undefined : field.value}
                accept={
                  field.type === 'file'
                    ? '.pdf,.png,.jpg,.jpeg,.webp,.gif,.txt,.md,.csv,.docx,.xlsx,.pptx'
                    : undefined
                }
              />
            )}
            {field.hint && <small>{field.hint}</small>}
          </div>
        ))}
        {error && (
          <p className="notice error" role="alert">
            {error}
          </p>
        )}
        <div className="dialog-actions">
          <button
            type="button"
            className="secondary"
            disabled={busy}
            onClick={close}
          >
            Cancel
          </button>
          <button className="primary" type="submit" disabled={busy}>
            {busy ? 'Saving…' : spec.submit || 'Save'}
          </button>
        </div>
      </form>
    </dialog>
  );
}
export function Status({ value }: { value: string }) {
  return (
    <span className={'status status-' + value.toLowerCase()}>
      {value.toLowerCase().replaceAll('_', ' ')}
    </span>
  );
}
export const textValue = (data: FormData, name: string) => {
  const value = data.get(name);
  return typeof value === 'string' ? value : '';
};
export const numberValue = (data: FormData, name: string) =>
  data.get(name) ? Number(data.get(name)) : null;
