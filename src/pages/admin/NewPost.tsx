import { useState, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { postService } from '@/services/postService';
import { useCategories } from '@/hooks/useCategories';
import { useToast } from '@/hooks/use-toast';
import MathRenderer from '@/components/MathRenderer';
import { ArrowLeft, Save, Send } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function NewPost() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { data: categories } = useCategories();

  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('');
  const [excerpt, setExcerpt] = useState('');
  const [content, setContent] = useState('');
  const [showPreview, setShowPreview] = useState(false);

  const mutation = useMutation({
    mutationFn: (published: boolean) =>
      postService.create({ title, category, excerpt, content, published }),
    onSuccess: () => {
      toast({ title: 'Post created!' });
      navigate('/admin');
    },
    onError: (err: Error) => {
      toast({ title: 'Error', description: err.message, variant: 'destructive' });
    },
  });

  return (
    <div className="container mx-auto px-4 py-12">
      <Link
        to="/admin"
        className="inline-flex items-center gap-1 text-sm text-accent hover:text-primary transition-colors mb-6"
      >
        <ArrowLeft className="h-3 w-3" /> Back to Dashboard
      </Link>

      <h1 className="font-heading text-3xl font-bold text-chalk-bright mb-8">New Post</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Editor */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-chalk mb-1.5">Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full rounded-lg border border-border bg-card px-4 py-2.5 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
              placeholder="The Beauty of Maxwell's Equations"
            />
          </div>

          <div>
            <label className="block text-sm text-chalk mb-1.5">Category</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full rounded-lg border border-border bg-card px-4 py-2.5 text-sm text-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            >
              <option value="">Select category…</option>
              {categories?.map((cat) => (
                <option key={cat.id} value={cat.name}>{cat.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm text-chalk mb-1.5">Excerpt</label>
            <textarea
              value={excerpt}
              onChange={(e) => setExcerpt(e.target.value)}
              rows={2}
              className="w-full rounded-lg border border-border bg-card px-4 py-2.5 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary resize-none"
              placeholder="A brief summary of the post…"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-sm text-chalk">Content (Markdown + LaTeX)</label>
              <button
                onClick={() => setShowPreview(!showPreview)}
                className="text-xs text-accent hover:text-primary transition-colors lg:hidden"
              >
                {showPreview ? 'Edit' : 'Preview'}
              </button>
            </div>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={20}
              className="w-full rounded-lg border border-border bg-card px-4 py-3 text-sm text-foreground font-mono placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary resize-y"
              placeholder={`# Introduction\n\nWrite your physics article here.\n\nUse $E = mc^2$ for inline math.\n\nUse $$F = ma$$ for block equations.`}
            />
          </div>

          <div className="flex gap-3">
            <button
              onClick={() => mutation.mutate(false)}
              disabled={mutation.isPending}
              className="inline-flex items-center gap-2 rounded-lg border border-border px-5 py-2 text-sm text-chalk hover:border-primary hover:text-primary transition-colors disabled:opacity-50"
            >
              <Save className="h-4 w-4" /> Save Draft
            </button>
            <button
              onClick={() => mutation.mutate(true)}
              disabled={mutation.isPending}
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
            >
              <Send className="h-4 w-4" /> Publish
            </button>
          </div>
        </div>

        {/* Preview */}
        <div className={`${showPreview ? 'block' : 'hidden'} lg:block`}>
          <div className="sticky top-24">
            <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider mb-4">Live Preview</h3>
            <div className="rounded-lg border border-border bg-card p-6 min-h-[400px] overflow-y-auto max-h-[calc(100vh-200px)]">
              {content ? (
                <MathRenderer content={content} />
              ) : (
                <p className="text-sm text-muted-foreground italic">Start writing to see a preview…</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
