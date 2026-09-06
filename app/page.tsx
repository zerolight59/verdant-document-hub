'use client';

import { useEffect, useMemo, useState } from 'react';
import {
  Archive, ArrowUpRight, Bell, BookOpen, Check, ChevronRight, CircleAlert,
  Clock3, CloudUpload, FileCheck2, FileClock, FileText, FolderKanban,
  LayoutDashboard, Link2, MoreHorizontal, Network, Plus, Search, Sparkles, Users,
} from 'lucide-react';

import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Sheet, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import {
  Sidebar, SidebarContent, SidebarFooter, SidebarGroup, SidebarGroupContent,
  SidebarGroupLabel, SidebarHeader, SidebarInset, SidebarMenu, SidebarMenuButton,
  SidebarMenuItem, SidebarProvider, SidebarTrigger,
} from '@/components/ui/sidebar';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';

type Status = 'Approved' | 'In review' | 'Draft' | 'Changes requested';
type Section = 'Overview' | 'Projects' | 'Documents' | 'Research library' | 'People';
type WebMCPTool = {
  name: string;
  title: string;
  description: string;
  inputSchema: Record<string, unknown>;
  annotations: { readOnlyHint: boolean; untrustedContentHint: boolean };
  execute: (input: unknown) => unknown | Promise<unknown>;
};

type WebMCPDocument = Document & {
  modelContext?: { registerTool: (tool: WebMCPTool, options?: { signal?: AbortSignal }) => void | Promise<void> };
};

type DocumentRecord = {
  id: number; name: string; type: string; version: string; owner: string;
  initials: string; updated: string; status: Status; description: string;
  reviewer: string; location: string; indexed: boolean;
};

const initialDocuments: DocumentRecord[] = [
  { id: 1, name: 'Site feasibility report', type: 'Feasibility', version: 'v3', owner: 'Ananya Rao', initials: 'AR', updated: 'Today, 10:42 AM', status: 'In review', description: 'Updated feasibility findings with field survey notes and revised risk assumptions.', reviewer: 'Vikram Mehta', location: '/projects/atlas/feasibility/v3', indexed: true },
  { id: 2, name: 'Environmental baseline study', type: 'Assessment', version: 'v2', owner: 'Kabir Shah', initials: 'KS', updated: 'Yesterday, 4:18 PM', status: 'Approved', description: 'Baseline environmental assessment approved for planning and permitting use.', reviewer: 'Meera Nair', location: '/projects/atlas/environment/v2', indexed: true },
  { id: 3, name: 'Land survey drawings', type: 'Technical drawing', version: 'v5', owner: 'Ishaan Patel', initials: 'IP', updated: '2 Sep, 2:05 PM', status: 'Changes requested', description: 'Latest boundary and contour drawings pending corrections from the survey team.', reviewer: 'Ananya Rao', location: '/projects/atlas/surveys/v5', indexed: false },
  { id: 4, name: 'Preliminary cost estimate', type: 'Commercial', version: 'v1', owner: 'Meera Nair', initials: 'MN', updated: '1 Sep, 11:20 AM', status: 'Draft', description: 'Initial project cost estimate covering development, approvals, and contingencies.', reviewer: 'Not assigned', location: '/projects/atlas/commercial/v1', indexed: false },
];

const navItems: { label: Section; icon: typeof LayoutDashboard }[] = [
  { label: 'Overview', icon: LayoutDashboard }, { label: 'Projects', icon: FolderKanban },
  { label: 'Documents', icon: FileText }, { label: 'Research library', icon: BookOpen },
  { label: 'People', icon: Users },
];

const statusStyle: Record<Status, string> = {
  Approved: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  'In review': 'border-amber-200 bg-amber-50 text-amber-700',
  Draft: 'border-slate-200 bg-slate-50 text-slate-600',
  'Changes requested': 'border-rose-200 bg-rose-50 text-rose-700',
};

function StatusBadge({ status }: { status: Status }) {
  return <Badge variant="outline" className={`font-medium ${statusStyle[status]}`}><span className="mr-1 size-1.5 rounded-full bg-current" />{status}</Badge>;
}

