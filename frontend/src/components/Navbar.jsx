import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, LogOut, User as UserIcon } from 'lucide-react';

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
    <nav style={{ background: '#1e3a8a', color: 'white', padding: '0.875rem 1.5rem', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Link to={getDashboardPath()} style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', color: 'white', textDecoration: 'none', fontWeight: '700', fontSize: '1.125rem' }}>
          <ShieldCheck size={26} color="#38bdf8" />
          <span>OEPMS</span>
          <span style={{ fontSize: '0.75rem', background: 'rgba(255,255,255,0.2)', padding: '0.125rem 0.5rem', borderRadius: '4px', fontWeight: '500' }}>
            Proctoring & Management
          </span>
        </Link>

        {user && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem' }}>
              <UserIcon size={16} />
              <span style={{ fontWeight: '600' }}>{user.name}</span>
              <span style={{ background: '#0284c7', padding: '0.125rem 0.5rem', borderRadius: '9999px', fontSize: '0.75rem', fontWeight: 'bold' }}>
                {user.role}
              </span>
            </div>
            <button
              onClick={handleLogout}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.375rem',
                background: 'rgba(239, 68, 68, 0.2)',
                border: '1px solid rgba(239, 68, 68, 0.4)',
                color: '#fca5a5',
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
    </nav>
  );
}
