import DashboardLayout from "@/components/DashboardLayout";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Plus, Loader2 } from "lucide-react";
import { useState, useEffect } from "react";
import { competitorService, type Competitor } from "@/services/competitorService";
import { useToast } from "@/hooks/use-toast";

const Competitors = () => {
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [newCompetitor, setNewCompetitor] = useState({ domain: "", name: "" });
  const { toast } = useToast();

  useEffect(() => {
    fetchCompetitors();
  }, []);

  const fetchCompetitors = async () => {
    try {
      setLoading(true);
      const data = await competitorService.getAll();
      setCompetitors(data);
    } catch (error) {
      console.error("Fetch competitors error:", error);
      // Don't show error toast for empty data
      setCompetitors([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCompetitor = async () => {
    try {
      await competitorService.create(newCompetitor);
      toast({
        title: "Success",
        description: "Competitor added successfully",
      });
      setDialogOpen(false);
      setNewCompetitor({ domain: "", name: "" });
      fetchCompetitors();
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to add competitor",
        variant: "destructive",
      });
    }
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
          <h1 className="text-2xl font-bold text-foreground">Competitors</h1>
          <p className="text-sm text-muted-foreground">Analyze how your competitors rank in AI search results</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-primary text-primary-foreground hover:bg-primary/90">
              <Plus className="h-4 w-4 mr-2" /> Add Competitor
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add New Competitor</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label>Domain</Label>
                <Input
                  value={newCompetitor.domain}
                  onChange={(e) => setNewCompetitor({ ...newCompetitor, domain: e.target.value })}
                  placeholder="e.g., competitor.com"
                />
              </div>
              <div>
                <Label>Name (Optional)</Label>
                <Input
                  value={newCompetitor.name}
                  onChange={(e) => setNewCompetitor({ ...newCompetitor, name: e.target.value })}
                  placeholder="e.g., Competitor Inc"
                />
              </div>
              <Button onClick={handleCreateCompetitor} className="w-full">Add Competitor</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-card rounded-xl border border-border p-5">
          <p className="text-sm text-muted-foreground">Total Competitors</p>
          <p className="text-3xl font-bold text-foreground mt-1">{competitors.length}</p>
        </div>
        <div className="bg-card rounded-xl border border-border p-5">
          <p className="text-sm text-muted-foreground">Active Competitors</p>
          <p className="text-3xl font-bold text-foreground mt-1">
            {competitors.filter(c => c.is_active).length}
          </p>
        </div>
        <div className="bg-card rounded-xl border border-border p-5">
          <p className="text-sm text-muted-foreground">Avg. Visibility</p>
          <p className="text-3xl font-bold text-primary mt-1">
            {competitors.length > 0 ? Math.round(competitors.reduce((a, b) => a + b.visibility_score, 0) / competitors.length) : 0}%
          </p>
        </div>
      </div>

      <div className="bg-card rounded-xl border border-border p-6">
        <h2 className="text-lg font-semibold text-card-foreground mb-4">Competitor Overview</h2>
        {competitors.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-muted-foreground">No competitors added yet. Add your first competitor to start tracking!</p>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-3 px-2 text-sm font-medium text-muted-foreground">Competitor</th>
                <th className="text-left py-3 px-2 text-sm font-medium text-muted-foreground">Domain</th>
                <th className="text-left py-3 px-2 text-sm font-medium text-muted-foreground">Visibility</th>
                <th className="text-left py-3 px-2 text-sm font-medium text-muted-foreground">Keywords</th>
                <th className="text-left py-3 px-2 text-sm font-medium text-muted-foreground">Avg. Position</th>
                <th className="text-left py-3 px-2 text-sm font-medium text-muted-foreground">Status</th>
              </tr>
            </thead>
            <tbody>
              {competitors.map((c) => (
                <tr key={c.id} className="border-b border-border last:border-0 hover:bg-muted/50 transition-colors">
                  <td className="py-3 px-2 text-sm font-medium text-foreground">{c.name || c.domain}</td>
                  <td className="py-3 px-2 text-sm text-muted-foreground">{c.domain}</td>
                  <td className="py-3 px-2 text-sm text-foreground">{c.visibility_score.toFixed(1)}%</td>
                  <td className="py-3 px-2 text-sm text-muted-foreground">{c.total_keywords}</td>
                  <td className="py-3 px-2 text-sm text-foreground">#{c.avg_position.toFixed(1)}</td>
                  <td className="py-3 px-2">
                    <Badge variant={c.is_active ? "default" : "secondary"}>
                      {c.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </DashboardLayout>
  );
};

export default Competitors;