function DocumentTable({ documents, onSelect }: { documents: DocumentRecord[]; onSelect: (document: DocumentRecord) => void }) {
  return (
    <Table>
      <TableHeader><TableRow className="border-slate-200 hover:bg-transparent">
        <TableHead className="h-11 pl-5 text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">Document</TableHead>
        <TableHead className="text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">Owner</TableHead>
        <TableHead className="text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">Updated</TableHead>
        <TableHead className="text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">Status</TableHead><TableHead className="w-12" />
      </TableRow></TableHeader>
      <TableBody>{documents.map((document) => (
        <TableRow key={document.id} tabIndex={0} role="button" onClick={() => onSelect(document)} onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') onSelect(document); }} className="cursor-pointer border-slate-100 bg-white hover:bg-[#f5f8f6] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-emerald-700">
          <TableCell className="py-3.5 pl-5"><div className="flex min-w-[240px] items-center gap-3"><span className="flex size-9 items-center justify-center rounded-lg border border-emerald-100 bg-emerald-50 text-emerald-800"><FileText className="size-4" /></span><div><p className="font-medium text-slate-900">{document.name}</p><p className="mt-0.5 text-xs text-slate-500">{document.type} · {document.version}</p></div></div></TableCell>
          <TableCell><div className="flex items-center gap-2.5"><Avatar className="size-7 border border-white shadow-sm"><AvatarFallback className="bg-slate-100 text-[11px] font-semibold text-slate-600">{document.initials}</AvatarFallback></Avatar><span className="text-slate-700">{document.owner}</span></div></TableCell>
          <TableCell className="text-slate-500">{document.updated}</TableCell><TableCell><StatusBadge status={document.status} /></TableCell><TableCell><MoreHorizontal className="size-4 text-slate-400" /></TableCell>
        </TableRow>
      ))}</TableBody>
    </Table>
  );
}

