'use client';
/* eslint-disable react/react-compiler */
import { useEffect, useState } from 'react';
import {
  BookOpen,
  ChevronRight,
  FileText,
  Folder,
  FolderOpen,
  Plus,
  Link as LinkIcon,
  BadgeCheck,
} from 'lucide-react';
import type {
  DocumentVersion,
  Employee,
  Project,
  ResearchCategory,
  ResearchDocument,
} from '../../domain-types';
import { request, json } from '../../workspace-api';
import { DocumentReader } from '../viewer/document-reader';
import { textValue, numberValue, type FormSpec } from './common';

type Props = {
  user: Employee;
  categories: ResearchCategory[];
  documents: ResearchDocument[];
  projects: Project[];
  selected: number | null;
  select: (id: number) => void;
  openProject: (id: number) => void;
  showForm: (spec: FormSpec) => void;
  refresh: () => Promise<void>;
  act: (work: () => Promise<void>, message?: string) => void;
};
export function ResearchWorkspace({
  user,
  categories,
  documents,
  projects,
  selected,
  select,
  openProject,
  showForm,
  refresh,
  act,
}: Props) {
  const [category, setCategory] = useState<number | null>(null);
  const [filter, setFilter] = useState('');
  const [versions, setVersions] = useState<DocumentVersion[]>([]);
  const [versionId, setVersionId] = useState<number | null>(null);
  const [error, setError] = useState('');
  const document = documents.find((d) => d.id === selected);
  useEffect(() => {
    if (document) setCategory(document.category_id);
  }, [document]);
  useEffect(() => {
    setVersionId(null);
    setVersions([]);
    setError('');
    if (!document) return;
    const controller = new AbortController();
    void request<DocumentVersion[]>('/research/' + document.id + '/versions', {
      signal: controller.signal,
    })
      .then(setVersions)
      .catch((e: unknown) => {
        if (!controller.signal.aborted)
          setError(e instanceof Error ? e.message : 'Unable to load history');
      });
    return () => controller.abort();
  }, [document]);
  const descendants = (id: number): number[] => [
    id,
    ...categories
      .filter((c) => c.parent_id === id)
      .flatMap((c) => descendants(c.id)),
  ];
  const visible = documents.filter(
    (d) =>
      (category === null || descendants(category).includes(d.category_id)) &&
      d.name.toLowerCase().includes(filter.toLowerCase()),
  );
  const trail: ResearchCategory[] = [];
  let ancestor = categories.find(
    (c) => c.id === (document?.category_id ?? category),
  );
  while (ancestor) {
    trail.unshift(ancestor);
    ancestor = categories.find((c) => c.id === ancestor?.parent_id);
  }
  const tree = (parent: number | null, level = 0): React.ReactNode =>
    categories
      .filter((c) => (c.parent_id ?? null) === parent)
      .map((c) => (
        <div key={c.id}>
          <button
            className={'category-row ' + (category === c.id ? 'active' : '')}
            style={{ paddingLeft: 14 + level * 16 }}
            onClick={() => setCategory(c.id)}
          >
            <Folder size={17} />
            <span>{c.name}</span>
            <small>
              {documents.filter((d) => d.category_id === c.id).length}
            </small>
          </button>
          {tree(c.id, level + 1)}
        </div>
      ));
  const save = async (path: string, body: unknown) => {
    await request(path, json(body));
    await refresh();
  };
  return (
    <>
      <header className="page-heading">
        <div>
          <div className="eyebrow">COMPANY KNOWLEDGE</div>
          <h1>Research library</h1>
          <p>
            Explore what your colleagues know. Connect it to what you’re working
            on.
          </p>
        </div>
        <button
          className="primary"
          onClick={() =>
            showForm({
              title: 'Add to the research library',
              description:
                'Published immediately to everyone in the company. No review pipeline.',
              submit: 'Upload document',
              fields: [
                { name: 'name', label: 'Document title', required: true },
                {
                  name: 'category_id',
                  label: 'Classification',
                  required: true,
                  value: category ?? undefined,
                  options: categories.map((c) => ({
                    value: c.id,
                    label: c.name,
                  })),
                },
                { name: 'description', label: 'Description', type: 'textarea' },
                { name: 'file', label: 'File', type: 'file', required: true },
              ],
              save: async (data) => {
                const created = await request<{ id: number }>('/research', {
                  method: 'POST',
                  body: data,
                });
                await refresh();
                select(created.id);
              },
            })
          }
        >
          <Plus size={17} />
          Upload document
        </button>
      </header>
      <div className="research-workspace">
        <aside className="category-tree">
          <div className="tree-heading">
            <h2>Classifications</h2>
            <button
              aria-label="Create classification"
              onClick={() =>
                showForm({
                  title: 'Create classification',
                  fields: [
                    { name: 'name', label: 'Name', required: true },
                    {
                      name: 'parent_id',
                      label: 'Parent classification (optional)',
                      value: category ?? undefined,
                      options: categories.map((c) => ({
                        value: c.id,
                        label: c.name,
                      })),
                    },
                  ],
                  save: async (data) =>
                    save('/research/categories', {
                      name: textValue(data, 'name'),
                      parent_id: numberValue(data, 'parent_id'),
                    }),
                })
              }
            >
              <Plus size={17} />
            </button>
          </div>
          <button
            className={'category-row ' + (category === null ? 'active' : '')}
            onClick={() => setCategory(null)}
          >
            <BookOpen size={17} />
            All research<small>{documents.length}</small>
          </button>
          {tree(null)}
          {!categories.length && (
            <p className="empty-small">
              Create your first classification with +.
            </p>
          )}
        </aside>
        <aside className="document-list research-files">
          <div className="list-heading">
            <h2>
              {category === null
                ? 'All documents'
                : categories.find((c) => c.id === category)?.name}
            </h2>
            <input
              aria-label="Filter research files"
              placeholder="Find in this classification…"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            />
          </div>
          {visible.map((d) => (
            <button
              key={d.id}
              className={'file-row ' + (selected === d.id ? 'selected' : '')}
              onClick={() => select(d.id)}
            >
              <FileText size={19} />
              <span>
                <strong>{d.name}</strong>
                <small>
                  {d.category} · v{d.current_version?.version_number || 1}
                </small>
                {!!d.endorsements.length && (
                  <small className="endorsed">
                    <BadgeCheck size={13} />
                    Endorsed
                  </small>
                )}
              </span>
              <ChevronRight size={14} />
            </button>
          ))}
          {!visible.length && (
            <div className="empty-small">
              <FolderOpen size={27} />
              <p>No documents here yet.</p>
            </div>
          )}
        </aside>
        {document ? (
          <section className="document-detail research-detail">
            <div className="breadcrumbs">
              Research{' '}
              {trail.map((c) => (
                <span key={c.id}> / {c.name}</span>
              ))}
            </div>
            <div className="detail-heading">
              <div>
                <h2>{document.name}</h2>
                <p>{document.description || 'Shared company research'}</p>
                <small>Added by {document.uploaded_by}</small>
              </div>
            </div>
            <div className="document-actions">
              <button
                className="secondary"
                onClick={() =>
                  showForm({
                    title: 'Upload research version',
                    description:
                      'The new version becomes the default. Previous versions stay available.',
                    fields: [
                      {
                        name: 'file',
                        label: 'File',
                        type: 'file',
                        required: true,
                      },
                    ],
                    save: async (data) => {
                      await request('/research/' + document.id + '/versions', {
                        method: 'POST',
                        body: data,
                      });
                      await refresh();
                    },
                  })
                }
              >
                <Plus size={16} />
                New version
              </button>
              {user.is_admin && (
                <button
                  className="quiet"
                  onClick={() =>
                    showForm({
                      title: 'Endorse this research',
                      description:
                        'An endorsement is a badge, not a publishing gate or review.',
                      fields: [
                        {
                          name: 'label',
                          label: 'Badge label',
                          value: 'Useful for company work',
                          required: true,
                        },
                      ],
                      save: async (data) =>
                        save('/research/' + document.id + '/endorse', {
                          label: textValue(data, 'label'),
                        }),
                    })
                  }
                >
                  <BadgeCheck size={16} />
                  Endorse
                </button>
              )}
              {(document.uploaded_by_id === user.id || user.is_admin) && (
                <button
                  className="quiet danger"
                  onClick={() =>
                    showForm({
                      title: 'Archive research document?',
                      description:
                        'The document is hidden from the library. Its files and audit history are retained.',
                      fields: [],
                      submit: 'Archive',
                      save: async () => {
                        await request('/research/' + document.id, {
                          method: 'DELETE',
                        });
                        await refresh();
                      },
                    })
                  }
                >
                  Archive
                </button>
              )}
              {!!versions.length && (
                <select
                  aria-label="Research version"
                  value={versionId || document.current_version?.id}
                  onChange={(e) => setVersionId(Number(e.target.value))}
                >
                  {versions.map((v) => (
                    <option key={v.id} value={v.id}>
                      Version {v.version_number}
                      {v.id === document.current_version?.id ? ' · latest' : ''}
                    </option>
                  ))}
                </select>
              )}
            </div>
            {!!document.endorsements.length && (
              <div className="endorsements">
                {document.endorsements.map((e, i) => (
                  <span key={i}>
                    <BadgeCheck size={15} />
                    {e.label} · {e.employee_name}
                  </span>
                ))}
              </div>
            )}
            <div className="links-panel">
              <div>
                <strong>
                  <LinkIcon size={14} />
                  Project references
                </strong>
                {document.projects.map((p) => (
                  <span className="link-chip" key={p.id}>
                    <button onClick={() => openProject(p.id)}>{p.name}</button>
                    <button
                      aria-label={'Unlink ' + p.name}
                      onClick={() =>
                        act(async () => {
                          await request(
                            '/research/' + document.id + '/links/' + p.id,
                            { method: 'DELETE' },
                          );
                          await refresh();
                        }, 'Project reference removed')
                      }
                    >
                      ×
                    </button>
                  </span>
                ))}
                <button
                  className="text-link"
                  onClick={() =>
                    showForm({
                      title: 'Link to a project',
                      fields: [
                        {
                          name: 'project_id',
                          label: 'Project',
                          required: true,
                          options: projects
                            .filter(
                              (p) =>
                                !document.projects.some((l) => l.id === p.id),
                            )
                            .map((p) => ({ value: p.id, label: p.name })),
                        },
                      ],
                      save: async (data) =>
                        save('/research/' + document.id + '/links', {
                          project_id: numberValue(data, 'project_id'),
                        }),
                    })
                  }
                >
                  + Link project
                </button>
              </div>
              <div>
                <strong>Related research</strong>
                {document.related.map((r) => (
                  <span className="link-chip" key={r.id}>
                    <button onClick={() => select(r.id)}>{r.name}</button>
                    <button
                      aria-label={'Remove reference ' + r.name}
                      onClick={() =>
                        act(async () => {
                          await request(
                            '/research/' + document.id + '/related/' + r.id,
                            { method: 'DELETE' },
                          );
                          await refresh();
                        }, 'Reference removed')
                      }
                    >
                      ×
                    </button>
                  </span>
                ))}
                <button
                  className="text-link"
                  onClick={() =>
                    showForm({
                      title: 'Connect related research',
                      fields: [
                        {
                          name: 'target_id',
                          label: 'Research document',
                          required: true,
                          options: documents
                            .filter(
                              (r) =>
                                r.id !== document.id &&
                                !document.related.some((l) => l.id === r.id),
                            )
                            .map((r) => ({ value: r.id, label: r.name })),
                        },
                      ],
                      save: async (data) =>
                        save(
                          '/research/' +
                            document.id +
                            '/related/' +
                            numberValue(data, 'target_id'),
                          {},
                        ),
                    })
                  }
                >
                  + Add reference
                </button>
              </div>
            </div>
            {error && <p className="notice error">{error}</p>}
            <DocumentReader
              version={
                versions.find((v) => v.id === versionId) ||
                document.current_version
              }
            />
          </section>
        ) : (
          <DocumentReader />
        )}
      </div>
    </>
  );
}
