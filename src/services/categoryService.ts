import apiFetch from './api';

export interface Category {
  id: string;
  name: string;
  slug: string;
}

export const categoryService = {
  getAll: () => apiFetch<Category[]>('/categories'),
};