function Overview({ documents, onSelect }: { documents: DocumentRecord[]; onSelect: (document: DocumentRecord) => void }) {
  const inReview = documents.filter((doc) => doc.status === 'In review').length;
  const approved = documents.filter((doc) => doc.status === 'Approved').length;
  return <div className="space-y-6">
    <section className="overflow-hidden rounded-2xl border border-[#cfdad4] bg-[#16392c] text-white shadow-[0_16px_40px_rgba(16,45,34,0.12)]">
      <div className="grid gap-6 px-6 py-6 lg:grid-cols-[1fr_360px] lg:px-8">
        <div className="flex items-start gap-5"><div className="progress-ring hidden size-24 shrink-0 items-center justify-center rounded-full sm:flex"><div className="flex size-[74px] flex-col items-center justify-center rounded-full bg-[#16392c]"><strong className="text-xl font-semibold">68%</strong><span className="text-[11px] uppercase tracking-wider text-emerald-100/70">ready</span></div></div>
          <div className="pt-1"><div className="mb-2 flex flex-wrap items-center gap-2"><Badge className="bg-[#c7f36b] text-[#173324] hover:bg-[#c7f36b]">On track</Badge><span className="text-xs text-emerald-100/65">Updated 12 minutes ago</span></div><h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">Project Atlas</h2><p className="mt-2 max-w-xl text-sm leading-6 text-emerald-50/75">Core planning documents are progressing well. One technical drawing needs attention before the next approval gate.</p></div>
        </div>
        <div className="grid grid-cols-3 gap-2 self-stretch rounded-xl border border-white/10 bg-white/[0.06] p-2">{[['12', 'Required'], ['8', 'Ready'], ['4', 'Open']].map(([value, label]) => <div key={label} className="flex flex-col items-center justify-center rounded-lg px-2 py-3 text-center"><strong className="text-xl font-semibold">{value}</strong><span className="mt-1 text-xs text-emerald-100/60">{label}</span></div>)}</div>
      </div>
      <div className="grid border-t border-white/10 bg-black/10 sm:grid-cols-3"><div className="flex items-center gap-3 px-6 py-3.5"><Check className="size-4 text-[#c7f36b]" /><span className="text-sm text-emerald-50/80">Feasibility gate complete</span></div><div className="flex items-center gap-3 border-white/10 px-6 py-3.5 sm:border-l"><Clock3 className="size-4 text-amber-300" /><span className="text-sm text-emerald-50/80">2 reviews due this week</span></div><div className="flex items-center gap-3 border-white/10 px-6 py-3.5 sm:border-l"><Sparkles className="size-4 text-sky-300" /><span className="text-sm text-emerald-50/80">9 versions searchable</span></div></div>
    </section>
    <section className="grid gap-4 md:grid-cols-3">{[
      { label: 'Documents ready', value: `${approved + 7}/12`, note: '+2 this week', icon: FileCheck2, tone: 'emerald' },
      { label: 'Awaiting review', value: String(inReview + 1), note: '1 due tomorrow', icon: FileClock, tone: 'amber' },
      { label: 'Research references', value: '24', note: '3 added this week', icon: Link2, tone: 'blue' },
    ].map((metric) => <article key={metric.label} className="rounded-xl border border-slate-200 bg-white p-5 shadow-[0_8px_24px_rgba(15,23,42,0.04)]"><div className="flex items-start justify-between"><div><p className="text-sm font-medium text-slate-500">{metric.label}</p><p className="mt-2 text-2xl font-semibold tracking-tight text-slate-900">{metric.value}</p><p className="mt-2 text-xs text-slate-500">{metric.note}</p></div><span className={`metric-icon metric-${metric.tone}`}><metric.icon className="size-5" /></span></div></article>)}</section>
    <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_330px]">
      <article className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-[0_8px_24px_rgba(15,23,42,0.04)]"><div className="flex items-center justify-between border-b border-slate-100 px-5 py-4"><div><h3 className="font-semibold text-slate-900">Recent documents</h3><p className="mt-1 text-xs text-slate-500">Latest project changes and approvals</p></div><Button variant="ghost" size="sm" className="text-emerald-800">View all <ArrowUpRight /></Button></div><DocumentTable documents={documents.slice(0, 4)} onSelect={onSelect} /></article>
      <aside className="rounded-xl border border-slate-200 bg-white p-5 shadow-[0_8px_24px_rgba(15,23,42,0.04)]"><div className="flex items-center justify-between"><div><h3 className="font-semibold text-slate-900">Next approval gate</h3><p className="mt-1 text-xs text-slate-500">Design readiness review</p></div><Badge variant="secondary" className="bg-amber-50 text-amber-700">18 Sep</Badge></div><div className="relative mt-5 space-y-1"><div className="absolute bottom-5 left-[17px] top-5 w-px bg-slate-200" />{[
        { name: 'Feasibility report', state: 'complete' }, { name: 'Baseline study', state: 'complete' }, { name: 'Survey drawings', state: 'attention' }, { name: 'Cost estimate', state: 'waiting' },
      ].map((item) => <div key={item.name} className="relative flex items-center gap-3 rounded-lg py-2"><span className={`z-10 flex size-9 items-center justify-center rounded-full border-4 border-white ${item.state === 'complete' ? 'bg-emerald-600 text-white' : item.state === 'attention' ? 'bg-rose-100 text-rose-700' : 'bg-slate-100 text-slate-400'}`}>{item.state === 'complete' ? <Check className="size-4" /> : item.state === 'attention' ? <CircleAlert className="size-4" /> : <Clock3 className="size-4" />}</span><div><p className="text-sm font-medium text-slate-800">{item.name}</p><p className="text-xs text-slate-500">{item.state === 'complete' ? 'Ready' : item.state === 'attention' ? 'Changes needed' : 'Waiting on dependency'}</p></div></div>)}</div></aside>
    </section>
  </div>;
}

