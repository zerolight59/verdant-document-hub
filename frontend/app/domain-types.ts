export type Employee = {
  id: number;
  employee_code: string;
  username?: string;
  name: string;
  email: string;
  job_title: string;
  department?: string;
  is_admin: boolean;
  is_active: boolean;
  created_at: string;
};

export type Project = {
  id: number;
  name: string;
  description?: string;
  owner_id: number;
  lifecycle_template_id?: number;
};

export type LifecycleTemplate = {
  id: number;
  name: string;
  stages: { id: number; name: string; position: number }[];
};

export type Person = {
  id: number;
  employee_code: string;
  name: string;
  job_title: string;
};

export type Review = {
  id: number;
  decision: string;
  comment?: string;
};

export type DocumentVersion = {
  id: number;
  version_number: number;
  file_name: string;
  mime_type: string;
  file_size: number;
  change_summary?: string;
  view_url: string;
  review?: Review;
};

export type Requirement = {
  id: number;
  title: string;
  description?: string;
  stage_id: number;
  document_type: string;
  status: string;
  due_date?: string;
  responsible?: Person;
  reviewer?: Person;
  document_id?: number;
  current_version?: DocumentVersion;
};

export type ProjectDashboard = {
  project: { id: number; name: string; description?: string; owner: Person };
  stages: { id: number; name: string; position: number }[];
  members: { id: number; employee: Person; access_level: string }[];
  requirements: Requirement[];
  progress: { total: number; approved: number };
};

export type ResearchCategory = {
  id: number;
  name: string;
  parent_id?: number;
};

export type ResearchDocument = {
  id: number;
  name: string;
  description?: string;
  category_id: number;
  category: string;
  uploaded_by: string;
  current_version?: DocumentVersion;
  endorsements: { employee_name: string; label: string }[];
};

export type AuditRecord = {
  id: number;
  actor: string;
  action: string;
  entity_type: string;
  entity_id?: number;
  project_id?: number;
  details?: Record<string, unknown>;
  created_at: string;
};

export type SearchResult = {
  kind: string;
  id: number;
  title: string;
  context: string;
  status?: string;
  project_id?: number;
};

export type SharedDocument = {
  requirement_id: number;
  project_id: number;
  project_name: string;
  title: string;
  status: string;
  access_level: string;
  current_version?: DocumentVersion;
};
