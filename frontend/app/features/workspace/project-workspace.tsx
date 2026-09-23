'use client';
/* eslint-disable react/react-compiler */
import { useEffect, useState } from 'react';
import {
  FileText,
  Plus,
  Users,
  Clock,
  Link as LinkIcon,
  ChevronRight,
  FolderOpen,
} from 'lucide-react';
import type {
  AuditRecord,
  DocumentVersion,
  Employee,
  Person,
  ProjectDashboard,
  Requirement,
  ResearchDocument,
} from '../../domain-types';
import { request, json } from '../../workspace-api';
import { DocumentReader } from '../viewer/document-reader';
import {
  Status,
  textValue,
  numberValue,
  type FormSpec,
  type Field,
} from './common';

type Props = {
  dashboard: ProjectDashboard;
  user: Employee;
  people: Person[];
  research: ResearchDocument[];
  selected: number | null;
  select: (id: number) => void;
  openResearch: (id: number) => void;
  showForm: (spec: FormSpec) => void;
  refresh: () => Promise<void>;
  act: (work: () => Promise<void>, message?: string) => void;
};
export function ProjectWorkspace({
  dashboard: d,
  user,
  people,
  research,
  selected,
  select,
  openResearch,
  showForm,
  refresh,
  act,
}: Props) {
  const [tab, setTab] = useState('documents');
  const [filter, setFilter] = useState('');
  const [stage, setStage] = useState<number | null>(null);
  const owner = d.project.owner.id === user.id;
  const requirement = d.requirements.find((item) => item.id === selected);
  const employeeOptions = d.members.map((member) => ({
    value: member.employee.id,
    label: member.employee.name,
  }));
  const assignments: Field[] = [
    {
      name: 'responsible_employee_id',
      label: 'Responsible employee',
      required: true,
      options: employeeOptions,
    },
    {
      name: 'reviewer_employee_id',
      label: 'Reviewer',
      required: true,
      options: employeeOptions,
    },
  ];
  const save = async (path: string, body: unknown, method = 'POST') => {
    await request(path, { ...json(body), method });
    await refresh();
  };
  const linked = research.filter((item) =>
    item.projects.some((project) => project.id === d.project.id),
  );
  return (
    <>
      <header className="page-heading">
        <div>
          <div className="eyebrow">PROJECT WORKSPACE</div>
          <h1>{d.project.name}</h1>
          <p>
            {d.project.description ||
              'Your project documents, responsibilities and review history.'}
          </p>
        </div>
        {owner && (
          <button
            className="primary"
            onClick={() =>
              showForm({
                title: 'Add required document',
                description:
                  'Create one document slot. Its uploads become versions of the same document.',
                fields: [
                  { name: 'title', label: 'Document title', required: true },
                  {
                    name: 'document_type_name',
                    label: 'Document type / part',
                    required: true,
                  },
                  {
                    name: 'stage_id',
                    label: 'Lifecycle stage',
                    required: true,
                    options: d.stages.map((s) => ({
                      value: s.id,
                      label: s.name,
                    })),
                  },
                  ...assignments,
                  { name: 'due_date', label: 'Due date', type: 'date' },
                  {
                    name: 'description',
                    label: 'Description',
                    type: 'textarea',
                  },
                ],
                save: async (data) =>
                  save('/projects/' + d.project.id + '/requirements', {
                    title: textValue(data, 'title'),
                    document_type_name: textValue(data, 'document_type_name'),
                    stage_id: numberValue(data, 'stage_id'),
                    responsible_employee_id: numberValue(
                      data,
                      'responsible_employee_id',
                    ),
                    reviewer_employee_id: numberValue(
                      data,
                      'reviewer_employee_id',
                    ),
                    due_date: textValue(data, 'due_date') || null,
                    description: textValue(data, 'description'),
                  }),
              })
            }
          >
            <Plus size={17} />
            Required document
          </button>
        )}
      </header>
      <div className="project-summary">
        <span>
          <strong>{d.progress.approved}</strong> of {d.progress.total} approved
        </span>
        <progress
          max={Math.max(d.progress.total, 1)}
          value={d.progress.approved}
        />
        <span>Owner · {d.project.owner.name}</span>
        <span>{d.members.length} members</span>
      </div>
      <div className="tabs" role="tablist" aria-label="Project sections">
        {[
          ['documents', 'Documents', FileText],
          ['references', 'Research links', LinkIcon],
          ['team', 'People & stages', Users],
          ['activity', 'Activity', Clock],
        ].map(([key, label, Icon]) => (
          <button
            key={String(key)}
            role="tab"
            aria-selected={tab === key}
            className={tab === key ? 'active' : ''}
            onClick={() => setTab(String(key))}
          >
            {typeof Icon !== 'string' && <Icon size={16} />} {String(label)}
            {key === 'references' && (
              <span className="count">{linked.length}</span>
            )}
          </button>
        ))}
      </div>
      {tab === 'documents' && (
        <div className="document-workspace">
          <aside className="document-list">
            <div className="list-heading">
              <h2>
                Documents <span className="count">{d.requirements.length}</span>
              </h2>
              <input
                aria-label="Filter project documents"
                placeholder="Filter documents…"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
              />
              <select
                aria-label="Lifecycle stage filter"
                value={stage ?? ''}
                onChange={(e) =>
                  setStage(e.target.value ? Number(e.target.value) : null)
                }
              >
                <option value="">All lifecycle stages</option>
                {d.stages.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </div>
            {d.stages
              .filter((s) => stage === null || stage === s.id)
              .map((s) => (
                <section key={s.id}>
                  <h3 className="group-label">{s.name}</h3>
                  {d.requirements
                    .filter(
                      (r) =>
                        r.stage_id === s.id &&
                        r.title.toLowerCase().includes(filter.toLowerCase()),
                    )
                    .map((r) => (
                      <button
                        className={
                          'file-row ' + (r.id === selected ? 'selected' : '')
                        }
                        key={r.id}
                        onClick={() => select(r.id)}
                      >
                        <FileText size={19} />
                        <span>
                          <strong>{r.title}</strong>
                          <small>
                            {r.responsible?.name || 'Unassigned'}
                            {r.current_version
                              ? ' · v' + r.current_version.version_number
                              : ''}
                          </small>
                          <Status value={r.status} />
                        </span>
                        <ChevronRight size={15} />
                      </button>
                    ))}
                </section>
              ))}
            {!d.requirements.length && (
              <p className="empty-small">
                No required documents yet. The owner can add stages, invite
                employees, then define required documents.
              </p>
            )}
          </aside>
          {requirement ? (
            <RequirementPane
              key={requirement.id}
              requirement={requirement}
              user={user}
              owner={owner}
              assignments={assignments}
              people={people}
              refresh={refresh}
              showForm={showForm}
              act={act}
            />
          ) : (
            <DocumentReader />
          )}
        </div>
      )}
      {tab === 'references' && (
        <section className="panel">
          <div className="section-heading">
            <div>
              <h2>Research used in this project</h2>
              <p className="muted">
                References stay in the company library. Open a document to view
                its latest version.
              </p>
            </div>
            <button
              className="primary"
              onClick={() =>
                showForm({
                  title: 'Link research to this project',
                  fields: [
                    {
                      name: 'document_id',
                      label: 'Research document',
                      required: true,
                      options: research
                        .filter((r) => !linked.some((l) => l.id === r.id))
                        .map((r) => ({ value: r.id, label: r.name })),
                    },
                  ],
                  save: async (data) =>
                    save(
                      '/research/' +
                        numberValue(data, 'document_id') +
                        '/links',
                      { project_id: d.project.id },
                    ),
                })
              }
            >
              <Plus size={17} />
              Link research
            </button>
          </div>
          {linked.map((r) => (
            <div className="reference-row" key={r.id}>
              <button className="text-link" onClick={() => openResearch(r.id)}>
                <FileText size={18} />
                {r.name}
              </button>
              <span>{r.category}</span>
              {owner && (
                <button
                  className="quiet"
                  onClick={() =>
                    act(async () => {
                      await request(
                        '/research/' + r.id + '/links/' + d.project.id,
                        { method: 'DELETE' },
                      );
                      await refresh();
                    }, 'Research link removed')
                  }
                >
                  Unlink
                </button>
              )}
            </div>
          ))}
          {!linked.length && (
            <p className="empty-small">No linked research yet.</p>
          )}
        </section>
      )}
      {tab === 'team' && (
        <div className="two-columns">
          <section className="panel">
            <div className="section-heading">
              <h2>Project members</h2>
              {owner && (
                <button
                  className="secondary"
                  onClick={() =>
                    showForm({
                      title: 'Add project member',
                      description:
                        'Members can view project documents. Uploading and reviewing are granted only by individual document assignments.',
                      fields: [
                        {
                          name: 'employee_id',
                          label: 'Employee',
                          required: true,
                          options: people
                            .filter(
                              (p) =>
                                !d.members.some((m) => m.employee.id === p.id),
                            )
                            .map((p) => ({ value: p.id, label: p.name })),
                        },
                      ],
                      save: async (data) =>
                        save('/projects/' + d.project.id + '/members', {
                          employee_id: numberValue(data, 'employee_id'),
                          access_level: 'VIEW',
                        }),
                    })
                  }
                >
                  <Plus size={16} />
                  Add member
                </button>
              )}
            </div>
            {d.members.map((m) => (
              <div className="person-row" key={m.id}>
                <div className="avatar">{m.employee.name.slice(0, 1)}</div>
                <div>
                  <strong>{m.employee.name}</strong>
                  <small>{m.employee.employee_code}</small>
                </div>
                <span>
                  {m.employee.id === d.project.owner.id ? 'Owner' : 'Member'}
                </span>
              </div>
            ))}
          </section>
          <section className="panel">
            <div className="section-heading">
              <h2>Lifecycle stages</h2>
              {owner && (
                <button
                  className="secondary"
                  onClick={() =>
                    showForm({
                      title: 'Add lifecycle stage',
                      fields: [
                        { name: 'name', label: 'Stage name', required: true },
                      ],
                      save: async (data) =>
                        save('/projects/' + d.project.id + '/stages', {
                          name: textValue(data, 'name'),
                          position:
                            Math.max(0, ...d.stages.map((s) => s.position)) + 1,
                        }),
                    })
                  }
                >
                  <Plus size={16} />
                  Add stage
                </button>
              )}
            </div>
            {d.stages.map((s) => (
              <div className="reference-row" key={s.id}>
                <FolderOpen size={18} />
                <strong>
                  {s.position}. {s.name}
                </strong>
                <span>
                  {d.requirements.filter((r) => r.stage_id === s.id).length}{' '}
                  documents
                </span>
              </div>
            ))}
            <p className="muted">
              Each project can have its own stages. A stage groups required
              documents; it is not a project-planning task.
            </p>
          </section>
        </div>
      )}
      {tab === 'activity' && <Activity projectId={d.project.id} />}
    </>
  );
}
function Activity({ projectId }: { projectId: number }) {
  const [rows, setRows] = useState<AuditRecord[]>([]);
  const [error, setError] = useState('');
  useEffect(() => {
    const controller = new AbortController();
    void request<AuditRecord[]>('/audit?project_id=' + projectId, {
      signal: controller.signal,
    })
      .then(setRows)
      .catch((e: unknown) => {
        if (!controller.signal.aborted)
          setError(e instanceof Error ? e.message : 'Unable to load activity');
      });
    return () => controller.abort();
  }, [projectId]);
  return (
    <section className="panel">
      <h2>Project activity</h2>
      {error && <p role="alert">{error}</p>}
      {rows.map((row) => (
        <div className="activity-row" key={row.id}>
          <Clock size={17} />
          <div>
            <strong>{row.action.toLowerCase().replaceAll('_', ' ')}</strong>
            <small>
              {row.actor} · {new Date(row.created_at).toLocaleString()}
            </small>
            {typeof row.details?.comment === 'string' ? (
              <p>{row.details.comment}</p>
            ) : null}
          </div>
        </div>
      ))}
    </section>
  );
}
function RequirementPane({
  requirement: r,
  user,
  owner,
  assignments,
  people,
  refresh,
  showForm,
  act,
}: {
  requirement: Requirement;
  user: Employee;
  owner: boolean;
  assignments: Field[];
  people: Person[];
  refresh: () => Promise<void>;
  showForm: (spec: FormSpec) => void;
  act: Props['act'];
}) {
  const [versions, setVersions] = useState<DocumentVersion[]>([]);
  const [versionId, setVersionId] = useState<number | null>(null);
  const [compare, setCompare] = useState(false);
  const [error, setError] = useState('');
  useEffect(() => {
    setVersionId(null);
    if (!r.document_id) {
      setVersions([]);
      return;
    }
    const controller = new AbortController();
    void request<DocumentVersion[]>(
      '/documents/' + r.document_id + '/versions',
      { signal: controller.signal },
    )
      .then(setVersions)
      .catch((e: unknown) => {
        if (!controller.signal.aborted)
          setError(e instanceof Error ? e.message : 'Unable to load versions');
      });
    return () => controller.abort();
  }, [r.document_id, r.current_version?.id]);
  const version = versions.find((v) => v.id === versionId) || r.current_version;
  const isLatest = version?.id === r.current_version?.id;
  const shownReview = version?.review;
  const previous = versions.find((v) => v.id !== version?.id);
  const uploader = r.responsible?.id === user.id;
  const reviewer = r.reviewer?.id === user.id;
  const waiting = ['SUBMITTED', 'UNDER_REVIEW'].includes(r.status);
  const review = r.current_version?.review;
  const perform = (path: string, body: unknown, message: string) =>
    act(async () => {
      await request(path, json(body));
      await refresh();
    }, message);
  return (
    <section className="document-detail">
      <div className="detail-heading">
        <div>
          <h2>{r.title}</h2>
          <p>{r.description || r.document_type}</p>
        </div>
        <Status value={r.status} />
      </div>
      <div className="responsibilities">
        <span>
          Responsible <strong>{r.responsible?.name || 'Not assigned'}</strong>
        </span>
        <span>
          Reviewer <strong>{r.reviewer?.name || 'Not assigned'}</strong>
        </span>
        {r.due_date && (
          <span>
            Due <strong>{r.due_date}</strong>
          </span>
        )}
        {owner && (
          <button
            disabled={waiting}
            className="text-link"
            onClick={() =>
              showForm({
                title: 'Assign document responsibilities',
                description:
                  'Only these employees can upload or review. Assignments cannot change during an active review.',
                fields: assignments.map((f) => ({
                  ...f,
                  value:
                    f.name === 'responsible_employee_id'
                      ? r.responsible?.id
                      : r.reviewer?.id,
                })),
                save: async (data) => {
                  await request('/projects/requirements/' + r.id + '/assign', {
                    method: 'PATCH',
                    body: JSON.stringify({
                      responsible_employee_id: numberValue(
                        data,
                        'responsible_employee_id',
                      ),
                      reviewer_employee_id: numberValue(
                        data,
                        'reviewer_employee_id',
                      ),
                    }),
                  });
                  await refresh();
                },
              })
            }
          >
            Change assignments
          </button>
        )}
      </div>
      {shownReview?.comment && (
        <div
          className={
            'feedback ' +
            (shownReview.decision === 'CHANGES_REQUESTED' ? 'needs-change' : '')
          }
        >
          <strong>
            Version {version?.version_number} ·{' '}
            {shownReview.decision.toLowerCase().replaceAll('_', ' ')}
          </strong>
          <p>{shownReview.comment}</p>
        </div>
      )}
      {!isLatest && version && (
        <div className="feedback">
          <strong>Viewing an earlier version</strong>
          <p>Switch to the latest version to submit or review it.</p>
          <button className="text-link" onClick={() => setVersionId(null)}>
            Return to latest
          </button>
        </div>
      )}
      <div className="document-actions">
        {uploader && !waiting && (
          <button
            className="primary"
            onClick={() =>
              showForm({
                title: r.current_version
                  ? 'Upload a new version'
                  : 'Upload document',
                description:
                  'The original and previous versions remain in the history.',
                submit: 'Upload',
                fields: [
                  { name: 'file', label: 'File', type: 'file', required: true },
                  {
                    name: 'change_summary',
                    label: 'What changed?',
                    type: 'textarea',
                    required: !!r.current_version,
                  },
                ],
                save: async (data) => {
                  await request(
                    '/documents/requirements/' + r.id + '/versions',
                    { method: 'POST', body: data },
                  );
                  await refresh();
                },
              })
            }
          >
            <Plus size={16} />
            Upload {r.current_version ? 'new version' : 'document'}
          </button>
        )}
        {uploader && isLatest && r.status === 'DRAFT' && r.current_version && (
          <button
            className="secondary"
            onClick={() =>
              perform(
                '/documents/versions/' + r.current_version?.id + '/submit',
                {},
                'Submitted to ' + r.reviewer?.name,
              )
            }
          >
            Submit for review
          </button>
        )}
        {reviewer && isLatest && r.status === 'SUBMITTED' && review && (
          <button
            className="primary"
            onClick={() =>
              perform(
                '/documents/reviews/' + review.id + '/start',
                {},
                'Review started',
              )
            }
          >
            Start review
          </button>
        )}
        {reviewer && isLatest && r.status === 'UNDER_REVIEW' && review && (
          <>
            <button
              className="primary"
              onClick={() =>
                showForm({
                  title: 'Approve this version',
                  fields: [
                    {
                      name: 'comment',
                      label: 'Review notes',
                      type: 'textarea',
                    },
                  ],
                  submit: 'Approve version',
                  save: async (data) => {
                    await request(
                      '/documents/reviews/' + review.id + '/decision',
                      json({
                        decision: 'APPROVED',
                        comment: textValue(data, 'comment'),
                      }),
                    );
                    await refresh();
                  },
                })
              }
            >
              Approve
            </button>
            <button
              className="secondary"
              onClick={() =>
                showForm({
                  title: 'Request changes',
                  description:
                    'Tell the responsible employee exactly what needs changing.',
                  fields: [
                    {
                      name: 'comment',
                      label: 'Feedback',
                      type: 'textarea',
                      required: true,
                    },
                  ],
                  submit: 'Send feedback',
                  save: async (data) => {
                    await request(
                      '/documents/reviews/' + review.id + '/decision',
                      json({
                        decision: 'CHANGES_REQUESTED',
                        comment: textValue(data, 'comment'),
                      }),
                    );
                    await refresh();
                  },
                })
              }
            >
              Request changes
            </button>
          </>
        )}
        {!uploader && !reviewer && (
          <span className="muted">
            View access · actions belong to assigned employees
          </span>
        )}
        {waiting && uploader && (
          <span className="muted">
            Waiting for {r.reviewer?.name} to review this version.
          </span>
        )}
        {owner && (
          <button
            className="quiet"
            onClick={() =>
              showForm({
                title: 'Share document',
                description:
                  'Read-only access to this document, not the whole project.',
                fields: [
                  {
                    name: 'employee_id',
                    label: 'Employee or visitor',
                    required: true,
                    options: people.map((p) => ({
                      value: p.id,
                      label: p.name,
                    })),
                  },
                ],
                save: async (data) => {
                  await request(
                    '/projects/requirements/' + r.id + '/permissions',
                    {
                      method: 'PUT',
                      body: JSON.stringify({
                        employee_id: numberValue(data, 'employee_id'),
                        access_level: 'VIEW',
                      }),
                    },
                  );
                  await refresh();
                },
              })
            }
          >
            Share
          </button>
        )}
        {owner && (
          <button
            className="quiet danger"
            onClick={() =>
              showForm({
                title: 'Archive document?',
                description:
                  'This hides the required document and its files. The database history and stored files are retained.',
                fields: [],
                submit: 'Archive',
                save: async () => {
                  await request('/documents/requirements/' + r.id, {
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
            aria-label="Document version"
            value={version?.id || ''}
            onChange={(e) => setVersionId(Number(e.target.value))}
          >
            {versions.map((v) => (
              <option key={v.id} value={v.id}>
                Version {v.version_number}
                {v.id === r.current_version?.id ? ' · latest' : ''}
              </option>
            ))}
          </select>
        )}
      </div>
      {version?.change_summary && (
        <p className="version-note">Version note: {version.change_summary}</p>
      )}
      {error && <p className="notice error">{error}</p>}
      {previous && (
        <button
          className="text-link compare-toggle"
          onClick={() => setCompare(!compare)}
        >
          {compare ? 'Close comparison' : 'Compare versions side by side'}
        </button>
      )}
      <div
        className={compare && previous ? 'reader-comparison' : 'reader-single'}
      >
        <DocumentReader version={version} />
        {compare && previous && <DocumentReader version={previous} />}
      </div>
    </section>
  );
}