function DocumentsView({ documents, query, onSelect }: { documents: DocumentRecord[]; query: string; onSelect: (document: DocumentRecord) => void }) {
  const filtered = documents.filter((doc) => `${doc.name} ${doc.type} ${doc.owner}`.toLowerCase().includes(query.toLowerCase()));
  return <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-[0_8px_24px_rgba(15,23,42,0.04)]"><Tabs defaultValue="all"><div className="flex flex-col gap-3 border-b border-slate-100 px-5 py-4 sm:flex-row sm:items-center sm:justify-between"><TabsList variant="line" className="h-9"><TabsTrigger value="all" className="px-3">All documents</TabsTrigger><TabsTrigger value="review" className="px-3">Needs review</TabsTrigger><TabsTrigger value="approved" className="px-3">Approved</TabsTrigger></TabsList><p className="text-xs text-slate-500">{filtered.length} records · all versions retained</p></div><TabsContent value="all"><DocumentTable documents={filtered} onSelect={onSelect} /></TabsContent><TabsContent value="review"><DocumentTable documents={filtered.filter((doc) => ['In review', 'Changes requested'].includes(doc.status))} onSelect={onSelect} /></TabsContent><TabsContent value="approved"><DocumentTable documents={filtered.filter((doc) => doc.status === 'Approved')} onSelect={onSelect} /></TabsContent></Tabs></section>;
}

function ResearchView() {
  const folders = [{ name: 'Policies & regulations', count: 8, color: 'bg-sky-100 text-sky-700' }, { name: 'Technical references', count: 11, color: 'bg-violet-100 text-violet-700' }, { name: 'Market studies', count: 5, color: 'bg-amber-100 text-amber-700' }];
  return <div className="space-y-5"><div className="grid gap-4 md:grid-cols-3">{folders.map((folder) => <article key={folder.name} className="group rounded-xl border border-slate-200 bg-white p-5 shadow-[0_8px_24px_rgba(15,23,42,0.04)] transition hover:-translate-y-0.5 hover:border-emerald-200"><div className="flex items-start justify-between"><span className={`flex size-10 items-center justify-center rounded-lg ${folder.color}`}><Archive className="size-5" /></span><ChevronRight className="size-4 text-slate-400 transition group-hover:translate-x-0.5" /></div><h3 className="mt-5 font-semibold text-slate-900">{folder.name}</h3><p className="mt-1 text-sm text-slate-500">{folder.count} references</p></article>)}</div><article className="rounded-xl border border-slate-200 bg-white p-5 shadow-[0_8px_24px_rgba(15,23,42,0.04)]"><div className="flex items-center justify-between"><div><h3 className="font-semibold text-slate-900">Research connected to Project Atlas</h3><p className="mt-1 text-xs text-slate-500">Shared knowledge linked to this project</p></div><Badge variant="outline" className="border-sky-200 bg-sky-50 text-sky-700"><Network /> Search ready</Badge></div><div className="mt-5 divide-y divide-slate-100">{['India Green Building Council reference guide', 'Urban water systems benchmarking study', 'State environmental clearance handbook'].map((name, index) => <div key={name} className="flex items-center gap-4 py-3.5"><span className="flex size-9 items-center justify-center rounded-lg bg-slate-100 text-slate-600"><BookOpen className="size-4" /></span><div className="min-w-0 flex-1"><p className="truncate text-sm font-medium text-slate-800">{name}</p><p className="mt-0.5 text-xs text-slate-500">Technical references · Added {index + 2} days ago</p></div><Button size="icon-sm" variant="ghost" aria-label={`Open ${name}`}><ArrowUpRight /></Button></div>)}</div></article></div>;
}

function ProjectsView() {
  return <div className="grid gap-4 lg:grid-cols-3">{[
    { name: 'Project Atlas', owner: 'Ananya Rao', progress: 68, documents: 12, status: 'On track' },
    { name: 'Project Cedar', owner: 'Kabir Shah', progress: 42, documents: 9, status: 'At risk' },
    { name: 'Project Horizon', owner: 'Meera Nair', progress: 91, documents: 16, status: 'On track' },
  ].map((project) => <article key={project.name} className="rounded-xl border border-slate-200 bg-white p-5 shadow-[0_8px_24px_rgba(15,23,42,0.04)]"><div className="flex items-start justify-between"><span className="flex size-10 items-center justify-center rounded-lg bg-emerald-50 text-emerald-800"><FolderKanban className="size-5" /></span><Badge variant="outline" className={project.status === 'On track' ? statusStyle.Approved : statusStyle['Changes requested']}>{project.status}</Badge></div><h3 className="mt-5 text-lg font-semibold text-slate-900">{project.name}</h3><p className="mt-1 text-sm text-slate-500">Owned by {project.owner}</p><div className="mt-5 h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-emerald-600" style={{ width: `${project.progress}%` }} /></div><div className="mt-3 flex justify-between text-xs text-slate-500"><span>{project.progress}% complete</span><span>{project.documents} documents</span></div></article>)}</div>;
}

