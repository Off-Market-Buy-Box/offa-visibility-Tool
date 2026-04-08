import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ThemeProvider } from "@/components/ThemeProvider";
import Keywords from "./pages/Keywords.tsx";
import Reddit from "./pages/Reddit.tsx";
import LinkedIn from "./pages/LinkedIn.tsx";
import Twitter from "./pages/Twitter.tsx";
import Facebook from "./pages/Facebook.tsx";
import Automation from "./pages/Automation.tsx";
import Outreach from "./pages/Outreach.tsx";
import Profile from "./pages/Profile.tsx";
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
            <Route path="/" element={<Keywords />} />
            <Route path="/keywords" element={<Keywords />} />
            <Route path="/reddit" element={<Reddit />} />
            <Route path="/linkedin" element={<LinkedIn />} />
            <Route path="/twitter" element={<Twitter />} />
            <Route path="/facebook" element={<Facebook />} />
            <Route path="/automation" element={<Automation />} />
            <Route path="/outreach" element={<Outreach />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  </ThemeProvider>
);

export default App;
