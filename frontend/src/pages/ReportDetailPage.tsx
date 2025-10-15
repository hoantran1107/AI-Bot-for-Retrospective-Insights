import { ArrowLeft, Flask, Lightbulb, Minus, TrendingDown, TrendingUp } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { getReportById, type ExperimentSuggestion, type Hypothesis, type RetrospectiveReport } from '../services/api';

export default function ReportDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [report, setReport] = useState<RetrospectiveReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      loadReport(parseInt(id));
    }
  }, [id]);

  const loadReport = async (reportId: number) => {
    try {
      setLoading(true);
      setError(null);
      const response = await getReportById(reportId);
      setReport(response.data);
    } catch (err: any) {
      console.error('Failed to load report:', err);
      setError(err.response?.data?.detail || 'Failed to load report');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="card text-center py-12">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        <p className="mt-2 text-sm text-gray-500">Loading report...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card text-center py-12">
        <div className="text-red-600 mb-4">
          <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900">Error Loading Report</h3>
        <p className="mt-1 text-sm text-gray-500">{error}</p>
        <Link to="/reports" className="mt-4 inline-block btn btn-primary">
          Back to Reports
        </Link>
      </div>
    );
  }

  if (!report) {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <Link to="/reports" className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700">
        <ArrowLeft className="h-4 w-4 mr-1" />
        Back to Reports
      </Link>

      {/* Header */}
      <div className="card">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-primary-100 text-primary-800 mb-3">
              {report.confidence_overall} Confidence
            </span>
            <h1 className="text-3xl font-bold text-gray-900">{report.headline}</h1>
            <p className="mt-2 text-lg text-gray-600">{report.summary}</p>
            <div className="mt-4 flex items-center gap-4 text-sm text-gray-500">
              <span>📊 {report.sprints_analyzed} sprints analyzed</span>
              <span>📅 {report.sprint_period}</span>
              <span>🕐 {new Date(report.generated_at).toLocaleString()}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Trends */}
      <div className="card">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">📈 Key Trends</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {report.trends.map((trend, index) => (
            <div key={index} className="p-4 border border-gray-200 rounded-lg">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-600">{trend.metric_name}</p>
                  <div className="mt-2 flex items-center gap-2">
                    {trend.direction === 'up' && <TrendingUp className="h-5 w-5 text-green-600" />}
                    {trend.direction === 'down' && <TrendingDown className="h-5 w-5 text-red-600" />}
                    {trend.direction === 'stable' && <Minus className="h-5 w-5 text-gray-600" />}
                    <span className="text-2xl font-bold text-gray-900">
                      {trend.change_percent > 0 ? '+' : ''}{trend.change_percent.toFixed(1)}%
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-gray-500">
                    {trend.previous_value.toFixed(1)} → {trend.current_value.toFixed(1)}
                  </p>
                </div>
                <span className={`text-xs font-medium px-2 py-1 rounded ${
                  trend.significance === 'high' ? 'bg-red-100 text-red-800' :
                  trend.significance === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {trend.significance}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Charts */}
      {report.charts && report.charts.length > 0 && (
        <div className="card">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">📊 Visual Analytics</h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {report.charts.slice(0, 4).map((chart, index) => (
              <div key={index} className="p-4 border border-gray-200 rounded-lg">
                <h3 className="text-lg font-medium text-gray-900 mb-4">{chart.title}</h3>
                <ResponsiveContainer width="100%" height={250}>
                  {chart.chart_type === 'line' ? (
                    <LineChart data={chart.data}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="sprint" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Line type="monotone" dataKey="value" stroke="#0ea5e9" strokeWidth={2} />
                    </LineChart>
                  ) : (
                    <BarChart data={chart.data}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="value" fill="#0ea5e9" />
                    </BarChart>
                  )}
                </ResponsiveContainer>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Hypotheses */}
      <div className="card">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">💡 Hypotheses</h2>
        <div className="space-y-4">
          {report.hypotheses.map((hypothesis: Hypothesis, index) => (
            <div key={index} className="p-6 border-2 border-primary-200 rounded-lg bg-primary-50">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Lightbulb className="h-6 w-6 text-primary-600" />
                  <h3 className="text-xl font-semibold text-gray-900">{hypothesis.title}</h3>
                </div>
                <span className={`text-xs font-medium px-3 py-1 rounded-full ${
                  hypothesis.confidence === 'High' ? 'bg-green-100 text-green-800' :
                  hypothesis.confidence === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {hypothesis.confidence} ({(hypothesis.confidence_score * 100).toFixed(0)}%)
                </span>
              </div>
              <p className="text-gray-700 mb-4">{hypothesis.description}</p>
              
              <div className="mb-4">
                <p className="text-sm font-medium text-gray-900 mb-2">Potential Impact:</p>
                <p className="text-sm text-gray-600">{hypothesis.potential_impact}</p>
              </div>

              <div className="mb-4">
                <p className="text-sm font-medium text-gray-900 mb-2">Affected Metrics:</p>
                <div className="flex flex-wrap gap-2">
                  {hypothesis.affected_metrics.map((metric, i) => (
                    <span key={i} className="text-xs px-2 py-1 bg-white border border-primary-200 rounded">
                      {metric}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <p className="text-sm font-medium text-gray-900 mb-2">Evidence:</p>
                <ul className="space-y-1">
                  {hypothesis.evidence.map((ev, i) => (
                    <li key={i} className="text-sm text-gray-600 flex items-start gap-2">
                      <span className="text-primary-600 font-bold">•</span>
                      <span>{ev.metric_name}: {ev.trend} ({ev.value})</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Suggested Experiments */}
      <div className="card">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">🧪 Suggested Experiments</h2>
        <div className="space-y-4">
          {report.suggested_experiments.map((experiment: ExperimentSuggestion, index) => (
            <div key={index} className="p-6 border-2 border-purple-200 rounded-lg bg-purple-50">
              <div className="flex items-start gap-3 mb-3">
                <Flask className="h-6 w-6 text-purple-600 flex-shrink-0 mt-1" />
                <div className="flex-1">
                  <h3 className="text-xl font-semibold text-gray-900">{experiment.title}</h3>
                  <p className="mt-2 text-gray-700">{experiment.description}</p>
                </div>
                <span className="text-xs font-medium px-3 py-1 rounded-full bg-purple-200 text-purple-800">
                  {experiment.duration_sprints} sprint{experiment.duration_sprints > 1 ? 's' : ''}
                </span>
              </div>

              <div className="mb-4">
                <p className="text-sm font-medium text-gray-900 mb-2">Rationale:</p>
                <p className="text-sm text-gray-600">{experiment.rationale}</p>
              </div>

              <div className="mb-4">
                <p className="text-sm font-medium text-gray-900 mb-2">Implementation Steps:</p>
                <ol className="space-y-1 list-decimal list-inside">
                  {experiment.implementation_steps.map((step, i) => (
                    <li key={i} className="text-sm text-gray-600">{step}</li>
                  ))}
                </ol>
              </div>

              <div className="mb-4">
                <p className="text-sm font-medium text-gray-900 mb-2">Success Metrics:</p>
                <div className="flex flex-wrap gap-2">
                  {experiment.success_metrics.map((metric, i) => (
                    <span key={i} className="text-xs px-2 py-1 bg-white border border-purple-200 rounded">
                      {metric}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <p className="text-sm font-medium text-gray-900 mb-2">Expected Outcome:</p>
                <p className="text-sm text-gray-600">{experiment.expected_outcome}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Facilitation Guide */}
      <div className="card bg-green-50 border-green-200">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">🎯 Facilitation Guide</h2>
        
        <div className="space-y-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Key Questions for Retrospective:</h3>
            <ul className="space-y-2">
              {report.facilitation_guide.retro_questions.map((question, i) => (
                <li key={i} className="text-gray-700 flex items-start gap-2">
                  <span className="text-green-600 font-bold">?</span>
                  <span>{question}</span>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">15-Minute Agenda:</h3>
            <ol className="space-y-2 list-decimal list-inside">
              {report.facilitation_guide.agenda_15min.map((item, i) => (
                <li key={i} className="text-gray-700">{item}</li>
              ))}
            </ol>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Focus Areas:</h3>
            <div className="flex flex-wrap gap-2">
              {report.facilitation_guide.focus_areas.map((area, i) => (
                <span key={i} className="px-3 py-1 bg-green-200 text-green-800 rounded-full text-sm font-medium">
                  {area}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

