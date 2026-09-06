export type View = 'my-work' | 'projects' | 'research' | 'audit';
export type DocStatus = 'Missing' | 'Draft' | 'Submitted' | 'Under review' | 'Changes requested' | 'Approved';
export type ProjectDocument = { id:number; name:string; stage:string; status:DocStatus; version:string; responsible:string; responsibleInitials:string; reviewer:string; reviewerInitials:string; updated:string; due:string; description:string };
export type ResearchFile = { id:number; name:string; category:string; uploadedBy:string; updated:string; kind:string; endorsed?:string };
export const initialProjectDocuments: ProjectDocument[] = [
{id:1,name:'Product concept brief',stage:'Discovery',status:'Approved',version:'v3',responsible:'Asha Menon',responsibleInitials:'AM',reviewer:'Raman Iyer',reviewerInitials:'RI',updated:'Today, 9:14 AM',due:'Completed',description:'Product positioning, target users, intended capabilities, and agreed concept boundaries.'},
{id:2,name:'Market requirements document',stage:'Definition',status:'Under review',version:'v2',responsible:'Nikhil Rao',responsibleInitials:'NR',reviewer:'Priya Shah',reviewerInitials:'PS',updated:'Today, 11:32 AM',due:'12 Sep',description:'Customer requirements, competitive benchmarks, and commercial acceptance criteria.'},
{id:3,name:'Design specification',stage:'Engineering',status:'Changes requested',version:'v4',responsible:'Devika Nair',responsibleInitials:'DN',reviewer:'Raman Iyer',reviewerInitials:'RI',updated:'Yesterday, 4:18 PM',due:'14 Sep',description:'System design decisions, interfaces, operating constraints, and verification approach.'},
{id:4,name:'Technical drawing — Front assembly',stage:'Engineering',status:'Draft',version:'v1',responsible:'Arjun Das',responsibleInitials:'AD',reviewer:'Priya Shah',reviewerInitials:'PS',updated:'5 Sep, 2:05 PM',due:'18 Sep',description:'Front assembly dimensional drawing and production tolerances.'},
{id:5,name:'Supplier validation report',stage:'Validation',status:'Missing',version:'—',responsible:'Unassigned',responsibleInitials:'—',reviewer:'Unassigned',reviewerInitials:'—',updated:'Not started',due:'25 Sep',description:'Evidence and conclusions from supplier process and quality validation.'},
];
export const initialResearch: ResearchFile[] = [
{id:101,name:'High-strength steel forming guide.pdf',category:'Materials / Metals',uploadedBy:'Asha Menon',updated:'Today',kind:'PDF',endorsed:'CEO endorsement'},
{id:102,name:'Automotive sealing systems benchmark.pdf',category:'Engineering / Body systems',uploadedBy:'Arjun Das',updated:'Yesterday',kind:'PDF'},
{id:103,name:'EV consumer preference study.pdf',category:'Market research / India',uploadedBy:'Nikhil Rao',updated:'3 Sep',kind:'PDF'},
{id:104,name:'Supplier quality checklist.xlsx',category:'Operations / Suppliers',uploadedBy:'Devika Nair',updated:'1 Sep',kind:'Spreadsheet',endorsed:'Leadership endorsed'},
];
export const auditEvents=[
{action:'Review started',detail:'Priya Shah opened Market requirements document v2',time:'Today, 11:32 AM',icon:'eye'},
{action:'New version submitted',detail:'Nikhil Rao submitted Market requirements document v2',time:'Today, 10:48 AM',icon:'upload'},
{action:'Document approved',detail:'Raman Iyer approved Product concept brief v3',time:'Today, 9:14 AM',icon:'approve'},
{action:'Changes requested',detail:'Raman Iyer returned Design specification v4 with 3 comments',time:'Yesterday, 4:18 PM',icon:'comment'},
{action:'Access updated',detail:'Project owner gave Arjun Das edit access to Front assembly drawing',time:'4 Sep, 3:40 PM',icon:'access'},
];
export const statusTone:Record<DocStatus,string>={Missing:'border-slate-200 bg-slate-100 text-slate-600',Draft:'border-blue-200 bg-blue-50 text-blue-700',Submitted:'border-violet-200 bg-violet-50 text-violet-700','Under review':'border-amber-200 bg-amber-50 text-amber-700','Changes requested':'border-rose-200 bg-rose-50 text-rose-700',Approved:'border-emerald-200 bg-emerald-50 text-emerald-700'};
