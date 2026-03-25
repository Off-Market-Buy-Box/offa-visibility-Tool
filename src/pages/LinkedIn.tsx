import DashboardLayout from "@/components/DashboardLayout";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Briefcase, TrendingUp, Eye, ArrowUpRight, Loader2, X, ChevronLeft, ChevronRight, Sparkles, Copy, Check, Brain, Bot, Send } from "lucide-react";
import { useState, useEffect } from "react";
import { linkedinService, type LinkedInPost } from "@/services/linkedinService";
import { aiService, type AIMetadata } from "@/services/aiService";
import { useToast } from "@/hooks/use-toast";

const POSTS_PER_PAGE = 10;
const MAX_CONTENT_LENGTH = 10000;

const INTENT_COLORS: Record<string, string> = {
  question: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  discussion: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  insight: "bg-green-500/20 text-green-400 border-green-500/30",
  problem: "bg-red-500/20 text-red-400 border-red-500/30",
  opportunity: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
};

const SENTIMENT_COLORS: Record<string, string> = {
  positive: "text-green-400",
  negative: "text-red-400",
  neutral: "text-gray-400",
  mixed: "text-yellow-400",
};

const LinkedIn = () => {
  const [posts, setPosts] = useState<LinkedInPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [monitoring, setMonitoring] = useState(false);
  const [selectedPost, setSelectedPost] = useState<LinkedInPost | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [customKeywords, setCustomKeywords] = useState("");
  const { toast } = useToast();

  // AI state
  const [aiMeta, setAiMeta] = useState<AIMetadata | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [generatingResponse, setGeneratingResponse] = useState(false);
  const [responseText, setResponseText] = useState("");
  const [copied, setCopied] = useState(false);
  const [fetchingContent, setFetchingContent] = useState(false);
  const [showFullContent, setShowFullContent] = useState(false);
  const [postingToLinkedIn, setPostingToLinkedIn] = useState(false);

  // Agent state
  const [agentDialogOpen, setAgentDialogOpen] = useState(false);
  const [agentRunning, setAgentRunning] = useState(false);
  const [agentMaxPosts, setAgentMaxPosts] = useState(1);
  const [agentDelay, setAgentDelay] = useState(30);
  const [agentResults, setAgentResults] = useState<any>(null);
  const [pendingCount, setPendingCount] = useState(0);
  const [agentLogs, setAgentLogs] = useState<Array<{ emoji: string; message: string; time: string }>>([]);
  const [agentCleanup, setAgentCleanup] = useState<(() => void) | null>(null);
  const [agentPosts, setAgentPosts] = useState<Array<any>>([]);
  const [expandedPost, setExpandedPost] = useState<number | null>(null);
  const [browserLoggingIn, setBrowserLoggingIn] = useState(false);

  useEffect(() => { fetchPosts(); }, []);

  const fetchPosts = async () => {
    try {
      setLoading(true);
      const data = await linkedinService.getPosts();
      setPosts(data);
    } catch {
      setPosts([]);
    } finally {
      setLoading(false);
    }
  };

  const handleMonitor = async () => {
    try {
      setMonitoring(true);
      const result = await linkedinService.monitor();
      toast({
        title: "LinkedIn Scan Complete",
        description: `Searched ${result.queries_searched} queries. Found ${result.total_found} posts. Saved ${result.new_saved} new.`,
      });
      fetchPosts();
    } catch {
      toast({ title: "Error", description: "Failed to scan LinkedIn", variant: "destructive" });
    } finally {
      setMonitoring(false);
    }
  };

  const handleCustomMonitor = async () => {
    try {
      setMonitoring(true);
      const keywords = customKeywords.split(",").map(k => k.trim()).filter(Boolean);
      const result = await linkedinService.monitor(keywords);
      toast({
        title: "Custom Scan Complete",
        description: `Found ${result.total_found} posts. Saved ${result.new_saved} new.`,
      });
      setDialogOpen(false);
      setCustomKeywords("");
      fetchPosts();
    } catch {
      toast({ title: "Error", description: "Failed to scan", variant: "destructive" });
    } finally {
      setMonitoring(false);
    }
  };

  const handleSelectPost = async (post: LinkedInPost) => {
    setSelectedPost(post);
    setResponseText("");
    setAiMeta(null);
    setShowFullContent(false);

    // Auto-fetch content if not already available
    if (!post.content) {
      setFetchingContent(true);
      try {
        const result = await linkedinService.fetchContent(post.id);
        if (result.success && result.content) {
          post = { ...post, content: result.content };
          setSelectedPost(post);
        }
      } catch { /* silently fail, snippet is still shown */ }
      setFetchingContent(false);
    }

    // Load existing AI metadata
    const meta = await aiService.getLinkedInMetadata(post.id);
    if (meta) setAiMeta(meta);

    // Load existing generated responses
    try {
      const responses = await aiService.getLinkedInResponses(post.id);
      if (Array.isArray(responses) && responses.length > 0) {
        setResponseText(responses[0].content);
      }
    } catch { /* no responses yet */ }
  };

  const handleAnalyze = async () => {
    if (!selectedPost) return;
    setAnalyzing(true);
    try {
      const meta = await aiService.analyzeLinkedIn(selectedPost.id);
      setAiMeta(meta);
      toast({ title: "Analysis Complete", description: `Intent: ${meta.intent}, Sentiment: ${meta.sentiment}` });
    } catch (e: any) {
      toast({ title: "Analysis Failed", description: e.message || "Check your OpenAI API key", variant: "destructive" });
    } finally {
      setAnalyzing(false);
    }
  };

  const handleGenerateResponse = async () => {
    if (!selectedPost) return;
    setGeneratingResponse(true);
    try {
      const resp = await aiService.generateLinkedInResponse(selectedPost.id);
      setResponseText(resp.content);
      toast({ title: "Response Generated" });
    } catch (e: any) {
      toast({ title: "Generation Failed", description: e.message || "Check your OpenAI API key", variant: "destructive" });
    } finally {
      setGeneratingResponse(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(responseText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handlePostToLinkedIn = async () => {
    if (!selectedPost || !responseText.trim()) return;
    setPostingToLinkedIn(true);
    try {
      const result = await linkedinService.postComment(selectedPost.id, responseText);
      toast({ title: "Posted to LinkedIn", description: "Comment posted via browser" });
    } catch (e: any) {
      toast({ title: "Failed to Post", description: e.message || "Check your LinkedIn credentials in .env", variant: "destructive" });
    } finally {
      setPostingToLinkedIn(false);
    }
  };

  const handleRunAgent = async () => {
    setAgentRunning(true);
    setAgentResults(null);
    setAgentLogs([]);
    setAgentPosts([]);
    setExpandedPost(null);

    const now = () => new Date().toLocaleTimeString();

    const cleanup = linkedinService.runAgentStream(
      agentMaxPosts,
      agentDelay,
      false,
      (event: any) => {
        if (event.type === "log" && event.emoji && event.message) {
          setAgentLogs((prev) => [...prev, { emoji: event.emoji, message: event.message, time: now() }]);
        } else if (event.type === "post_start") {
          setAgentPosts((prev) => [...prev, { ...event.post, step: "generating", response_content: null }]);
        } else if (event.type === "post_response") {
          setAgentPosts((prev) =>
            prev.map((p) =>
              p.id === event.post_id
                ? { ...p, response_content: event.response_content, char_count: event.char_count, step: "posting" }
                : p
            )
          );
        } else if (event.type === "post_result") {
          setAgentPosts((prev) =>
            prev.map((p) =>
              p.id === event.post?.id
                ? { ...p, ...event.post, step: "done" }
                : p
            )
          );
        } else if (event.type === "result") {
          setAgentResults(event.stats);
          toast({
            title: "Agent Run Complete",
            description: `${event.stats?.threads_found || 0} posts, ${event.stats?.comments_posted || 0} posted`,
          });
          fetchPosts();
        } else if (event.type === "error") {
          setAgentLogs((prev) => [...prev, { emoji: "❌", message: event.message || "Unknown error", time: now() }]);
          toast({ title: "Agent Error", description: event.message, variant: "destructive" });
        }
      },
      () => {
        setAgentRunning(false);
        setAgentCleanup(null);
      },
      (err) => {
        toast({ title: "Agent Failed", description: err, variant: "destructive" });
      },
    );

    setAgentCleanup(() => cleanup);
  };

  const fetchPendingCount = async () => {
    try {
      const data = await linkedinService.getPendingCount();
      setPendingCount(data.pending_count);
    } catch { /* ignore */ }
  };

  useEffect(() => { fetchPendingCount(); }, [posts]);

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "";
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  };

  const getDisplayContent = (text: string) => {
    if (showFullContent || text.length <= MAX_CONTENT_LENGTH) return text;
    return text.substring(0, MAX_CONTENT_LENGTH) + "...";
  };

  const totalPages = Math.ceil(posts.length / POSTS_PER_PAGE);
  const paginatedPosts = posts.slice((currentPage - 1) * POSTS_PER_PAGE, currentPage * POSTS_PER_PAGE);

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div>
          <h1 className="text-xl font-bold text-foreground">LinkedIn Monitoring</h1>
          <p className="text-xs text-muted-foreground">Find real estate discussions on LinkedIn via Google · AI-powered analysis</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={handleMonitor} disabled={monitoring} className="bg-primary text-primary-foreground hover:bg-primary/90">
            {monitoring ? (<><Loader2 className="h-4 w-4 mr-2 animate-spin" />Scanning...</>) : (<><TrendingUp className="h-4 w-4 mr-2" />Scan LinkedIn</>)}
          </Button>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="outline"><Eye className="h-4 w-4 mr-2" />Custom</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader><DialogTitle>Custom LinkedIn Search</DialogTitle></DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label>Keywords (comma separated)</Label>
                  <Input value={customKeywords} onChange={(e) => setCustomKeywords(e.target.value)} placeholder="e.g., off market deals, real estate investing" />
                </div>
                <Button onClick={handleCustomMonitor} disabled={monitoring} className="w-full">
                  {monitoring ? "Scanning..." : "Search LinkedIn"}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
          <Dialog open={agentDialogOpen} onOpenChange={(open) => {
            setAgentDialogOpen(open);
            if (!open && agentCleanup) { agentCleanup(); setAgentCleanup(null); setAgentRunning(false); }
          }}>
            <DialogTrigger asChild>
              <Button variant="outline" className="gap-2">
                <Bot className="h-4 w-4" />Agent
                {pendingCount > 0 && <span className="bg-primary text-primary-foreground text-[10px] px-1.5 py-0.5 rounded-full">{pendingCount}</span>}
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
              <DialogHeader><DialogTitle className="flex items-center gap-2"><Bot className="h-5 w-5" />LinkedIn Posting Agent</DialogTitle></DialogHeader>
              <div className="space-y-4 overflow-y-auto flex-1 pr-1">
                <p className="text-sm text-muted-foreground">The agent will automatically generate AI responses and post them as comments on LinkedIn posts that haven't been processed yet.</p>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label>Max Posts</Label>
                    <Input type="number" min={1} max={20} value={agentMaxPosts} onChange={(e) => setAgentMaxPosts(Number(e.target.value))} />
                  </div>
                  <div>
                    <Label>Delay (seconds)</Label>
                    <Input type="number" min={5} max={600} value={agentDelay} onChange={(e) => setAgentDelay(Number(e.target.value))} placeholder="30" />
                  </div>
                </div>
                <Button onClick={handleRunAgent} disabled={agentRunning} className="w-full">
                  {agentRunning ? (<><Loader2 className="h-4 w-4 mr-2 animate-spin" />Agent Running...</>) : (<><Bot className="h-4 w-4 mr-2" />Run Agent</>)}
                </Button>

                <Button
                  variant="outline"
                  className="w-full text-xs"
                  disabled={browserLoggingIn}
                  onClick={async () => {
                    setBrowserLoggingIn(true);
                    try {
                      await linkedinService.browserLogin();
                      toast({ title: "Logged in!", description: "LinkedIn session saved. You can now post." });
                    } catch (e: any) {
                      toast({ title: "Login Issue", description: e.message || "Complete verification in the browser window", variant: "destructive" });
                    } finally {
                      setBrowserLoggingIn(false);
                    }
                  }}
                >
                  {browserLoggingIn ? (<><Loader2 className="h-3 w-3 mr-1 animate-spin" />Browser opening — complete verification...</>) : "🔐 Login to LinkedIn (first time setup)"}
                </Button>

                {agentLogs.length > 0 && (
                  <div className="bg-black/40 rounded-lg p-3 space-y-0.5 text-[11px] max-h-[160px] overflow-y-auto font-mono border border-border" ref={(el) => { if (el) el.scrollTop = el.scrollHeight; }}>
                    <div className="text-muted-foreground mb-1.5 text-[10px] uppercase tracking-wider flex items-center gap-2">
                      Activity Log
                      {agentRunning && <Loader2 className="h-2.5 w-2.5 animate-spin" />}
                    </div>
                    {agentLogs.map((log, i) => (
                      <div key={i} className="flex items-start gap-1.5 leading-tight">
                        <span className="text-muted-foreground/60 shrink-0">{log.time}</span>
                        <span className="shrink-0">{log.emoji}</span>
                        <span className="text-foreground/80">{log.message}</span>
                      </div>
                    ))}
                  </div>
                )}

                {agentPosts.length > 0 && (
                  <div className="space-y-3">
                    <div className="text-xs text-muted-foreground uppercase tracking-wider flex items-center justify-between">
                      <span>Processed Posts ({agentPosts.length})</span>
                      {agentResults && (
                        <span className="normal-case tracking-normal">
                          {agentResults.responses_generated} generated · {agentResults.comments_posted} posted · {agentResults.errors?.length || 0} errors
                        </span>
                      )}
                    </div>
                    {agentPosts.map((post, i) => {
                      const isExpanded = expandedPost === i;
                      const statusColor = post.status === "posted"
                        ? "border-green-500/40 bg-green-500/5"
                        : post.status === "error"
                          ? "border-red-500/40 bg-red-500/5"
                          : "border-yellow-500/40 bg-yellow-500/5";
                      const statusBadge = post.status === "posted"
                        ? "bg-green-500/20 text-green-400"
                        : post.status === "error"
                          ? "bg-red-500/20 text-red-400"
                          : "bg-yellow-500/20 text-yellow-400";
                      const stepLabel = post.step === "generating"
                        ? "Generating..."
                        : post.step === "posting"
                          ? "Posting..."
                          : post.status;

                      return (
                        <div key={i} className={`rounded-lg border p-3 ${statusColor} transition-all`}>
                          <div className="flex items-start justify-between gap-2 cursor-pointer" onClick={() => setExpandedPost(isExpanded ? null : i)}>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="text-[10px] text-muted-foreground">{post.author || "LinkedIn"}</span>
                              </div>
                              <p className="text-sm font-medium text-foreground leading-tight">{post.title}</p>
                            </div>
                            <div className="flex items-center gap-2 shrink-0">
                              {post.step !== "done" && <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />}
                              <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${statusBadge}`}>{stepLabel}</span>
                              <ChevronRight className={`h-3.5 w-3.5 text-muted-foreground transition-transform ${isExpanded ? "rotate-90" : ""}`} />
                            </div>
                          </div>

                          {isExpanded && (
                            <div className="mt-3 space-y-3 border-t border-border/50 pt-3">
                              {post.content_preview && (
                                <div>
                                  <div className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">Original Post</div>
                                  <p className="text-xs text-foreground/70 leading-relaxed bg-background/50 rounded p-2">{post.content_preview}...</p>
                                </div>
                              )}
                              {post.response_content && (
                                <div>
                                  <div className="flex items-center justify-between mb-1">
                                    <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Generated Response ({post.response_content.length} chars)</span>
                                    <Button variant="ghost" size="sm" className="h-5 px-1.5 text-[10px]" onClick={(e) => { e.stopPropagation(); navigator.clipboard.writeText(post.response_content); toast({ title: "Copied!" }); }}>
                                      <Copy className="h-2.5 w-2.5 mr-1" />Copy
                                    </Button>
                                  </div>
                                  <div className="text-xs text-foreground leading-relaxed bg-background/50 rounded p-2 max-h-[200px] overflow-y-auto whitespace-pre-wrap">
                                    {post.response_content}
                                  </div>
                                </div>
                              )}
                              {post.comment_url && (
                                <div className="flex items-center gap-2">
                                  <Check className="h-3 w-3 text-green-400" />
                                  <a href={post.comment_url} target="_blank" rel="noopener noreferrer" className="text-xs text-primary hover:underline truncate">{post.comment_url}</a>
                                </div>
                              )}
                              {post.error && (
                                <div className="flex items-start gap-2 bg-red-500/10 rounded p-2">
                                  <X className="h-3 w-3 text-red-400 shrink-0 mt-0.5" />
                                  <p className="text-xs text-red-400">{post.error}</p>
                                </div>
                              )}
                              {post.url && (
                                <a href={post.url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground">
                                  <ArrowUpRight className="h-3 w-3" />View on LinkedIn
                                </a>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Stats */}
      <div className="flex items-center gap-4 text-xs text-muted-foreground mb-2">
        <span>All ({posts.length})</span>
      </div>

      {/* Main Content */}
      {posts.length === 0 ? (
        <div className="bg-card rounded-xl border border-border p-12 text-center">
          <Briefcase className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <p className="text-muted-foreground mb-4">No LinkedIn posts found yet.</p>
          <p className="text-sm text-muted-foreground">Click "Scan LinkedIn" to search Google for LinkedIn posts about real estate.</p>
        </div>
      ) : (
        <div className="flex border border-border rounded-xl overflow-hidden bg-card w-full" style={{ height: "calc(100vh - 180px)" }}>

          {/* Left Panel - Post List */}
          <div className={`${selectedPost ? "hidden md:flex" : "flex"} flex-col w-full md:w-[320px] md:min-w-[320px] md:max-w-[320px] border-r border-border`}>
            <div className="flex-1 overflow-y-auto">
              {paginatedPosts.map((post) => (
                <div
                  key={post.id}
                  onClick={() => handleSelectPost(post)}
                  className={`p-3 cursor-pointer border-b border-border transition-colors hover:bg-muted/50 ${selectedPost?.id === post.id ? "bg-primary/10 border-l-2 border-l-primary" : ""
                    }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-muted-foreground">{post.author || "LinkedIn"}</span>
                    <span className="text-xs text-muted-foreground">{formatDate(post.created_at)}</span>
                  </div>
                  <p className="text-sm font-semibold text-foreground line-clamp-2 mb-1">{post.title}</p>
                  <p className="text-xs text-muted-foreground line-clamp-2 mb-2">{post.snippet?.substring(0, 120)}...</p>
                  <div className="flex items-center gap-1.5 flex-wrap">
                    {post.keywords_matched?.split(", ").slice(0, 2).map((kw, i) => (
                      <Badge key={i} className="text-[10px] px-1.5 py-0 h-5 bg-blue-500/20 text-blue-400 border-blue-500/30">{kw}</Badge>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-3 p-2 border-t border-border shrink-0">
                <Button variant="ghost" size="sm" disabled={currentPage === 1} onClick={() => setCurrentPage(p => p - 1)}>
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <span className="text-xs text-muted-foreground">{currentPage}/{totalPages}</span>
                <Button variant="ghost" size="sm" disabled={currentPage === totalPages} onClick={() => setCurrentPage(p => p + 1)}>
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            )}
          </div>

          {/* Right Panel - Post Detail */}
          {selectedPost ? (
            <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
              {/* Detail Header */}
              <div className="flex flex-col gap-2 p-4 border-b border-border shrink-0">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0 pr-4">
                    <h2 className="text-base font-semibold text-foreground leading-tight">{selectedPost.title}</h2>
                    <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                      {selectedPost.author && <span>{selectedPost.author}</span>}
                      {selectedPost.author && <span>·</span>}
                      <span>LinkedIn</span>
                      <span>·</span>
                      <span>Saved {formatDate(selectedPost.created_at)}</span>
                    </div>
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => { setSelectedPost(null); setResponseText(""); setAiMeta(null); setShowFullContent(false); }}>
                    <X className="h-4 w-4" />
                  </Button>
                </div>
                <div className="flex items-center gap-2 flex-wrap">
                  <Button size="sm" variant={aiMeta ? "secondary" : "default"} onClick={handleAnalyze} disabled={analyzing}>
                    {analyzing ? <Loader2 className="h-3 w-3 mr-1 animate-spin" /> : <Brain className="h-3 w-3 mr-1" />}
                    {aiMeta ? "Re-analyze" : "AI Analyze"}
                  </Button>
                  <Button size="sm" variant="outline" onClick={handleGenerateResponse} disabled={generatingResponse}>
                    {generatingResponse ? <Loader2 className="h-3 w-3 mr-1 animate-spin" /> : <Sparkles className="h-3 w-3 mr-1" />}
                    Generate Response
                  </Button>
                  <Button variant="outline" size="sm" className="ml-auto" onClick={() => window.open(selectedPost.url, '_blank')}>
                    <ArrowUpRight className="h-3 w-3 mr-1" />Open on LinkedIn
                  </Button>
                </div>
              </div>

              {/* Scrollable Detail Body */}
              <div className="flex-1 overflow-y-auto p-5 space-y-5">
                {/* AI Analysis Results */}
                {aiMeta && (
                  <div className="bg-primary/5 border border-primary/20 rounded-lg p-4 space-y-3">
                    <div className="flex items-center gap-2">
                      <Brain className="h-4 w-4 text-primary" />
                      <span className="text-sm font-semibold text-foreground">AI Analysis</span>
                    </div>
                    <div className="grid grid-cols-2 gap-3 text-sm">
                      <div>
                        <span className="text-xs text-muted-foreground">Intent</span>
                        <div className="mt-0.5">
                          <span className={`inline-block px-2 py-0.5 rounded text-xs border ${INTENT_COLORS[aiMeta.intent || "discussion"] || INTENT_COLORS.discussion}`}>
                            {aiMeta.intent}
                          </span>
                        </div>
                      </div>
                      <div>
                        <span className="text-xs text-muted-foreground">Sentiment</span>
                        <p className={`text-sm font-medium ${SENTIMENT_COLORS[aiMeta.sentiment || "neutral"]}`}>{aiMeta.sentiment}</p>
                      </div>
                      <div className="col-span-2">
                        <span className="text-xs text-muted-foreground">Topic</span>
                        <p className="text-sm text-foreground">{aiMeta.main_topic}</p>
                      </div>
                      <div className="col-span-2">
                        <span className="text-xs text-muted-foreground">Summary</span>
                        <p className="text-sm text-foreground">{aiMeta.summary}</p>
                      </div>
                    </div>
                    {aiMeta.pain_points && aiMeta.pain_points.length > 0 && (
                      <div>
                        <span className="text-xs text-muted-foreground">Pain Points</span>
                        <div className="flex gap-1.5 flex-wrap mt-1">
                          {aiMeta.pain_points.map((p, i) => (
                            <Badge key={i} variant="outline" className="text-xs text-red-400 border-red-500/30">{p}</Badge>
                          ))}
                        </div>
                      </div>
                    )}
                    {aiMeta.opportunities && aiMeta.opportunities.length > 0 && (
                      <div>
                        <span className="text-xs text-muted-foreground">Opportunities</span>
                        <div className="flex gap-1.5 flex-wrap mt-1">
                          {aiMeta.opportunities.map((o, i) => (
                            <Badge key={i} variant="outline" className="text-xs text-green-400 border-green-500/30">{o}</Badge>
                          ))}
                        </div>
                      </div>
                    )}
                    {aiMeta.keywords && aiMeta.keywords.length > 0 && (
                      <div>
                        <span className="text-xs text-muted-foreground">Keywords</span>
                        <div className="flex gap-1.5 flex-wrap mt-1">
                          {aiMeta.keywords.map((k, i) => (
                            <Badge key={i} variant="secondary" className="text-xs">{k}</Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Matched Keywords */}
                {selectedPost.keywords_matched && (
                  <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-3">
                    <p className="text-xs font-medium text-blue-400 mb-1.5">🔍 Matched Keywords</p>
                    <div className="flex gap-1.5 flex-wrap">
                      {selectedPost.keywords_matched.split(", ").map((kw, i) => (
                        <Badge key={i} className="text-xs bg-blue-500/20 text-blue-400 border-blue-500/30">{kw}</Badge>
                      ))}
                    </div>
                  </div>
                )}

                {/* Post Content */}
                {fetchingContent ? (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Fetching full content...
                  </div>
                ) : selectedPost.content ? (
                  <div>
                    <p className="text-xs text-muted-foreground mb-2">Full Content</p>
                    <div className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">
                      {getDisplayContent(selectedPost.content)}
                    </div>
                    {selectedPost.content.length > MAX_CONTENT_LENGTH && (
                      <Button variant="link" size="sm" className="mt-1 p-0 h-auto text-xs" onClick={() => setShowFullContent(!showFullContent)}>
                        {showFullContent ? "Show less" : `Show full content (${selectedPost.content.length} chars)`}
                      </Button>
                    )}
                  </div>
                ) : (
                  <div>
                    <p className="text-xs text-muted-foreground mb-2">Google Snippet</p>
                    <div className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">
                      {selectedPost.snippet || "No preview available. Click 'Fetch Full Content' or 'Open on LinkedIn' to view the post."}
                    </div>
                  </div>
                )}

                {/* Source URL */}
                <div className="text-xs text-muted-foreground break-all">
                  {selectedPost.url}
                </div>
              </div>

              {/* Sticky Bottom - Response Editor */}
              <div className="shrink-0 border-t border-border bg-card p-3 space-y-2">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                    <Sparkles className="h-3 w-3 text-primary" />
                    Response
                  </h3>
                  <Button variant="ghost" size="sm" className="h-6 w-6 p-0" onClick={handleCopy}>
                    {copied ? <Check className="h-3 w-3 text-green-400" /> : <Copy className="h-3 w-3" />}
                  </Button>
                  <Button
                    size="sm"
                    variant="default"
                    className="h-7 text-xs gap-1"
                    disabled={postingToLinkedIn || !responseText.trim()}
                    onClick={handlePostToLinkedIn}
                  >
                    {postingToLinkedIn ? <Loader2 className="h-3 w-3 animate-spin" /> : <Send className="h-3 w-3" />}
                    Post to LinkedIn
                  </Button>
                </div>
                <textarea
                  className="w-full min-h-[200px] max-h-[40vh] bg-background border border-border rounded-lg p-3 text-sm text-foreground leading-relaxed resize-y focus:outline-none focus:ring-1 focus:ring-primary placeholder:text-muted-foreground"
                  placeholder="Write your response here or click 'Generate Response' to auto-generate..."
                  value={responseText}
                  onChange={(e) => setResponseText(e.target.value)}
                />
              </div>
            </div>

          ) : (
            <div className="hidden md:flex flex-1 items-center justify-center text-muted-foreground bg-card">
              <div className="text-center">
                <Briefcase className="h-10 w-10 mx-auto mb-3 opacity-30" />
                <p className="text-sm">Select a post to view details</p>
              </div>
            </div>
          )}
        </div>
      )}
    </DashboardLayout>
  );
};

export default LinkedIn;
