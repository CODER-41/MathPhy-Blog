import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import ProtectedRoute from "@/components/ProtectedRoute";
import Home from "./pages/Home";
import BlogList from "./pages/BlogList";
import PostDetail from "./pages/PostDetail";
import Login from "./pages/Login";
import Dashboard from "./pages/admin/Dashboard";
import NewPost from "./pages/admin/NewPost";
import EditPost from "./pages/admin/EditPost";
import ManageComments from "./pages/admin/ManageComments";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <BrowserRouter>
        <div className="flex flex-col min-h-screen">
          <Navbar />
          <main className="flex-1">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/blog" element={<BlogList />} />
              <Route path="/blog/:slug" element={<PostDetail />} />
              <Route path="/login" element={<Login />} />
              <Route path="/admin" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
              <Route path="/admin/posts/new" element={<ProtectedRoute><NewPost /></ProtectedRoute>} />
              <Route path="/admin/posts/:id/edit" element={<ProtectedRoute><EditPost /></ProtectedRoute>} />
              <Route path="/admin/comments" element={<ProtectedRoute><ManageComments /></ProtectedRoute>} />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </main>
          <Footer />
        </div>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
