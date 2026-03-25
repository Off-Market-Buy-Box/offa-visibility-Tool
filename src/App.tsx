import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ThemeProvider } from "@/components/ThemeProvider";
import Index from "./pages/Index.tsx";
import Keywords from "./pages/Keywords.tsx";
import Competitors from "./pages/Competitors.tsx";
import Reddit from "./pages/Reddit.tsx";
import LinkedIn from "./pages/LinkedIn.tsx";
import Twitter from "./pages/Twitter.tsx";
import SmartTasks from "./pages/SmartTasks.tsx";
import Settings from "./pages/Settings.tsx";
import TestAPI from "./pages/TestAPI.tsx";
import NotFound from "./pages/NotFound.tsx";

const queryClient = new QueryClient();

const App = () => (
  <ThemeProvider defaultTheme="light" storageKey="app-theme">
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Index />} />
            <Route path="/keywords" element={<Keywords />} />
            <Route path="/competitors" element={<Competitors />} />
            <Route path="/reddit" element={<Reddit />} />
            <Route path="/linkedin" element={<LinkedIn />} />
            <Route path="/twitter" element={<Twitter />} />
            <Route path="/smart-tasks" element={<SmartTasks />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/test-api" element={<TestAPI />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  </ThemeProvider>
);

export default App;
