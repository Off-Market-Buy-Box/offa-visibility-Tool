import { Eye } from "lucide-react";

const BrandVisibilityCard = () => {
  return (
    <div className="bg-card rounded-xl border border-border p-6">
      <div className="flex items-center gap-2 mb-4">
        <Eye className="h-5 w-5 text-muted-foreground" />
        <h2 className="text-lg font-semibold text-card-foreground">Your Brand Visibility</h2>
      </div>

      <div className="flex flex-wrap items-start gap-8">
        <div>
          <p className="text-5xl font-extrabold text-primary">36%</p>
          <p className="text-sm text-muted-foreground">visible</p>
        </div>

        <div className="flex flex-wrap gap-8">
          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-primary" />
            <div>
              <p className="text-sm text-muted-foreground">Cited as Source</p>
              <p className="text-2xl font-bold text-card-foreground">42%</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-blue-500" />
            <div>
              <p className="text-sm text-muted-foreground">Mentioned in Text</p>
              <p className="text-2xl font-bold text-card-foreground">0%</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-purple-500" />
            <div>
              <p className="text-sm text-muted-foreground">In Rankings</p>
              <p className="text-2xl font-bold text-card-foreground">0%</p>
            </div>
          </div>
        </div>
      </div>

      <p className="mt-4 text-sm text-muted-foreground">
        4 analyses · 4 keywords · 42 avg citations — avg rank
      </p>
    </div>
  );
};

export default BrandVisibilityCard;
