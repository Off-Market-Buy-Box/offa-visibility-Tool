import DashboardLayout from "@/components/DashboardLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Loader2, Plus, Trash2, Play, Square, Eye, RefreshCw, Download } from "lucide-react";
import RedditIcon from "@/components/icons/RedditIcon";
import { useState, useEffect, useRef } from "react";
import { outreachService, type OutreachTarget, type OutreachPost, type OutreachStatus } from "@/services/outreachService";
import { useToast } from "@/hooks/use-toast";
const Outreach = () => {
    const [status, setStatus] = useState<OutreachStatus | null>(null);
    const [targets, setTargets] = useState<OutreachTarget[]>([]);
    const [posts, setPosts] = useState<OutreachPost[]>([]);
    const [loading, setLoading] = useState(true);
    const [toggling, setToggling] = useState(false);
    const [preview, setPreview] = useState<{ title: string; body: string } | null>(null);
    const [previewing, setPreviewing] = useState(false);
    const [newUrl, setNewUrl] = useState("");
    const [newName, setNewName] = useState("");
    const [adding, setAdding] = useState(false);
    const [addingDefaults, setAddingDefaults] = useState(false);
    const { toast } = useToast();
    const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const fetchAll = async () => { try { const [st, t, p] = await Promise.all([outreachService.getStatus(), outreachService.getTargets(), outreachService.getPosts()]); setStatus(st); setTargets(t); setPosts(p); } catch {} finally { setLoading(false); } };
    useEffect(() => { fetchAll(); pollRef.current = setInterval(fetchAll, 5000); return () => { if (pollRef.current) clearInterval(pollRef.current); }; }, []);
    const handleToggle = async () => { if (!status) return; setToggling(true); try { if (status.running) { await outreachService.stop(); toast({ title: "Outreach stopped" }); } else { await outreachService.start(); toast({ title: "Outreach started" }); } await fetchAll(); } catch (e: any) { toast({ title: "Error", description: e.message, variant: "destructive" }); } finally { setToggling(false); } };
    const handleAdd = async () => { if (!newUrl) return; const name = newName || "r/" + newUrl.replace(/\/$/, "").split("/r/").pop()?.split("/")[0]; setAdding(true); try { await outreachService.addTarget({ name, url: newUrl }); setNewUrl(""); setNewName(""); toast({ title: "Subreddit added" }); await fetchAll(); } catch (e: any) { toast({ title: "Error", description: e.message, variant: "destructive" }); } finally { setAdding(false); } };
    const handleAddDefaults = async () => { setAddingDefaults(true); try { const res = await outreachService.addDefaults(); toast({ title: `Added ${res.added} subreddits` }); await fetchAll(); } catch (e: any) { toast({ title: "Error", description: e.message, variant: "destructive" }); } finally { setAddingDefaults(false); } };
    const handleDelete = async (id: number) => { if (!confirm("Remove this subreddit?")) return; await outreachService.deleteTarget(id); await fetchAll(); };
    const handleTargetToggle = async (id: number, enabled: boolean) => { await outreachService.updateTarget(id, { enabled }); await fetchAll(); };
    const handleIntervalChange = async (hours: number) => { await outreachService.updateSettings({ interval_hours: hours }); await fetchAll(); };
    const handlePreview = async () => { setPreviewing(true); try { const res = await outreachService.generatePreview(); setPreview(res); } catch (e: any) { toast({ title: "Error", description: e.message, variant: "destructive" }); } finally { setPreviewing(false); } };
    const formatDate = (iso: string | null) => { if (!iso) return "Never"; return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }); };
    if (loading || !status) { return (<DashboardLayout><div className="flex items-center justify-center h-64"><Loader2 className="h-8 w-8 animate-spin text-primary" /></div></DashboardLayout>); }
    return (
        <DashboardLayout>
            <div className="flex items-center justify-between mb-4">
                <div><h1 className="text-xl font-bold text-foreground">Reddit Outreach</h1><p className="text-xs text-muted-foreground">{status.running ? (<span className="text-green-500">Running — {status.current_action || "active"}</span>) : "Stopped"}{status.last_run_at && <span> · Last: {formatDate(status.last_run_at)}</span>}</p></div>
                <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={handlePreview} disabled={previewing} className="gap-2">{previewing ? <Loader2 className="h-3 w-3 animate-spin" /> : <Eye className="h-3 w-3" />} Preview</Button>
                    <Button onClick={handleToggle} disabled={toggling} variant={status.running ? "destructive" : "default"} className="gap-2">{toggling ? <Loader2 className="h-4 w-4 animate-spin" /> : status.running ? <Square className="h-4 w-4" /> : <Play className="h-4 w-4" />}{status.running ? "Stop" : "Start"}</Button>
                </div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                <div className="bg-card rounded-xl border border-border p-3 text-center"><p className="text-lg font-bold text-foreground">{status.enabled_targets}</p><p className="text-[10px] text-muted-foreground">Subreddits</p></div>
                <div className="bg-card rounded-xl border border-border p-3 text-center"><p className="text-lg font-bold text-green-500">{status.total_posted}</p><p className="text-[10px] text-muted-foreground">Posted</p></div>
                <div className="bg-card rounded-xl border border-border p-3 text-center"><p className="text-lg font-bold text-red-400">{status.total_errors}</p><p className="text-[10px] text-muted-foreground">Errors</p></div>
                <div className="bg-card rounded-xl border border-border p-3 text-center"><p className="text-lg font-bold text-foreground">{status.interval_hours}h</p><p className="text-[10px] text-muted-foreground">Interval</p></div>
            </div>

            {preview && (<div className="bg-card rounded-xl border border-primary/30 p-4 mb-4"><div className="flex items-center justify-between mb-2"><p className="text-sm font-semibold text-foreground">AI Preview</p><Button variant="ghost" size="sm" onClick={() => setPreview(null)} className="text-xs h-6">Dismiss</Button></div><p className="text-sm font-medium text-foreground mb-2">{preview.title}</p><p className="text-sm text-muted-foreground whitespace-pre-wrap">{preview.body}</p></div>)}
            <div className="bg-card rounded-xl border border-border p-4 mb-4"><div className="flex items-center justify-between mb-3"><p className="text-sm font-semibold text-foreground">Settings</p><Button variant="outline" size="sm" onClick={handleAddDefaults} disabled={addingDefaults} className="gap-2 text-xs h-7">{addingDefaults ? <Loader2 className="h-3 w-3 animate-spin" /> : <Download className="h-3 w-3" />} Add Popular Subreddits</Button></div><div className="grid grid-cols-1 md:grid-cols-4 gap-3 items-end"><div><Label className="text-xs text-muted-foreground">Interval (hours)</Label><Input type="number" min={1} max={168} value={status.interval_hours} onChange={(e) => handleIntervalChange(Number(e.target.value))} className="mt-1 h-8" /></div><div><Label className="text-xs text-muted-foreground">Name (optional)</Label><Input value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="r/realestateinvesting" className="mt-1 h-8" /></div><div><Label className="text-xs text-muted-foreground">Subreddit URL</Label><Input value={newUrl} onChange={(e) => setNewUrl(e.target.value)} placeholder="https://www.reddit.com/r/..." className="mt-1 h-8" /></div><Button onClick={handleAdd} disabled={adding || !newUrl} size="sm" className="gap-2 h-8">{adding ? <Loader2 className="h-3 w-3 animate-spin" /> : <Plus className="h-3 w-3" />} Add</Button></div></div>
            <div className="bg-card rounded-xl border border-border p-4 mb-4"><p className="text-sm font-semibold text-foreground mb-3">Subreddits ({targets.length})</p>{targets.length === 0 ? (<p className="text-xs text-muted-foreground text-center py-4">No subreddits yet.</p>) : (<div className="space-y-1">{targets.map((t) => (<div key={t.id} className="flex items-center gap-3 py-2 px-3 rounded-lg hover:bg-muted/50"><RedditIcon className="h-4 w-4 shrink-0 text-orange-500" /><p className="text-sm font-medium text-foreground flex-1 min-w-0 truncate">{t.name}</p><span className="text-[10px] text-muted-foreground shrink-0">{t.total_posts} posts · Last: {formatDate(t.last_posted_at)}</span><Switch checked={t.enabled} onCheckedChange={(v) => handleTargetToggle(t.id, v)} /><Button variant="ghost" size="sm" onClick={() => handleDelete(t.id)} className="h-6 w-6 p-0 text-red-400 hover:text-red-500"><Trash2 className="h-3 w-3" /></Button></div>))}</div>)}</div>
            <div className="bg-card rounded-xl border border-border p-4"><div className="flex items-center justify-between mb-3"><p className="text-sm font-semibold text-foreground">Post History</p><Button variant="ghost" size="sm" onClick={fetchAll} className="h-6 w-6 p-0"><RefreshCw className="h-3 w-3" /></Button></div><div className="space-y-2 max-h-[400px] overflow-y-auto">{posts.length === 0 ? (<p className="text-xs text-muted-foreground text-center py-4">No posts yet.</p>) : posts.map((p) => { const target = targets.find(t => t.id === p.target_id); return (<div key={p.id} className="py-2 px-2 rounded hover:bg-muted/50 text-xs"><div className="flex items-center gap-2 mb-1"><RedditIcon className="h-3 w-3 text-orange-500" /><span className="font-medium text-foreground">{target?.name || `#${p.target_id}`}</span><span className={`px-1.5 py-0.5 rounded text-[10px] ${p.status === "posted" ? "bg-green-500/20 text-green-500" : p.status === "error" ? "bg-red-500/20 text-red-400" : "bg-yellow-500/20 text-yellow-500"}`}>{p.status}</span><span className="text-muted-foreground ml-auto">{formatDate(p.posted_at || p.created_at)}</span></div><p className="text-foreground font-medium pl-5">{p.title}</p><p className="text-muted-foreground line-clamp-2 pl-5">{p.content}</p>{p.error && <p className="text-red-400 pl-5 mt-1">{p.error}</p>}</div>); })}</div></div>
        </DashboardLayout>
    );
};
export default Outreach;
