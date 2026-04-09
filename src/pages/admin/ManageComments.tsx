import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { commentService, type Comment } from '@/services/commentService';
import { formatDate } from '@/utils/formatDate';
import { useToast } from '@/hooks/use-toast';
import { Link } from 'react-router-dom';
import { ArrowLeft, Check, Trash2, Loader2, MessageSquare } from 'lucide-react';

export default function ManageComments() {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const { data: comments, isLoading } = useQuery({
    queryKey: ['admin-comments'],
    queryFn: () => commentService.getAll(),
  });

  const approveMutation = useMutation({
    mutationFn: (id: string) => commentService.approve(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-comments'] });
      toast({ title: 'Comment approved' });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => commentService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-comments'] });
      toast({ title: 'Comment deleted' });
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

      <h1 className="font-heading text-3xl font-bold text-chalk-bright mb-8">Manage Comments</h1>

      {isLoading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="h-8 w-8 text-primary animate-spin" />
        </div>
      ) : comments && comments.length > 0 ? (
        <div className="space-y-4">
          {comments.map((comment: Comment) => (
            <div
              key={comment.id}
              className={`rounded-lg border p-4 transition-colors ${
                comment.approved ? 'border-border bg-card' : 'border-yellow-800/40 bg-yellow-900/10'
              }`}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-sm font-medium text-chalk-bright">{comment.author}</span>
                    <span className="text-xs text-muted-foreground">{comment.email}</span>
                    <span className={`inline-block rounded-full px-2 py-0.5 text-xs ${
                      comment.approved
                        ? 'bg-green-900/30 text-green-400'
                        : 'bg-yellow-900/30 text-yellow-400'
                    }`}>
                      {comment.approved ? 'Approved' : 'Pending'}
                    </span>
                  </div>
                  {comment.post_title && (
                    <p className="text-xs text-muted-foreground mb-1">
                      On: <span className="text-accent">{comment.post_title}</span>
                    </p>
                  )}
                  <p className="text-sm text-chalk">{comment.content}</p>
                  <time className="text-xs text-muted-foreground mt-2 block">{formatDate(comment.created_at)}</time>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {!comment.approved && (
                    <button
                      onClick={() => approveMutation.mutate(comment.id)}
                      className="p-1.5 rounded text-muted-foreground hover:text-green-400 transition-colors"
                      title="Approve"
                    >
                      <Check className="h-4 w-4" />
                    </button>
                  )}
                  <button
                    onClick={() => {
                      if (confirm('Delete this comment?')) deleteMutation.mutate(comment.id);
                    }}
                    className="p-1.5 rounded text-muted-foreground hover:text-destructive transition-colors"
                    title="Delete"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-16 rounded-lg border border-border bg-card">
          <MessageSquare className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <p className="text-muted-foreground">No comments yet.</p>
        </div>
      )}
    </div>
  );
}
