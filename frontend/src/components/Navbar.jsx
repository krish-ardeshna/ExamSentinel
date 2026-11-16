import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, LogOut, User as UserIcon } from 'lucide-react';
import ThemeToggle from './ThemeToggle';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const getDashboardPath = () => {
    switch (user?.role) {
      case 'Student': return '/dashboard/student';
      case 'Teacher': return '/dashboard/teacher';
      case 'Parent': return '/dashboard/parent';
      case 'HOD': return '/dashboard/hod';
      case 'Admin': return '/dashboard/admin';
      default: return '/login';
    }
  };

  return (
    <nav style={{ background: 'var(--nav-bg)', color: 'var(--nav-text)', padding: '0.875rem 1.5rem', borderBottom: '1px solid var(--nav-border)', boxShadow: 'var(--shadow-sm)' }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Link to={getDashboardPath()} style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', color: 'var(--nav-text)', textDecoration: 'none', fontWeight: '700', fontSize: '1.125rem' }}>
          <ShieldCheck size={26} color="currentColor" />
          <span>ExamSentinel</span>
          <span style={{ fontSize: '0.75rem', background: 'var(--nav-badge-bg)', border: '1px solid var(--border)', padding: '0.125rem 0.5rem', borderRadius: '4px', fontWeight: '500', color: 'var(--text-muted)' }}>
            OEPMS
          </span>
        </Link>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <ThemeToggle />

          {user && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem' }}>
                <UserIcon size={16} />
                <span style={{ fontWeight: '600' }}>{user.name}</span>
                <span style={{ background: 'var(--bg-card-subtle)', border: '1px solid var(--border)', color: 'var(--text-main)', padding: '0.125rem 0.5rem', borderRadius: '9999px', fontSize: '0.75rem', fontWeight: 'bold' }}>
                  {user.role}
                </span>
              </div>
              <button
                onClick={handleLogout}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.375rem',
                  background: 'var(--danger-light)',
                  border: '1px solid var(--danger)',
                  color: 'var(--danger)',
                  padding: '0.375rem 0.75rem',
                  borderRadius: '0.375rem',
                  fontSize: '0.8125rem',
                  fontWeight: '600',
                }}
              >
                <LogOut size={14} />
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}
