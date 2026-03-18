import DashboardLayout from "@/components/DashboardLayout";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Search, Plus, TrendingUp, TrendingDown, Minus, Loader2, RefreshCw, ExternalLink, Trash2, Edit2, Check, X } from "lucide-react";
import { useState, useEffect } from "react";
import { keywordService, type Keyword } from "@/services/keywordService";
import { rankingService, type Ranking } from "@/services/rankingService";
import { useToast } from "@/hooks/use-toast";

const Keywords = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [keywords, setKeywords] = useState<Keyword[]>([]);
  const [loading, setLoading] = useState(true);
  const [checkingRanking, setCheckingRanking] = useState<number | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [resultsDialogOpen, setResultsDialogOpen] = useState(false);
  const [selectedKeyword, setSelectedKeyword] = useState<Keyword | null>(null);
  const [searchResults, setSearchResults] = useState<Ranking[]>([]);
  const [loadingResults, setLoadingResults] = useState(false);
  const [newKeyword, setNewKeyword] = useState({ keyword: "", domain: "" });
  const { toast } = useToast();

  useEffect(() => {
    fetchKeywords();
  }, []);

  const fetchKeywords = async () => {
    try {
      setLoading(true);
      const data = await keywordService.getAll();
      setKeywords(data);
    } catch (error) {
      console.error("Fetch keywords error:", error);
      // Don't show error toast for empty data
      setKeywords([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateKeyword = async () => {
    try {
      await keywordService.create(newKeyword);
      toast({
        title: "Success",
        description: "Keyword created successfully",
      });
      setDialogOpen(false);
      setNewKeyword({ keyword: "", domain: "" });
      fetchKeywords();
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to create keyword",
        variant: "destructive",
      });
    }
  };

  const handleCheckRanking = async (keywordId: number) => {
    try {
      setCheckingRanking(keywordId);
      const result = await rankingService.checkRanking(keywordId);
      toast({
        title: "Ranking Check Complete",
        description: `Found ${result.total_results} total results, ${result.domain_found_count} contain your domain`,
      });
      fetchKeywords();
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to check ranking",
        variant: "destructive",
      });
    } finally {
      setCheckingRanking(null);
    }
  };

  const handleViewResults = async (keyword: Keyword) => {
    setSelectedKeyword(keyword);
    setResultsDialogOpen(true);
    setLoadingResults(true);
    
    try {
      const results = await rankingService.getKeywordResults(keyword.id);
      setSearchResults(results);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load results",
        variant: "destructive",
      });
      setSearchResults([]);
    } finally {
      setLoadingResults(false);
    }
  };

  const handleDeleteKeyword = async (keywordId: number, keywordName: string) => {
    if (!confirm(`Are you sure you want to delete "${keywordName}"? This will also delete all ranking history.`)) {
      return;
    }

    try {
      await keywordService.delete(keywordId);
      toast({
        title: "Success",
        description: "Keyword deleted successfully",
      });
      fetchKeywords();
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to delete keyword",
        variant: "destructive",
      });
    }
  };

  const filtered = keywords.filter((kw) =>
    kw.keyword.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getTrendIcon = (change: number) => {
    if (change > 0) return <TrendingUp className="h-4 w-4 text-primary" />;
    if (change < 0) return <TrendingDown className="h-4 w-4 text-destructive" />;
    return <Minus className="h-4 w-4 text-muted-foreground" />;
  };

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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Keywords</h1>
          <p className="text-sm text-muted-foreground">Track your brand's visibility for target keywords in AI search results</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-primary text-primary-foreground hover:bg-primary/90">
              <Plus className="h-4 w-4 mr-2" /> Add Keyword
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add New Keyword</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label>Keyword</Label>
                <Input
                  value={newKeyword.keyword}
                  onChange={(e) => setNewKeyword({ ...newKeyword, keyword: e.target.value })}
                  placeholder="e.g., off market real estate deals"
                />
              </div>
              <div>
                <Label>Domain</Label>
                <Input
                  value={newKeyword.domain}
                  onChange={(e) => setNewKeyword({ ...newKeyword, domain: e.target.value })}
                  placeholder="e.g., offa.com"
                />
              </div>
              <Button onClick={handleCreateKeyword} className="w-full">Create Keyword</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-card rounded-xl border border-border p-5">
          <p className="text-sm text-muted-foreground">Total Keywords</p>
          <p className="text-3xl font-bold text-foreground mt-1">{keywords.length}</p>
        </div>
        <div className="bg-card rounded-xl border border-border p-5">
          <p className="text-sm text-muted-foreground">Active Keywords</p>
          <p className="text-3xl font-bold text-foreground mt-1">
            {keywords.filter(k => k.is_active).length}
          </p>
        </div>
      </div>

      <div className="bg-card rounded-xl border border-border p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search keywords..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9"
            />
          </div>
        </div>

        {filtered.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-muted-foreground">No keywords found. Add your first keyword to get started!</p>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-3 px-2 text-sm font-medium text-muted-foreground">Keyword</th>
                <th className="text-left py-3 px-2 text-sm font-medium text-muted-foreground">Domain</th>
                <th className="text-left py-3 px-2 text-sm font-medium text-muted-foreground">Status</th>
                <th className="text-left py-3 px-2 text-sm font-medium text-muted-foreground">Created</th>
                <th className="text-left py-3 px-2 text-sm font-medium text-muted-foreground">Actions</th>
                <th className="text-left py-3 px-2 text-sm font-medium text-muted-foreground">Best Rank</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((kw) => (
                <tr key={kw.id} className="border-b border-border last:border-0 hover:bg-muted/50 transition-colors">
                  <td className="py-3 px-2 text-sm font-medium text-foreground">{kw.keyword}</td>
                  <td className="py-3 px-2 text-sm text-muted-foreground">{kw.domain}</td>
                  <td className="py-3 px-2">
                    <Badge variant={kw.is_active ? "default" : "secondary"}>
                      {kw.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </td>
                  <td className="py-3 px-2 text-sm text-muted-foreground">
                    {new Date(kw.created_at).toLocaleDateString()}
                  </td>
                  <td className="py-3 px-2">
                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleCheckRanking(kw.id)}
                        disabled={checkingRanking === kw.id}
                      >
                        {checkingRanking === kw.id ? (
                          <>
                            <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                            Checking...
                          </>
                        ) : (
                          <>
                            <RefreshCw className="h-3 w-3 mr-1" />
                            Check Ranking
                          </>
                        )}
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleDeleteKeyword(kw.id, kw.keyword)}
                        className="text-destructive hover:text-destructive hover:bg-destructive/10"
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  </td>
                  <td className="py-3 px-2 text-sm text-foreground">
                    {kw.best_rank ? (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleViewResults(kw)}
                        className="p-0 h-auto"
                      >
                        <Badge 
                          variant="default"
                          className={
                            kw.best_rank <= 3 ? "bg-green-600 hover:bg-green-700" :
                            kw.best_rank <= 10 ? "bg-blue-600 hover:bg-blue-700" :
                            "bg-gray-600 hover:bg-gray-700"
                          }
                        >
                          #{kw.best_rank}
                        </Badge>
                      </Button>
                    ) : (
                      <span className="text-muted-foreground text-xs">Not ranked</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Search Results Dialog */}
      <Dialog open={resultsDialogOpen} onOpenChange={setResultsDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              Search Results for "{selectedKeyword?.keyword}"
            </DialogTitle>
            <p className="text-sm text-muted-foreground">
              Domain: {selectedKeyword?.domain}
            </p>
          </DialogHeader>
          
          {loadingResults ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : searchResults.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-muted-foreground">No results found. Click "Check Ranking" first.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {searchResults.map((result) => {
                const containsDomain = result.extra_data?.contains_domain as boolean;
                return (
                  <div
                    key={result.id}
                    className={`p-4 rounded-lg border ${
                      containsDomain
                        ? 'border-primary bg-primary/5'
                        : 'border-border bg-card'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <Badge variant="outline" className="mt-1">
                        #{result.position}
                      </Badge>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-medium text-foreground truncate">
                            {result.title}
                          </h3>
                          {containsDomain && (
                            <Badge variant="default" className="shrink-0">
                              Your Domain
                            </Badge>
                          )}
                        </div>
                        <a
                          href={result.url || '#'}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm text-primary hover:underline flex items-center gap-1 mb-2"
                        >
                          {result.url}
                          <ExternalLink className="h-3 w-3" />
                        </a>
                        <p className="text-sm text-muted-foreground line-clamp-2">
                          {result.snippet}
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </DashboardLayout>
  );
};

export default Keywords;
