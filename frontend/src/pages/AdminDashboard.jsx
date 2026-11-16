import React, { useState, useEffect } from 'react';
import { dashboardApi, userApi, settingsApi } from '../services/api';
import Navbar from '../components/Navbar';
import { Users, Settings, UserPlus, Trash2, Ban, CheckCircle, AlertCircle, Shield } from 'lucide-react';

export default function AdminDashboard() {
  const [activeTab, setActiveTab] = useState('users'); // 'users' | 'settings'

  // Overview Stats
  const [stats, setStats] = useState(null);

  // Users Management
  const [users, setUsers] = useState([]);
  const [usersLoading, setUsersLoading] = useState(false);
  const [userModalOpen, setUserModalOpen] = useState(false);
  const [newUser, setNewUser] = useState({
    name: '',
    email: '',
    password: '',
    role: 'Student',
    status: 'Active',
  });

  // Settings
  const [settingsList, setSettingsList] = useState([]);
  const [aiLimit, setAiLimit] = useState('10');
  const [maxDuration, setMaxDuration] = useState('180');

  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    loadAdminStats();
    loadUsers();
    loadSettings();
  }, []);

  const loadAdminStats = async () => {
    try {
      const data = await dashboardApi.admin();
      setStats(data.stats);
    } catch (e) {
      console.error(e);
    }
  };

  const loadUsers = async () => {
    try {
      setUsersLoading(true);
      const data = await userApi.list();
      setUsers(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setUsersLoading(false);
    }
  };

  const loadSettings = async () => {
    try {
      const data = await settingsApi.get();
      setSettingsList(data);
      const ai = data.find((s) => s.key === 'AI_HELP_DAILY_LIMIT');
      if (ai) setAiLimit(ai.value);
      const dur = data.find((s) => s.key === 'MAX_EXAM_DURATION_MIN');
      if (dur) setMaxDuration(dur.value);
    } catch (e) {
      console.error(e);
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    try {
      await userApi.create(newUser);
      setSuccess(`User account created for ${newUser.name} (${newUser.role})`);
      setUserModalOpen(false);
      setNewUser({ name: '', email: '', password: '', role: 'Student', status: 'Active' });
      loadUsers();
      loadAdminStats();
    } catch (err) {
      setError(err.message || 'Failed to create user');
    }
  };

  const handleToggleStatus = async (user) => {
    setError('');
    setSuccess('');
    const newStatus = user.status === 'Active' ? 'Suspended' : 'Active';
    try {
      await userApi.update(user.user_id, { status: newStatus });
      setSuccess(`User ${user.name} status updated to ${newStatus}`);
      loadUsers();
    } catch (err) {
      setError(err.message || 'Status update failed');
    }
  };

  const handleDeleteUser = async (userId, name) => {
    if (!window.confirm(`Are you sure you want to delete user ${name}?`)) return;
    setError('');
    setSuccess('');
    try {
      await userApi.delete(userId);
      setSuccess(`User ${name} deleted successfully`);
      loadUsers();
      loadAdminStats();
    } catch (err) {
      setError(err.message || 'Failed to delete user');
    }
  };

  const handleSaveSetting = async (key, val) => {
    setError('');
    setSuccess('');
    try {
      await settingsApi.update(key, val);
      setSuccess(`Platform setting ${key} updated to ${val}`);
      loadSettings();
    } catch (err) {
      setError(err.message || 'Setting update failed');
    }
  };

  return (
    <div>
      <Navbar />
      <div className="container">
        {/* Admin Banner */}
        <div className="card" style={{ background: 'linear-gradient(135deg, #0f172a, #1e293b)', color: 'white' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <span style={{ fontSize: '0.8125rem', opacity: 0.9, textTransform: 'uppercase' }}>Administrator Console</span>
              <h1 style={{ fontSize: '1.5rem', fontWeight: '700' }}>Platform Configuration & Governance</h1>
              <p style={{ opacity: 0.8, fontSize: '0.875rem' }}>System-wide user lifecycle, proctoring security, and AI limit policies</p>
            </div>

            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                onClick={() => setActiveTab('users')}
                className={`btn btn-sm ${activeTab === 'users' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ gap: '0.375rem' }}
              >
                <Users size={16} /> User Management
              </button>
              <button
                onClick={() => setActiveTab('settings')}
                className={`btn btn-sm ${activeTab === 'settings' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ gap: '0.375rem' }}
              >
                <Settings size={16} /> Platform Settings
              </button>
            </div>
          </div>
        </div>

        {error && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: '#fee2e2', border: '1px solid #f87171', color: '#b91c1c', padding: '0.75rem', borderRadius: '0.5rem', marginBottom: '1rem', fontSize: '0.875rem' }}>
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: '#dcfce7', border: '1px solid #86efac', color: '#15803d', padding: '0.75rem', borderRadius: '0.5rem', marginBottom: '1rem', fontSize: '0.875rem' }}>
            <CheckCircle size={18} />
            <span>{success}</span>
          </div>
        )}

        {/* Stats Grid */}
        {stats && (
          <div className="grid-4" style={{ marginBottom: '1.5rem' }}>
            <div className="card" style={{ marginBottom: 0, padding: '1rem' }}>
              <span style={{ fontSize: '0.75rem', color: '#64748b', textTransform: 'uppercase' }}>Total Users</span>
              <h3 style={{ fontSize: '1.5rem', fontWeight: '800' }}>{stats.total_users}</h3>
            </div>
            <div className="card" style={{ marginBottom: 0, padding: '1rem' }}>
              <span style={{ fontSize: '0.75rem', color: '#64748b', textTransform: 'uppercase' }}>Total Exams</span>
              <h3 style={{ fontSize: '1.5rem', fontWeight: '800' }}>{stats.total_exams}</h3>
            </div>
            <div className="card" style={{ marginBottom: 0, padding: '1rem' }}>
              <span style={{ fontSize: '0.75rem', color: '#64748b', textTransform: 'uppercase' }}>Exam Attempts</span>
              <h3 style={{ fontSize: '1.5rem', fontWeight: '800' }}>{stats.total_attempts}</h3>
            </div>
            <div className="card" style={{ marginBottom: 0, padding: '1rem' }}>
              <span style={{ fontSize: '0.75rem', color: '#dc2626', textTransform: 'uppercase' }}>Flagged Violations</span>
              <h3 style={{ fontSize: '1.5rem', fontWeight: '800', color: '#dc2626' }}>{stats.flagged_attempts}</h3>
            </div>
          </div>
        )}

        {/* Tab 1: User Management */}
        {activeTab === 'users' && (
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <h2 style={{ fontSize: '1.125rem', fontWeight: '700' }}>System Users & Role Directory</h2>
              <button onClick={() => setUserModalOpen(true)} className="btn btn-primary btn-sm" style={{ gap: '0.375rem' }}>
                <UserPlus size={16} /> Add New User
              </button>
            </div>

            {usersLoading ? (
              <p>Loading user list...</p>
            ) : (
              <div className="table-responsive">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>User ID</th>
                      <th>Name</th>
                      <th>Email</th>
                      <th>Role</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((u) => (
                      <tr key={u.user_id}>
                        <td>#{u.user_id}</td>
                        <td style={{ fontWeight: '600' }}>{u.name}</td>
                        <td>{u.email}</td>
                        <td>
                          <span className="badge badge-info">{u.role}</span>
                        </td>
                        <td>
                          <span className={`badge ${u.status === 'Active' ? 'badge-success' : 'badge-danger'}`}>
                            {u.status}
                          </span>
                        </td>
                        <td>
                          <div style={{ display: 'flex', gap: '0.5rem' }}>
                            <button
                              onClick={() => handleToggleStatus(u)}
                              className={`btn btn-sm ${u.status === 'Active' ? 'btn-secondary' : 'btn-success'}`}
                              title={u.status === 'Active' ? 'Suspend Account' : 'Activate Account'}
                            >
                              <Ban size={14} />
                              {u.status === 'Active' ? 'Suspend' : 'Activate'}
                            </button>
                            <button
                              onClick={() => handleDeleteUser(u.user_id, u.name)}
                              className="btn btn-danger btn-sm"
                              title="Delete Account"
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Platform Settings */}
        {activeTab === 'settings' && (
          <div className="card">
            <h2 style={{ fontSize: '1.125rem', fontWeight: '700', marginBottom: '1.25rem' }}>
              Platform Parameters & Guardrails (UC-A2)
            </h2>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '600px' }}>
              <div style={{ border: '1px solid var(--border)', borderRadius: '0.5rem', padding: '1.25rem' }}>
                <h4 style={{ fontWeight: '700', marginBottom: '0.25rem' }}>Daily AI Concept Help Limit (per Student)</h4>
                <p style={{ fontSize: '0.8125rem', color: '#64748b', marginBottom: '1rem' }}>
                  Maximum number of plain-language concept explanations a student can request per calendar day.
                </p>
                <div style={{ display: 'flex', gap: '0.75rem' }}>
                  <input
                    type="number"
                    min="1"
                    className="form-input"
                    style={{ maxWidth: '120px' }}
                    value={aiLimit}
                    onChange={(e) => setAiLimit(e.target.value)}
                  />
                  <button onClick={() => handleSaveSetting('AI_HELP_DAILY_LIMIT', aiLimit)} className="btn btn-primary btn-sm">
                    Save Parameter
                  </button>
                </div>
              </div>

              <div style={{ border: '1px solid var(--border)', borderRadius: '0.5rem', padding: '1.25rem' }}>
                <h4 style={{ fontWeight: '700', marginBottom: '0.25rem' }}>Maximum Exam Duration</h4>
                <p style={{ fontSize: '0.8125rem', color: '#64748b', marginBottom: '1rem' }}>
                  Upper limit in minutes that teachers can set when scheduling an exam (default 180 min).
                </p>
                <div style={{ display: 'flex', gap: '0.75rem' }}>
                  <input
                    type="number"
                    min="1"
                    max="180"
                    className="form-input"
                    style={{ maxWidth: '120px' }}
                    value={maxDuration}
                    onChange={(e) => setMaxDuration(e.target.value)}
                  />
                  <button onClick={() => handleSaveSetting('MAX_EXAM_DURATION_MIN', maxDuration)} className="btn btn-primary btn-sm">
                    Save Parameter
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Modal: Add User */}
        {userModalOpen && (
          <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999, padding: '1rem' }}>
            <div style={{ background: '#fff', borderRadius: '1rem', maxWidth: '480px', width: '100%', padding: '1.75rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', borderBottom: '1px solid #e2e8f0', paddingBottom: '0.75rem' }}>
                <h3 style={{ fontSize: '1.25rem', fontWeight: '700' }}>Create User Account</h3>
                <button onClick={() => setUserModalOpen(false)} style={{ background: 'transparent', border: 'none', fontSize: '1.25rem', cursor: 'pointer' }}>✕</button>
              </div>

              <form onSubmit={handleCreateUser}>
                <div className="form-group">
                  <label className="form-label">Full Name (Letters and spaces only, 2-100 chars)</label>
                  <input
                    type="text"
                    required
                    className="form-input"
                    placeholder="e.g. Riya Sharma"
                    value={newUser.name}
                    onChange={(e) => setNewUser({ ...newUser, name: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Email Address</label>
                  <input
                    type="email"
                    required
                    className="form-input"
                    placeholder="e.g. riya@amity.edu"
                    value={newUser.email}
                    onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Password (8-20 chars, upper, lower, digit, special, no spaces)</label>
                  <input
                    type="password"
                    required
                    className="form-input"
                    placeholder="Stud@1234"
                    value={newUser.password}
                    onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                  />
                </div>

                <div className="grid-2">
                  <div className="form-group">
                    <label className="form-label">Role</label>
                    <select
                      className="form-select"
                      value={newUser.role}
                      onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                    >
                      <option value="Student">Student</option>
                      <option value="Teacher">Teacher</option>
                      <option value="Parent">Parent</option>
                      <option value="HOD">HOD</option>
                      <option value="Admin">Admin</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Account Status</label>
                    <select
                      className="form-select"
                      value={newUser.status}
                      onChange={(e) => setNewUser({ ...newUser, status: e.target.value })}
                    >
                      <option value="Active">Active</option>
                      <option value="Suspended">Suspended</option>
                    </select>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
                  <button type="button" onClick={() => setUserModalOpen(false)} className="btn btn-secondary">
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary">
                    Create User
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
