import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "./context/AuthContext";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { AppShell } from "./components/AppShell";
import { LoginPage, RegisterPage } from "./pages/AuthPages";
import { BooksPage } from "./pages/BooksPage";
import { BookDetailPage } from "./pages/BookDetailPage";
import { ProfilePage } from "./pages/ProfilePage";
import { TrendingPage } from "./pages/TrendingPage";
import { ArticlesPage, ArticlePage, AuthorPage } from "./pages/ArticlesPage";
import { JournalPage, WriterPage } from "./pages/JournalPage";
import { ChatPage } from "./pages/ChatPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30_000 },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* Public */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />

            <Route path="/articles" element={<AppShell><ArticlesPage /></AppShell>} />
            <Route path="/articles/:articleId" element={<AppShell><ArticlePage /></AppShell>} />
            <Route path="/authors/:authorId" element={<AppShell><AuthorPage /></AppShell>} />

            {/* Protected — wrapped in AppShell */}
            <Route element={<ProtectedRoute />}>
              <Route
                path="/*"
                element={
                  <AppShell>
                    <Routes>
                      <Route path="/journal" element={<JournalPage />} />
                      <Route path="/write" element={<WriterPage />} />
                      <Route path="/write/:draftId" element={<WriterPage />} />
                      <Route path="/books" element={<BooksPage />} />
                      <Route path="/books/:bookId" element={<BookDetailPage />} />
                      <Route path="/trending" element={<TrendingPage />} />
                      <Route path="/profile" element={<ProfilePage />} />
                      <Route path="/chat" element={<ChatPage />} />
                      <Route path="*" element={<Navigate to="/books" replace />} />
                    </Routes>
                  </AppShell>
                }
              />
            </Route>

            <Route path="/" element={<Navigate to="/books" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}
