import { Play, Plus, RefreshCw, XCircle } from 'lucide-react';
import { useState } from 'react';
import { generateReportAsync, getTaskStatus, revokeTask, syncMetricsAsync } from '../services/api';

interface Task {
  id: string;
  type: 'report' | 'metrics';
  status: string;
  createdAt: Date;
}

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [generating, setGenerating] = useState(false);
  const [syncing, setSyncing] = useState(false);

  const handleGenerateReport = async () => {
    try {
      setGenerating(true);
      const response = await generateReportAsync({ sprint_count: 5 });
      const newTask: Task = {
        id: response.data.task_id,
        type: 'report',
        status: 'PENDING',
        createdAt: new Date(),
      };
      setTasks([newTask, ...tasks]);
      alert(`Report generation started! Task ID: ${response.data.task_id}`);
    } catch (error) {
      console.error('Failed to start report generation:', error);
      alert('Failed to start report generation');
    } finally {
      setGenerating(false);
    }
  };

  const handleSyncMetrics = async () => {
    try {
      setSyncing(true);
      const response = await syncMetricsAsync({ sprint_count: 10, force_refresh: true });
      const newTask: Task = {
        id: response.data.task_id,
        type: 'metrics',
        status: 'PENDING',
        createdAt: new Date(),
      };
      setTasks([newTask, ...tasks]);
      alert(`Metrics sync started! Task ID: ${response.data.task_id}`);
    } catch (error) {
      console.error('Failed to start metrics sync:', error);
      alert('Failed to start metrics sync');
    } finally {
      setSyncing(false);
    }
  };

  const handleCheckStatus = async (taskId: string) => {
    try {
      const response = await getTaskStatus(taskId);
      alert(`Task Status: ${response.data.status}\n${JSON.stringify(response.data.result || response.data.error || '', null, 2)}`);
      // Update task status
      setTasks(tasks.map(t => t.id === taskId ? { ...t, status: response.data.status } : t));
    } catch (error) {
      console.error('Failed to get task status:', error);
      alert('Failed to get task status');
    }
  };

  const handleCancelTask = async (taskId: string) => {
    try {
      await revokeTask(taskId);
      setTasks(tasks.map(t => t.id === taskId ? { ...t, status: 'REVOKED' } : t));
      alert('Task cancelled successfully');
    } catch (error) {
      console.error('Failed to cancel task:', error);
      alert('Failed to cancel task');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'SUCCESS':
        return 'bg-green-100 text-green-800';
      case 'FAILURE':
        return 'bg-red-100 text-red-800';
      case 'PENDING':
      case 'STARTED':
        return 'bg-yellow-100 text-yellow-800';
      case 'REVOKED':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-blue-100 text-blue-800';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Async Tasks</h1>
          <p className="mt-1 text-sm text-gray-500">
            Monitor and manage background task execution
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleSyncMetrics}
            disabled={syncing}
            className="btn btn-secondary flex items-center gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${syncing ? 'animate-spin' : ''}`} />
            {syncing ? 'Starting...' : 'Sync Metrics'}
          </button>
          <button
            onClick={handleGenerateReport}
            disabled={generating}
            className="btn btn-primary flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            {generating ? 'Starting...' : 'Generate Report'}
          </button>
        </div>
      </div>

      {/* Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card bg-blue-50 border-blue-200">
          <h3 className="text-sm font-medium text-blue-900 mb-1">Total Tasks</h3>
          <p className="text-3xl font-bold text-blue-700">{tasks.length}</p>
        </div>
        <div className="card bg-yellow-50 border-yellow-200">
          <h3 className="text-sm font-medium text-yellow-900 mb-1">Running</h3>
          <p className="text-3xl font-bold text-yellow-700">
            {tasks.filter(t => ['PENDING', 'STARTED'].includes(t.status)).length}
          </p>
        </div>
        <div className="card bg-green-50 border-green-200">
          <h3 className="text-sm font-medium text-green-900 mb-1">Completed</h3>
          <p className="text-3xl font-bold text-green-700">
            {tasks.filter(t => t.status === 'SUCCESS').length}
          </p>
        </div>
      </div>

      {/* Task Instructions */}
      <div className="card bg-primary-50 border-primary-200">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">How to use async tasks:</h2>
        <ol className="space-y-2 text-sm text-gray-700 list-decimal list-inside">
          <li>Click "Generate Report" or "Sync Metrics" to start a new background task</li>
          <li>The task will run asynchronously on the server using Celery</li>
          <li>Click "Check Status" to see the current state of a task</li>
          <li>Tasks can be in states: PENDING, STARTED, SUCCESS, FAILURE, or REVOKED</li>
          <li>You can cancel PENDING or STARTED tasks using the "Cancel" button</li>
        </ol>
      </div>

      {/* Tasks List */}
      <div className="card">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Recent Tasks</h2>
        
        {tasks.length === 0 ? (
          <div className="text-center py-12">
            <Play className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No tasks yet</h3>
            <p className="mt-1 text-sm text-gray-500">
              Start a report generation or metrics sync task to see it here
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {tasks.map((task) => (
              <div
                key={task.id}
                className="p-4 border border-gray-200 rounded-lg hover:border-primary-300 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <span className={`text-xs font-medium px-3 py-1 rounded-full ${getStatusColor(task.status)}`}>
                        {task.status}
                      </span>
                      <span className="text-sm font-medium text-gray-900">
                        {task.type === 'report' ? '📊 Report Generation' : '🔄 Metrics Sync'}
                      </span>
                    </div>
                    <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
                      <span>🆔 {task.id}</span>
                      <span>🕐 {task.createdAt.toLocaleTimeString()}</span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleCheckStatus(task.id)}
                      className="btn btn-secondary text-xs"
                    >
                      Check Status
                    </button>
                    {['PENDING', 'STARTED'].includes(task.status) && (
                      <button
                        onClick={() => handleCancelTask(task.id)}
                        className="btn text-xs bg-red-100 text-red-800 hover:bg-red-200"
                      >
                        <XCircle className="h-3 w-3 mr-1" />
                        Cancel
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Example cURL Commands */}
      <div className="card bg-gray-50 border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900 mb-3">API Examples</h2>
        <div className="space-y-3">
          <div>
            <p className="text-sm font-medium text-gray-700 mb-1">Generate Report:</p>
            <code className="block p-2 bg-gray-800 text-green-400 text-xs rounded overflow-x-auto">
              curl -X POST http://localhost:8000/tasks/reports/generate \<br />
              &nbsp;&nbsp;-H "Content-Type: application/json" \<br />
              &nbsp;&nbsp;-d '{"{"}"sprint_count": 5{"}"}'
            </code>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-700 mb-1">Check Task Status:</p>
            <code className="block p-2 bg-gray-800 text-green-400 text-xs rounded overflow-x-auto">
              curl http://localhost:8000/tasks/status/TASK_ID
            </code>
          </div>
        </div>
      </div>
    </div>
  );
}

