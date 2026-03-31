import DashboardLayout from "@/components/DashboardLayout";
import { Button } from "@/components/ui/button";
import { Loader2, LogIn, CheckCircle2, XCircle } from "lucide-react";
import RedditIcon from "@/components/icons/RedditIcon";
import LinkedInIcon from "@/components/icons/LinkedInIcon";
import TwitterIcon from "@/components/icons/TwitterIcon";
import FacebookIcon from "@/components/icons/FacebookIcon";
import { useState, useEffect } from "react";
import { redditService } from "@/services/redditService";
import { linkedinService } from "@/services/linkedinService";
import { twitterService } from "@/services/twitterService";
import { facebookService } from "@/services/facebookService";
import { useToast } from "@/hooks/use-toast";

const PLATFORMS = [
    { key: "reddit", label: "Reddit", icon: RedditIcon, color: "text-orange-500", borderColor: "border-orange-500/30" },
    { key: "linkedin", label: "LinkedIn", icon: LinkedInIcon, color: "text-blue-600", borderColor: "border-blue-600/30" },
    { key: "twitter", label: "Twitter / X", icon: TwitterIcon, color: "text-sky-500", borderColor: "border-sky-500/30" },
    { key: "facebook", label: "Facebook", icon: FacebookIcon, color: "text-blue-500", borderColor: "border-blue-500/30" },
];

const loginFn: Record<string, () => Promise<any>> = {
    reddit: () => redditService.browserLogin(),
    linkedin: () => linkedinService.browserLogin(),
    twitter: () => twitterService.browserLogin(),
    facebook: () => facebookService.browserLogin(),
};

const authFn: Record<string, () => Promise<any>> = {
    reddit: () => redditService.getAuthStatus(),
    linkedin: () => linkedinService.getAuthStatus(),
    twitter: () => twitterService.getAuthStatus(),
    facebook: () => facebookService.getAuthStatus(),
};

const Profile = () => {
    const [statuses, setStatuses] = useState<Record<string, boolean | null>>({});
    const [loggingIn, setLoggingIn] = useState<Record<string, boolean>>({});
    const [loading, setLoading] = useState(true);
    const { toast } = useToast();

    useEffect(() => {
        const check = async () => {
            const results: Record<string, boolean | null> = {};
            for (const p of PLATFORMS) {
                try {
                    const res = await authFn[p.key]();
                    results[p.key] = res?.authenticated ?? false;
                } catch {
                    results[p.key] = false;
                }
            }
            setStatuses(results);
            setLoading(false);
        };
        check();
    }, []);

    const handleLogin = async (key: string, label: string) => {
        setLoggingIn(prev => ({ ...prev, [key]: true }));
        try {
            await loginFn[key]();
            setStatuses(prev => ({ ...prev, [key]: true }));
            toast({ title: `${label} login successful`, description: "Session saved." });
        } catch (e: any) {
            toast({ title: "Login Issue", description: e.message || "Complete login in the browser window", variant: "destructive" });
            // Re-check status after attempt
            try {
                const res = await authFn[key]();
                setStatuses(prev => ({ ...prev, [key]: res?.authenticated ?? false }));
            } catch { /* ignore */ }
        } finally {
            setLoggingIn(prev => ({ ...prev, [key]: false }));
        }
    };

    return (
        <DashboardLayout>
            <div>
                <h1 className="text-2xl font-bold text-foreground">Profile</h1>
                <p className="text-sm text-muted-foreground">Log in to your social media accounts for automated posting</p>
            </div>

            <div className="space-y-3">
                {PLATFORMS.map((p) => {
                    const Icon = p.icon;
                    const isLoggedIn = statuses[p.key] === true;
                    const isLogging = loggingIn[p.key] || false;

                    return (
                        <div key={p.key} className={`bg-card rounded-xl border ${p.borderColor} p-5 flex items-center justify-between`}>
                            <div className="flex items-center gap-3">
                                <Icon className={`h-6 w-6 ${p.color}`} />
                                <div>
                                    <p className="text-sm font-semibold text-foreground">{p.label}</p>
                                    {loading ? (
                                        <p className="text-xs text-muted-foreground">Checking...</p>
                                    ) : isLoggedIn ? (
                                        <p className="text-xs text-green-500 flex items-center gap-1"><CheckCircle2 className="h-3 w-3" />Logged in</p>
                                    ) : (
                                        <p className="text-xs text-muted-foreground flex items-center gap-1"><XCircle className="h-3 w-3" />Not logged in</p>
                                    )}
                                </div>
                            </div>
                            <Button
                                variant={isLoggedIn ? "outline" : "default"}
                                size="sm"
                                onClick={() => handleLogin(p.key, p.label)}
                                disabled={isLogging}
                            >
                                {isLogging ? (
                                    <><Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" />Opening browser...</>
                                ) : (
                                    <><LogIn className="h-3.5 w-3.5 mr-1.5" />{isLoggedIn ? "Re-login" : "Login"}</>
                                )}
                            </Button>
                        </div>
                    );
                })}
            </div>
        </DashboardLayout>
    );
};

export default Profile;
