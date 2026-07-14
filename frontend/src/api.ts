const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
export const API_ORIGIN = API_BASE.replace(/\/api$/, '');

export function resolveFileUrl(path: string | null | undefined): string | null {
  if (!path) return null;
  if (path.startsWith('http')) return path;
  return `${API_ORIGIN}${path}`;
}

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

function getToken(): string | null {
  return localStorage.getItem('token');
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> || {}),
  };

  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (!res.ok) {
    let detail = 'Request failed';
    try {
      const data = await res.json();
      detail = data.detail || detail;
    } catch {
      /* ignore */
    }
    if (res.status === 404 && path.includes('paper')) {
      detail = 'Paper OCR is not available yet. The backend is still starting or needs a rebuild.';
    }
    throw new ApiError(typeof detail === 'string' ? detail : JSON.stringify(detail), res.status);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  login: async (email: string, password: string) => {
    const body = new URLSearchParams({ username: email, password });
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body,
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new ApiError(data.detail || 'Login failed', res.status);
    }
    return res.json() as Promise<{ access_token: string }>;
  },

  register: (name: string, email: string, password: string) =>
    request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ name, email, password }),
    }),

  me: () => request<import('./types').Instructor>('/auth/me'),

  getStats: () => request<import('./types').DashboardStats>('/dashboard/stats'),

  getQuestions: () => request<import('./types').Question[]>('/questions'),

  getQuestion: (id: number) => request<import('./types').Question>(`/questions/${id}`),

  createQuestion: (data: {
    title: string;
    question_text: string;
    model_answer: string;
    max_score: number;
    subject: string;
  }) =>
    request<import('./types').Question>('/questions', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  updateQuestion: (id: number, data: Partial<import('./types').Question>) =>
    request<import('./types').Question>(`/questions/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  deleteQuestion: (id: number) =>
    request<void>(`/questions/${id}`, { method: 'DELETE' }),

  getSubmissions: (questionId: number) =>
    request<import('./types').Submission[]>(`/questions/${questionId}/submissions`),

  submitAnswer: (
    questionId: number,
    data: { student_name: string; student_id?: string; answer_text: string }
  ) =>
    request<import('./types').Submission>(`/questions/${questionId}/submissions`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  previewPaperOcr: (questionId: number, file: File) => {
    const body = new FormData();
    body.append('file', file);
    return request<import('./types').OCRPreview>(`/questions/${questionId}/paper/ocr`, {
      method: 'POST',
      body,
    });
  },

  submitPaper: (
    questionId: number,
    data: { student_name: string; student_id?: string; file: File; answer_override?: string }
  ) => {
    const body = new FormData();
    body.append('file', data.file);
    body.append('student_name', data.student_name);
    if (data.student_id) body.append('student_id', data.student_id);
    if (data.answer_override) body.append('answer_override', data.answer_override);
    return request<import('./types').Submission>(`/questions/${questionId}/submissions/paper`, {
      method: 'POST',
      body,
    });
  },

  previewScore: (data: {
    model_answer: string;
    student_answer: string;
    max_score: number;
  }) =>
    request<import('./types').ScorePreview>('/questions/preview-score', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
};

export { ApiError };
