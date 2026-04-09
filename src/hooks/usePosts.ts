import { useQuery } from '@tanstack/react-query';
import { postService } from '@/services/postService';

export function usePosts(params?: { page?: number; category?: string; search?: string }) {
  return useQuery({
    queryKey: ['posts', params],
    queryFn: () => postService.getAll(params),
  });
}

export function usePost(slug: string) {
  return useQuery({
    queryKey: ['post', slug],
    queryFn: () => postService.getBySlug(slug),
    enabled: !!slug,
  });
}
