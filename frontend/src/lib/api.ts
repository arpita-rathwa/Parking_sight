const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8004";

let _token: string | null = localStorage.getItem("parksight_token");

export function setToken(token: string | null) {
  _token = token;
  if (token) {
    localStorage.setItem("parksight_token", token);
  } else {
    localStorage.removeItem("parksight_token");
  }
}

export function getToken(): string | null {
  return _token;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string>),
  };
  if (_token) {
    headers["Authorization"] = `Bearer ${_token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body}`);
  }

  return res.json();
}

export const api = {
  get<T>(path: string): Promise<T> {
    return request<T>(path);
  },
  post<T>(path: string, body?: unknown): Promise<T> {
    return request<T>(path, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    });
  },
  put<T>(path: string, body?: unknown): Promise<T> {
    return request<T>(path, {
      method: "PUT",
      body: body ? JSON.stringify(body) : undefined,
    });
  },
};
