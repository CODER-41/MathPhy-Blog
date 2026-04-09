import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { commentService, type Comment } from '@/services/commentService';
import { formatDate } from '@/utils/formatDate';
import { MessageCircle, Send } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface Props {
  postId: string;
}

export default function CommentSection({ postId }: Props) {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [author, setAuthor] = useState('');
  const [email, setEmail] = useState('');
  const [content, setContent] = useState('');

  const { data: comments, isLoading } = useQuery({
    queryKey: ['comments', postId],
    queryFn: () => commentService.getByPost(postId),
  });

  const mutation = useMutation({
    mutationFn: (data: { author: string; email: string; content: string }) =>
      commentService.create(postId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comments', postId] });
      setAuthor('');
      setEmail('');
      setContent('');
      toast({ title: 'Comment submitted', description: 'Your comment is pending approval.' });
    },
    onError: () => {
      toast({ title: 'Error', description: 'Failed to submit comment.', variant: 'destructive' });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!author.trim() || !email.trim() || !content.trim()) return;
    mutation.mutate({ author, email, content });
  };

  return (
    <section className="mt-12 border-t border-border pt-8">
      <h3 className="font-heading text-xl font-semibold text-primary flex items-center gap-2 mb-6">
        <MessageCircle className="h-5 w-5" />
        Comments
      </h3>

      {/* List */}
      {isLoading ? (
        <p className="text-muted-foreground text-sm">Loading comments…</p>
      ) : comments && comments.length > 0 ? (
        <div className="space-y-4 mb-8">
          {comments.filter(c => c.approved).map((c: Comment) => (
            <div key={c.id} className="rounded-lg border border-border bg-secondary/50 p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-chalk-bright">{c.author}</span>
                <time className="text-xs text-muted-foreground">{formatDate(c.created_at)}</time>
              </div>
              <p className="text-sm text-chalk">{c.content}</p>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-muted-foreground mb-8">No comments yet. Be the first!</p>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <h4 className="text-sm font-medium text-chalk-bright">Leave a comment</h4>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <input
            type="text"
            placeholder="Name"
            value={author}
            onChange={(e) => setAuthor(e.target.value)}
            className="rounded-lg border border-border bg-card px-4 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
          />
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="rounded-lg border border-border bg-card px-4 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>
        <textarea
          placeholder="Your thoughts…"
          rows={4}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          className="w-full rounded-lg border border-border bg-card px-4 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary resize-none"
        />
        <button
          type="submit"
          disabled={mutation.isPending}
          className="inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
        >
          <Send className="h-4 w-4" />
          {mutation.isPending ? 'Submitting…' : 'Submit'}
        </button>
      </form>
    </section>
  );
}
