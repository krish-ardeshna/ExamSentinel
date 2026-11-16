import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams, Link } from 'react-router-dom';
import { examApi } from '../services/api';
import Navbar from '../components/Navbar';
import { PlusCircle, Key, Send, AlertCircle, CheckCircle, ArrowLeft } from 'lucide-react';

export default function ExamBuilder() {
  const { examId } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const isEditing = !!examId;
  const [subjects, setSubjects] = useState([]);
  const [exam, setExam] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Form for creating exam
  const [formData, setFormData] = useState({
    subject_id: searchParams.get('subject_id') || '',
    title: '',
    start_time: '',
    end_time: '',
    duration_min: 60,
    total_marks: 20,
    status: 'Draft',
  });

  // Question Form
  const [qText, setQText] = useState('');
  const [optA, setOptA] = useState('');
  const [optB, setOptB] = useState('');
  const [optC, setOptC] = useState('');
  const [optD, setOptD] = useState('');
  const [qMarks, setQMarks] = useState(1);
  const [qCorrect, setQCorrect] = useState('A');

  // Answer Key state
  const [answerKey, setAnswerKey] = useState({});

  useEffect(() => {
    loadSubjects();
    if (isEditing) {
      loadExamAndQuestions();
    }
  }, [examId]);

  const loadSubjects = async () => {
    try {
      const subs = await examApi.listSubjects();
      setSubjects(subs);
      if (subs.length > 0 && !formData.subject_id) {
        setFormData((prev) => ({ ...prev, subject_id: subs[0].subject_id }));
      }
    } catch (err) {
      console.error(err);
    }
  };

  const loadExamAndQuestions = async () => {
    try {
      setLoading(true);
      const ex = await examApi.get(examId);
      setExam(ex);
      setFormData({
        subject_id: ex.subject_id,
        title: ex.title,
        start_time: ex.start_time.slice(0, 19).replace('T', ' '),
        end_time: ex.end_time.slice(0, 19).replace('T', ' '),
        duration_min: ex.duration_min,
        total_marks: ex.total_marks,
        status: ex.status,
      });

      const paper = await examApi.getPaper(examId);
      setQuestions(paper);
    } catch (err) {
      setError(err.message || 'Failed to load exam details');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateExam = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      const payload = {
        subject_id: parseInt(formData.subject_id),
        title: formData.title,
        start_time: formData.start_time,
        end_time: formData.end_time,
        duration_min: parseInt(formData.duration_min),
        total_marks: parseInt(formData.total_marks),
        status: 'Draft',
      };
      const created = await examApi.create(payload);
      setSuccess('Exam draft created successfully!');
      navigate(`/teacher/exam/${created.exam_id}`);
    } catch (err) {
      setError(err.message || 'Failed to create exam');
    } finally {
      setLoading(false);
    }
  };

  const handleAddQuestion = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    try {
      const payload = {
        text: qText,
        options: { A: optA, B: optB, C: optC, D: optD },
        marks: parseInt(qMarks),
      };
      const createdQ = await examApi.addQuestion(examId, payload);

      // Record correct option in answerKey
      const updatedKey = { ...answerKey, [createdQ.question_id]: qCorrect };
      setAnswerKey(updatedKey);
      await examApi.submitAnswerKey(examId, updatedKey);

      setQuestions((prev) => [...prev, createdQ]);
      setQText('');
      setOptA('');
      setOptB('');
      setOptC('');
      setOptD('');
      setQMarks(1);
      setSuccess('Question and answer key added successfully!');
    } catch (err) {
      setError(err.message || 'Failed to add question');
    }
  };

  const handlePublish = async () => {
    setError('');
    setSuccess('');
    try {
      const res = await examApi.publish(examId);
      setExam(res);
      setSuccess('Exam successfully published! It is now visible to students and parents.');
    } catch (err) {
      setError(err.message || 'Publish rejected');
    }
  };

  const sumMarks = questions.reduce((sum, q) => sum + q.marks, 0);

  return (
    <div>
      <Navbar />
      <div className="container">
        <Link to="/teacher/dashboard" className="btn btn-secondary btn-sm" style={{ marginBottom: '1rem', gap: '0.375rem' }}>
          <ArrowLeft size={16} /> Back to Faculty Dashboard
        </Link>

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

        {/* Step 1: Schedule Exam Details */}
        <div className="card">
          <h2 style={{ fontSize: '1.25rem', fontWeight: '700', marginBottom: '1rem' }}>
            {isEditing ? `Exam Settings: ${exam?.title}` : 'Step 1: Schedule New Exam'}
          </h2>

          <form onSubmit={handleCreateExam}>
            <div className="grid-2">
              <div className="form-group">
                <label className="form-label">Subject</label>
                <select
                  disabled={isEditing}
                  className="form-select"
                  value={formData.subject_id}
                  onChange={(e) => setFormData({ ...formData, subject_id: e.target.value })}
                >
                  {subjects.map((s) => (
                    <option key={s.subject_id} value={s.subject_id}>
                      {s.name} ({s.code}) - Sem {s.semester}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Exam Title</label>
                <input
                  type="text"
                  required
                  disabled={isEditing && exam?.status === 'Published'}
                  className="form-input"
                  placeholder="e.g. Data Structures Unit Test 1"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                />
              </div>
            </div>

            <div className="grid-4">
              <div className="form-group">
                <label className="form-label">Start Time (YYYY-MM-DD HH:MM:SS)</label>
                <input
                  type="text"
                  required
                  disabled={isEditing && exam?.status === 'Published'}
                  className="form-input"
                  placeholder="2026-11-20 10:00:00"
                  value={formData.start_time}
                  onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">End Time (YYYY-MM-DD HH:MM:SS)</label>
                <input
                  type="text"
                  required
                  disabled={isEditing && exam?.status === 'Published'}
                  className="form-input"
                  placeholder="2026-11-20 12:00:00"
                  value={formData.end_time}
                  onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Duration (Mins, 1-180)</label>
                <input
                  type="number"
                  min="1"
                  max="180"
                  required
                  disabled={isEditing && exam?.status === 'Published'}
                  className="form-input"
                  value={formData.duration_min}
                  onChange={(e) => setFormData({ ...formData, duration_min: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Total Marks (1-100)</label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  required
                  disabled={isEditing && exam?.status === 'Published'}
                  className="form-input"
                  value={formData.total_marks}
                  onChange={(e) => setFormData({ ...formData, total_marks: e.target.value })}
                />
              </div>
            </div>

            {!isEditing && (
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? 'Creating...' : 'Save Draft & Proceed to Questions'}
              </button>
            )}
          </form>
        </div>

        {/* Step 2: Add Questions & Answer Key (Available once exam exists) */}
        {isEditing && (
          <div>
            {/* Status & Publish Bar */}
            <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-card-subtle)' }}>
              <div>
                <span style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Current Status: </span>
                <span className={`badge ${exam?.status === 'Published' ? 'badge-success' : 'badge-warning'}`}>
                  {exam?.status}
                </span>
                <span style={{ marginLeft: '1.5rem', fontSize: '0.875rem' }}>
                  Total Questions: <strong>{questions.length}</strong> | Marks Assigned: <strong>{sumMarks}</strong> / {formData.total_marks}
                </span>
              </div>

              {exam?.status === 'Draft' && (
                <button onClick={handlePublish} className="btn btn-success" style={{ gap: '0.5rem' }}>
                  <Send size={16} /> Publish Exam to Students
                </button>
              )}
            </div>

            {/* Question Creation Form */}
            {exam?.status === 'Draft' && (
              <div className="card">
                <h3 style={{ fontSize: '1.125rem', fontWeight: '700', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <PlusCircle size={18} color="var(--primary)" /> Add New Question & Official Key
                </h3>

                <form onSubmit={handleAddQuestion}>
                  <div className="form-group">
                    <label className="form-label">Question Text</label>
                    <textarea
                      required
                      rows="3"
                      className="form-textarea"
                      placeholder="Enter question statement..."
                      value={qText}
                      onChange={(e) => setQText(e.target.value)}
                    />
                  </div>

                  <div className="grid-2">
                    <div className="form-group">
                      <label className="form-label">Option A</label>
                      <input type="text" required className="form-input" value={optA} onChange={(e) => setOptA(e.target.value)} />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Option B</label>
                      <input type="text" required className="form-input" value={optB} onChange={(e) => setOptB(e.target.value)} />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Option C</label>
                      <input type="text" required className="form-input" value={optC} onChange={(e) => setOptC(e.target.value)} />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Option D</label>
                      <input type="text" required className="form-input" value={optD} onChange={(e) => setOptD(e.target.value)} />
                    </div>
                  </div>

                  <div className="grid-2">
                    <div className="form-group">
                      <label className="form-label">Marks for this Question</label>
                      <input type="number" min="1" required className="form-input" value={qMarks} onChange={(e) => setQMarks(e.target.value)} />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Official Correct Option (Hidden from students)</label>
                      <select className="form-select" value={qCorrect} onChange={(e) => setQCorrect(e.target.value)}>
                        <option value="A">Option A</option>
                        <option value="B">Option B</option>
                        <option value="C">Option C</option>
                        <option value="D">Option D</option>
                      </select>
                    </div>
                  </div>

                  <button type="submit" className="btn btn-primary">
                    Add Question to Paper
                  </button>
                </form>
              </div>
            )}

            {/* Existing Questions List */}
            <div className="card">
              <h3 style={{ fontSize: '1.125rem', fontWeight: '700', marginBottom: '1rem' }}>
                Question Paper ({questions.length} Questions)
              </h3>

              {questions.length === 0 ? (
                <p style={{ color: 'var(--text-muted)' }}>No questions added yet. Add at least one question to publish.</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {questions.map((q, idx) => (
                    <div key={q.question_id} style={{ border: '1px solid var(--border)', borderRadius: '0.5rem', padding: '1rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                        <span style={{ fontWeight: '700' }}>Q{idx + 1}. {q.text}</span>
                        <span className="badge badge-info">{q.marks} {q.marks === 1 ? 'Mark' : 'Marks'}</span>
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.5rem', fontSize: '0.875rem', color: '#475569' }}>
                        {Object.entries(q.options || {}).map(([key, val]) => (
                          <div key={key}><strong>{key}:</strong> {val}</div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
