import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { resultApi, aiHelpApi } from '../services/api';
import Navbar from '../components/Navbar';
import { CheckCircle2, XCircle, Sparkles, AlertCircle, ArrowLeft, RefreshCw, BookOpen } from 'lucide-react';

export default function ResultReviewPage() {
  const { attemptId } = useParams();
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // AI Modal state
  const [aiModalOpen, setAiModalOpen] = useState(false);
  const [selectedQuestion, setSelectedQuestion] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiResponse, setAiResponse] = useState('');
  const [aiError, setAiError] = useState('');

  useEffect(() => {
    loadResult();
  }, [attemptId]);

  const loadResult = async () => {
    try {
      setLoading(true);
      const data = await resultApi.getByAttempt(attemptId);
      setResult(data);
    } catch (err) {
      setError(err.message || 'Failed to load results');
    } finally {
      setLoading(false);
    }
  };

  const handleAskAI = async (question) => {
    setSelectedQuestion(question);
    setAiModalOpen(true);
    setAiLoading(true);
    setAiResponse('');
    setAiError('');

    try {
      const res = await aiHelpApi.ask(attemptId, question.question_id);
      setAiResponse(res.explanation);
    } catch (err) {
      setAiError(err.message || 'AI service temporarily unavailable. Please try again.');
    } finally {
      setAiLoading(false);
    }
  };

  if (loading) {
    return (
      <div>
        <Navbar />
        <div className="container" style={{ textAlign: 'center', padding: '4rem' }}>
          <p>Loading evaluation results...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <Navbar />
        <div className="container" style={{ textAlign: 'center', padding: '4rem' }}>
          <div className="card" style={{ maxWidth: '500px', margin: '0 auto' }}>
            <AlertCircle size={40} color="#dc2626" style={{ margin: '0 auto 1rem' }} />
            <h3 style={{ marginBottom: '1rem', color: '#991b1b' }}>Result Not Available</h3>
            <p style={{ color: '#64748b', marginBottom: '1.5rem' }}>{error}</p>
            <Link to="/dashboard/student" className="btn btn-primary">Return to Dashboard</Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <Navbar />
      <div className="container">
        <Link to="/dashboard/student" className="btn btn-secondary btn-sm" style={{ marginBottom: '1rem', gap: '0.375rem' }}>
          <ArrowLeft size={16} /> Back to Dashboard
        </Link>

        {/* Score Card Header */}
        <div className="card" style={{ background: 'linear-gradient(135deg, #1e3a8a, #1e40af)', color: 'white' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <span style={{ fontSize: '0.8125rem', opacity: 0.85, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Evaluation Report
              </span>
              <h1 style={{ fontSize: '1.5rem', fontWeight: '700', marginTop: '0.25rem' }}>{result.exam_title}</h1>
              <p style={{ fontSize: '0.875rem', opacity: 0.9, marginTop: '0.25rem' }}>
                Published on: {result.published_at ? new Date(result.published_at).toLocaleString() : 'Pending'}
              </p>
            </div>

            <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center' }}>
              <div style={{ textAlign: 'center', background: 'rgba(255,255,255,0.15)', padding: '0.75rem 1.5rem', borderRadius: '0.75rem' }}>
                <span style={{ fontSize: '1.75rem', fontWeight: '800' }}>{result.score}</span>
                <span style={{ opacity: 0.85, fontSize: '0.875rem' }}> / {result.total_marks}</span>
                <span style={{ display: 'block', fontSize: '0.75rem', opacity: 0.9, marginTop: '0.25rem' }}>Score</span>
              </div>

              <div style={{ textAlign: 'center', background: 'rgba(255,255,255,0.15)', padding: '0.75rem 1.5rem', borderRadius: '0.75rem' }}>
                <span style={{ fontSize: '1.75rem', fontWeight: '800' }}>{result.percentage}%</span>
                <span style={{ display: 'block', fontSize: '0.75rem', opacity: 0.9, marginTop: '0.25rem' }}>Percentage</span>
              </div>

              <div style={{ textAlign: 'center' }}>
                {result.status === 'Terminated (violation)' ? (
                  <span className="badge badge-danger" style={{ fontSize: '0.8125rem', padding: '0.5rem 1rem' }}>
                    Terminated (violation)
                  </span>
                ) : (
                  <span className="badge badge-success" style={{ fontSize: '0.8125rem', padding: '0.5rem 1rem' }}>
                    {result.status}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Question Review Section */}
        <h2 style={{ fontSize: '1.25rem', fontWeight: '700', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <BookOpen size={20} color="var(--primary)" />
          Question Breakdown & Concept Analysis
        </h2>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {result.questions?.map((q, idx) => {
            const isCorrect = q.is_correct;
            return (
              <div
                key={q.question_id}
                className="card"
                style={{
                  borderLeft: isCorrect ? '4px solid #16a34a' : '4px solid #dc2626',
                  marginBottom: 0,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    {isCorrect ? (
                      <CheckCircle2 size={20} color="#16a34a" />
                    ) : (
                      <XCircle size={20} color="#dc2626" />
                    )}
                    <span style={{ fontWeight: '700', fontSize: '0.9375rem' }}>
                      Question {idx + 1}
                    </span>
                    <span className="badge badge-info">{q.marks} {q.marks === 1 ? 'Mark' : 'Marks'}</span>
                  </div>

                  {!isCorrect && (
                    <button
                      onClick={() => handleAskAI(q)}
                      className="btn btn-sm"
                      style={{
                        background: 'linear-gradient(135deg, #7c3aed, #4f46e5)',
                        color: 'white',
                        gap: '0.375rem',
                      }}
                    >
                      <Sparkles size={14} />
                      Ask AI (Concept Help)
                    </button>
                  )}
                </div>

                <p style={{ fontSize: '1rem', fontWeight: '600', color: '#1e293b', marginBottom: '1rem' }}>
                  {q.text}
                </p>

                {/* Options display */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.5rem', marginBottom: '1rem' }}>
                  {Object.entries(q.options || {}).map(([key, text]) => {
                    const isSelected = q.selected_option === key;
                    const isOfficialCorrect = q.correct_option === key;

                    let bg = '#f8fafc';
                    let border = '1px solid #e2e8f0';
                    let textCol = '#334155';

                    if (isOfficialCorrect) {
                      bg = '#dcfce7';
                      border = '1px solid #86efac';
                      textCol = '#15803d';
                    } else if (isSelected && !isCorrect) {
                      bg = '#fee2e2';
                      border = '1px solid #fca5a5';
                      textCol = '#b91c1c';
                    }

                    return (
                      <div
                        key={key}
                        style={{
                          background: bg,
                          border: border,
                          color: textCol,
                          padding: '0.625rem 0.875rem',
                          borderRadius: '0.375rem',
                          fontSize: '0.875rem',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.5rem',
                        }}
                      >
                        <strong>{key}.</strong>
                        <span>{text}</span>
                        {isSelected && <span style={{ marginLeft: 'auto', fontSize: '0.75rem', fontWeight: 'bold' }}>[Your Answer]</span>}
                        {isOfficialCorrect && !isSelected && <span style={{ marginLeft: 'auto', fontSize: '0.75rem', fontWeight: 'bold' }}>[Correct]</span>}
                      </div>
                    );
                  })}
                </div>

                {/* Status text */}
                <div style={{ fontSize: '0.8125rem', color: '#64748b' }}>
                  {isCorrect ? (
                    <span style={{ color: '#16a34a', fontWeight: '600' }}>Full marks awarded ({q.marks}/{q.marks})</span>
                  ) : (
                    <span style={{ color: '#dc2626', fontWeight: '600' }}>
                      0 marks awarded (Your answer: {q.selected_option || 'None'} | Correct: {q.correct_option})
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* AI Concept Explanation Modal */}
      {aiModalOpen && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999, padding: '1rem' }}>
          <div style={{ background: '#ffffff', borderRadius: '1rem', maxWidth: '600px', width: '100%', maxHeight: '90vh', overflowY: 'auto', padding: '1.75rem', boxShadow: '0 25px 50px -12px rgba(0,0,0,0.25)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', borderBottom: '1px solid #e2e8f0', paddingBottom: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Sparkles size={22} color="#7c3aed" />
                <h3 style={{ fontSize: '1.25rem', fontWeight: '700', color: '#4c1d95' }}>AI Concept Explainer</h3>
              </div>
              <button
                onClick={() => setAiModalOpen(false)}
                style={{ background: 'transparent', border: 'none', fontSize: '1.25rem', color: '#94a3b8', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            {selectedQuestion && (
              <div style={{ background: '#f5f3ff', border: '1px solid #ddd6fe', borderRadius: '0.5rem', padding: '0.875rem', marginBottom: '1.25rem', fontSize: '0.875rem' }}>
                <p style={{ fontWeight: '600', color: '#5b21b6', marginBottom: '0.375rem' }}>Question:</p>
                <p style={{ color: '#1e1b4b', marginBottom: '0.5rem' }}>{selectedQuestion.text}</p>
                <div style={{ display: 'flex', gap: '1rem', fontSize: '0.8125rem' }}>
                  <span>Your Answer: <strong style={{ color: '#dc2626' }}>{selectedQuestion.selected_option || 'None'}</strong></span>
                  <span>Correct Answer: <strong style={{ color: '#16a34a' }}>{selectedQuestion.correct_option}</strong></span>
                </div>
              </div>
            )}

            {aiLoading && (
              <div style={{ textAlign: 'center', padding: '2rem' }}>
                <RefreshCw size={28} className="animate-spin" color="#7c3aed" style={{ margin: '0 auto 1rem', animation: 'spin 1s linear infinite' }} />
                <p style={{ color: '#6d28d9', fontWeight: '600' }}>Consulting Google Gemini AI...</p>
                <p style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Generating personalized concept clarification (15s timeout)</p>
              </div>
            )}

            {aiError && (
              <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '0.5rem', padding: '1rem', color: '#991b1b', marginBottom: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                  <AlertCircle size={18} />
                  <strong>AI Explanation Unavailable</strong>
                </div>
                <p style={{ fontSize: '0.875rem', marginBottom: '0.75rem' }}>{aiError}</p>
                <button
                  onClick={() => handleAskAI(selectedQuestion)}
                  className="btn btn-sm btn-primary"
                  style={{ gap: '0.375rem' }}
                >
                  <RefreshCw size={14} /> Retry Request
                </button>
              </div>
            )}

            {aiResponse && !aiLoading && (
              <div style={{ background: '#ffffff', borderRadius: '0.5rem', lineHeight: '1.7', fontSize: '0.9375rem', color: '#1e293b', whiteSpace: 'pre-line' }}>
                {aiResponse}
              </div>
            )}

            <div style={{ marginTop: '1.5rem', textAlign: 'right', borderTop: '1px solid #e2e8f0', paddingTop: '1rem' }}>
              <button onClick={() => setAiModalOpen(false)} className="btn btn-secondary">
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
