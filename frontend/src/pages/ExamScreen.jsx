import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { attemptApi, examApi } from '../services/api';
import { ShieldAlert, Clock, Check, AlertTriangle, Maximize, ArrowLeft, ArrowRight, Send } from 'lucide-react';

export default function ExamScreen() {
  const { attemptId } = useParams();
  const navigate = useNavigate();

  const [attempt, setAttempt] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState({});
  const [saveStatus, setSaveStatus] = useState('Saved');
  const [timeLeft, setTimeLeft] = useState(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isLocked, setIsLocked] = useState(false);
  const [lockReason, setLockReason] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [showSubmitModal, setShowSubmitModal] = useState(false);
  const [error, setError] = useState('');

  const answersRef = useRef(answers);
  answersRef.current = answers;

  useEffect(() => {
    loadAttemptAndPaper();
  }, [attemptId]);

  // Load attempt & questions
  const loadAttemptAndPaper = async () => {
    try {
      const att = await attemptApi.get(attemptId);
      setAttempt(att);
      setAnswers(att.answers || {});

      if (att.status === 'Auto-Locked') {
        setIsLocked(true);
        setLockReason('Attempt was terminated due to a proctoring violation');
        return;
      }
      if (att.status === 'Submitted') {
        navigate(`/results/${attemptId}`);
        return;
      }

      // Fetch questions
      const paper = await examApi.getPaper(att.exam_id);
      setQuestions(paper);

      // Initialize timer based on start_at and duration
      const startTime = new Date(att.start_at).getTime();
      const durationMs = (att.duration_min || 60) * 60 * 1000;
      const endTime = startTime + durationMs;
      const remainingSec = Math.max(0, Math.floor((endTime - Date.now()) / 1000));
      setTimeLeft(remainingSec);

    } catch (err) {
      setError(err.message || 'Failed to load exam attempt');
    }
  };

  // Timer countdown
  useEffect(() => {
    if (timeLeft === null || isLocked) return;

    if (timeLeft <= 0) {
      handleAutoSubmit('Time Expired');
      return;
    }

    const interval = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          handleAutoSubmit('Time Expired');
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [timeLeft, isLocked]);

  // Fullscreen & Page Visibility proctoring listeners
  useEffect(() => {
    if (!isFullscreen || isLocked) return;

    const handleVisibilityChange = async () => {
      if (document.hidden) {
        try {
          const res = await attemptApi.postEvent(attemptId, 'TAB_SWITCH');
          if (res.locked || res.status === 'Auto-Locked') {
            setIsLocked(true);
            setLockReason('Tab Switch detected. The exam has been auto-locked.');
          }
        } catch (e) {
          console.error('Error logging tab switch:', e);
        }
      }
    };

    const handleFullscreenChange = async () => {
      if (!document.fullscreenElement) {
        setIsFullscreen(false);
        try {
          const res = await attemptApi.postEvent(attemptId, 'FULLSCREEN_EXIT');
          if (res.locked || res.status === 'Auto-Locked') {
            setIsLocked(true);
            setLockReason('Fullscreen exited. The exam has been auto-locked.');
          }
        } catch (e) {
          console.error('Error logging fullscreen exit:', e);
        }
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    document.addEventListener('fullscreenchange', handleFullscreenChange);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
    };
  }, [isFullscreen, isLocked, attemptId]);

  // Enter Fullscreen handler
  const requestFullscreen = async () => {
    try {
      const elem = document.documentElement;
      if (elem.requestFullscreen) {
        await elem.requestFullscreen();
      } else if (elem.webkitRequestFullscreen) {
        await elem.webkitRequestFullscreen();
      }
      setIsFullscreen(true);
    } catch (err) {
      alert('Fullscreen permission is required to attempt the exam.');
    }
  };

  // Autosave answer on option selection
  const handleSelectOption = async (questionId, optionKey) => {
    if (isLocked) return;

    const newAnswers = { ...answers, [questionId]: optionKey };
    setAnswers(newAnswers);
    setSaveStatus('Saving...');

    try {
      await attemptApi.autosave(attemptId, { [questionId]: optionKey });
      setSaveStatus('Saved');
    } catch (err) {
      setSaveStatus('Error saving');
    }
  };

  // Manual or Auto Submit
  const handleAutoSubmit = async (reason = 'Manual Submit') => {
    if (submitting) return;
    setSubmitting(true);
    try {
      await attemptApi.submit(attemptId);
      if (document.fullscreenElement) {
        document.exitFullscreen().catch(() => {});
      }
      navigate(`/results/${attemptId}`);
    } catch (err) {
      alert(`Submission error: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  // Format seconds to MM:SS
  const formatTime = (seconds) => {
    if (seconds === null) return '--:--';
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  // If exam is locked due to violation
  if (isLocked) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#450a0a', padding: '1.5rem' }}>
        <div style={{ maxWidth: '480px', width: '100%', background: '#fff', borderRadius: '1rem', padding: '2rem', textAlign: 'center', boxShadow: '0 25px 50px -12px rgba(0,0,0,0.5)' }}>
          <div style={{ display: 'inline-flex', padding: '1rem', background: '#fee2e2', borderRadius: '50%', marginBottom: '1rem' }}>
            <ShieldAlert size={48} color="#dc2626" />
          </div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#991b1b', marginBottom: '0.75rem' }}>
            Exam Auto-Locked
          </h2>
          <p style={{ color: '#4b5563', fontSize: '0.9375rem', marginBottom: '1.5rem', lineHeight: 1.6 }}>
            {lockReason || 'A proctoring violation was detected (Tab Switch or Fullscreen Exit). Your attempt has been terminated.'}
          </p>
          <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '0.5rem', padding: '0.875rem', marginBottom: '1.5rem', textAlign: 'left', fontSize: '0.8125rem', color: '#991b1b' }}>
            <strong>Note:</strong> All answers saved up to the moment of violation have been submitted and evaluated automatically.
          </div>
          <button
            onClick={() => {
              if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
              navigate(`/results/${attemptId}`);
            }}
            className="btn btn-primary"
            style={{ width: '100%' }}
          >
            View Evaluation Results
          </button>
        </div>
      </div>
    );
  }

  // Fullscreen Gate Modal
  if (!isFullscreen) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#0f172a', padding: '1.5rem' }}>
        <div style={{ maxWidth: '520px', width: '100%', background: '#fff', borderRadius: '1rem', padding: '2rem', textAlign: 'center' }}>
          <div style={{ display: 'inline-flex', padding: '1rem', background: '#dbeafe', borderRadius: '50%', marginBottom: '1rem' }}>
            <Maximize size={42} color="#1e40af" />
          </div>
          <h2 style={{ fontSize: '1.375rem', fontWeight: '700', marginBottom: '0.5rem' }}>
            Proctored Assessment Gate
          </h2>
          <h3 style={{ fontSize: '1.125rem', color: '#1e40af', marginBottom: '1rem' }}>
            {attempt?.exam_title || 'Online Examination'}
          </h3>
          <div style={{ textAlign: 'left', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '0.5rem', padding: '1rem', marginBottom: '1.5rem', fontSize: '0.875rem', color: '#334155' }}>
            <p style={{ fontWeight: '600', marginBottom: '0.5rem' }}>Strict Proctoring Rules:</p>
            <ul style={{ paddingLeft: '1.25rem', lineHeight: '1.6' }}>
              <li>The exam runs strictly in <strong>Fullscreen Mode</strong>.</li>
              <li><strong>Switching tabs</strong> or minimizing the window will <strong>immediately auto-lock</strong> your exam.</li>
              <li><strong>Exiting fullscreen</strong> will <strong>immediately auto-lock</strong> your exam.</li>
              <li>Your answers are autosaved in real time.</li>
            </ul>
          </div>
          <button onClick={requestFullscreen} className="btn btn-primary" style={{ width: '100%', padding: '0.875rem', fontSize: '1rem' }}>
            Enter Fullscreen & Begin Exam
          </button>
        </div>
      </div>
    );
  }

  const currentQ = questions[currentIdx];

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: '#f1f5f9' }}>
      {/* Top Proctoring Header */}
      <header style={{ background: '#1e3a8a', color: 'white', padding: '0.75rem 1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', boxShadow: '0 2px 4px rgba(0,0,0,0.15)' }}>
        <div>
          <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', opacity: 0.8 }}>Proctored Session</span>
          <h2 style={{ fontSize: '1.125rem', fontWeight: '700' }}>{attempt?.exam_title}</h2>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
          {/* Autosave Status */}
          <div style={{ fontSize: '0.8125rem', display: 'flex', alignItems: 'center', gap: '0.375rem', opacity: 0.9 }}>
            <Check size={16} />
            <span>{saveStatus}</span>
          </div>

          {/* Timer Display */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            background: timeLeft && timeLeft < 300 ? '#dc2626' : 'rgba(255,255,255,0.15)',
            padding: '0.375rem 0.875rem',
            borderRadius: '0.5rem',
            fontWeight: '700',
            fontSize: '1.125rem',
          }}>
            <Clock size={18} />
            <span>{formatTime(timeLeft)}</span>
          </div>

          <button onClick={() => setShowSubmitModal(true)} className="btn btn-danger btn-sm">
            <Send size={14} />
            Finish & Submit
          </button>
        </div>
      </header>

      {/* Main Examination Body */}
      <div style={{ flex: 1, display: 'flex', maxWidth: '1400px', width: '100%', margin: '0 auto', padding: '1.5rem', gap: '1.5rem' }}>
        {/* Left Side: Question Card */}
        <div style={{ flex: 1 }}>
          {currentQ ? (
            <div className="card" style={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', borderBottom: '1px solid #e2e8f0', paddingBottom: '0.75rem' }}>
                  <span style={{ fontSize: '0.875rem', fontWeight: '700', color: '#1e3a8a' }}>
                    Question {currentIdx + 1} of {questions.length}
                  </span>
                  <span className="badge badge-info">{currentQ.marks} {currentQ.marks === 1 ? 'Mark' : 'Marks'}</span>
                </div>

                <p style={{ fontSize: '1.0625rem', fontWeight: '600', color: '#0f172a', marginBottom: '1.5rem', lineHeight: 1.6 }}>
                  {currentQ.text}
                </p>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {Object.entries(currentQ.options || {}).map(([key, optText]) => {
                    const isSelected = answers[currentQ.question_id] === key;
                    return (
                      <label
                        key={key}
                        onClick={() => handleSelectOption(currentQ.question_id, key)}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.875rem',
                          padding: '1rem',
                          borderRadius: '0.5rem',
                          border: isSelected ? '2px solid #2563eb' : '1px solid #cbd5e1',
                          background: isSelected ? '#eff6ff' : '#ffffff',
                          cursor: 'pointer',
                          transition: 'all 0.15s ease',
                        }}
                      >
                        <input
                          type="radio"
                          name={`q_${currentQ.question_id}`}
                          checked={isSelected}
                          onChange={() => {}}
                          style={{ width: '1.125rem', height: '1.125rem' }}
                        />
                        <span style={{ fontWeight: '700', minWidth: '1.5rem', color: isSelected ? '#1e40af' : '#64748b' }}>
                          {key}.
                        </span>
                        <span style={{ fontSize: '0.9375rem', color: '#1e293b' }}>
                          {optText}
                        </span>
                      </label>
                    );
                  })}
                </div>
              </div>

              {/* Navigation Controls */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '2rem', paddingTop: '1rem', borderTop: '1px solid #e2e8f0' }}>
                <button
                  onClick={() => setCurrentIdx((prev) => Math.max(0, prev - 1))}
                  disabled={currentIdx === 0}
                  className="btn btn-secondary"
                  style={{ gap: '0.375rem' }}
                >
                  <ArrowLeft size={16} /> Previous
                </button>

                <button
                  onClick={() => setCurrentIdx((prev) => Math.min(questions.length - 1, prev + 1))}
                  disabled={currentIdx === questions.length - 1}
                  className="btn btn-primary"
                  style={{ gap: '0.375rem' }}
                >
                  Next <ArrowRight size={16} />
                </button>
              </div>
            </div>
          ) : (
            <p>Loading questions...</p>
          )}
        </div>

        {/* Right Side: Question Navigation Palette */}
        <div style={{ width: '320px' }}>
          <div className="card">
            <h3 style={{ fontSize: '0.9375rem', fontWeight: '700', marginBottom: '1rem' }}>
              Question Palette
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '0.5rem', marginBottom: '1.5rem' }}>
              {questions.map((q, idx) => {
                const isAnswered = !!answers[q.question_id];
                const isCurrent = idx === currentIdx;
                let bg = '#f1f5f9';
                let color = '#475569';
                let border = '1px solid #cbd5e1';

                if (isAnswered) {
                  bg = '#22c55e';
                  color = '#fff';
                  border = '1px solid #16a34a';
                }
                if (isCurrent) {
                  border = '2px solid #1e3a8a';
                }

                return (
                  <button
                    key={q.question_id}
                    onClick={() => setCurrentIdx(idx)}
                    style={{
                      height: '2.5rem',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: '700',
                      borderRadius: '0.375rem',
                      background: bg,
                      color: color,
                      border: border,
                      fontSize: '0.875rem',
                    }}
                  >
                    {idx + 1}
                  </button>
                );
              })}
            </div>

            <div style={{ fontSize: '0.75rem', color: '#64748b', display: 'flex', flexDirection: 'column', gap: '0.375rem', borderTop: '1px solid #e2e8f0', paddingTop: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ width: '12px', height: '12px', background: '#22c55e', borderRadius: '2px' }}></span>
                <span>Answered ({Object.keys(answers).length})</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ width: '12px', height: '12px', background: '#f1f5f9', border: '1px solid #cbd5e1', borderRadius: '2px' }}></span>
                <span>Unanswered ({Math.max(0, questions.length - Object.keys(answers).length)})</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Confirmation Submit Modal */}
      {showSubmitModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999 }}>
          <div style={{ background: '#fff', borderRadius: '0.75rem', padding: '1.75rem', maxWidth: '420px', width: '100%', textAlign: 'center' }}>
            <h3 style={{ fontSize: '1.25rem', fontWeight: '700', marginBottom: '0.75rem' }}>Submit Examination?</h3>
            <p style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: '1.25rem' }}>
              You have answered <strong>{Object.keys(answers).length}</strong> of <strong>{questions.length}</strong> questions.
              Once submitted, your answers cannot be changed.
            </p>
            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center' }}>
              <button onClick={() => setShowSubmitModal(false)} className="btn btn-secondary">
                Continue Test
              </button>
              <button onClick={() => handleAutoSubmit('Manual Submit')} className="btn btn-primary" disabled={submitting}>
                {submitting ? 'Submitting...' : 'Yes, Submit Exam'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
