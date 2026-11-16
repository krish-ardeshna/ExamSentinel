import React, { useState, useEffect } from 'react';
import { dashboardApi, examApi } from '../services/api';
import Navbar from '../components/Navbar';
import { Activity, FileText, RefreshCw, ShieldAlert, Users, Calendar, Filter } from 'lucide-react';

export default function HODDashboard() {
  const [activeTab, setActiveTab] = useState('monitor'); // 'monitor' | 'reports'

  // Monitor State
  const [monitorData, setMonitorData] = useState(null);
  const [monitorLoading, setMonitorLoading] = useState(true);
  const [lastRefreshed, setLastRefreshed] = useState(new Date());

  // Reports State
  const [reportsData, setReportsData] = useState(null);
  const [reportsLoading, setReportsLoading] = useState(false);
  const [subjects, setSubjects] = useState([]);
  const [filters, setFilters] = useState({
    subject_id: '',
    semester: '',
    start_date: '',
    end_date: '',
    page: 1,
    page_size: 15,
  });
  const [reportError, setReportError] = useState('');

  // Auto-refresh monitor every 30 seconds (UC-H1 requirement)
  useEffect(() => {
    loadMonitor();
    const interval = setInterval(() => {
      loadMonitor();
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    loadSubjects();
  }, []);

  useEffect(() => {
    if (activeTab === 'reports') {
      loadReports();
    }
  }, [activeTab, filters.page]);

  const loadSubjects = async () => {
    try {
      const subs = await examApi.listSubjects();
      setSubjects(subs);
    } catch (e) {
      console.error(e);
    }
  };

  const loadMonitor = async () => {
    try {
      setMonitorLoading(true);
      const res = await dashboardApi.hodMonitor();
      setMonitorData(res);
      setLastRefreshed(new Date());
    } catch (e) {
      console.error('Failed to load monitor data:', e);
    } finally {
      setMonitorLoading(false);
    }
  };

  const loadReports = async () => {
    try {
      setReportsLoading(true);
      setReportError('');
      const params = {
        page: filters.page,
        page_size: filters.page_size,
        ...(filters.subject_id ? { subject_id: filters.subject_id } : {}),
        ...(filters.semester ? { semester: filters.semester } : {}),
        ...(filters.start_date ? { start_date: filters.start_date } : {}),
        ...(filters.end_date ? { end_date: filters.end_date } : {}),
      };
      const res = await dashboardApi.hodReports(params);
      setReportsData(res);
    } catch (err) {
      setReportError(err.message || 'Failed to fetch reports');
    } finally {
      setReportsLoading(false);
    }
  };

  const handleApplyFilter = (e) => {
    e.preventDefault();
    setFilters((prev) => ({ ...prev, page: 1 }));
    loadReports();
  };

  return (
    <div>
      <Navbar />
      <div className="container">
        {/* Header */}
        <div className="card" style={{ background: 'linear-gradient(135deg, #047857, #065f46)', color: 'white' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <span style={{ fontSize: '0.8125rem', opacity: 0.9, textTransform: 'uppercase' }}>HOD Administration</span>
              <h1 style={{ fontSize: '1.5rem', fontWeight: '700' }}>{monitorData?.hod_name || 'Department Oversight'}</h1>
              <p style={{ opacity: 0.9, fontSize: '0.875rem' }}>{monitorData?.department || 'Computer Science & Engineering'}</p>
            </div>

            {/* Navigation Tabs */}
            <div style={{ display: 'flex', gap: '0.5rem', background: 'rgba(0,0,0,0.2)', padding: '0.375rem', borderRadius: '0.5rem' }}>
              <button
                onClick={() => setActiveTab('monitor')}
                className={`btn btn-sm ${activeTab === 'monitor' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ gap: '0.375rem' }}
              >
                <Activity size={16} /> Live Proctoring Monitor
              </button>
              <button
                onClick={() => setActiveTab('reports')}
                className={`btn btn-sm ${activeTab === 'reports' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ gap: '0.375rem' }}
              >
                <FileText size={16} /> All Results & Reports
              </button>
            </div>
          </div>
        </div>

        {/* Tab 1: Live Exam Monitor */}
        {activeTab === 'monitor' && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ width: '10px', height: '10px', background: '#22c55e', borderRadius: '50%', display: 'inline-block' }}></span>
                <span style={{ fontSize: '0.875rem', color: '#64748b' }}>
                  Live auto-refresh every 30s | Last updated: {lastRefreshed.toLocaleTimeString()}
                </span>
              </div>
              <button onClick={loadMonitor} className="btn btn-secondary btn-sm" style={{ gap: '0.375rem' }} disabled={monitorLoading}>
                <RefreshCw size={14} className={monitorLoading ? 'animate-spin' : ''} /> Refresh Now
              </button>
            </div>

            {monitorData?.active_exams?.length === 0 ? (
              <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
                <p style={{ color: 'var(--text-muted)' }}>No live exam sessions currently in progress.</p>
              </div>
            ) : (
              monitorData?.active_exams?.map((exam) => (
                <div key={exam.exam_id} className="card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.25rem', borderBottom: '1px solid #e2e8f0', paddingBottom: '0.75rem' }}>
                    <div>
                      <span className="badge badge-info">{exam.subject_name}</span>
                      <h3 style={{ fontSize: '1.25rem', fontWeight: '700', marginTop: '0.25rem' }}>{exam.title}</h3>
                      <p style={{ fontSize: '0.8125rem', color: '#64748b' }}>
                        Window: {new Date(exam.start_time).toLocaleTimeString()} - {new Date(exam.end_time).toLocaleTimeString()}
                      </p>
                    </div>

                    <div style={{ display: 'flex', gap: '1rem' }}>
                      <div style={{ textAlign: 'center', padding: '0.5rem 1rem', background: '#dbeafe', borderRadius: '0.5rem' }}>
                        <span style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#1e40af' }}>{exam.in_progress_count}</span>
                        <span style={{ display: 'block', fontSize: '0.75rem', color: '#1e40af' }}>In Progress</span>
                      </div>
                      <div style={{ textAlign: 'center', padding: '0.5rem 1rem', background: '#dcfce7', borderRadius: '0.5rem' }}>
                        <span style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#15803d' }}>{exam.submitted_count}</span>
                        <span style={{ display: 'block', fontSize: '0.75rem', color: '#15803d' }}>Submitted</span>
                      </div>
                      <div style={{ textAlign: 'center', padding: '0.5rem 1rem', background: '#fee2e2', borderRadius: '0.5rem' }}>
                        <span style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#b91c1c' }}>{exam.locked_count}</span>
                        <span style={{ display: 'block', fontSize: '0.75rem', color: '#b91c1c' }}>Auto-Locked</span>
                      </div>
                    </div>
                  </div>

                  {/* Violation Feed for this Exam */}
                  <div>
                    <h4 style={{ fontSize: '0.875rem', fontWeight: '700', color: '#334155', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                      <ShieldAlert size={16} color="#dc2626" /> Screen Violation Event Log
                    </h4>

                    {exam.recent_violations?.length === 0 ? (
                      <p style={{ fontSize: '0.8125rem', color: '#16a34a' }}>✓ Zero violations recorded for this exam session.</p>
                    ) : (
                      <div className="table-responsive">
                        <table className="data-table" style={{ fontSize: '0.8125rem' }}>
                          <thead>
                            <tr>
                              <th>Timestamp</th>
                              <th>Student</th>
                              <th>Violation Type</th>
                              <th>Automated Action</th>
                            </tr>
                          </thead>
                          <tbody>
                            {exam.recent_violations.map((v) => (
                              <tr key={v.log_id}>
                                <td>{new Date(v.occurred_at).toLocaleTimeString()}</td>
                                <td style={{ fontWeight: '600' }}>{v.student_name}</td>
                                <td>
                                  <span className="badge badge-danger">{v.type}</span>
                                </td>
                                <td>
                                  <span style={{ color: '#dc2626', fontWeight: '600' }}>
                                    Attempt Auto-Locked & Evaluated on Partial Answers
                                  </span>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Tab 2: All Results & Reports */}
        {activeTab === 'reports' && (
          <div>
            {/* Filter Bar */}
            <div className="card">
              <h3 style={{ fontSize: '1rem', fontWeight: '700', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Filter size={18} /> Department Reports & Filtering
              </h3>

              {reportError && (
                <div className="badge badge-danger" style={{ width: '100%', padding: '0.5rem', marginBottom: '1rem' }}>
                  {reportError}
                </div>
              )}

              <form onSubmit={handleApplyFilter} className="grid-4">
                <div className="form-group">
                  <label className="form-label">Subject</label>
                  <select
                    className="form-select"
                    value={filters.subject_id}
                    onChange={(e) => setFilters({ ...filters, subject_id: e.target.value })}
                  >
                    <option value="">All Subjects</option>
                    {subjects.map((s) => (
                      <option key={s.subject_id} value={s.subject_id}>{s.name} ({s.code})</option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Semester</label>
                  <input
                    type="number"
                    min="1"
                    max="8"
                    className="form-input"
                    placeholder="e.g. 5"
                    value={filters.semester}
                    onChange={(e) => setFilters({ ...filters, semester: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Start Date (YYYY-MM-DD)</label>
                  <input
                    type="date"
                    className="form-input"
                    value={filters.start_date}
                    onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">End Date (YYYY-MM-DD)</label>
                  <input
                    type="date"
                    className="form-input"
                    value={filters.end_date}
                    onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
                  />
                </div>

                <div style={{ gridColumn: 'span 4', textAlign: 'right' }}>
                  <button type="submit" className="btn btn-primary btn-sm">
                    Apply Filters
                  </button>
                </div>
              </form>
            </div>

            {/* Paginated Results Table */}
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3 style={{ fontSize: '1rem', fontWeight: '700' }}>
                  Assessment Outcomes ({reportsData?.total || 0} Records)
                </h3>
                <span style={{ fontSize: '0.8125rem', color: '#64748b' }}>
                  Page {reportsData?.page || 1}
                </span>
              </div>

              {reportsLoading ? (
                <p>Loading reports...</p>
              ) : reportsData?.items?.length === 0 ? (
                <p style={{ color: 'var(--text-muted)' }}>No records match the selected filters.</p>
              ) : (
                <div className="table-responsive">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Student</th>
                        <th>Enrollment No</th>
                        <th>Subject</th>
                        <th>Semester</th>
                        <th>Exam Title</th>
                        <th>Score</th>
                        <th>Percentage</th>
                        <th>Status</th>
                        <th>Published At</th>
                      </tr>
                    </thead>
                    <tbody>
                      {reportsData?.items?.map((item) => (
                        <tr key={item.result_id}>
                          <td style={{ fontWeight: '600' }}>{item.student_name}</td>
                          <td>{item.enrollment_no}</td>
                          <td>{item.subject_name}</td>
                          <td>Sem {item.semester}</td>
                          <td>{item.exam_title}</td>
                          <td><strong>{item.score}</strong> / {item.total_marks}</td>
                          <td>{item.percentage}%</td>
                          <td>
                            {item.status === 'Terminated (violation)' ? (
                              <span className="badge badge-danger">Terminated (violation)</span>
                            ) : (
                              <span className="badge badge-success">{item.status}</span>
                            )}
                          </td>
                          <td style={{ fontSize: '0.75rem' }}>
                            {item.published_at ? new Date(item.published_at).toLocaleString() : 'N/A'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Pagination controls */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1.25rem' }}>
                <button
                  onClick={() => setFilters({ ...filters, page: Math.max(1, filters.page - 1) })}
                  disabled={filters.page === 1}
                  className="btn btn-secondary btn-sm"
                >
                  Previous Page
                </button>
                <span style={{ fontSize: '0.8125rem', color: '#64748b' }}>
                  Page {filters.page} of {Math.ceil((reportsData?.total || 1) / (filters.page_size || 15))}
                </span>
                <button
                  onClick={() => setFilters({ ...filters, page: filters.page + 1 })}
                  disabled={filters.page * filters.page_size >= (reportsData?.total || 0)}
                  className="btn btn-secondary btn-sm"
                >
                  Next Page
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
