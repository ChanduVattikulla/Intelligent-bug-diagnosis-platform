import { useState } from 'react';
import { loadJSON, saveJSON, removeItem } from '../utils/storage';
import { CloseIcon } from '../components/Icons';
import '../styles/SettingsPage.css';

const NOTIFICATIONS_KEY = 'bugfix-notifications';
const API_URL_KEY = 'bugfix-api-url';
const DEFAULT_API_URL = 'http://localhost:8000/api';

function isValidUrl(value) {
  try {
    // eslint-disable-next-line no-new
    new URL(value);
    return true;
  } catch {
    return false;
  }
}

function SettingsPage({ theme, toggleTheme, onNavigate, user, onLogout }) {
  const [notifications, setNotifications] = useState(() => loadJSON(NOTIFICATIONS_KEY, true));
  const [apiUrl, setApiUrl] = useState(() => loadJSON(API_URL_KEY, DEFAULT_API_URL));
  const [savedNote, setSavedNote] = useState(false);

  const urlIsValid = apiUrl.trim() === '' || isValidUrl(apiUrl.trim());

  const handleToggleNotifications = () => {
    setNotifications((prev) => {
      const next = !prev;
      saveJSON(NOTIFICATIONS_KEY, next);
      return next;
    });
  };

  const handleClearData = () => {
    if (window.confirm('Are you sure you want to clear all chat history? This cannot be undone.')) {
      removeItem('bugfix-chats');
      window.location.reload();
    }
  };

  const handleSaveApiUrl = () => {
    if (!urlIsValid) return;
    saveJSON(API_URL_KEY, apiUrl.trim());
    setSavedNote(true);
    setTimeout(() => setSavedNote(false), 2000);
  };

  const handleBackgroundClick = (e) => {
    if (e.target === e.currentTarget) onNavigate('diagnoses');
  };

  return (
    <div className="settings-container" onClick={handleBackgroundClick}>
      <div className="settings-card">
        <button
          className="settings-close-btn"
          onClick={() => onNavigate('diagnoses')}
          aria-label="Close settings"
        >
          <CloseIcon size={18} />
        </button>

        <h1 className="settings-title">Settings</h1>
        <p className="settings-subtitle">Manage your preferences</p>

        <div className="settings-section">
          <div className="settings-section-title">Profile</div>
          <div className="settings-row">
            <span className="settings-label">Display Name</span>
            <span className="settings-value">{user?.name || 'User'}</span>
          </div>
          <div className="settings-row">
            <span className="settings-label">Email</span>
            <span className="settings-value">{user?.email || ''}</span>
          </div>
          <div className="settings-row">
            <span className="settings-label">Signed in with</span>
            <span className="settings-value">
              {(Array.isArray(user?.providers) ? user.providers : [user?.provider || 'local'])
                .map((p) => (p === 'google' ? 'Google' : p === 'local' ? 'Password' : p))
                .join(', ')}
            </span>
          </div>
          <div className="settings-row">
            <span className="settings-label">
              Log out
              <span className="settings-label-desc">Ends your session on this device</span>
            </span>
            <button className="settings-danger-btn" onClick={onLogout}>
              Log out
            </button>
          </div>
        </div>

        <div className="settings-section">
          <div className="settings-section-title">Appearance</div>
          <div className="settings-row">
            <span className="settings-label">{theme === 'dark' ? 'Dark Mode' : 'Light Mode'}</span>
            <button className="settings-toggle-btn" onClick={toggleTheme}>
              {theme === 'dark' ? 'Switch to Light' : 'Switch to Dark'}
            </button>
          </div>
        </div>

        <div className="settings-section">
          <div className="settings-section-title">Notifications</div>
          <div className="settings-row">
            <span className="settings-label">
              Enable Notifications
              <span className="settings-label-desc">Diagnosis completion alerts</span>
            </span>
            <button
              className={`settings-switch ${notifications ? 'on' : ''}`}
              onClick={handleToggleNotifications}
              role="switch"
              aria-checked={notifications}
              aria-label="Enable notifications"
            >
              <span className="settings-switch-knob" />
            </button>
          </div>
        </div>

        <div className="settings-section">
          <div className="settings-section-title">API Configuration</div>
          <div className="settings-row">
            <span className="settings-label">Backend URL</span>
            <div>
              <div className="settings-input-group">
                <input
                  type="text"
                  className={`settings-input ${urlIsValid ? '' : 'invalid'}`}
                  value={apiUrl}
                  onChange={(e) => setApiUrl(e.target.value)}
                  aria-label="Backend URL"
                  aria-invalid={!urlIsValid}
                />
                <button
                  className="settings-small-btn"
                  onClick={handleSaveApiUrl}
                  disabled={!urlIsValid}
                >
                  Save
                </button>
              </div>
              {!urlIsValid && <div className="settings-error">Enter a valid URL, e.g. http://localhost:8000/api</div>}
              {savedNote && <div className="settings-saved-note">Saved ✓</div>}
            </div>
          </div>
        </div>

        <div className="settings-section">
          <div className="settings-section-title">Data</div>
          <div className="settings-row">
            <span className="settings-label">
              Clear Chat History
              <span className="settings-label-desc">Deletes all saved diagnoses</span>
            </span>
            <button className="settings-danger-btn" onClick={handleClearData}>
              Clear
            </button>
          </div>
        </div>

        <div className="settings-version">BugFix AI v1.2.0 · React</div>
      </div>
    </div>
  );
}

export default SettingsPage;
