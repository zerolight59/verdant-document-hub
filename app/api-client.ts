export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export async function api<T>(path: string, token?: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (token) headers.set('Authorization', `Bearer ${token}`);
  if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  const response = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try { message = ((await response.json()) as { detail?: string }).detail || message; } catch {}
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export async function fileBlob(path: string, token: string): Promise<Blob> {
  const response = await fetch(`${API_URL}${path.replace(/^\/api/, '')}`, { headers: { Authorization: `Bearer ${token}` } });
  if (!response.ok) throw new Error('The document preview could not be opened.');
  return response.blob();
}

