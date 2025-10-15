import { FileText, Search, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { deleteReport, listReports, type ReportListItem } from '../services/api';

export default function ReportsPage() {
  const [reports, setReports] = useState<ReportListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    try {
      setLoading(true);
      const response = await listReports(50);
      setReports(response.data);
    } catch (error) {
      console.error('Failed to load reports:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number, event: React.MouseEvent) => {
    event.preventDefault();
    event.stopPropagation();
    
    if (!confirm('Are you sure you want to delete this report?')) {
      return;
    }

    try {
      await deleteReport(id);
      setReports(reports.filter(r => r.id !== id));
    } catch (error) {
      console.error('Failed to delete report:', error);
      alert('Failed to delete report. Please try again.');
    }
  };

  const filteredReports = reports.filter(report =>
    report.headline.toLowerCase().includes(searchTerm.toLowerCase()) ||
    report.summary.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Reports</h1>
          <p className="mt-1 text-sm text-gray-500">
            Browse and manage all retrospective reports
          </p>
        </div>
      </div>

      {/* Search */}
      <div className="card">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search reports..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Reports List */}
      {loading ? (
        <div className="card text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <p className="mt-2 text-sm text-gray-500">Loading reports...</p>
        </div>
      ) : filteredReports.length === 0 ? (
        <div className="card text-center py-12">
          <FileText className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">
            {searchTerm ? 'No reports found' : 'No reports yet'}
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            {searchTerm
              ? 'Try adjusting your search terms'
              : 'Get started by generating your first report'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {filteredReports.map((report) => (
            <Link
              key={report.id}
              to={`/reports/${report.id}`}
              className="card hover:shadow-lg transition-all group"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <FileText className="h-6 w-6 text-primary-600" />
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 group-hover:text-primary-600 transition-colors">
                        {report.headline}
                      </h3>
                      <p className="mt-1 text-sm text-gray-600">{report.summary}</p>
                    </div>
                  </div>

                  <div className="mt-4 flex items-center gap-4 text-xs text-gray-500">
                    <span className="inline-flex items-center gap-1">
                      📊 <strong>{report.sprint_ids.length}</strong> sprints
                    </span>
                    <span className="inline-flex items-center gap-1">
                      📅 {new Date(report.report_date).toLocaleDateString()}
                    </span>
                    <span className="inline-flex items-center gap-1">
                      🆔 ID: {report.id}
                    </span>
                  </div>
                </div>

                <button
                  onClick={(e) => handleDelete(report.id, e)}
                  className="ml-4 p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
                  title="Delete report"
                >
                  <Trash2 className="h-5 w-5" />
                </button>
              </div>
            </Link>
          ))}
        </div>
      )}

      {/* Stats */}
      <div className="card bg-primary-50 border-primary-200">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-primary-900">Total Reports</p>
            <p className="mt-1 text-2xl font-bold text-primary-700">{reports.length}</p>
          </div>
          {searchTerm && (
            <div>
              <p className="text-sm font-medium text-primary-900">Filtered Results</p>
              <p className="mt-1 text-2xl font-bold text-primary-700">{filteredReports.length}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

