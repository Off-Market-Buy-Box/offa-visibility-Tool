import { useState } from "react";
import { keywordService } from "@/services/keywordService";
import { competitorService } from "@/services/competitorService";
import { smartTaskService } from "@/services/smartTaskService";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import DashboardLayout from "@/components/DashboardLayout";

const TestAPI = () => {
  const [result, setResult] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const testKeywords = async () => {
    setLoading(true);
    try {
      const keywords = await keywordService.getAll();
      setResult(`✅ Success! Found ${keywords.length} keywords\n${JSON.stringify(keywords, null, 2)}`);
    } catch (error) {
      setResult(`❌ Error: ${error}`);
    }
    setLoading(false);
  };

  const createTestKeyword = async () => {
    setLoading(true);
    try {
      const keyword = await keywordService.create({
        keyword: "best seo tools",
        domain: "yoursite.com",
        search_volume: 1000,
        difficulty: 45
      });
      setResult(`✅ Keyword created!\n${JSON.stringify(keyword, null, 2)}`);
    } catch (error) {
      setResult(`❌ Error: ${error}`);
    }
    setLoading(false);
  };

  const testCompetitors = async () => {
    setLoading(true);
    try {
      const competitors = await competitorService.getAll();
      setResult(`✅ Success! Found ${competitors.length} competitors\n${JSON.stringify(competitors, null, 2)}`);
    } catch (error) {
      setResult(`❌ Error: ${error}`);
    }
    setLoading(false);
  };

  const testTasks = async () => {
    setLoading(true);
    try {
      const tasks = await smartTaskService.getAll();
      setResult(`✅ Success! Found ${tasks.length} tasks\n${JSON.stringify(tasks, null, 2)}`);
    } catch (error) {
      setResult(`❌ Error: ${error}`);
    }
    setLoading(false);
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <h1 className="text-3xl font-bold">API Connection Test</h1>
        
        <Card>
          <CardHeader>
            <CardTitle>Test Backend Connection</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2 flex-wrap">
              <Button onClick={testKeywords} disabled={loading}>
                Get Keywords
              </Button>
              <Button onClick={createTestKeyword} disabled={loading}>
                Create Test Keyword
              </Button>
              <Button onClick={testCompetitors} disabled={loading}>
                Get Competitors
              </Button>
              <Button onClick={testTasks} disabled={loading}>
                Get Tasks
              </Button>
            </div>

            {result && (
              <div className="mt-4">
                <h3 className="font-semibold mb-2">Result:</h3>
                <pre className="bg-muted p-4 rounded-lg overflow-auto text-sm">
                  {result}
                </pre>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default TestAPI;
