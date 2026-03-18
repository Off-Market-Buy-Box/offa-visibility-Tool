import DashboardLayout from "@/components/DashboardLayout";
import BrandVisibilityCard from "@/components/BrandVisibilityCard";
import RankingsChart from "@/components/RankingsChart";
import TopVisibilityCard from "@/components/TopVisibilityCard";
import MonitoredKeywordsTable from "@/components/MonitoredKeywordsTable";

const Index = () => {
  return (
    <DashboardLayout>
      <BrandVisibilityCard />
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        <div className="lg:col-span-3">
          <RankingsChart />
        </div>
        <div className="lg:col-span-2">
          <TopVisibilityCard />
        </div>
      </div>
      <MonitoredKeywordsTable />
    </DashboardLayout>
  );
};

export default Index;
