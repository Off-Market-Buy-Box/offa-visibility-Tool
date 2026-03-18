import { BarChart3, Search, TrendingUp, Zap, Settings } from "lucide-react";
import { NavLink } from "@/components/NavLink";
import RedditIcon from "@/components/icons/RedditIcon";
import LinkedInIcon from "@/components/icons/LinkedInIcon";

const navSections = [
  {
    label: "AI VISIBILITY",
    items: [
      { title: "Analytics", icon: BarChart3, url: "/", color: "" },
      { title: "Keywords", icon: Search, url: "/keywords", color: "" },
      { title: "Competitors", icon: TrendingUp, url: "/competitors", color: "" },
    ],
  },
  {
    label: "PLATFORMS",
    items: [
      { title: "Reddit", icon: RedditIcon, url: "/reddit", color: "" },
      { title: "LinkedIn", icon: LinkedInIcon, url: "/linkedin", color: "" },
    ],
  },
  {
    label: "CONTENT & TOOLS",
    items: [
      { title: "Smart Tasks", icon: Zap, url: "/smart-tasks", color: "" },
    ],
  },
  {
    label: "ACCOUNT",
    items: [
      { title: "Settings", icon: Settings, url: "/settings", color: "" },
    ],
  },
];

const DashboardSidebar = () => {
  return (
    <aside className="w-56 min-h-screen bg-sidebar flex flex-col shrink-0">
      <div className="px-5 py-6">
        <h1 className="text-2xl font-bold text-sidebar-foreground">Offa</h1>
        <p className="text-xs text-sidebar-foreground/70">Visibility Tool</p>
      </div>

      <nav className="flex-1 px-3 space-y-6">
        {navSections.map((section) => (
          <div key={section.label}>
            <p className="px-3 mb-2 text-[11px] font-semibold tracking-wider text-sidebar-foreground/60">
              {section.label}
            </p>
            <ul className="space-y-1">
              {section.items.map((item) => (
                <li key={item.title}>
                  <NavLink
                    to={item.url}
                    end
                    className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-sidebar-foreground/80 hover:bg-sidebar-accent transition-colors"
                    activeClassName="bg-sidebar-active/20 text-sidebar-foreground"
                  >
                    <item.icon className={`h-5 w-5 ${item.color}`} />
                    <span>{item.title}</span>
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>

      <div className="p-4 border-t border-sidebar-border">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center text-primary-foreground text-xs font-bold">
            B
          </div>
          <div className="min-w-0">
            <p className="text-sm font-medium text-sidebar-foreground truncate">bilel MAALOUL</p>
            <p className="text-xs text-sidebar-foreground/60 truncate">bilelmaaloulm@gmail.com</p>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default DashboardSidebar;
