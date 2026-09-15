// src/pages/RegisterPage.js
import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { validateRegistration } from '../utils/auth';
import SocialButtons from '../components/SocialButtons';
import '../styles/AuthPages.css';

const EMPTY_FIELDS = { name: '', email: '', password: '', confirmPassword: '' };

function RegisterPage({ onSwitchToLogin }) {
  const { register } = useAuth();
  const [fields, setFields] = useState(EMPTY_FIELDS);
  const [fieldErrors, setFieldErrors] = useState({});
  const [formError, setFormError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const updateField = (key) => (e) => setFields((prev) => ({ ...prev, [key]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (isSubmitting) return;
    setFormError('');

    const errors = validateRegistration(fields);
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) return;

    setIsSubmitting(true);
    try {
      await register(fields);
      // On success, AuthContext's user state flips and App.js swaps the view.
    } catch (err) {
      setFormError(err.message || 'Could not create your account. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-brand">🐞 BugFix AI</div>
        <p className="auth-subtitle">Create an account to save your diagnoses.</p>

        {formError && (
          <div className="auth-form-error" role="alert">
            {formError}
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <div className="auth-field">
            <label htmlFor="register-name">Name</label>
            <input
              id="register-name"
              type="text"
              value={fields.name}
              onChange={updateField('name')}
              className={fieldErrors.name ? 'invalid' : ''}
              autoComplete="name"
              autoFocus
            />
            {fieldErrors.name && <div className="auth-field-error">{fieldErrors.name}</div>}
          </div>

          <div className="auth-field">
            <label htmlFor="register-email">Email</label>
            <input
              id="register-email"
              type="email"
              value={fields.email}
              onChange={updateField('email')}
              className={fieldErrors.email ? 'invalid' : ''}
              autoComplete="email"
            />
            {fieldErrors.email && <div className="auth-field-error">{fieldErrors.email}</div>}
          </div>

          <div className="auth-field">
            <label htmlFor="register-password">Password</label>
            <input
              id="register-password"
              type="password"
              value={fields.password}
              onChange={updateField('password')}
              className={fieldErrors.password ? 'invalid' : ''}
              autoComplete="new-password"
            />
            {fieldErrors.password ? (
              <div className="auth-field-error">{fieldErrors.password}</div>
            ) : (
              <div className="auth-hint">At least 8 characters.</div>
            )}
          </div>

          <div className="auth-field">
            <label htmlFor="register-confirm-password">Confirm password</label>
            <input
              id="register-confirm-password"
              type="password"
              value={fields.confirmPassword}
              onChange={updateField('confirmPassword')}
              className={fieldErrors.confirmPassword ? 'invalid' : ''}
              autoComplete="new-password"
            />
            {fieldErrors.confirmPassword && (
              <div className="auth-field-error">{fieldErrors.confirmPassword}</div>
            )}
          </div>

          <button className="auth-submit-btn" type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Creating account…' : 'Sign up'}
          </button>
        </form>

        <SocialButtons onError={setFormError} />

        <div className="auth-switch">
          Already have an account?{' '}
          <button type="button" className="auth-switch-link" onClick={onSwitchToLogin}>
            Log in
          </button>
        </div>

        <p className="auth-disclaimer">
          Demo account storage: your account lives only in this browser's local storage — there's
          no server behind it yet.
        </p>
      </div>
    </div>
  );
}

export default RegisterPage;
