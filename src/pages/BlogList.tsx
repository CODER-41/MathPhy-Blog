import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { usePosts } from '@/hooks/usePosts';
import { useCategories } from '@/hooks/useCategories';
import PostCard from '@/components/PostCard';
import SearchBar from '@/components/SearchBar';
import CategoryBadge from '@/components/CategoryBadge';
import { BookOpen, ChevronLeft, ChevronRight } from 'lucide-react';

export default function BlogList() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [search, setSearch] = useState(searchParams.get('search') || '');
  const activeCategory = searchParams.get('category') || '';
  const page = parseInt(searchParams.get('page') || '1', 10);

  const { data, isLoading } = usePosts({ page, category: activeCategory, search });
  const { data: categories } = useCategories();

  const setCategory = (cat: string) => {
    const params = new URLSearchParams(searchParams);
    if (cat) params.set('category', cat);
    else params.delete('category');
    params.delete('page');
    setSearchParams(params);
  };

  const setPage = (p: number) => {
    const params = new URLSearchParams(searchParams);
    params.set('page', String(p));
    setSearchParams(params);
  };

  return (
    <div className="container mx-auto px-4 py-12">
      <h1 className="font-heading text-3xl font-bold text-chalk-bright mb-2">Articles</h1>
      <p className="text-chalk mb-8">Explorations in physics, mathematics, and the nature of reality.</p>

      {/* Search + Filters */}
      <div className="flex flex-col md:flex-row gap-4 mb-8">
        <div className="md:w-80">
          <SearchBar value={search} onChange={setSearch} />
        </div>
        <div className="flex flex-wrap gap-2 items-center">
          <CategoryBadge
            category="All"
            active={!activeCategory}
            onClick={() => setCategory('')}
          />
          {categories?.map((cat) => (
            <CategoryBadge
              key={cat.id}
              category={cat.name}
              active={activeCategory === cat.slug}
              onClick={() => setCategory(activeCategory === cat.slug ? '' : cat.slug)}
            />
          ))}
        </div>
      </div>

      {/* Posts grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="rounded-lg border border-border bg-card p-6 animate-pulse">
              <div className="h-4 bg-secondary rounded w-20 mb-3" />
              <div className="h-6 bg-secondary rounded w-3/4 mb-2" />
              <div className="h-4 bg-secondary rounded w-full mb-1" />
              <div className="h-4 bg-secondary rounded w-2/3" />
            </div>
          ))}
        </div>
      ) : data?.posts && data.posts.length > 0 ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {data.posts.map((post) => (
              <PostCard key={post.id} post={post} />
            ))}
          </div>

          {/* Pagination */}
          {data.pages > 1 && (
            <div className="flex items-center justify-center gap-4 mt-12">
              <button
                onClick={() => setPage(page - 1)}
                disabled={page <= 1}
                className="inline-flex items-center gap-1 rounded-lg border border-border px-3 py-2 text-sm text-chalk hover:border-primary hover:text-primary transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="h-4 w-4" /> Previous
              </button>
              <span className="text-sm text-muted-foreground">
                Page {page} of {data.pages}
              </span>
              <button
                onClick={() => setPage(page + 1)}
                disabled={page >= data.pages}
                className="inline-flex items-center gap-1 rounded-lg border border-border px-3 py-2 text-sm text-chalk hover:border-primary hover:text-primary transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
              >
                Next <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          )}
        </>
      ) : (
        <div className="text-center py-16 rounded-lg border border-border bg-card">
          <BookOpen className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <p className="text-muted-foreground">No articles found. Connect your backend to see posts.</p>
        </div>
      )}
    </div>
  );
}
