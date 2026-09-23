'use client';
/* eslint-disable react/react-compiler */
import { useCallback, useEffect, useState } from 'react';
import {
  ArrowRight,
  BookOpen,
  CheckCircle2,
  FileText,
  FolderOpen,
  Home,
  Leaf,
  LogOut,
  Plus,
  Search,
  Share2,
  X,
} from 'lucide-react';
import type {
  Employee,
  LifecycleTemplate,
  Person,
  Project,
  ProjectDashboard,
  ResearchCategory,
  ResearchDocument,
  SearchResult,
  SharedDocument,
} from './domain-types';
import { request, json } from './workspace-api';
import {
  FormDialog,
  Status,
  textValue,
  numberValue,
  type FormSpec,
} from './features/workspace/common';
import { ProjectWorkspace } from './features/workspace/project-workspace';
import { ResearchWorkspace } from './features/workspace/research-workspace';
import { DocumentReader } from './features/viewer/document-reader';

type Space = {
  projects: Project[];
  dashboards: ProjectDashboard[];
  people: Person[];
  research: ResearchDocument[];
  categories: ResearchCategory[];
  shared: SharedDocument[];
  templates: LifecycleTemplate[];
};
const empty: Space = {
  projects: [],
  dashboards: [],
  people: [],
  research: [],
  categories: [],
  shared: [],
  templates: [],
};
export default function VerdantApp() {
  const [user, setUser] = useState<Employee | null>(null);
  const [boot, setBoot] = useState(true);
  const [space, setSpace] = useState<Space>(empty);
  const [view, setView] = useState('home');
  const [projectId, setProjectId] = useState<number | null>(null);
  const [documentId, setDocumentId] = useState<number | null>(null);
  const [researchId, setResearchId] = useState<number | null>(null);
  const [shareId, setShareId] = useState<number | null>(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState<FormSpec | null>(null);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  useEffect(() => {
    const expire = () => {
      setUser(null);
      setSpace(empty);
      setForm(null);
      setNotice('');
    };
    window.addEventListener('verdant:session-expired', expire);
    return () => window.removeEventListener('verdant:session-expired', expire);
  }, []);
  const refresh = useCallback(async () => {
    const [projects, people, research, categories, shared, templates] =
      await Promise.all([
        request<Project[]>('/projects'),
        request<Person[]>('/auth/employees'),
        request<ResearchDocument[]>('/research'),
        request<ResearchCategory[]>('/research/categories'),
        request<SharedDocument[]>('/projects/shared-documents'),
        request<LifecycleTemplate[]>('/projects/templates'),
      ]);
    const dashboards = await Promise.all(
      projects.map((p) =>
        request<ProjectDashboard>('/projects/' + p.id + '/dashboard'),
      ),
    );
    const nextSpace = {
      projects,
      dashboards,
      people,
      research,
      categories,
      shared,
      templates,
    };
    setSpace((previous) =>
      JSON.stringify(previous) === JSON.stringify(nextSpace)
        ? previous
        : nextSpace,
    );
  }, []);
  useEffect(() => {
    if (!user || form || busy) return;
    const timer = window.setInterval(() => {
      if (document.visibilityState === 'visible') {
        void refresh().catch((reason: unknown) => {
          setError(
            reason instanceof Error
              ? reason.message
              : 'Unable to refresh the workspace.',
          );
        });
      }
    }, 30000);
    return () => window.clearInterval(timer);
  }, [user, form, busy, refresh]);
  useEffect(() => {
    // Remove legacy JavaScript-readable credentials; session cookies are HttpOnly.
    localStorage.removeItem('verdant_token');
    if (location.search)
      history.replaceState(null, '', location.pathname + location.hash);
    void request<Employee>('/auth/me')
      .then(async (employee) => {
        setUser(employee);
        await refresh();
      })
      .catch((reason: unknown) => {
        if (reason instanceof Error && !reason.message.includes('credentials'))
          setError(reason.message);
      })
      .finally(() => setBoot(false));
  }, [refresh]);
  useEffect(() => {
    if (!query.trim() || !user) {
      setResults([]);
      setSearching(false);
      return;
    }
    const controller = new AbortController();
    setSearching(true);
    const timer = setTimeout(() => {
      void request<SearchResult[]>('/search?q=' + encodeURIComponent(query), {
        signal: controller.signal,
      })
        .then(setResults)
        .catch((reason: unknown) => {
          if (!controller.signal.aborted)
            setError(
              reason instanceof Error ? reason.message : 'Search failed',
            );
        })
        .finally(() => {
          if (!controller.signal.aborted) setSearching(false);
        });
    }, 220);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [query, user]);
  const act = (work: () => Promise<void>, message = 'Changes saved') => {
    if (busy) return;
    setBusy(true);
    setError('');
    setNotice('');
    void work()
      .then(() => setNotice(message))
      .catch((reason: unknown) =>
        setError(
          reason instanceof Error
            ? reason.message
            : 'Unable to complete the action',
        ),
      )
      .finally(() => setBusy(false));
  };
  const openProject = (id: number, requirementId?: number) => {
    setProjectId(id);
    setDocumentId(requirementId ?? null);
    setView('project');
    setQuery('');
    setError('');
  };
  const openResearch = (id: number) => {
    setResearchId(id);
    setView('research');
    setQuery('');
    setError('');
  };
  const navigate = (destination: string) => {
    setView(destination);
    setQuery('');
    setError('');
    setNotice('');
  };
  const dashboard = space.dashboards.find((d) => d.project.id === projectId);
  const tasks = space.dashboards.flatMap((d) =>
    d.requirements
      .filter(
        (r) =>
          (r.responsible?.id === user?.id &&
            ['MISSING', 'DRAFT', 'CHANGES_REQUESTED'].includes(r.status)) ||
          (r.reviewer?.id === user?.id &&
            ['SUBMITTED', 'UNDER_REVIEW'].includes(r.status)),
      )
      .map((r) => ({ requirement: r, project: d.project })),
  );
  const createProject = () =>
    setForm({
      title: 'Create project',
      description:
        'Start a document workspace, then add your team and required documents.',
      submit: 'Create project',
      fields: [
        { name: 'name', label: 'Project name', required: true },
        { name: 'description', label: 'Description', type: 'textarea' },
        {
          name: 'lifecycle_template_id',
          label: 'Company lifecycle template (optional)',
          options: space.templates.map((t) => ({ value: t.id, label: t.name })),
        },
      ],
      save: async (data) => {
        const created = await request<Project>(
          '/projects',
          json({
            name: textValue(data, 'name'),
            description: textValue(data, 'description'),
            lifecycle_template_id: numberValue(data, 'lifecycle_template_id'),
          }),
        );
        await refresh();
        openProject(created.id);
        setNotice(
          'Project created. Add people and stages, then define required documents.',
        );
      },
    });
  if (boot)
    return (
      <div className="boot-screen">
        <Leaf size={32} />
        <h2>Opening your workspace…</h2>
      </div>
    );
  if (!user)
    return (
      <Login
        error={error}
        busy={busy}
        signIn={(employeeCode, password) =>
          act(async () => {
            const response = await request<{ employee: Employee }>(
              '/auth/login',
              json({ employee_code: employeeCode, password }),
            );
            await refresh();
            setUser(response.employee);
            setView('home');
          }, 'Signed in')
        }
      />
    );
  return (
    <div className="app-shell" aria-busy={busy}>
      <aside className="main-sidebar">
        <button className="brand" onClick={() => navigate('home')}>
          <span>
            <Leaf size={23} />
          </span>
          verdant<span className="brand-dot">.</span>
        </button>
        <div className="sidebar-caption">YOUR WORKSPACE</div>
        <nav aria-label="Main navigation">
          <button
            className={view === 'home' ? 'active' : ''}
            onClick={() => navigate('home')}
          >
            <Home size={19} />
            Home
          </button>
          <button
            className={['projects', 'project'].includes(view) ? 'active' : ''}
            onClick={() => navigate('projects')}
          >
            <FolderOpen size={19} />
            My projects
            <span className="nav-count">{space.projects.length}</span>
          </button>
          <button
            className={view === 'tasks' ? 'active' : ''}
            onClick={() => navigate('tasks')}
          >
            <CheckCircle2 size={19} />
            My actions<span className="nav-count">{tasks.length}</span>
          </button>
          <button
            className={view === 'research' ? 'active' : ''}
            onClick={() => navigate('research')}
          >
            <BookOpen size={19} />
            Research library
          </button>
          <button
            className={view === 'shared' ? 'active' : ''}
            onClick={() => navigate('shared')}
          >
            <Share2 size={19} />
            Shared with me
          </button>
        </nav>
        <div className="sidebar-note">
          <FileText size={21} />
          <strong>Knowledge, in one place.</strong>
          <p>Read documents, follow reviews and connect your research.</p>
        </div>
        <div className="account">
          <div className="avatar">{user.name.slice(0, 1)}</div>
          <div>
            <strong>{user.name}</strong>
            <small>{user.employee_code}</small>
          </div>
          <button
            aria-label="Sign out"
            title="Sign out"
            onClick={() =>
              act(async () => {
                await request('/auth/logout', json({}));
                setUser(null);
                setSpace(empty);
                setView('home');
              }, 'Signed out')
            }
          >
            <LogOut size={18} />
          </button>
        </div>
      </aside>
      <div className="main-column">
        <header className="topbar">
          <span className="topbar-context">
            {view === 'project'
              ? dashboard?.project.name
              : 'Document workspace'}
          </span>
          <div className="global-search">
            <Search size={18} />
            <input
              aria-label="Search all documents"
              placeholder="Search documents, types and research…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            {query && (
              <button aria-label="Clear search" onClick={() => setQuery('')}>
                <X size={16} />
              </button>
            )}
            {!!query.trim() && (
              <section className="search-results" aria-label="Search results">
                {searching ? (
                  <p>Searching…</p>
                ) : results.length ? (
                  results.map((result) => (
                    <button
                      key={result.kind + result.id}
                      onClick={() =>
                        result.project_id
                          ? space.projects.some(
                              (p) => p.id === result.project_id,
                            )
                            ? openProject(result.project_id, result.id)
                            : (setShareId(result.id), navigate('shared'))
                          : openResearch(result.id)
                      }
                    >
                      <FileText size={18} />
                      <span>
                        <strong>{result.title}</strong>
                        <small>
                          {result.context} ·{' '}
                          {result.kind === 'research_document'
                            ? 'Research'
                            : 'Project document'}
                        </small>
                      </span>
                      <ArrowRight size={16} />
                    </button>
                  ))
                ) : (
                  <p>
                    No matching documents. Try a title, description or document
                    type.
                  </p>
                )}
              </section>
            )}
          </div>
          <span className="private-label">
            <span />
            Company workspace
          </span>
        </header>
        <main
          className={
            'workspace-main ' +
            (['project', 'research', 'shared'].includes(view) ? 'wide' : '')
          }
        >
          {error && (
            <div className="notice error" role="alert">
              {error}
              <button aria-label="Dismiss error" onClick={() => setError('')}>
                <X size={16} />
              </button>
            </div>
          )}
          {notice && (
            <output className="notice success">
              {notice}
              <button
                aria-label="Dismiss notification"
                onClick={() => setNotice('')}
              >
                <X size={16} />
              </button>
            </output>
          )}
          {['home', 'projects', 'tasks'].includes(view) && (
            <>
              <header className="page-heading">
                <div>
                  <div className="eyebrow">
                    {view === 'home'
                      ? 'YOUR PERSONAL WORKSPACE'
                      : 'KEEP EVERYTHING MOVING'}
                  </div>
                  <h1>
                    {view === 'home'
                      ? 'Welcome back, ' + user.name.split(' ')[0] + '.'
                      : view === 'projects'
                        ? 'My projects'
                        : 'My actions'}
                  </h1>
                  <p>
                    {view === 'home'
                      ? 'Your projects, documents and next steps — all in one place.'
                      : view === 'projects'
                        ? 'Only the projects you own or belong to.'
                        : 'Documents waiting for your upload, submission or review.'}
                  </p>
                </div>
                {view !== 'tasks' && (
                  <button className="primary" onClick={createProject}>
                    <Plus size={17} />
                    Create project
                  </button>
                )}
              </header>
              {view === 'home' && (
                <div className="home-stats">
                  <button onClick={() => navigate('projects')}>
                    <span className="stat-icon">
                      <FolderOpen size={22} />
                    </span>
                    <span>
                      <strong>{space.projects.length}</strong>
                      <small>Your projects</small>
                    </span>
                    <ArrowRight size={18} />
                  </button>
                  <button onClick={() => navigate('tasks')}>
                    <span className="stat-icon amber">
                      <CheckCircle2 size={22} />
                    </span>
                    <span>
                      <strong>{tasks.length}</strong>
                      <small>Need your action</small>
                    </span>
                    <ArrowRight size={18} />
                  </button>
                  <button onClick={() => navigate('research')}>
                    <span className="stat-icon blue">
                      <BookOpen size={22} />
                    </span>
                    <span>
                      <strong>{space.research.length}</strong>
                      <small>Research documents</small>
                    </span>
                    <ArrowRight size={18} />
                  </button>
                </div>
              )}
              {view !== 'tasks' && (
                <section>
                  <div className="section-heading">
                    <h2>Your projects</h2>
                    <span className="muted">
                      {space.projects.length} workspaces
                    </span>
                  </div>
                  <div className="project-grid">
                    {space.dashboards.map((d) => (
                      <button
                        className="project-card"
                        key={d.project.id}
                        onClick={() => openProject(d.project.id)}
                      >
                        <div className="project-card-top">
                          <span className="project-symbol">
                            <FolderOpen size={24} />
                          </span>
                          <span className="pill">
                            {d.project.owner.id === user.id
                              ? 'Owner'
                              : 'Member'}
                          </span>
                        </div>
                        <h3>{d.project.name}</h3>
                        <p>
                          {d.project.description ||
                            'Project documentation workspace'}
                        </p>
                        <div className="progress-label">
                          <span>Documents approved</span>
                          <strong>
                            {d.progress.approved} / {d.progress.total}
                          </strong>
                        </div>
                        <progress
                          max={Math.max(d.progress.total, 1)}
                          value={d.progress.approved}
                        />
                        <div className="project-card-foot">
                          <span>{d.members.length} members</span>
                          <span>
                            Open workspace <ArrowRight size={15} />
                          </span>
                        </div>
                      </button>
                    ))}
                    {!space.projects.length && (
                      <div className="panel empty-state">
                        <FolderOpen size={32} />
                        <h3>No project memberships yet</h3>
                        <p>
                          Create a project or ask a project owner to add you.
                          Individually shared documents are under Shared with
                          me.
                        </p>
                      </div>
                    )}
                  </div>
                </section>
              )}
              {view !== 'projects' && (
                <section className="action-section">
                  <div className="section-heading">
                    <div>
                      <h2>Needs your attention</h2>
                      <p className="muted">
                        These actions are assigned to you—not to everyone on the
                        project.
                      </p>
                    </div>
                  </div>
                  <div className="panel action-list">
                    {tasks.length ? (
                      tasks.map(({ requirement: r, project: p }) => (
                        <button
                          className="task-row"
                          key={r.id}
                          onClick={() => openProject(p.id, r.id)}
                        >
                          <FileText size={20} />
                          <span>
                            <strong>{r.title}</strong>
                            <small>
                              {p.name} ·{' '}
                              {r.reviewer?.id === user.id
                                ? 'Review assigned to you'
                                : 'You are responsible'}
                            </small>
                          </span>
                          <Status value={r.status} />
                          <ArrowRight size={17} />
                        </button>
                      ))
                    ) : (
                      <div className="empty-state">
                        <CheckCircle2 size={30} />
                        <h3>You’re all caught up</h3>
                        <p>
                          No document actions are currently waiting for you.
                        </p>
                      </div>
                    )}
                  </div>
                </section>
              )}
            </>
          )}
          {view === 'project' && dashboard && (
            <ProjectWorkspace
              key={dashboard.project.id}
              dashboard={dashboard}
              user={user}
              people={space.people}
              research={space.research}
              selected={documentId}
              select={setDocumentId}
              openResearch={openResearch}
              showForm={setForm}
              refresh={refresh}
              act={act}
            />
          )}
          {view === 'research' && (
            <ResearchWorkspace
              user={user}
              categories={space.categories}
              documents={space.research}
              projects={space.projects}
              selected={researchId}
              select={setResearchId}
              openProject={openProject}
              showForm={setForm}
              refresh={refresh}
              act={act}
            />
          )}
          {view === 'shared' && (
            <>
              <header className="page-heading">
                <div>
                  <div className="eyebrow">DOCUMENT-ONLY ACCESS</div>
                  <h1>Shared with me</h1>
                  <p>
                    Read files shared directly with you, without accessing the
                    whole project.
                  </p>
                </div>
              </header>
              <div className="document-workspace">
                <aside className="document-list">
                  <div className="list-heading">
                    <h2>Shared documents</h2>
                  </div>
                  {space.shared.map((s) => (
                    <button
                      className={
                        'file-row ' +
                        (shareId === s.requirement_id ? 'selected' : '')
                      }
                      key={s.requirement_id}
                      onClick={() => setShareId(s.requirement_id)}
                    >
                      <FileText size={18} />
                      <span>
                        <strong>{s.title}</strong>
                        <small>{s.project_name}</small>
                        <Status value={s.status} />
                      </span>
                    </button>
                  ))}
                  {!space.shared.length && (
                    <p className="empty-small">
                      No documents shared directly with you yet.
                    </p>
                  )}
                </aside>
                <DocumentReader
                  version={
                    space.shared.find((s) => s.requirement_id === shareId)
                      ?.current_version
                  }
                />
              </div>
            </>
          )}
        </main>
      </div>
      {form && <FormDialog spec={form} close={() => setForm(null)} />}
    </div>
  );
}
function Login({
  error,
  busy,
  signIn,
}: {
  error: string;
  busy: boolean;
  signIn: (code: string, password: string) => void;
}) {
  const [code, setCode] = useState('');
  const [password, setPassword] = useState('');
  return (
    <main className="login-page">
      <section className="login-story">
        <div className="brand">
          <span>
            <Leaf size={25} />
          </span>
          verdant.
        </div>
        <div>
          <div className="eyebrow">YOUR COMPANY’S KNOWLEDGE, CONNECTED</div>
          <h1>
            Less searching.
            <br />
            More understanding.
          </h1>
          <p>
            A calm place for the documents your work depends on. Find the right
            version, understand the feedback, and keep knowledge moving.
          </p>
          <div className="login-feature">
            <FileText />
            Read without leaving your workspace
          </div>
          <div className="login-feature">
            <CheckCircle2 />
            Clear ownership and review history
          </div>
          <div className="login-feature">
            <BookOpen />A shared home for company research
          </div>
        </div>
        <small>Project documentation · Research · Version history</small>
      </section>
      <section className="login-form">
        <div>
          <div className="eyebrow">WELCOME TO VERDANT</div>
          <h2>Sign in to your workspace</h2>
          <p className="muted">Use your employee ID or company username.</p>
          <form
            method="post"
            onSubmit={(event) => {
              event.preventDefault();
              signIn(code, password);
            }}
          >
            <label className="field">
              <span>Employee ID or username</span>
              <input
                autoComplete="username"
                required
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="e.g. EMP-1042"
              />
            </label>
            <label className="field">
              <span>Password</span>
              <input
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </label>
            {error && (
              <p className="notice error" role="alert">
                {error}
              </p>
            )}
            <button className="primary" type="submit" disabled={busy}>
              {busy ? 'Signing in…' : 'Sign in'}
              <ArrowRight size={17} />
            </button>
          </form>
          <p className="login-help">
            Need access? Contact your company administrator.
          </p>
        </div>
      </section>
    </main>
  );
}
