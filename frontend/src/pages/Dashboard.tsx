import { AlertCircle, FileText, Plus, RefreshCw, TrendingUp, Zap } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { fetchMetrics, generateReportAsync, listReports, type ReportListItem } from '../services/api';

export default function Dashboard() {
  const [reports, setReports] = useState<ReportListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    try {
      setLoading(true);
      const response = await listReports(5);
      setReports(response.data);
    } catch (error) {
      console.error('Failed to load reports:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSyncMetrics = async () => {
    try {
      setSyncing(true);
      await fetchMetrics(10);
      alert('Metrics synced successfully!');
    } catch (error) {
      console.error('Failed to sync metrics:', error);
      alert('Failed to sync metrics. Please try again.');
    } finally {
      setSyncing(false);
    }
  };

  const handleGenerateReport = async () => {
    try {
      setGenerating(true);
      const response = await generateReportAsync({
        sprint_count: 5,
      });
      alert(`Report generation started! Task ID: ${response.data.task_id}`);
      // Reload reports after a delay
      setTimeout(() => loadReports(), 3000);
    } catch (error) {
      console.error('Failed to generate report:', error);
      alert('Failed to generate report. Please try again.');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="mt-1 text-sm text-gray-500">
            AI-powered retrospective insights for your team
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleSyncMetrics}
            disabled={syncing}
            className="btn btn-secondary flex items-center gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${syncing ? 'animate-spin' : ''}`} />
            {syncing ? 'Syncing...' : 'Sync Metrics'}
          </button>
          <button
            onClick={handleGenerateReport}
            disabled={generating}
            className="btn btn-primary flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            {generating ? 'Generating...' : 'Generate Report'}
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Reports</p>
              <p className="mt-2 text-3xl font-semibold text-gray-900">{reports.length}</p>
            </div>
            <FileText className="h-12 w-12 text-primary-600 opacity-20" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Trends Detected</p>
              <p className="mt-2 text-3xl font-semibold text-gray-900">24</p>
            </div>
            <TrendingUp className="h-12 w-12 text-green-600 opacity-20" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Active Hypotheses</p>
              <p className="mt-2 text-3xl font-semibold text-gray-900">8</p>
            </div>
            <AlertCircle className="h-12 w-12 text-yellow-600 opacity-20" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Experiments</p>
              <p className="mt-2 text-3xl font-semibold text-gray-900">12</p>
            </div>
            <Zap className="h-12 w-12 text-purple-600 opacity-20" />
          </div>
        </div>
      </div>

      {/* Recent Reports */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Recent Reports</h2>
          <Link to="/reports" className="text-sm text-primary-600 hover:text-primary-700 font-medium">
            View All →
          </Link>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            <p className="mt-2 text-sm text-gray-500">Loading reports...</p>
          </div>
        ) : reports.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No reports yet</h3>
            <p className="mt-1 text-sm text-gray-500">Get started by generating your first report</p>
            <button
              onClick={handleGenerateReport}
              className="mt-4 btn btn-primary"
            >
              Generate First Report
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {reports.map((report) => (
              <Link
                key={report.id}
                to={`/reports/${report.id}`}
                className="block p-4 border border-gray-200 rounded-lg hover:border-primary-500 hover:shadow-md transition-all"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="text-lg font-medium text-gray-900">{report.headline}</h3>
                    <p className="mt-1 text-sm text-gray-500">{report.summary}</p>
                    <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
                      <span>📊 {report.sprint_ids.length} sprints analyzed</span>
                      <span>📅 {new Date(report.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
                    View Report
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link to="/reports" className="card hover:shadow-lg transition-shadow">
          <FileText className="h-8 w-8 text-primary-600 mb-3" />
          <h3 className="text-lg font-medium text-gray-900">View All Reports</h3>
          <p className="mt-1 text-sm text-gray-500">
            Browse through all generated retrospective reports
          </p>
        </Link>

        <Link to="/tasks" className="card hover:shadow-lg transition-shadow">
          <Zap className="h-8 w-8 text-purple-600 mb-3" />
          <h3 className="text-lg font-medium text-gray-900">Monitor Tasks</h3>
          <p className="mt-1 text-sm text-gray-500">
            Track async report generation and metrics sync tasks
          </p>
        </Link>

        <div className="card hover:shadow-lg transition-shadow cursor-pointer" onClick={handleGenerateReport}>
          <Plus className="h-8 w-8 text-green-600 mb-3" />
          <h3 className="text-lg font-medium text-gray-900">Generate New Report</h3>
          <p className="mt-1 text-sm text-gray-500">
            Create a new retrospective insights report
          </p>
        </div>
      </div>
    </div>
  );
}

