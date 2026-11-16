import React from 'react';
import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import ProtectedRoute from './components/ProtectedRoute';

import LoginPage from './pages/LoginPage';
import StudentDashboard from './pages/StudentDashboard';
import ExamScreen from './pages/ExamScreen';
import ResultReviewPage from './pages/ResultReviewPage';
import TeacherDashboard from './pages/TeacherDashboard';
import ExamBuilder from './pages/ExamBuilder';
import ParentDashboard from './pages/ParentDashboard';
import HODDashboard from './pages/HODDashboard';
import AdminDashboard from './pages/AdminDashboard';

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <HashRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />

          {/* Student Routes */}
          <Route
            path="/dashboard/student"
            element={
              <ProtectedRoute allowedRoles={['Student']}>
                <StudentDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/exam/:attemptId"
            element={
              <ProtectedRoute allowedRoles={['Student']}>
                <ExamScreen />
              </ProtectedRoute>
            }
          />

          {/* Result Review & AI Help (Student, Teacher, Parent, HOD, Admin) */}
          <Route
            path="/results/:attemptId"
            element={
              <ProtectedRoute allowedRoles={['Student', 'Teacher', 'Parent', 'HOD', 'Admin']}>
                <ResultReviewPage />
              </ProtectedRoute>
            }
          />

          {/* Teacher Routes */}
          <Route
            path="/dashboard/teacher"
            element={
              <ProtectedRoute allowedRoles={['Teacher']}>
                <TeacherDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/teacher/exam/new"
            element={
              <ProtectedRoute allowedRoles={['Teacher']}>
                <ExamBuilder />
              </ProtectedRoute>
            }
          />
          <Route
            path="/teacher/exam/:examId"
            element={
              <ProtectedRoute allowedRoles={['Teacher']}>
                <ExamBuilder />
              </ProtectedRoute>
            }
          />

          {/* Parent Routes */}
          <Route
            path="/dashboard/parent"
            element={
              <ProtectedRoute allowedRoles={['Parent']}>
                <ParentDashboard />
              </ProtectedRoute>
            }
          />

          {/* HOD Routes */}
          <Route
            path="/dashboard/hod"
            element={
              <ProtectedRoute allowedRoles={['HOD', 'Admin']}>
                <HODDashboard />
              </ProtectedRoute>
            }
          />

          {/* Admin Routes */}
          <Route
            path="/dashboard/admin"
            element={
              <ProtectedRoute allowedRoles={['Admin']}>
                <AdminDashboard />
              </ProtectedRoute>
            }
          />

          {/* Default fallback */}
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </HashRouter>
    </AuthProvider>
  </ThemeProvider>
  );
}
