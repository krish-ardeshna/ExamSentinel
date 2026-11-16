import React, { useState, useEffect } from 'react';
import { dashboardApi } from '../services/api';
import Navbar from '../components/Navbar';
import { Users, BookOpen, CheckCircle, AlertTriangle } from 'lucide-react';

export default function ParentDashboard() {
  const [data, setData] = useState(null);
  const [selectedChildId, setSelectedChildId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadParentData(selectedChildId);
  }, [selectedChildId]);

  const loadParentData = async (childId) => {
    try {
      setLoading(true);
      const res = await dashboardApi.parent(childId);
      setData(res);
      if (!selectedChildId && res.selected_child) {
        setSelectedChildId(res.selected_child.student_id);
      }
    } catch (err) {
      setError(err.message || 'Failed to load parent dashboard');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !data) {
    return (
      <div>
        <Navbar />
        <div className="container" style={{ textAlign: 'center', padding: '3rem' }}>
          <p>Loading parent portal...</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <Navbar />
      <div className="container">
        {/* Welcome Header */}
        <div className="card" style={{ background: 'linear-gradient(135deg, #4338ca, #3730a3)', color: 'white' }}>
          <span style={{ fontSize: '0.8125rem', opacity: 0.9, textTransform: 'uppercase' }}>Parent Portal</span>
          <h1 style={{ fontSize: '1.5rem', fontWeight: '700' }}>Welcome, {data?.parent_name}!</h1>
          <p style={{ opacity: 0.9, fontSize: '0.875rem' }}>
            Academic Performance Monitoring for Linked Wards
          </p>
        </div>

        {error && (
          <div className="badge badge-danger" style={{ width: '100%', padding: '0.75rem', marginBottom: '1rem' }}>
            {error}
          </div>
        )}

        {/* Child Selector (if multiple children) */}
        {data?.children?.length > 1 && (
          <div className="card" style={{ padding: '1rem' }}>
            <label className="form-label">Select Ward / Child:</label>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              {data.children.map((c) => (
                <button
                  key={c.student_id}
                  onClick={() => setSelectedChildId(c.student_id)}
                  className={`btn btn-sm ${selectedChildId === c.student_id ? 'btn-primary' : 'btn-secondary'}`}
                >
                  {c.name} ({c.enrollment_no})
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Selected Child Results */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem' }}>
            <Users size={20} color="var(--primary)" />
            <h2 style={{ fontSize: '1.125rem', fontWeight: '700' }}>
              Academic Report: {data?.selected_child?.name} ({data?.selected_child?.enrollment_no})
            </h2>
          </div>

          {data?.selected_child?.results?.length === 0 ? (
            <p style={{ color: 'var(--text-muted)' }}>No published examination results yet for this student.</p>
          ) : (
            <div className="table-responsive">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Exam Title</th>
                    <th>Subject</th>
                    <th>Marks Obtained</th>
                    <th>Percentage</th>
                    <th>Status / Proctoring</th>
                    <th>Published On</th>
                  </tr>
                </thead>
                <tbody>
                  {data?.selected_child?.results?.map((res, idx) => (
                    <tr key={idx}>
                      <td style={{ fontWeight: '600' }}>{res.exam_title}</td>
                      <td>{res.subject_name}</td>
                      <td><strong>{res.score}</strong> / {res.total_marks}</td>
                      <td>{res.percentage}%</td>
                      <td>
                        {res.status === 'Terminated (violation)' ? (
                          <span className="badge badge-danger">Terminated (Violation)</span>
                        ) : (
                          <span className="badge badge-success">{res.status}</span>
                        )}
                      </td>
                      <td style={{ fontSize: '0.8125rem' }}>
                        {res.published_at ? new Date(res.published_at).toLocaleDateString() : 'Pending'}
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
