import apiFetch from './api';

export interface Post {
  id: string;
  title: string;
  slug: string;
  excerpt: string;
  content: string;
  category: string;
  published: boolean;
  created_at: string;
  updated_at: string;
}

export interface PostsResponse {
  posts: Post[];
  total: number;
  page: number;
  pages: number;
}

export const postService = {
  getAll: (params?: { page?: number; category?: string; search?: string }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set('page', String(params.page));
    if (params?.category) query.set('category', params.category);
    if (params?.search) query.set('search', params.search);
    const qs = query.toString();
    return apiFetch<PostsResponse>(`/posts${qs ? `?${qs}` : ''}`);
  },

  getBySlug: (slug: string) => apiFetch<Post>(`/posts/${slug}`),

  create: (data: Partial<Post>) =>
    apiFetch<Post>('/posts', { method: 'POST', body: JSON.stringify(data) }),

  update: (id: string, data: Partial<Post>) =>
    apiFetch<Post>(`/posts/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  delete: (id: string) =>
    apiFetch<void>(`/posts/${id}`, { method: 'DELETE' }),

  togglePublish: (id: string, published: boolean) =>
    apiFetch<Post>(`/posts/${id}`, { method: 'PUT', body: JSON.stringify({ published }) }),
};
