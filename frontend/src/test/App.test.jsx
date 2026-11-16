import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import App from '../App';

describe('OEPMS Frontend Application Tests', () => {
  it('renders login page with portal title and inputs', () => {
    render(<App />);
    expect(screen.getByText('OEPMS Portal')).toBeInTheDocument();
    expect(screen.getByText('Online Exam Proctoring & Management System')).toBeInTheDocument();
    expect(screen.getByLabelText(/Email Address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Sign In to Dashboard/i })).toBeInTheDocument();
  });

  it('displays quick demo accounts fill buttons', () => {
    render(<App />);
    expect(screen.getByText('Student (Riya)')).toBeInTheDocument();
    expect(screen.getByText('Teacher (Rajesh)')).toBeInTheDocument();
    expect(screen.getByText('HOD (Dr. Kumar)')).toBeInTheDocument();
    expect(screen.getByText('Admin (System)')).toBeInTheDocument();
  });
});
