import DashboardLayout from "@/components/DashboardLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Play, Square, Loader2, RefreshCw, MessageSquare, Search, ExternalLink, Trash2 } from "lucide-react";
import RedditIcon from "@/components/icons/RedditIcon";
import LinkedInIcon from "@/components/icons/LinkedInIcon";
import TwitterIcon from "@/components/icons/TwitterIcon";
import FacebookIcon from "@/components/icons/FacebookIcon";
import { useState, useEffect, useRef } from "react";
import { automationService, type AutomationStatus, type AutomationLog, type CommentedPost } from "@/services/automationService";
import { useToast } from "@/hooks/use-toast";

const ICONS: Record<string, any> = { reddit: RedditIcon, linkedin: LinkedInIcon, twitter: TwitterIcon, facebook: FacebookIcon };
const COLORS: Record<string, string> = { reddit: "text-orange-500", linkedin: "text-blue-600", twitter: "text-sky-500", facebook: "text-blue-500" };
const LABELS: Record<string, string> = { reddit: "Reddit", linkedin: "LinkedIn", twitter: "Twitter / X", facebook: "Facebook" };
const PLATFORMS = ["reddit", "linkedin", "twitter", "facebook"];

type Tab = "activity" | "commented";

const Automation = () => {
    const [status, setStatus] = useState<AutomationStatus | null>(null);
    const [logs, setLogs] = useState<AutomationLog[]>([]);
    const [commentedPosts, setCommentedPosts] = useState<CommentedPost[]>([]);
    const [loading, setLoading] = useState(true);
    const [toggling, setToggling] = useState(false);
    const [tab, setTab] = useState<Tab>("activity");
    const [filterPlatform, setFilterPlatform] = useState<string>("all");
    const [clearing, setClearing] = useState(false);
    const { toast } = useToast();
    const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

    const fetchAll = async () => {
        try {
            const [s, l, c] = await Promise.all([
                automationService.getStatus(),
                automationService.getLogs(undefined, 50),
                automationService.getCommentedPosts(undefined, 100),
            ]);
            setStatus(s);
            setLogs(l);
            setCommentedPosts(c);
        } catch { /* ignore */ }
        finally { setLoading(false); }
    };

    useEffect(() => {
        fetchAll();
        pollRef.current = setInterval(fetchAll, 5000);
        return () => { if (pollRef.current) clearInterval(pollRef.current); };
    }, []);

    const handleToggle = async () => {
        if (!status) return;
        setToggling(true);
        try {
            if (status.running) { await automationService.stop(); toast({ title: "Automation stopped" }); }
            else { await automationService.start(); toast({ title: "Automation started" }); }
            await fetchAll();
        } catch (e: any) { toast({ title: "Error", description: e.message, variant: "destructive" }); }
        finally { setToggling(false); }
    };

    const handlePlatformToggle = async (platform: string, enabled: boolean) => {
        try { await automationService.updateSettings({ platforms: { [platform]: { enabled } } } as any); await fetchAll(); } catch { /* */ }
    };

    const handleSettingChange = async (key: string, value: number) => {
        try { await automationService.updateSettings({ [key]: value } as any); await fetchAll(); } catch { /* */ }
    };

    const handleClearAll = async () => {
        if (!confirm("Are you sure? This will delete ALL scanned posts, comments, logs, and stats across every platform.")) return;
        setClearing(true);
        try {
            await automationService.clearAll();
            toast({ title: "All data cleared" });
            await fetchAll();
        } catch (e: any) { toast({ title: "Error", description: e.message, variant: "destructive" }); }
        finally { setClearing(false); }
    };

    const formatTime = (iso: string | null) => {
        if (!iso) return "Never";
        return new Date(iso).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
    };

    const formatDate = (iso: string | null) => {
        if (!iso) return "";
        return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
    };

    const filteredLogs = filterPlatform === "all" ? logs : logs.filter(l => l.platform === filterPlatform);
    const filteredCommented = filterPlatform === "all" ? commentedPosts : commentedPosts.filter(c => c.platform === filterPlatform);

    if (loading || !status) {
        return (<DashboardLayout><div className="flex items-center justify-center h-64"><Loader2 className="h-8 w-8 animate-spin text-primary" /></div></DashboardLayout>);
    }

    return (
        <DashboardLayout>
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <div>
                    <h1 className="text-xl font-bold text-foreground">Automation</h1>
                    <p className="text-xs text-muted-foreground">
                        {status.running ? (
                            <span className="text-green-500">Running — Cycle #{status.cycle_count}
                                {status.current_platform && ` · ${LABELS[status.current_platform]} · ${status.current_action}`}
                            </span>
                        ) : "Stopped"}
                    </p>
                </div>
                <Button onClick={handleToggle} disabled={toggling} variant={status.running ? "destructive" : "default"} className="gap-2">
                    {toggling ? <Loader2 className="h-4 w-4 animate-spin" /> : status.running ? <Square className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                    {status.running ? "Stop" : "Start"}
                </Button>
            </div>

            {/* Platform Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
                {PLATFORMS.map((p) => {
                    const Icon = ICONS[p];
                    const ps = status.platforms[p];
                    const isActive = status.running && status.current_platform === p;
                    return (
                        <div key={p} className={`bg-card rounded-xl border p-4 ${isActive ? "border-primary ring-1 ring-primary/30" : "border-border"}`}>
                            <div className="flex items-center justify-between mb-3">
                                <div className="flex items-center gap-2">
                                    <Icon className={`h-5 w-5 ${COLORS[p]}`} />
                                    <span className="text-sm font-semibold text-foreground">{LABELS[p]}</span>
                                    {isActive && <Loader2 className="h-3 w-3 animate-spin text-primary" />}
                                </div>
                                <Switch checked={ps.enabled} onCheckedChange={(v) => handlePlatformToggle(p, v)} />
                            </div>
                            <div className="grid grid-cols-3 gap-2 text-center">
                                <div><p className="text-lg font-bold text-foreground">{ps.total_scanned}</p><p className="text-[10px] text-muted-foreground">Scanned</p></div>
                                <div><p className="text-lg font-bold text-green-500">{ps.total_commented}</p><p className="text-[10px] text-muted-foreground">Commented</p></div>
                                <div><p className="text-lg font-bold text-red-400">{ps.errors}</p><p className="text-[10px] text-muted-foreground">Errors</p></div>
                            </div>
                            <div className="flex items-center justify-between mt-2 text-[10px] text-muted-foreground">
                                <span>Last scan: {formatTime(ps.last_scan)}</span>
                                <span>Last comment: {formatTime(ps.last_comment)}</span>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Settings */}
            <div className="bg-card rounded-xl border border-border p-4 mb-4">
                <p className="text-sm font-semibold text-foreground mb-3">Settings</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div><Label className="text-xs text-muted-foreground">Posts per run</Label><Input type="number" min={1} max={50} value={status.max_posts_per_run} onChange={(e) => handleSettingChange("max_posts_per_run", Number(e.target.value))} className="mt-1 h-8" /></div>
                    <div><Label className="text-xs text-muted-foreground">Delay between cycles (sec)</Label><Input type="number" min={5} max={3600} value={status.delay_between_cycles} onChange={(e) => handleSettingChange("delay_between_cycles", Number(e.target.value))} className="mt-1 h-8" /></div>
                </div>
                <div className="mt-3 pt-3 border-t border-border">
                    <Button variant="destructive" size="sm" onClick={handleClearAll} disabled={clearing || status.running} className="gap-2 text-xs">
                        {clearing ? <Loader2 className="h-3 w-3 animate-spin" /> : <Trash2 className="h-3 w-3" />}
                        Clear All Data
                    </Button>
                    <p className="text-[10px] text-muted-foreground mt-1">Deletes all scanned posts, comments, logs, and stats.</p>
                </div>
            </div>

            {/* Tabs + Filter */}
            <div className="bg-card rounded-xl border border-border p-4">
                <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-1">
                        <Button variant={tab === "activity" ? "default" : "ghost"} size="sm" onClick={() => setTab("activity")} className="text-xs h-7">Activity Log</Button>
                        <Button variant={tab === "commented" ? "default" : "ghost"} size="sm" onClick={() => setTab("commented")} className="text-xs h-7">
                            Commented Posts ({commentedPosts.length})
                        </Button>
                    </div>
                    <div className="flex items-center gap-1">
                        {["all", ...PLATFORMS].map((p) => (
                            <Button key={p} variant={filterPlatform === p ? "secondary" : "ghost"} size="sm" className="text-[10px] h-6 px-2" onClick={() => setFilterPlatform(p)}>
                                {p === "all" ? "All" : LABELS[p]}
                            </Button>
                        ))}
                        <Button variant="ghost" size="sm" onClick={fetchAll} className="h-6 w-6 p-0"><RefreshCw className="h-3 w-3" /></Button>
                    </div>
                </div>

                {tab === "activity" && (
                    <div className="space-y-1 max-h-[400px] overflow-y-auto">
                        {filteredLogs.length === 0 ? (
                            <p className="text-xs text-muted-foreground text-center py-4">No activity yet.</p>
                        ) : filteredLogs.map((log) => {
                            const Icon = ICONS[log.platform] || Search;
                            const isComment = log.action === "comment";
                            return (
                                <div key={log.id} className="flex items-center gap-3 py-1.5 px-2 rounded hover:bg-muted/50 text-xs">
                                    <Icon className={`h-4 w-4 shrink-0 ${COLORS[log.platform] || ""}`} />
                                    <span className="text-muted-foreground w-16 shrink-0">{formatTime(log.created_at)}</span>
                                    <span className={`w-16 shrink-0 ${isComment ? "text-green-500" : "text-blue-400"}`}>
                                        {isComment ? <MessageSquare className="h-3 w-3 inline mr-1" /> : <Search className="h-3 w-3 inline mr-1" />}
                                        {log.action}
                                    </span>
                                    <span className="text-foreground flex-1">
                                        {isComment ? `${log.posts_commented} commented / ${log.posts_found} found` : `${log.posts_found} posts found`}
                                    </span>
                                    {log.errors > 0 && <span className="text-red-400">{log.errors} err</span>}
                                </div>
                            );
                        })}
                    </div>
                )}

                {tab === "commented" && (
                    <div className="space-y-1 max-h-[400px] overflow-y-auto">
                        {filteredCommented.length === 0 ? (
                            <p className="text-xs text-muted-foreground text-center py-4">No commented posts yet.</p>
                        ) : filteredCommented.map((post) => {
                            const Icon = ICONS[post.platform] || Search;
                            return (
                                <div key={`${post.platform}-${post.id}`} className="flex items-center gap-3 py-2 px-2 rounded hover:bg-muted/50 text-xs">
                                    <Icon className={`h-4 w-4 shrink-0 ${COLORS[post.platform] || ""}`} />
                                    <span className="text-muted-foreground w-28 shrink-0">{formatDate(post.posted_at)}</span>
                                    <span className="text-foreground flex-1 truncate">{post.title}</span>
                                    <span className="text-muted-foreground shrink-0">{post.author || ""}</span>
                                    {post.url && (
                                        <a href={post.url} target="_blank" rel="noopener noreferrer" className="shrink-0 text-primary hover:text-primary/80">
                                            <ExternalLink className="h-3 w-3" />
                                        </a>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </DashboardLayout>
    );
};

export default Automation;
