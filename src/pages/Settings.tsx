import DashboardLayout from "@/components/DashboardLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { User, Bell, Shield, CreditCard } from "lucide-react";

const Settings = () => {
  return (
    <DashboardLayout>
      <div>
        <h1 className="text-2xl font-bold text-foreground">Settings</h1>
        <p className="text-sm text-muted-foreground">Manage your account and preferences</p>
      </div>

      {/* Profile */}
      <div className="bg-card rounded-xl border border-border p-6">
        <div className="flex items-center gap-2 mb-4">
          <User className="h-5 w-5 text-muted-foreground" />
          <h2 className="text-lg font-semibold text-card-foreground">Profile</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label className="text-sm text-muted-foreground">Full Name</Label>
            <Input defaultValue="bilel MAALOUL" className="mt-1" />
          </div>
          <div>
            <Label className="text-sm text-muted-foreground">Email</Label>
            <Input defaultValue="bilelmaaloulm@gmail.com" className="mt-1" />
          </div>
          <div>
            <Label className="text-sm text-muted-foreground">Company</Label>
            <Input defaultValue="Offa" className="mt-1" />
          </div>
          <div>
            <Label className="text-sm text-muted-foreground">Website</Label>
            <Input defaultValue="https://offa.com" className="mt-1" />
          </div>
        </div>
        <Button className="mt-4 bg-primary text-primary-foreground hover:bg-primary/90">Save Changes</Button>
      </div>

      {/* Notifications */}
      <div className="bg-card rounded-xl border border-border p-6">
        <div className="flex items-center gap-2 mb-4">
          <Bell className="h-5 w-5 text-muted-foreground" />
          <h2 className="text-lg font-semibold text-card-foreground">Notifications</h2>
        </div>
        <div className="space-y-4">
          {[
            { label: "Email notifications for visibility changes", desc: "Get notified when your rankings change significantly" },
            { label: "Reddit mention alerts", desc: "Receive alerts when your brand is mentioned on Reddit" },
            { label: "Weekly visibility report", desc: "Get a weekly summary of your AI visibility metrics" },
            { label: "Smart task recommendations", desc: "Receive AI-generated task suggestions" },
          ].map((item, i) => (
            <div key={i} className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-foreground">{item.label}</p>
                <p className="text-xs text-muted-foreground">{item.desc}</p>
              </div>
              <Switch defaultChecked={i < 2} />
            </div>
          ))}
        </div>
      </div>

      {/* Plan */}
      <div className="bg-card rounded-xl border border-border p-6">
        <div className="flex items-center gap-2 mb-4">
          <CreditCard className="h-5 w-5 text-muted-foreground" />
          <h2 className="text-lg font-semibold text-card-foreground">Plan & Billing</h2>
        </div>
        <div className="flex items-center justify-between p-4 rounded-lg border border-primary/20 bg-primary/5">
          <div>
            <p className="text-sm font-semibold text-foreground">Starter Plan — $99/month</p>
            <p className="text-xs text-muted-foreground">3 daily keywords · 10 manual AI keywords · Basic Reddit monitoring</p>
          </div>
          <Button variant="outline" className="border-primary text-primary hover:bg-primary hover:text-primary-foreground">
            Upgrade Plan
          </Button>
        </div>
      </div>

      {/* Security */}
      <div className="bg-card rounded-xl border border-border p-6">
        <div className="flex items-center gap-2 mb-4">
          <Shield className="h-5 w-5 text-muted-foreground" />
          <h2 className="text-lg font-semibold text-card-foreground">Security</h2>
        </div>
        <div className="space-y-4">
          <div>
            <Label className="text-sm text-muted-foreground">Current Password</Label>
            <Input type="password" className="mt-1 max-w-sm" />
          </div>
          <div>
            <Label className="text-sm text-muted-foreground">New Password</Label>
            <Input type="password" className="mt-1 max-w-sm" />
          </div>
          <Button variant="outline">Update Password</Button>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default Settings;
