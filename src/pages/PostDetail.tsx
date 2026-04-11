import { useParams, Link } from 'react-router-dom';
import { usePost } from '@/hooks/usePosts';
import MathRenderer from '@/components/MathRenderer';
import CategoryBadge from '@/components/CategoryBadge';
import CommentSection from '@/components/CommentSection';
import { formatDate } from '@/utils/formatDate';
import { ArrowLeft, Calendar, Loader2 } from 'lucide-react';

export default function PostDetail() {
  const { slug } = useParams<{ slug: string }>();
  const { data: post, isLoading, isError } = usePost(slug || '');

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="h-8 w-8 text-primary animate-spin" />
      </div>
    );
  }

  if (isError || !post) {
    return (
      <div className="container mx-auto px-4 py-16 text-center">
        <h2 className="font-heading text-2xl text-chalk-bright mb-4">Post not found</h2>
        <p className="text-muted-foreground mb-6">The article you're looking for doesn't exist or your backend isn't connected.</p>
        <Link to="/blog" className="text-accent hover:text-primary transition-colors">
          ← Back to articles
        </Link>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-12">
      <Link
        to="/blog"
        className="inline-flex items-center gap-1 text-sm text-accent hover:text-primary transition-colors mb-8"
      >
        <ArrowLeft className="h-3 w-3" /> Back to articles
      </Link>

      <article className="max-w-3xl mx-auto">
        <header className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <CategoryBadge category={post.category} />
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Calendar className="h-3 w-3" />
              {formatDate(post.created_at)}
            </div>
          </div>
          <h1 className="font-heading text-3xl md:text-4xl font-bold text-chalk-bright leading-tight">
            {post.title}
          </h1>
          {post.excerpt && (
            <p className="mt-4 text-lg text-chalk leading-relaxed">{post.excerpt}</p>
          )}
        </header>

        <div className="border-t border-border pt-8">
          <MathRenderer content={post.content} />
        </div>

        <CommentSection postId={post.id} />
      </article>
    </div>
  );
}
