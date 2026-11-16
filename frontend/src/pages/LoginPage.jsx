import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, Lock, Mail, AlertCircle, Server } from 'lucide-react';
import { getApiBaseUrl, setApiBaseUrl } from '../services/api';

const DEMO_ACCOUNTS = [
  { role: 'Student', email: 'riya.student@oepms.edu', pass: 'Stud@1234', label: 'Student (Riya)' },
  { role: 'Teacher', email: 'rajesh.teacher@oepms.edu', pass: 'Teach@1234', label: 'Teacher (Rajesh)' },
  { role: 'Parent', email: 'suresh.parent@oepms.edu', pass: 'Parent@123', label: 'Parent (Suresh)' },
  { role: 'HOD', email: 'hod@oepms.edu', pass: 'Hod@12345', label: 'HOD (Dr. Kumar)' },
  { role: 'Admin', email: 'admin@oepms.edu', pass: 'Admin@1234', label: 'Admin (System)' },
];

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [apiUrl, setApiUrl] = useState(getApiBaseUrl());
  const [showConfig, setShowConfig] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const user = await login(email, password);
      switch (user.role) {
        case 'Student': navigate('/dashboard/student'); break;
        case 'Teacher': navigate('/dashboard/teacher'); break;
        case 'Parent': navigate('/dashboard/parent'); break;
        case 'HOD': navigate('/dashboard/hod'); break;
        case 'Admin': navigate('/dashboard/admin'); break;
        default: navigate('/login');
      }
    } catch (err) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const autofill = (acc) => {
    setEmail(acc.email);
    setPassword(acc.pass);
    setError('');
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem', background: 'linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%)' }}>
      <div style={{ maxWidth: '440px', width: '100%', background: 'white', borderRadius: '1rem', padding: '2rem', boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3)' }}>
        <div style={{ textAlign: 'center', marginBottom: '1.75rem' }}>
          <div style={{ display: 'inline-flex', padding: '0.75rem', background: '#dbeafe', borderRadius: '1rem', marginBottom: '0.75rem' }}>
            <ShieldCheck size={36} color="#1e40af" />
          </div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: '700', color: '#0f172a' }}>OEPMS Portal</h1>
          <p style={{ fontSize: '0.875rem', color: '#64748b' }}>Online Exam Proctoring & Management System</p>
        </div>

        {error && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: '#fee2e2', border: '1px solid #f87171', color: '#b91c1c', padding: '0.75rem', borderRadius: '0.5rem', fontSize: '0.875rem', marginBottom: '1.25rem' }}>
            <AlertCircle size={18} style={{ flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="email">Email Address</label>
            <div style={{ position: 'relative' }}>
              <input
                id="email"
                type="email"
                required
                className="form-input"
                style={{ paddingLeft: '2.5rem' }}
                placeholder="name@oepms.edu"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
              <Mail size={18} color="#94a3b8" style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)' }} />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="password">Password</label>
            <div style={{ position: 'relative' }}>
              <input
                id="password"
                type="password"
                required
                className="form-input"
                style={{ paddingLeft: '2.5rem' }}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <Lock size={18} color="#94a3b8" style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)' }} />
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', marginTop: '0.5rem', padding: '0.75rem' }}
            disabled={loading}
          >
            {loading ? 'Authenticating...' : 'Sign In to Dashboard'}
          </button>
        </form>

        <div style={{ marginTop: '1.75rem', paddingTop: '1.5rem', borderTop: '1px solid #e2e8f0' }}>
          <p style={{ fontSize: '0.75rem', fontWeight: '600', color: '#64748b', textTransform: 'uppercase', marginBottom: '0.75rem', textAlign: 'center' }}>
            Quick Demo Accounts (1-Click Fill)
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.5rem' }}>
            {DEMO_ACCOUNTS.map((acc) => (
              <button
                key={acc.role}
                type="button"
                onClick={() => autofill(acc)}
                className="btn btn-secondary btn-sm"
                style={{ fontSize: '0.75rem', justifyContent: 'center' }}
              >
                {acc.label}
              </button>
            ))}
          </div>

          <div style={{ marginTop: '1.25rem', textAlign: 'center' }}>
            <button
              type="button"
              onClick={() => setShowConfig(!showConfig)}
              style={{ background: 'none', border: 'none', color: '#64748b', fontSize: '0.75rem', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}
            >
              <Server size={12} /> {showConfig ? 'Hide API URL Settings' : 'Configure Backend API URL'}
            </button>

            {showConfig && (
              <div style={{ marginTop: '0.75rem', padding: '0.75rem', background: '#f8fafc', borderRadius: '0.5rem', textAlign: 'left' }}>
                <label style={{ fontSize: '0.75rem', fontWeight: '600', color: '#475569', display: 'block', marginBottom: '0.25rem' }}>
                  Backend Server Base URL:
                </label>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <input
                    type="text"
                    value={apiUrl}
                    onChange={(e) => setApiUrl(e.target.value)}
                    placeholder="http://localhost:8000"
                    style={{ flex: 1, padding: '0.4rem 0.5rem', fontSize: '0.75rem', border: '1px solid #cbd5e1', borderRadius: '0.375rem' }}
                  />
                  <button
                    type="button"
                    onClick={() => {
                      setApiBaseUrl(apiUrl);
                      setError('');
                      alert(`Backend URL updated to: ${apiUrl}`);
                    }}
                    className="btn btn-primary btn-sm"
                    style={{ fontSize: '0.75rem', padding: '0.4rem 0.75rem' }}
                  >
                    Save
                  </button>
                </div>
                <p style={{ fontSize: '0.7rem', color: '#94a3b8', marginTop: '0.35rem' }}>
                  For GitHub Pages, point this to your deployed backend (e.g., https://your-backend.onrender.com).
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
