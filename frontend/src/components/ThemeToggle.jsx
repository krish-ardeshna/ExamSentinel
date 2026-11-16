import React from 'react';
import { useTheme } from '../context/ThemeContext';
import { Sun, Moon } from 'lucide-react';

export default function ThemeToggle({ style = {}, showLabel = false }) {
  const { theme, toggleTheme, isDark } = useTheme();

  return (
    <button
      type="button"
      onClick={toggleTheme}
      title={`Switch to ${isDark ? 'Light' : 'Dark'} Mode`}
      aria-label={`Switch to ${isDark ? 'Light' : 'Dark'} Mode`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.4rem',
        background: 'var(--toggle-bg)',
        border: '1px solid var(--border)',
        color: 'var(--text-main)',
        padding: '0.4rem 0.65rem',
        borderRadius: '0.5rem',
        cursor: 'pointer',
        fontSize: '0.8125rem',
        fontWeight: '500',
        transition: 'all 0.2s ease',
        ...style,
      }}
    >
      {isDark ? <Sun size={16} color="#fbbf24" /> : <Moon size={16} color="#475569" />}
      {showLabel && <span>{isDark ? 'Light' : 'Dark'}</span>}
    </button>
  );
}
