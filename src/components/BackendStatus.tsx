import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Loader2, CheckCircle, XCircle } from "lucide-react";

export function BackendStatus() {
  const [status, setStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking');

  useEffect(() => {
    checkBackend();
    const interval = setInterval(checkBackend, 30000); // Check every 30s
    return () => clearInterval(interval);
  }, []);

  const checkBackend = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/health', { 
        method: 'GET',
        mode: 'cors'
      });
      setStatus(response.ok ? 'connected' : 'disconnected');
    } catch (error) {
      console.error('Backend health check failed:', error);
      setStatus('disconnected');
    }
  };

  if (status === 'checking') {
    return (
      <Badge variant="outline" className="gap-1">
        <Loader2 className="h-3 w-3 animate-spin" />
        Checking...
      </Badge>
    );
  }

  if (status === 'connected') {
    return (
      <Badge variant="outline" className="gap-1 text-primary border-primary">
        <CheckCircle className="h-3 w-3" />
        Backend Connected
      </Badge>
    );
  }

  return (
    <Badge variant="outline" className="gap-1 text-destructive border-destructive">
      <XCircle className="h-3 w-3" />
      Backend Offline
    </Badge>
  );
}
