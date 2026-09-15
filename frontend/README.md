# BugFix AI

A chat-style UI for the bug-diagnosis assistant. Initial submissions call the
FastAPI diagnosis endpoint and render structured Triage, Log Analysis, Root
Cause, Duplicate Detection, and Remediation findings. Follow-up messages are
persisted in the active diagnosis session.

## Run it

```bash
npm install
npm start      # dev server at http://localhost:3000
npm run build   # production build, compiles clean with zero warnings
```

## Authentication

Register/login is now required before you can reach the chat UI (`src/App.js`
gates everything on `AuthContext`). Important to know:

- **This is client-only demo auth, not production security.** There's no
  backend, so "accounts" are stored in this browser's `localStorage`
  (`src/utils/auth.js`). Passwords are salted and hashed with SHA-256 (Web
  Crypto) before being stored — better than plaintext, but still not a
  substitute for a real auth server. Don't reuse a real password when trying
  this out.
- Each account gets its own chat history (`bugfix-chats:<userId>`), so two
  people sharing a browser don't see each other's diagnoses.
- No password-reset or email-verification flow exists yet — if you forget a
  demo password, clear site storage and re-register.
- To wire this up to a real backend later: replace the functions in
  `src/utils/auth.js` (`registerUser`, `loginUser`, `logoutUser`,
  `getCurrentUser`, `upsertSocialUser`) with calls to your API; `AuthContext`
  and every page consuming `useAuth()` don't need to change.

## Google sign-in setup

The "Continue with Google" button appears on the login/register screens
automatically, but is **disabled with an explanatory tooltip** until you
configure it — nothing breaks if you skip this.

1. Go to [Google Cloud Console → Credentials](https://console.cloud.google.com/apis/credentials).
2. **Create Credentials → OAuth client ID → Web application**.
3. Under **Authorized JavaScript origins**, add `http://localhost:3000` (and your deployed URL later).
4. Copy the Client ID into `.env.local` (copy from `.env.example`):
   ```
   REACT_APP_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   ```
5. Restart `npm start`. The button will now be Google's official rendered "Continue with Google" widget.

This uses [Google Identity Services](https://developers.google.com/identity/gsi/web),
which is genuinely serverless — Google hands the browser a signed ID token
directly, no backend required. `src/utils/googleAuth.js` reads the token's
claims (name, email, picture, `sub`) client-side but does **not** verify its
cryptographic signature — that's fine here because nothing server-side ever
trusts this data (it just becomes a profile in `localStorage`, same as
everything else in this demo). A real backend must independently verify any
Google ID token before trusting it.

### How a Google account links to a local one
Signing in with Google creates a local account keyed by Google's user ID
(`sub`). If you later register with a **password using that same email
address** (or vice versa), it's linked to that same account automatically —
standard behavior for social login, and it only stays safe because Google
verifies the person actually owns that email.

## What changed from the original upload

**Missing functionality, now working**
- The sidebar now actually lists your past diagnoses (chat history), with
  select and delete — `deleteChat` existed in the original code but nothing
  ever called it because there was no chat list rendered.
- The sidebar search box is now wired up and filters that list live.
- `src/components/ChatArea.js` was an empty file in the upload (dead import
  risk); it's now the real messages+composer component, extracted out of
  `ChatPage.js` for readability.
- File attachments show as a removable chip above the composer instead of
  being silently spliced into the textarea's text.
- Settings now actually persist (notifications toggle, backend URL) instead
  of only showing an `alert()`. The backend URL is validated before saving.

**Bugs fixed**
- `localStorage` reads (`JSON.parse`) were unguarded — a corrupted or
  hand-edited value would throw and crash the whole app on load. All storage
  access now goes through `src/utils/storage.js`, which never throws.
- Chat IDs used `Date.now()`, which can collide if two items are created in
  the same millisecond (this happens easily under React StrictMode's double
  invoke). Replaced with a small monotonic id helper.
- The diagnosis pipeline had no cancellation: switching chats or
  starting a new diagnosis while one was still "running" left stale timers
  that could apply a stale agent-workflow update or finished message to the
  wrong chat. It's now driven by an `AbortController`, cancelled on chat
  switch, new-chat, and unmount.
- `AgentWorkflow` injected a fresh `<style>` tag with `@keyframes` on every
  single render. Moved the keyframes into the global stylesheet.
- Fixed `MessageBubble`'s bold-text parser, which produced unstable list keys
  under fast-changing content.

**Cleanup / maintainability**
- Every component's large inline `style={{...}}` object was moved into a
  co-located CSS file, so styles are computed once instead of new objects
  on every render, and the theme's CSS variables are easy to scan in one place.
- Added `src/components/ErrorBoundary.js` so an unexpected runtime error
  shows a recoverable screen instead of a blank white page.
- Added `:focus-visible` styles and `aria-label`s across interactive
  elements (sidebar buttons, delete buttons, notification switch, textarea)
  for keyboard and screen-reader users.
- Respects `prefers-reduced-motion`.
- `public/manifest.json` and `index.html` now reflect the actual app name
  instead of the CRA default "React App".

**Google sign-in**
- Added "Continue with Google" on both the login and register screens via
  Google Identity Services — see the setup section above.
- Accounts can now have more than one identity (password and/or Google)
  attached, linked automatically by matching, verified email address.
- Settings → Profile shows which method(s) an account is signed in with, and
  a Google avatar renders in the sidebar when available.
