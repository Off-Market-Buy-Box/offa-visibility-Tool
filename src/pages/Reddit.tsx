import DashboardLayout from "@/components/DashboardLayout";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { MessageSquare, TrendingUp, Eye, ArrowUpRight, Loader2, X, ChevronLeft, ChevronRight, Brain, Sparkles, FileText, Copy, Check } from "lucide-react";
import { useState, useEffect } from "react";
import { redditService, type RedditMention, type RedditComment } from "@/services/redditService";
import { aiService, type AIMetadata, type GeneratedResponse } from "@/services/aiService";
import { useToast } from "@/hooks/use-toast";

const POSTS_PER_PAGE = 10;

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

const Reddit = () => {
  const [mentions, setMentions] = useState<RedditMention[]>([]);
  const [loading, setLoading] = useState(true);
  const [monitoring, setMonitoring] = useState(false);
  const [selectedPost, setSelectedPost] = useState<RedditMention | null>(null);
  const [comments, setComments] = useState<RedditComment[]>([]);
  const [loadingComments, setLoadingComments] = useState(false);
  const [showComments, setShowComments] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [monitorData, setMonitorData] = useState({ subreddit: "", keywords: "" });
  const { toast } = useToast();

  // AI state
  const [aiMeta, setAiMeta] = useState<AIMetadata | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [generatingResponse, setGeneratingResponse] = useState(false);
  const [generatingBlog, setGeneratingBlog] = useState(false);
  const [generatedResponses, setGeneratedResponses] = useState<GeneratedResponse[]>([]);
  const [copiedId, setCopiedId] = useState<number | null>(null);
  const [responseText, setResponseText] = useState("");

  // Filters
  const [filterSubreddit, setFilterSubreddit] = useState<string>("all");

  useEffect(() => { fetchMentions(); }, []);

  const fetchMentions = async () => {
    try {
      setLoading(true);
      const data = await redditService.getMentions();
      setMentions(data);
    } catch {
      setMentions([]);
    } finally {
      setLoading(false);
    }
  };

  const handleMonitor = async () => {
    try {
      const keywords = monitorData.keywords.split(",").map(k => k.trim());
      const result = await redditService.monitor(monitorData.subreddit, keywords);
      toast({ title: "Success", description: `Found ${result.mentions_found} mentions, saved ${result.new_mentions_saved} new` });
      setDialogOpen(false);
      setMonitorData({ subreddit: "", keywords: "" });
      fetchMentions();
    } catch {
      toast({ title: "Error", description: "Failed to monitor subreddit", variant: "destructive" });
    }
  };

  const handleMonitorRealEstate = async () => {
    try {
      setMonitoring(true);
      const result = await redditService.monitorRealEstate();
      toast({
        title: "Monitoring Complete",
        description: `Checked ${result.subreddits_checked} subreddits. Found ${result.total_mentions_found} posts. Saved ${result.new_mentions_saved} new.`,
      });
      fetchMentions();
    } catch {
      toast({ title: "Error", description: "Failed to monitor", variant: "destructive" });
    } finally {
      setMonitoring(false);
    }
  };

  const handleSelectPost = async (post: RedditMention) => {
    setSelectedPost(post);
    setComments([]);
    setShowComments(false);
    setAiMeta(null);
    setGeneratedResponses([]);
    setResponseText("");

    // Try to load existing AI metadata
    const meta = await aiService.getMetadata(post.id);
    if (meta) setAiMeta(meta);

    // Load existing generated responses
    try {
      const responses = await aiService.getResponses(post.id);
      if (Array.isArray(responses) && responses.length > 0) {
        setGeneratedResponses(responses);
        setResponseText(responses[0].content);
      }
    } catch { /* no responses yet */ }
  };

  const handleLoadComments = async () => {
    if (!selectedPost) return;
    if (showComments) { setShowComments(false); return; }
    setLoadingComments(true);
    setShowComments(true);
    try {
      const data = await redditService.getComments(selectedPost.id);
      setComments(data.comments);
    } catch {
      setComments([]);
    } finally {
      setLoadingComments(false);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedPost) return;
    setAnalyzing(true);
    try {
      const meta = await aiService.analyze(selectedPost.id);
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
      const resp = await aiService.generateResponse(selectedPost.id);
      setGeneratedResponses([resp]);
      setResponseText(resp.content);
      toast({ title: "Response Generated" });
    } catch (e: any) {
      toast({ title: "Generation Failed", description: e.message || "Check your OpenAI API key", variant: "destructive" });
    } finally {
      setGeneratingResponse(false);
    }
  };

  const handleGenerateBlog = async () => {
    if (!selectedPost) return;
    setGeneratingBlog(true);
    try {
      const blog = await aiService.generateBlog([selectedPost.id]);
      setGeneratedResponses([blog]);
      toast({ title: "Blog Post Generated" });
    } catch (e: any) {
      toast({ title: "Generation Failed", description: e.message || "Check your OpenAI API key", variant: "destructive" });
    } finally {
      setGeneratingBlog(false);
    }
  };

  const handleCopy = (id: number, content: string) => {
    navigator.clipboard.writeText(content);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const timeAgo = (dateStr: string | null) => {
    if (!dateStr) return "";
    const diff = Date.now() - new Date(dateStr).getTime();
    const days = Math.floor(diff / 86400000);
    if (days > 0) return `${days}d ago`;
    const hours = Math.floor(diff / 3600000);
    if (hours > 0) return `${hours}h ago`;
    return "just now";
  };

  // Get unique subreddits for filter
  const subreddits = [...new Set(mentions.map(m => m.subreddit))].sort();

  // Apply filters
  const filteredMentions = mentions.filter(m => {
    if (filterSubreddit !== "all" && m.subreddit !== filterSubreddit) return false;
    return true;
  });

  const totalPages = Math.ceil(filteredMentions.length / POSTS_PER_PAGE);
  const paginatedMentions = filteredMentions.slice((currentPage - 1) * POSTS_PER_PAGE, currentPage * POSTS_PER_PAGE);

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
          <h1 className="text-xl font-bold text-foreground">Reddit Monitoring</h1>
          <p className="text-xs text-muted-foreground">Track real estate conversations · AI-powered analysis</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={handleMonitorRealEstate} disabled={monitoring} className="bg-primary text-primary-foreground hover:bg-primary/90">
            {monitoring ? (<><Loader2 className="h-4 w-4 mr-2 animate-spin" />Scanning...</>) : (<><TrendingUp className="h-4 w-4 mr-2" />Monitor Real Estate</>)}
          </Button>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="outline"><Eye className="h-4 w-4 mr-2" />Custom</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader><DialogTitle>Monitor Subreddit</DialogTitle></DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label>Subreddit</Label>
                  <Input value={monitorData.subreddit} onChange={(e) => setMonitorData({ ...monitorData, subreddit: e.target.value })} placeholder="e.g., realestateinvesting" />
                </div>
                <div>
                  <Label>Keywords (comma separated)</Label>
                  <Input value={monitorData.keywords} onChange={(e) => setMonitorData({ ...monitorData, keywords: e.target.value })} placeholder="e.g., off market, wholesale, offa.com" />
                </div>
                <Button onClick={handleMonitor} className="w-full">Start Monitoring</Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 text-xs text-muted-foreground mb-2">
        <span>All ({mentions.length})</span>
        <span>·</span>
        <Select value={filterSubreddit} onValueChange={(v) => { setFilterSubreddit(v); setCurrentPage(1); }}>
          <SelectTrigger className="h-7 w-[160px] text-xs">
            <SelectValue placeholder="All Subreddits" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Subreddits</SelectItem>
            {subreddits.map(s => (
              <SelectItem key={s} value={s}>r/{s}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Main Content */}
      {mentions.length === 0 ? (
        <div className="bg-card rounded-xl border border-border p-12 text-center">
          <MessageSquare className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <p className="text-muted-foreground mb-4">No mentions found yet.</p>
          <p className="text-sm text-muted-foreground">Click "Monitor Real Estate" to scan Reddit for relevant posts.</p>
        </div>
      ) : (
        <div className="flex border border-border rounded-xl overflow-hidden bg-card w-full" style={{ height: "calc(100vh - 180px)" }}>
          
          {/* Left Panel - Post List */}
          <div className={`${selectedPost ? "hidden md:flex" : "flex"} flex-col w-full md:w-[320px] md:min-w-[320px] md:max-w-[320px] border-r border-border`}>
            <div className="flex-1 overflow-y-auto">
              {paginatedMentions.map((post) => (
                <div
                  key={post.id}
                  onClick={() => handleSelectPost(post)}
                  className={`p-3 cursor-pointer border-b border-border transition-colors hover:bg-muted/50 ${
                    selectedPost?.id === post.id ? "bg-primary/10 border-l-2 border-l-primary" : ""
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-muted-foreground">r/{post.subreddit}</span>
                    <span className="text-xs text-muted-foreground">{timeAgo(post.posted_at)}</span>
                  </div>
                  <p className="text-sm font-semibold text-foreground line-clamp-2 mb-1">{post.title}</p>
                  <p className="text-xs text-muted-foreground line-clamp-2 mb-2">{post.content?.substring(0, 120)}...</p>
                  <div className="flex items-center gap-1.5 flex-wrap mb-1.5">
                    {post.keywords_matched?.split(", ").slice(0, 2).map((kw, i) => (
                      <Badge key={i} variant="destructive" className="text-[10px] px-1.5 py-0 h-5">{kw}</Badge>
                    ))}
                  </div>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span>↑ {post.score}</span>
                    <span>💬 {post.num_comments}</span>
                    <span className="ml-auto truncate max-w-[100px]">{post.author}</span>
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
                    <div className="flex items-center gap-2">
                      <h2 className="text-base font-semibold text-foreground leading-tight">{selectedPost.title}</h2>
                    </div>
                    <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                      <span>r/{selectedPost.subreddit}</span>
                      <span>·</span>
                      <span>{timeAgo(selectedPost.posted_at)}</span>
                      <span>·</span>
                      <span>u/{selectedPost.author}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <Button variant={showComments ? "default" : "outline"} size="sm" onClick={handleLoadComments} disabled={loadingComments}>
                      {loadingComments ? <Loader2 className="h-3 w-3 mr-1 animate-spin" /> : <MessageSquare className="h-3 w-3 mr-1" />}
                      Comments
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => { setSelectedPost(null); setShowComments(false); setComments([]); setAiMeta(null); setGeneratedResponses([]); setResponseText(""); }}>
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
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
                  {selectedPost.url && (
                    <Button variant="outline" size="sm" className="ml-auto" asChild>
                      <a href={selectedPost.url} target="_blank" rel="noopener noreferrer">
                        <ArrowUpRight className="h-3 w-3 mr-1" />Open on Reddit
                      </a>
                    </Button>
                  )}
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
                  <div className="bg-orange-500/10 border border-orange-500/20 rounded-lg p-3">
                    <p className="text-xs font-medium text-orange-400 mb-1.5">🔍 Matched Keywords</p>
                    <div className="flex gap-1.5 flex-wrap">
                      {selectedPost.keywords_matched.split(", ").map((kw, i) => (
                        <Badge key={i} variant="destructive" className="text-xs">{kw}</Badge>
                      ))}
                    </div>
                  </div>
                )}

                {/* Stats */}
                <div className="flex items-center gap-4 text-sm">
                  <span className="text-primary font-medium">↑ {selectedPost.score}</span>
                  <span className="text-foreground">{selectedPost.num_comments} comments</span>
                  <Badge variant={selectedPost.is_relevant ? "default" : "secondary"} className="text-xs">
                    {selectedPost.is_relevant ? "Relevant" : "Low Relevance"}
                  </Badge>
                </div>

                {/* Post Content */}
                <div className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">
                  {selectedPost.content || "No text content available."}
                </div>

                {/* Comments Section */}
                {showComments && (
                  <div className="border-t border-border pt-4">
                    <h3 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
                      <MessageSquare className="h-4 w-4" />
                      Comments ({comments.length})
                    </h3>
                    {loadingComments ? (
                      <div className="flex items-center justify-center py-6">
                        <Loader2 className="h-5 w-5 animate-spin text-primary" />
                      </div>
                    ) : comments.length === 0 ? (
                      <p className="text-sm text-muted-foreground py-4">No comments found.</p>
                    ) : (
                      <div className="space-y-3">
                        {comments.map((comment) => (
                          <div key={comment.id} className="border border-border rounded-lg p-3" style={{ marginLeft: `${Math.min(comment.depth || 0, 4) * 20}px` }}>
                            <div className="flex items-center gap-2 mb-1.5 text-xs text-muted-foreground">
                              {(comment.depth || 0) > 0 && <span className="text-primary">↳</span>}
                              <span className="font-medium text-foreground">u/{comment.author}</span>
                              <span>·</span>
                              <span>{comment.score} pts</span>
                              <span>·</span>
                              <span>{timeAgo(comment.created_at)}</span>
                            </div>
                            <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">{comment.body}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Sticky Bottom - Response Editor */}
              <div className="shrink-0 border-t border-border bg-card p-3 space-y-2">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                    <Sparkles className="h-3 w-3 text-primary" />
                    Response
                  </h3>
                  <Button variant="ghost" size="sm" className="h-6 w-6 p-0" onClick={() => { navigator.clipboard.writeText(responseText); setCopiedId(-1); setTimeout(() => setCopiedId(null), 2000); }}>
                    {copiedId === -1 ? <Check className="h-3 w-3 text-green-400" /> : <Copy className="h-3 w-3" />}
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
                <MessageSquare className="h-10 w-10 mx-auto mb-3 opacity-30" />
                <p className="text-sm">Select a post to view details</p>
              </div>
            </div>
          )}
        </div>
      )}
    </DashboardLayout>
  );
};

export default Reddit;
