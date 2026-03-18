import { TrendingUp } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

const data = [
  { date: "Mar 5", value: 30 },
  { date: "Mar 6", value: 28 },
  { date: "Mar 7", value: 35 },
  { date: "Mar 8", value: 38 },
  { date: "Mar 9", value: 42 },
  { date: "Mar 10", value: 45 },
  { date: "Mar 12", value: 52 },
];

const RankingsChart = () => {
  return (
    <div className="bg-card rounded-xl border border-border p-6 flex flex-col">
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp className="h-5 w-5 text-muted-foreground" />
        <h2 className="text-lg font-semibold text-card-foreground">Average Rankings Over Time</h2>
      </div>

      <div className="flex-1 min-h-[250px]">
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 13%, 91%)" />
            <XAxis dataKey="date" tick={{ fontSize: 12, fill: "hsl(220, 10%, 46%)" }} />
            <YAxis tick={{ fontSize: 12, fill: "hsl(220, 10%, 46%)" }} />
            <Tooltip />
            <Line
              type="monotone"
              dataKey="value"
              stroke="hsl(217, 91%, 60%)"
              strokeWidth={2}
              dot={{ r: 4, fill: "hsl(217, 91%, 60%)" }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="flex items-center justify-center gap-2 mt-2">
        <span className="h-2 w-2 rounded-full bg-blue-500" />
        <span className="text-sm text-muted-foreground">Visibility %</span>
      </div>
    </div>
  );
};

export default RankingsChart;
