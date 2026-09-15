// src/components/SocialButtons.js
import { useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { renderGoogleButton, isGoogleConfigured } from '../utils/googleAuth';

function SocialButtons({ onError }) {
  const { loginWithGoogle } = useAuth();
  const googleContainerRef = useRef(null);
  const googleConfigured = isGoogleConfigured();

  useEffect(() => {
    if (!googleConfigured) return;
    renderGoogleButton(
      googleContainerRef.current,
      async (profile) => {
        try {
          await loginWithGoogle(profile);
        } catch (err) {
          onError(err.message || 'Google sign-in failed.');
        }
      },
      (err) => onError(err.message)
    );
    // renderGoogleButton is stable; only re-run if config availability changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [googleConfigured]);

  return (
    <div className="social-auth">
      <div className="social-divider">
        <span>or continue with</span>
      </div>

      <div className="social-buttons">
        {googleConfigured ? (
          <div ref={googleContainerRef} className="google-btn-container" />
        ) : (
          <button
            type="button"
            className="social-btn disabled"
            disabled
            title="Set REACT_APP_GOOGLE_CLIENT_ID to enable — see README.md"
          >
            <span className="social-icon" aria-hidden="true">G</span> Continue with Google
          </button>
        )}
      </div>
    </div>
  );
}

export default SocialButtons;
