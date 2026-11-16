import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { dashboardApi } from '../services/api';
import Navbar from '../components/Navbar';
import { BookOpen, PlusCircle, Users, AlertTriangle, CheckCircle, BarChart3 } from 'lucide-react';

export default function TeacherDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedSubjectId, setSelectedSubjectId] = useState('');

  useEffect(() => {
    loadDashboard();
  }, [selectedSubjectId]);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const res = await dashboardApi.teacher(selectedSubjectId ? parseInt(selectedSubjectId) : null);
      setData(res);
    } catch (err) {
      setError(err.message || 'Failed to load teacher dashboard');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !data) {
    return (
      <div>
        <Navbar />
        <div className="container" style={{ textAlign: 'center', padding: '3rem' }}>
          <p>Loading teacher dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <Navbar />
      <div className="container">
        {/* Welcome Header */}
        <div className="card" style={{ background: 'linear-gradient(135deg, #0d9488, #0f766e)', color: 'white' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <span style={{ fontSize: '0.8125rem', opacity: 0.9, textTransform: 'uppercase' }}>Faculty Portal</span>
              <h1 style={{ fontSize: '1.5rem', fontWeight: '700' }}>{data?.teacher_name}</h1>
              <p style={{ opacity: 0.9, fontSize: '0.875rem' }}>Department: {data?.department || 'CSE'}</p>
            </div>
            <Link to="/teacher/exam/new" className="btn btn-primary" style={{ background: '#fff', color: '#0f766e', gap: '0.5rem' }}>
              <PlusCircle size={18} /> Schedule New Exam
            </Link>
          </div>
        </div>

        {error && (
          <div className="badge badge-danger" style={{ width: '100%', padding: '0.75rem', marginBottom: '1rem' }}>
            {error}
          </div>
        )}

        {/* Subjects & Exams List */}
        {data?.subjects?.map((sub) => (
          <div key={sub.subject_id} className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', borderBottom: '1px solid #e2e8f0', paddingBottom: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <BookOpen size={20} color="var(--primary)" />
                <h2 style={{ fontSize: '1.125rem', fontWeight: '700' }}>
                  {sub.name} ({sub.code})
                </h2>
                <span className="badge badge-info">Semester {sub.semester}</span>
              </div>
              <Link to={`/teacher/exam/new?subject_id=${sub.subject_id}`} className="btn btn-secondary btn-sm" style={{ gap: '0.375rem' }}>
                <PlusCircle size={14} /> Add Exam
              </Link>
            </div>

            {sub.exams?.length === 0 ? (
              <p style={{ color: 'var(--text-muted)' }}>No exams scheduled for this subject yet.</p>
            ) : (
              <div className="table-responsive">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Exam Title</th>
                      <th>Status</th>
                      <th>Scheduled Window</th>
                      <th>Total Marks</th>
                      <th>Total Attempts</th>
                      <th>Auto-Locked (Violations)</th>
                      <th>Average Score</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sub.exams.map((ex) => (
                      <tr key={ex.exam_id}>
                        <td style={{ fontWeight: '600' }}>{ex.title}</td>
                        <td>
                          <span className={`badge ${
                            ex.status === 'Published' ? 'badge-success' :
                            ex.status === 'Draft' ? 'badge-warning' : 'badge-info'
                          }`}>
                            {ex.status}
                          </span>
                        </td>
                        <td style={{ fontSize: '0.8125rem' }}>
                          {new Date(ex.start_time).toLocaleString()} - {new Date(ex.end_time).toLocaleTimeString()}
                        </td>
                        <td>{ex.total_marks}</td>
                        <td><strong>{ex.total_attempts}</strong></td>
                        <td>
                          {ex.locked_attempts > 0 ? (
                            <span className="badge badge-danger">
                              {ex.locked_attempts} ({ex.violations_count} events)
                            </span>
                          ) : (
                            <span style={{ color: '#16a34a' }}>0</span>
                          )}
                        </td>
                        <td>
                          <strong>{ex.average_score}</strong> / {ex.total_marks}
                        </td>
                        <td>
                          <Link
                            to={`/teacher/exam/${ex.exam_id}`}
                            className="btn btn-secondary btn-sm"
                          >
                            Manage Paper
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
