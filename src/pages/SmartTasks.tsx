import DashboardLayout from "@/components/DashboardLayout";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Zap, CheckCircle, Clock, Plus, Loader2 } from "lucide-react";
import { useState, useEffect } from "react";
import { smartTaskService, type SmartTask, type TaskStatus, type TaskPriority } from "@/services/smartTaskService";
import { useToast } from "@/hooks/use-toast";

const SmartTasks = () => {
  const [tasks, setTasks] = useState<SmartTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [newTask, setNewTask] = useState({ title: "", description: "", priority: "medium" as TaskPriority });
  const { toast } = useToast();

  useEffect(() => {
    fetchTasks();
  }, []);

  const fetchTasks = async () => {
    try {
      setLoading(true);
      const data = await smartTaskService.getAll();
      setTasks(data);
    } catch (error) {
      console.error("Fetch tasks error:", error);
      // Don't show error toast for empty data
      setTasks([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTask = async () => {
    try {
      await smartTaskService.create(newTask);
      toast({
        title: "Success",
        description: "Task created successfully",
      });
      setDialogOpen(false);
      setNewTask({ title: "", description: "", priority: "medium" });
      fetchTasks();
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to create task",
        variant: "destructive",
      });
    }
  };

  const handleUpdateStatus = async (id: number, status: TaskStatus) => {
    try {
      await smartTaskService.update(id, { status });
      toast({
        title: "Success",
        description: "Task updated successfully",
      });
      fetchTasks();
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to update task",
        variant: "destructive",
      });
    }
  };

  const statusBadge = (status: TaskStatus) => {
    if (status === "completed") return <Badge className="bg-primary/10 text-primary border-0"><CheckCircle className="h-3 w-3 mr-1" /> Done</Badge>;
    if (status === "in_progress") return <Badge className="bg-blue-500/10 text-blue-600 border-0"><Clock className="h-3 w-3 mr-1" /> In Progress</Badge>;
    if (status === "failed") return <Badge className="bg-destructive/10 text-destructive border-0">Failed</Badge>;
    return <Badge variant="outline" className="text-muted-foreground">Pending</Badge>;
  };

  const priorityColor = (priority: TaskPriority) => {
    if (priority === "urgent") return "text-destructive border-destructive";
    if (priority === "high") return "text-orange-600 border-orange-600";
    if (priority === "medium") return "text-yellow-600 border-yellow-600";
    return "text-muted-foreground border-border";
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </DashboardLayout>
    );
  }

  const pending = tasks.filter(t => t.status === "pending");
  const inProgress = tasks.filter(t => t.status === "in_progress");
  const completed = tasks.filter(t => t.status === "completed");

  return (
    <DashboardLayout>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Smart Tasks</h1>
          <p className="text-sm text-muted-foreground">AI-recommended actions to boost your visibility</p>
        </div>
        <div className="flex gap-2">
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="outline">
                <Plus className="h-4 w-4 mr-2" /> Add Task
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New Task</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label>Title</Label>
                  <Input
                    value={newTask.title}
                    onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
                    placeholder="Task title"
                  />
                </div>
                <div>
                  <Label>Description</Label>
                  <Textarea
                    value={newTask.description}
                    onChange={(e) => setNewTask({ ...newTask, description: e.target.value })}
                    placeholder="Task description"
                  />
                </div>
                <div>
                  <Label>Priority</Label>
                  <Select value={newTask.priority} onValueChange={(value: TaskPriority) => setNewTask({ ...newTask, priority: value })}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="low">Low</SelectItem>
                      <SelectItem value="medium">Medium</SelectItem>
                      <SelectItem value="high">High</SelectItem>
                      <SelectItem value="urgent">Urgent</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button onClick={handleCreateTask} className="w-full">Create Task</Button>
              </div>
            </DialogContent>
          </Dialog>
          <Button className="bg-primary text-primary-foreground hover:bg-primary/90">
            <Zap className="h-4 w-4 mr-2" /> Generate Tasks
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-card rounded-xl border border-border p-5">
          <p className="text-sm text-muted-foreground">Pending</p>
          <p className="text-3xl font-bold text-foreground mt-1">{pending.length}</p>
        </div>
        <div className="bg-card rounded-xl border border-border p-5">
          <p className="text-sm text-muted-foreground">In Progress</p>
          <p className="text-3xl font-bold text-blue-600 mt-1">{inProgress.length}</p>
        </div>
        <div className="bg-card rounded-xl border border-border p-5">
          <p className="text-sm text-muted-foreground">Completed</p>
          <p className="text-3xl font-bold text-primary mt-1">{completed.length}</p>
        </div>
      </div>

      <div className="bg-card rounded-xl border border-border p-6">
        <h2 className="text-lg font-semibold text-card-foreground mb-4">All Tasks</h2>
        {tasks.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-muted-foreground">No tasks yet. Create your first task or generate AI recommendations!</p>
          </div>
        ) : (
          <div className="space-y-3">
            {tasks.map((task) => (
              <div key={task.id} className="flex items-center justify-between p-4 rounded-lg border border-border hover:bg-muted/50 transition-colors">
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-foreground truncate">{task.title}</p>
                    {task.description && (
                      <p className="text-xs text-muted-foreground mt-1 truncate">{task.description}</p>
                    )}
                    <div className="flex items-center gap-3 mt-2">
                      <Badge variant="outline" className={`text-xs ${priorityColor(task.priority)}`}>
                        {task.priority}
                      </Badge>
                      {task.task_type && (
                        <Badge variant="outline" className="text-xs">{task.task_type}</Badge>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {statusBadge(task.status)}
                  {task.status !== "completed" && (
                    <Select value={task.status} onValueChange={(value: TaskStatus) => handleUpdateStatus(task.id, value)}>
                      <SelectTrigger className="w-32">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="pending">Pending</SelectItem>
                        <SelectItem value="in_progress">In Progress</SelectItem>
                        <SelectItem value="completed">Completed</SelectItem>
                        <SelectItem value="failed">Failed</SelectItem>
                      </SelectContent>
                    </Select>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

export default SmartTasks;
