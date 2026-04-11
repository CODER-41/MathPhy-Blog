import { Link } from 'react-router-dom';
import { usePosts } from '@/hooks/usePosts';
import { useCategories } from '@/hooks/useCategories';
import PostCard from '@/components/PostCard';
import CategoryBadge from '@/components/CategoryBadge';
import { ArrowRight, BookOpen, Sparkles } from 'lucide-react';

export default function Home() {
  const { data, isLoading } = usePosts({ page: 1 });
  const { data: categories } = useCategories();

  const latestPosts = data?.posts?.slice(0, 3) ?? [];

  return (
    <div className="min-h-screen">
      {/* Hero */}
      <section className="relative overflow-hidden py-24 md:py-32">
        <div className="absolute inset-0 bg-gradient-to-b from-primary/5 to-transparent" />
        <div className="container mx-auto px-4 relative">
          <div className="max-w-3xl mx-auto text-center animate-fade-in">
            <div className="inline-flex items-center gap-2 rounded-full bg-secondary px-4 py-1.5 text-xs text-secondary-foreground mb-6">
              <Sparkles className="h-3 w-3 text-primary" />
              Exploring the universe through equations
            </div>
            <h1 className="font-heading text-4xl md:text-6xl font-bold text-chalk-bright leading-tight mb-6">
              The Elegant Laws of{' '}
              <span className="text-primary italic">Physics</span>
            </h1>
            <p className="text-lg text-chalk max-w-xl mx-auto mb-8 leading-relaxed">
              A journal of mathematical beauty — from quantum mechanics to general relativity, 
              rendered with precision and care.
            </p>
            <Link
              to="/blog"
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-6 py-3 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              <BookOpen className="h-4 w-4" />
              Browse Articles
            </Link>
          </div>
        </div>
      </section>

      {/* Categories */}
      {categories && categories.length > 0 && (
        <section className="container mx-auto px-4 py-12">
          <h2 className="font-heading text-2xl font-semibold text-chalk-bright mb-6">Topics</h2>
          <div className="flex flex-wrap gap-2">
            {categories.map((cat) => (
              <Link key={cat.id} to={`/blog?category=${cat.slug}`}>
                <CategoryBadge category={cat.name} />
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* Latest Posts */}
      <section className="container mx-auto px-4 py-12">
        <div className="flex items-center justify-between mb-8">
          <h2 className="font-heading text-2xl font-semibold text-chalk-bright">Latest Articles</h2>
          <Link
            to="/blog"
            className="inline-flex items-center gap-1 text-sm text-accent hover:text-primary transition-colors"
          >
            View all <ArrowRight className="h-3 w-3" />
          </Link>
        </div>
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="rounded-lg border border-border bg-card p-6 animate-pulse">
                <div className="h-4 bg-secondary rounded w-20 mb-3" />
                <div className="h-6 bg-secondary rounded w-3/4 mb-2" />
                <div className="h-4 bg-secondary rounded w-full mb-1" />
                <div className="h-4 bg-secondary rounded w-2/3" />
              </div>
            ))}
          </div>
        ) : latestPosts.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {latestPosts.map((post) => (
              <PostCard key={post.id} post={post} />
            ))}
          </div>
        ) : (
          <div className="text-center py-16 rounded-lg border border-border bg-card">
            <BookOpen className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground">No articles yet. Connect your backend to get started.</p>
          </div>
        )}
      </section>
    </div>
  );
}
