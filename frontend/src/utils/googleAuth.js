// src/utils/googleAuth.js
// Wraps Google Identity Services (https://accounts.google.com/gsi/client).
// This flow is genuinely serverless — Google issues a signed ID token
// directly to the browser, so no backend is required to sign a user in.
//
// IMPORTANT: this module only decodes the ID token's claims client-side; it
// does not verify the token's cryptographic signature. That's acceptable
// here because nothing server-side ever trusts this data (it just becomes a
// profile in localStorage, same as everything else in this demo). A real
// backend must independently verify any Google ID token before trusting it
// (e.g. Google's tokeninfo endpoint, or a JWT library using Google's public
// keys) — never trust a client-decoded token for anything security-sensitive.

let scriptLoadingPromise = null;

function loadGoogleScript() {
  if (window.google?.accounts?.id) return Promise.resolve();
  if (scriptLoadingPromise) return scriptLoadingPromise;

  scriptLoadingPromise = new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = resolve;
    script.onerror = () => reject(new Error('Could not load Google Sign-In. Check your connection.'));
    document.head.appendChild(script);
  });
  return scriptLoadingPromise;
}

function decodeJwt(token) {
  const payload = token.split('.')[1];
  const base64 = payload.replace(/-/g, '+').replace(/_/g, '/');
  const json = decodeURIComponent(
    atob(base64)
      .split('')
      .map((c) => '%' + c.charCodeAt(0).toString(16).padStart(2, '0'))
      .join('')
  );
  return JSON.parse(json);
}

export function isGoogleConfigured() {
  return Boolean(process.env.REACT_APP_GOOGLE_CLIENT_ID);
}

/**
 * Renders Google's official "Continue with Google" button into `container`.
 * Calls onSuccess(profile) or onError(err) once the person completes (or
 * fails) sign-in. Safe to call more than once for the same container.
 */
export async function renderGoogleButton(container, onSuccess, onError) {
  const clientId = process.env.REACT_APP_GOOGLE_CLIENT_ID;
  if (!clientId) {
    onError(new Error('Google sign-in is not configured. See README.md for setup.'));
    return;
  }
  if (!container) return;

  try {
    await loadGoogleScript();
  } catch (err) {
    onError(err);
    return;
  }

  window.google.accounts.id.initialize({
    client_id: clientId,
    callback: (response) => {
      try {
        const claims = decodeJwt(response.credential);
        if (claims.aud !== clientId) throw new Error('Token audience mismatch.');
        if (!claims.exp || claims.exp * 1000 < Date.now()) throw new Error('Token expired.');
        onSuccess({
          providerId: claims.sub,
          name: claims.name || claims.email,
          email: claims.email,
          avatarUrl: claims.picture,
        });
      } catch (err) {
        onError(err);
      }
    },
  });

  window.google.accounts.id.renderButton(container, {
    type: 'standard',
    theme: 'outline',
    size: 'large',
    width: 320,
    text: 'continue_with',
  });
}
