import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { AlertTriangle } from "lucide-react";
import { api } from "@/lib/api";

interface CredentialsBannerProps {
    platform: string;
    label: string;
}

const CredentialsBanner = ({ platform, label }: CredentialsBannerProps) => {
    const [loggedIn, setLoggedIn] = useState<boolean | null>(null);

    useEffect(() => {
        api.get<{ authenticated: boolean }>(`/${platform}/auth-status`)
            .then((res) => setLoggedIn(res?.authenticated ?? false))
            .catch(() => setLoggedIn(false));
    }, [platform]);

    if (loggedIn === null || loggedIn === true) return null;

    return (
        <div className="flex items-center gap-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg px-4 py-2.5 mb-3">
            <AlertTriangle className="h-4 w-4 text-yellow-500 shrink-0" />
            <p className="text-sm text-yellow-200/90">
                Not logged in to {label}. Posting and agent features won't work.{" "}
                <Link to="/profile" className="text-primary underline underline-offset-2 hover:text-primary/80">
                    Login in Profile →
                </Link>
            </p>
        </div>
    );
};

export default CredentialsBanner;
