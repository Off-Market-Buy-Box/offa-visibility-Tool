import DashboardSidebar from "@/components/DashboardSidebar";
import { ThemeToggle } from "@/components/ThemeToggle";
import { BackendStatus } from "@/components/BackendStatus";
import { ReactNode } from "react";

const DashboardLayout = ({ children }: { children: ReactNode }) => {
  return (
    <div className="flex min-h-screen bg-background">
      <DashboardSidebar />
      <main className="flex-1 p-4 overflow-auto">
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <BackendStatus />
            <ThemeToggle />
          </div>
          {children}
        </div>
      </main>
    </div>
  );
};

export default DashboardLayout;