function PeopleView() {
  return <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{[
    ['Ananya Rao', 'Project lead', 'AR', '5 documents'], ['Vikram Mehta', 'Reviewer', 'VM', '2 reviews open'],
    ['Kabir Shah', 'Environmental', 'KS', '3 documents'], ['Meera Nair', 'Commercial', 'MN', '1 review open'],
  ].map(([name, role, initials, note]) => <article key={name} className="rounded-xl border border-slate-200 bg-white p-5 text-center shadow-[0_8px_24px_rgba(15,23,42,0.04)]"><Avatar className="mx-auto size-14"><AvatarFallback className="bg-[#16392c] text-sm font-semibold text-white">{initials}</AvatarFallback></Avatar><h3 className="mt-4 font-semibold text-slate-900">{name}</h3><p className="mt-1 text-sm text-slate-500">{role}</p><Badge variant="secondary" className="mt-4 bg-slate-100 text-slate-600">{note}</Badge></article>)}</div>;
}

export default function Home() {
  const [section, setSection] = useState<Section>('Overview');
  const [documents, setDocuments] = useState(initialDocuments);
  const [selectedDocument, setSelectedDocument] = useState<DocumentRecord | null>(null);
  const [addOpen, setAddOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [project, setProject] = useState('atlas');
  const [notice, setNotice] = useState<string | null>(null);
  useEffect(() => {
    const modelContext = (document as WebMCPDocument).modelContext;
    if (!modelContext?.registerTool) return;
    const lifecycle = new AbortController();
    const register = (tool: WebMCPTool) => {
      void Promise.resolve(modelContext.registerTool(tool, { signal: lifecycle.signal })).catch(() => undefined);
    };

    register({
      name: 'create_project_document',
      title: 'Create project document',
      description: 'Create a new draft document record in the current Project Atlas workspace.',
      inputSchema: {
        type: 'object',
        properties: { name: { type: 'string', minLength: 1 }, type: { type: 'string', minLength: 1 }, description: { type: 'string' } },
        required: ['name', 'type'],
        additionalProperties: false,
      },
      annotations: { readOnlyHint: false, untrustedContentHint: false },
      async execute(input) {
        if (!input || typeof input !== 'object') throw new Error('Document details are required.');
        const values = input as Record<string, unknown>;
        if (typeof values.name !== 'string' || !values.name.trim() || typeof values.type !== 'string' || !values.type.trim()) throw new Error('Both name and type are required.');
        const record: DocumentRecord = {
          id: Date.now(), name: values.name.trim(), type: values.type.trim(),
          description: typeof values.description === 'string' ? values.description : 'New project document.',
          version: 'v1', owner: 'Manu Sankar', initials: 'MS', updated: 'Just now', status: 'Draft',
          reviewer: 'Not assigned', location: `/projects/atlas/${values.name.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-')}/v1`, indexed: false,
        };
        setDocuments((current) => [record, ...current]); setSection('Documents'); setNotice(`${record.name} was added as a draft.`);
        await new Promise<void>((resolve) => requestAnimationFrame(() => resolve()));
        return { id: record.id, name: record.name, status: record.status, version: record.version };
      },
    });

    register({
      name: 'approve_document_version',
      title: 'Approve document version',
      description: 'Approve the current version of an existing project document by numeric document ID.',
      inputSchema: { type: 'object', properties: { documentId: { type: 'number' } }, required: ['documentId'], additionalProperties: false },
      annotations: { readOnlyHint: false, untrustedContentHint: false },
      async execute(input) {
        if (!input || typeof input !== 'object' || typeof (input as Record<string, unknown>).documentId !== 'number') throw new Error('A numeric documentId is required.');
        const documentId = (input as { documentId: number }).documentId;
        const current = documents.find((item) => item.id === documentId);
        if (!current) throw new Error('Document not found.');
        const updated = { ...current, status: 'Approved' as Status, updated: 'Just now', reviewer: 'Manu Sankar' };
        setDocuments((items) => items.map((item) => item.id === documentId ? updated : item)); setSelectedDocument(updated); setNotice(`${updated.name} is now approved.`);
        await new Promise<void>((resolve) => requestAnimationFrame(() => resolve()));
        return { id: updated.id, name: updated.name, status: updated.status, version: updated.version };
      },
    });

    return () => lifecycle.abort();
  }, [documents]);
  const sectionCopy = useMemo(() => ({
    Overview: ['Good evening, Manu', 'Here is what needs attention across Project Atlas.'],
    Projects: ['Projects', 'Track document readiness across active work.'],
    Documents: ['Project documents', 'Find every file, version, owner, and approval in one place.'],
    'Research library': ['Research library', 'Reusable knowledge that can be connected to any project.'],
    People: ['Project people', 'Ownership and review responsibilities for this workspace.'],
  }[section]), [section]);

  function addDocument(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const name = String(form.get('name') || 'Untitled document');
    const type = String(form.get('type') || 'Project document');
    const description = String(form.get('description') || 'New project document.');
    const record: DocumentRecord = { id: Date.now(), name, type, description, version: 'v1', owner: 'Manu Sankar', initials: 'MS', updated: 'Just now', status: 'Draft', reviewer: 'Not assigned', location: `/projects/atlas/${name.toLowerCase().replace(/[^a-z0-9]+/g, '-')}/v1`, indexed: false };
    setDocuments((current) => [record, ...current]); setAddOpen(false); setSection('Documents'); setNotice(`${name} was added as a draft.`); event.currentTarget.reset();
  }

  function approveSelected() {
    if (!selectedDocument) return;
    const updated = { ...selectedDocument, status: 'Approved' as Status, updated: 'Just now', reviewer: 'Manu Sankar' };
    setDocuments((current) => current.map((doc) => doc.id === updated.id ? updated : doc)); setSelectedDocument(updated); setNotice(`${updated.name} is now approved.`);
  }

  return <SidebarProvider style={{ '--sidebar-width': '15.5rem' } as React.CSSProperties}>
    <Sidebar collapsible="icon" className="border-r-0">
      <SidebarHeader className="border-b border-white/10 bg-[#102d23] px-3 py-4 text-white"><div className="flex items-center gap-3 overflow-hidden px-1"><span className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-[#c7f36b] text-[#143326]"><Network className="size-5" /></span><div className="min-w-0 group-data-[collapsible=icon]:hidden"><p className="font-semibold tracking-[0.18em]">VERDANT</p><p className="text-[11px] text-emerald-100/55">DOCUMENT HUB</p></div></div></SidebarHeader>
      <SidebarContent className="bg-[#102d23] text-emerald-50"><SidebarGroup className="pt-4"><SidebarGroupLabel className="text-emerald-100/45">Workspace</SidebarGroupLabel><SidebarGroupContent><SidebarMenu className="gap-1">{navItems.map((item) => <SidebarMenuItem key={item.label}><SidebarMenuButton isActive={section === item.label} tooltip={item.label} onClick={() => setSection(item.label)} className="h-10 text-emerald-50/70 hover:bg-white/10 hover:text-white data-active:bg-[#c7f36b] data-active:text-[#143326]"><item.icon /><span>{item.label}</span></SidebarMenuButton></SidebarMenuItem>)}</SidebarMenu></SidebarGroupContent></SidebarGroup>
        <SidebarGroup className="mt-auto"><SidebarGroupLabel className="text-emerald-100/45">System</SidebarGroupLabel><div className="mx-2 rounded-lg border border-white/10 bg-white/[0.06] p-3 group-data-[collapsible=icon]:hidden"><div className="flex items-center gap-2 text-xs text-emerald-50/70"><span className="size-2 rounded-full bg-[#c7f36b]" />Search index healthy</div><div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/10"><div className="h-full w-[78%] rounded-full bg-[#c7f36b]" /></div><p className="mt-2 text-[11px] text-emerald-100/45">37 of 47 versions indexed</p></div></SidebarGroup>
      </SidebarContent>
      <SidebarFooter className="border-t border-white/10 bg-[#102d23] p-3 text-white"><div className="flex items-center gap-3 overflow-hidden"><Avatar className="size-8 shrink-0"><AvatarFallback className="bg-white/10 text-xs text-white">MS</AvatarFallback></Avatar><div className="min-w-0 group-data-[collapsible=icon]:hidden"><p className="truncate text-sm font-medium">Manu Sankar</p><p className="truncate text-[11px] text-emerald-100/45">Project manager</p></div></div></SidebarFooter>
    </Sidebar>
    <SidebarInset className="min-w-0 bg-[#f4f7f5]">
      <header className="sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-slate-200/80 bg-white/90 px-4 backdrop-blur md:px-6"><SidebarTrigger className="md:hidden" /><Select value={project} onValueChange={(value) => setProject(value as string)}><SelectTrigger className="hidden h-9 min-w-44 border-slate-200 bg-white sm:flex"><FolderKanban className="text-emerald-700" /><SelectValue /></SelectTrigger><SelectContent><SelectItem value="atlas">Project Atlas</SelectItem><SelectItem value="cedar">Project Cedar</SelectItem><SelectItem value="horizon">Project Horizon</SelectItem></SelectContent></Select><div className="relative ml-auto w-full max-w-md"><Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" /><Input value={query} onChange={(event) => setQuery(event.target.value)} onFocus={() => section !== 'Documents' && setSection('Documents')} placeholder="Search documents, versions, owners…" aria-label="Search documents" className="h-9 border-slate-200 bg-slate-50 pl-9 shadow-none focus-visible:bg-white" /></div><Button size="icon" variant="ghost" aria-label="Notifications" className="relative"><Bell /><span className="absolute right-1.5 top-1.5 size-2 rounded-full border-2 border-white bg-rose-500" /></Button><Button onClick={() => setAddOpen(true)} className="h-9 bg-[#1b5e45] px-3 text-white hover:bg-[#144b37]"><Plus /><span className="hidden sm:inline">Add document</span></Button></header>
      <div className="mx-auto w-full max-w-[1500px] px-4 py-6 md:px-7 lg:py-8">{notice && <div className="mb-5 flex items-center justify-between rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800" role="status"><span className="flex items-center gap-2"><Check className="size-4" />{notice}</span><button onClick={() => setNotice(null)} className="text-xs font-medium underline underline-offset-4">Dismiss</button></div>}<div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.12em] text-emerald-700">Project Atlas workspace</p><h1 className="mt-1 text-2xl font-semibold tracking-tight text-slate-950 sm:text-[28px]">{sectionCopy[0]}</h1><p className="mt-1.5 text-sm text-slate-500">{sectionCopy[1]}</p></div>{section === 'Overview' && <div className="flex items-center gap-2 text-xs text-slate-500"><span className="size-2 rounded-full bg-emerald-500" />Live project view</div>}</div>{section === 'Overview' && <Overview documents={documents} onSelect={setSelectedDocument} />}{section === 'Documents' && <DocumentsView documents={documents} query={query} onSelect={setSelectedDocument} />}{section === 'Research library' && <ResearchView />}{section === 'Projects' && <ProjectsView />}{section === 'People' && <PeopleView />}</div>
    </SidebarInset>
    <Dialog open={addOpen} onOpenChange={setAddOpen}><DialogContent className="sm:max-w-lg"><form onSubmit={addDocument}><DialogHeader><DialogTitle>Add a project document</DialogTitle><DialogDescription>Create the first version and place it in the Project Atlas workflow.</DialogDescription></DialogHeader><div className="grid gap-4 py-5"><div className="grid gap-2"><Label htmlFor="document-name">Document name</Label><Input id="document-name" name="name" placeholder="e.g. Detailed design report" required /></div><div className="grid gap-2"><Label htmlFor="document-type">Document type</Label><Input id="document-type" name="type" placeholder="e.g. Design report" required /></div><div className="grid gap-2"><Label htmlFor="document-description">Description</Label><Textarea id="document-description" name="description" placeholder="What does this document cover?" /></div><div className="rounded-lg border border-dashed border-emerald-300 bg-emerald-50/50 p-4 text-center"><CloudUpload className="mx-auto size-5 text-emerald-700" /><p className="mt-2 text-sm font-medium text-slate-700">File upload will connect to the company file server</p><p className="mt-1 text-xs text-slate-500">Prototype mode creates the record only.</p></div></div><DialogFooter><Button type="button" variant="outline" onClick={() => setAddOpen(false)}>Cancel</Button><Button type="submit" className="bg-[#1b5e45] hover:bg-[#144b37]">Create draft</Button></DialogFooter></form></DialogContent></Dialog>
    <Sheet open={Boolean(selectedDocument)} onOpenChange={(open) => !open && setSelectedDocument(null)}><SheetContent className="w-full overflow-y-auto p-0 sm:max-w-xl">{selectedDocument && <><SheetHeader className="border-b border-slate-200 px-6 py-6 pr-14"><div className="mb-3 flex items-center gap-2"><StatusBadge status={selectedDocument.status} /><Badge variant="secondary">{selectedDocument.version}</Badge></div><SheetTitle className="text-xl font-semibold text-slate-950">{selectedDocument.name}</SheetTitle><SheetDescription className="leading-6">{selectedDocument.description}</SheetDescription></SheetHeader><div className="space-y-6 p-6"><section><h3 className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-500">Document details</h3><dl className="mt-3 divide-y divide-slate-100 rounded-lg border border-slate-200">{[['Type', selectedDocument.type], ['Owner', selectedDocument.owner], ['Reviewer', selectedDocument.reviewer], ['Last updated', selectedDocument.updated], ['Location', selectedDocument.location]].map(([label, value]) => <div key={label} className="grid grid-cols-[110px_1fr] gap-3 px-4 py-3 text-sm"><dt className="text-slate-500">{label}</dt><dd className="break-all font-medium text-slate-800">{value}</dd></div>)}</dl></section><section><h3 className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-500">Version history</h3><div className="mt-3 space-y-3">{[selectedDocument.version, selectedDocument.version === 'v1' ? null : `v${Math.max(1, Number(selectedDocument.version.slice(1)) - 1)}`].filter(Boolean).map((version, index) => <div key={version} className="flex items-center gap-3 rounded-lg border border-slate-200 p-3"><span className={`flex size-8 items-center justify-center rounded-full ${index === 0 ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}><FileText className="size-4" /></span><div className="flex-1"><p className="text-sm font-medium text-slate-800">{version} {index === 0 && '· Current'}</p><p className="text-xs text-slate-500">Created by {selectedDocument.owner}</p></div></div>)}</div></section><section className={`rounded-lg border p-4 ${selectedDocument.indexed ? 'border-sky-200 bg-sky-50' : 'border-slate-200 bg-slate-50'}`}><div className="flex gap-3"><Sparkles className={`mt-0.5 size-5 ${selectedDocument.indexed ? 'text-sky-700' : 'text-slate-400'}`} /><div><p className="text-sm font-medium text-slate-800">{selectedDocument.indexed ? 'Available in smart search' : 'Waiting to be indexed'}</p><p className="mt-1 text-xs leading-5 text-slate-500">{selectedDocument.indexed ? 'This version can be found through semantic search and linked to related research.' : 'Indexing begins automatically after the document is approved.'}</p></div></div></section></div><SheetFooter className="sticky bottom-0 flex-row border-t border-slate-200 bg-white px-6 py-4"><Button variant="outline" className="flex-1">Open file</Button><Button onClick={approveSelected} disabled={selectedDocument.status === 'Approved'} className="flex-1 bg-[#1b5e45] hover:bg-[#144b37]"><FileCheck2 />{selectedDocument.status === 'Approved' ? 'Approved' : 'Approve version'}</Button></SheetFooter></>}</SheetContent></Sheet>
  </SidebarProvider>;
}


