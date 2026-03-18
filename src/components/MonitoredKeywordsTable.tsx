import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const keywords = [
  { trend: "New", keyword: "luxury homes in Miami", rank: "—", vis: "0/1", lastRun: "Now" },
  { trend: "New", keyword: "luxury homes in Miami", rank: "—", vis: "0/1", lastRun: "Now" },
  { trend: "New", keyword: "off market real estate deals", rank: "—", vis: "0/1", lastRun: "Now" },
  { trend: "New", keyword: "best real estate marketplace", rank: "—", vis: "0/1", lastRun: "Now" },
];

const MonitoredKeywordsTable = () => {
  return (
    <div className="bg-card rounded-xl border border-border p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-card-foreground">Monitored Keywords</h2>
        <Button size="sm" className="bg-primary text-primary-foreground hover:bg-primary/90">
          Manage Keywords
        </Button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left py-3 px-2 text-sm font-medium text-muted-foreground">Trend</th>
              <th className="text-left py-3 px-2 text-sm font-medium text-muted-foreground">Keyword</th>
              <th className="text-left py-3 px-2 text-sm font-medium text-muted-foreground">Rank</th>
              <th className="text-left py-3 px-2 text-sm font-medium text-muted-foreground">Vis.</th>
              <th className="text-left py-3 px-2 text-sm font-medium text-muted-foreground">Last Run</th>
            </tr>
          </thead>
          <tbody>
            {keywords.map((kw, i) => (
              <tr key={i} className="border-b border-border last:border-0">
                <td className="py-3 px-2">
                  <Badge variant="outline" className="text-xs border-primary text-primary">
                    {kw.trend}
                  </Badge>
                </td>
                <td className="py-3 px-2 text-sm text-card-foreground">{kw.keyword}</td>
                <td className="py-3 px-2 text-sm text-muted-foreground">{kw.rank}</td>
                <td className="py-3 px-2 text-sm text-muted-foreground">{kw.vis}</td>
                <td className="py-3 px-2 text-sm text-muted-foreground">{kw.lastRun}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default MonitoredKeywordsTable;
