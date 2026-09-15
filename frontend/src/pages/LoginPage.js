// src/pages/LoginPage.js
import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import SocialButtons from '../components/SocialButtons';
import '../styles/AuthPages.css';

function LoginPage({ onSwitchToRegister }) {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [formError, setFormError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (isSubmitting) return;
    setFormError('');

    if (!email.trim() || !password) {
      setFormError('Enter your email and password.');
      return;
    }

    setIsSubmitting(true);
    try {
      await login({ email, password });
      // On success, AuthContext's user state flips and App.js swaps the view.
    } catch (err) {
      setFormError(err.message || 'Could not log in. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-brand">🐞 BugFix AI</div>
        <p className="auth-subtitle">Log in to see your saved diagnoses.</p>

        {formError && (
          <div className="auth-form-error" role="alert">
            {formError}
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <div className="auth-field">
            <label htmlFor="login-email">Email</label>
            <input
              id="login-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              autoFocus
            />
          </div>

          <div className="auth-field">
            <label htmlFor="login-password">Password</label>
            <input
              id="login-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </div>

          <button className="auth-submit-btn" type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Logging in…' : 'Log in'}
          </button>
        </form>

        <SocialButtons onError={setFormError} />

        <div className="auth-switch">
          Don't have an account?{' '}
          <button type="button" className="auth-switch-link" onClick={onSwitchToRegister}>
            Sign up
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

export default LoginPage;
