import { Search, KeyRound, Bot } from "lucide-react";
import { NavLink } from "@/components/NavLink";
import RedditIcon from "@/components/icons/RedditIcon";
import LinkedInIcon from "@/components/icons/LinkedInIcon";
import TwitterIcon from "@/components/icons/TwitterIcon";
import FacebookIcon from "@/components/icons/FacebookIcon";

const navSections = [
  {
    label: "AI VISIBILITY",
    items: [
      { title: "Keywords", icon: Search, url: "/keywords", color: "" },
    ],
  },
  {
    label: "PLATFORMS",
    items: [
      { title: "Reddit", icon: RedditIcon, url: "/reddit", color: "" },
      { title: "LinkedIn", icon: LinkedInIcon, url: "/linkedin", color: "" },
      { title: "Twitter", icon: TwitterIcon, url: "/twitter", color: "" },
      { title: "Facebook", icon: FacebookIcon, url: "/facebook", color: "" },
    ],
  },
  {
    label: "AUTOMATION",
    items: [
      { title: "Automation", icon: Bot, url: "/automation", color: "" },
    ],
  },
  {
    label: "ACCOUNT",
    items: [
      { title: "Profile", icon: KeyRound, url: "/profile", color: "" },
    ],
  },
];

const DashboardSidebar = () => {
  return (
    <aside className="w-56 h-screen bg-sidebar flex flex-col shrink-0 sticky top-0">
      <div className="px-5 py-6">
        <h1 className="text-2xl font-bold text-sidebar-foreground">Offa Flow</h1>
        <p className="text-xs text-sidebar-foreground/70">Visibility Tool</p>
      </div>

      <nav className="flex-1 px-3 space-y-6 overflow-y-auto">
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

    </aside>
  );
};

export default DashboardSidebar;
