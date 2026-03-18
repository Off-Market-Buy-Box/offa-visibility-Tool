import { BarChart3, MoreHorizontal } from "lucide-react";

const items = [
  { rank: 1, name: "Zillow", position: "#1.0", visibility: "67%" },
  { rank: 2, name: "Zillow", position: "#1.0", visibility: "67%" },
  { rank: 3, name: "Zillow", position: "#1.0", visibility: "67%" },
  { rank: 4, name: "Zillow", position: "#1.0", visibility: "67%" },
];

const TopVisibilityCard = () => {
  return (
    <div className="bg-card rounded-xl border border-border p-6">
      <div className="flex items-center gap-2 mb-4">
        <BarChart3 className="h-5 w-5 text-muted-foreground" />
        <h2 className="text-lg font-semibold text-card-foreground">Top Visibility</h2>
      </div>

      <div className="space-y-3">
        {items.map((item) => (
          <div key={item.rank} className="flex items-center justify-between py-1">
            <div className="flex items-center gap-3">
              <span className="text-sm text-muted-foreground w-4">{item.rank}</span>
              <span className="text-sm font-medium text-card-foreground">{item.name}</span>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-primary font-semibold">{item.position}</span>
              <span className="text-sm text-muted-foreground">{item.visibility}</span>
              <MoreHorizontal className="h-4 w-4 text-muted-foreground" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TopVisibilityCard;
