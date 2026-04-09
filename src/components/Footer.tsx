import { Atom } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="border-t border-border bg-card mt-auto">
      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Atom className="h-4 w-4 text-primary" />
            <span className="font-heading text-sm text-primary">Physics Blog</span>
          </div>
          <p className="text-xs text-muted-foreground">
            Exploring the fundamental laws of the universe through mathematics and reason.
          </p>
          <p className="text-xs text-muted-foreground">
            &copy; {new Date().getFullYear()} All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
