import { Link } from 'react-router-dom';
import type { Post } from '@/services/postService';
import { formatDate } from '@/utils/formatDate';
import CategoryBadge from './CategoryBadge';
import { ArrowRight } from 'lucide-react';

interface Props {
  post: Post;
}

export default function PostCard({ post }: Props) {
  return (
    <article className="group rounded-lg border border-border bg-card p-6 transition-all hover:border-primary/30 hover:shadow-lg hover:shadow-primary/5">
      <div className="flex items-center gap-3 mb-3">
        <CategoryBadge category={post.category} />
        <time className="text-xs text-muted-foreground">{formatDate(post.created_at)}</time>
      </div>
      <h3 className="font-heading text-xl font-semibold text-chalk-bright mb-2 group-hover:text-primary transition-colors">
        <Link to={`/blog/${post.slug}`}>{post.title}</Link>
      </h3>
      <p className="text-sm text-chalk leading-relaxed mb-4 line-clamp-3">{post.excerpt}</p>
      <Link
        to={`/blog/${post.slug}`}
        className="inline-flex items-center gap-1 text-sm text-accent hover:text-primary transition-colors"
      >
        Read more <ArrowRight className="h-3 w-3" />
      </Link>
    </article>
  );
}
