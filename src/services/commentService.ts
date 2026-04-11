import apiFetch from './api';

export interface Comment {
  id: string;
  post_id: string;
  post_title?: string;
  author: string;
  email: string;
  content: string;
  approved: boolean;
  created_at: string;
}

export const commentService = {
  getByPost: (postId: string) =>
    apiFetch<Comment[]>(`/posts/${postId}/comments`),

  create: (postId: string, data: { author: string; email: string; content: string }) =>
    apiFetch<Comment>(`/posts/${postId}/comments`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getAll: () => apiFetch<Comment[]>('/comments'),

  approve: (id: string) =>
    apiFetch<Comment>(`/comments/${id}/approve`, { method: 'PATCH' }),

  delete: (id: string) =>
    apiFetch<void>(`/comments/${id}`, { method: 'DELETE' }),
};
