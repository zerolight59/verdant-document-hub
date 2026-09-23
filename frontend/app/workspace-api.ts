export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body && !(options.body instanceof FormData))
    headers.set('Content-Type', 'application/json');
  const response = await fetch(API_URL + path.replace(/^\/api/, ''), {
    ...options,
    headers,
    credentials: 'include',
  });
  if (!response.ok) {
    if (
      response.status === 401 &&
      path !== '/auth/login' &&
      typeof window !== 'undefined'
    ) {
      window.dispatchEvent(new Event('verdant:session-expired'));
    }
    let message = 'Request failed (' + response.status + ')';
    try {
      const body = (await response.json()) as {
        detail?: string | { msg: string }[];
      };
      if (typeof body.detail === 'string') message = body.detail;
      else if (Array.isArray(body.detail))
        message = body.detail.map((item) => item.msg).join('; ');
    } catch {
      /* Keep the HTTP error if the server has no JSON body. */
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}
export const json = (value: unknown): RequestInit => ({
  method: 'POST',
  body: JSON.stringify(value),
});
export async function getFile(
  path: string,
  signal: AbortSignal,
): Promise<Blob> {
  const response = await fetch(API_URL + path.replace(/^\/api/, ''), {
    credentials: 'include',
    signal,
  });
  if (!response.ok)
    throw new Error(
      'Unable to open this file. Check your access or sign in again.',
    );
  return response.blob();
}
