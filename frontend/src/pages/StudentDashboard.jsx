import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { dashboardApi, attemptApi } from '../services/api';
import Navbar from '../components/Navbar';
import { BookOpen, CheckCircle, Clock, AlertTriangle, ArrowRight, Sparkles } from 'lucide-react';

export default function StudentDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [startingExamId, setStartingExamId] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const res = await dashboardApi.student();
      setData(res);
    } catch (err) {
      setError(err.message || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleStartExam = async (examId) => {
    try {
      setStartingExamId(examId);
      const res = await attemptApi.start(examId);
      navigate(`/exam/${res.attempt_id}`);
    } catch (err) {
      alert(`Cannot start exam: ${err.message}`);
    } finally {
      setStartingExamId(null);
    }
  };

  if (loading) {
    return (
      <div>
        <Navbar />
        <div className="container" style={{ textAlign: 'center', padding: '3rem' }}>
          <p>Loading student portal...</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <Navbar />
      <div className="container">
        {error && (
          <div className="badge badge-danger" style={{ width: '100%', padding: '0.75rem', marginBottom: '1rem' }}>
            {error}
          </div>
        )}

        {/* Student Welcome Banner */}
        <div className="card" style={{ background: 'linear-gradient(135deg, #1e3a8a, #2563eb)', color: 'white' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <h1 style={{ fontSize: '1.5rem', fontWeight: '700' }}>Welcome, {data?.student_info?.name}!</h1>
              <p style={{ opacity: 0.9, fontSize: '0.875rem' }}>
                Enrollment: {data?.student_info?.enrollment_no} | Program: {data?.student_info?.program} (Sem {data?.student_info?.semester})
              </p>
            </div>
            <div style={{ display: 'flex', gap: '1rem' }}>
              <div style={{ background: 'rgba(255,255,255,0.15)', padding: '0.75rem 1.25rem', borderRadius: '0.5rem', textAlign: 'center' }}>
                <span style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>{data?.results?.length || 0}</span>
                <span style={{ display: 'block', fontSize: '0.75rem', opacity: 0.9 }}>Exams Completed</span>
              </div>
            </div>
          </div>
        </div>

        {/* Active & Upcoming Exams Section */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <Clock size={20} color="var(--primary)" />
            <h2 style={{ fontSize: '1.125rem', fontWeight: '700' }}>Available & Scheduled Exams</h2>
          </div>

          {data?.upcoming_exams?.length === 0 ? (
            <p style={{ color: 'var(--text-muted)' }}>No exams scheduled currently.</p>
          ) : (
            <div className="grid-2">
              {data?.upcoming_exams?.map((exam) => (
                <div
                  key={exam.exam_id}
                  style={{
                    border: '1px solid var(--border)',
                    borderRadius: '0.5rem',
                    padding: '1.25rem',
                    background: exam.is_active ? '#f0fdf4' : '#fff',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <span className="badge badge-info">{exam.subject_name}</span>
                      {exam.is_active && <span className="badge badge-success">Active Now</span>}
                      {exam.is_upcoming && <span className="badge badge-warning">Upcoming</span>}
                    </div>
                    <h3 style={{ fontSize: '1rem', fontWeight: '600', marginBottom: '0.5rem' }}>{exam.title}</h3>
                    <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>
                      Duration: {exam.duration_min} mins | Total Marks: {exam.total_marks}
                    </p>
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      Window: {new Date(exam.start_time).toLocaleString()} - {new Date(exam.end_time).toLocaleString()}
                    </p>
                  </div>

                  <div style={{ marginTop: '1rem' }}>
                    {exam.already_attempted ? (
                      <span className="badge badge-info">Already Attempted</span>
                    ) : exam.is_active ? (
                      <button
                        onClick={() => handleStartExam(exam.exam_id)}
                        className="btn btn-success btn-sm"
                        style={{ width: '100%' }}
                        disabled={startingExamId === exam.exam_id}
                      >
                        {startingExamId === exam.exam_id ? 'Launching...' : 'Start Exam (Proctored)'}
                      </button>
                    ) : (
                      <button className="btn btn-secondary btn-sm" disabled style={{ width: '100%' }}>
                        Starts at scheduled time
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Results & AI Concept Help Section */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <CheckCircle size={20} color="var(--success)" />
            <h2 style={{ fontSize: '1.125rem', fontWeight: '700' }}>Published Results & AI Concept Help</h2>
          </div>

          {data?.results?.length === 0 ? (
            <p style={{ color: 'var(--text-muted)' }}>No published results yet.</p>
          ) : (
            <div className="table-responsive">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Exam Title</th>
                    <th>Subject</th>
                    <th>Score</th>
                    <th>Percentage</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {data?.results?.map((res) => (
                    <tr key={res.attempt_id}>
                      <td style={{ fontWeight: '600' }}>{res.exam_title}</td>
                      <td>{res.subject_name}</td>
                      <td><strong>{res.score}</strong> / {res.total_marks}</td>
                      <td>{res.percentage}%</td>
                      <td>
                        {res.status === 'Terminated (violation)' ? (
                          <span className="badge badge-danger" title="Attempt was auto-locked due to a proctoring violation">
                            Terminated (violation)
                          </span>
                        ) : (
                          <span className="badge badge-success">{res.status}</span>
                        )}
                      </td>
                      <td>
                        <Link
                          to={`/results/${res.attempt_id}`}
                          className="btn btn-primary btn-sm"
                          style={{ gap: '0.375rem' }}
                        >
                          <Sparkles size={14} />
                          Review & AI Help
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
