// src/utils/auth.js
// Client-only auth for a demo app with no backend yet. Local passwords are
// salted and hashed with SHA-256 (Web Crypto) before ever touching storage,
// but everything — including social-login profiles — still lives in the
// browser's localStorage. That's fine for a prototype, but a real deployment
// needs a server to own credentials and sessions. Swap this module for real
// API calls when a backend exists; the exported function contract below is
// written so AuthContext shouldn't need to change when you do.
//
// Each account can have more than one *identity* attached to it — a local
// password, a Google account — so the same person can sign in whichever way
// is convenient. Identities are linked automatically when their email
// matches an existing account. That's standard behavior for "Sign in with
// Google" buttons, but it only stays safe because Google verifies the person
// owns that email. If you add another identity provider later, only link
// this way for providers that verify email ownership.

import { loadJSON, saveJSON, makeId } from './storage';

const USERS_KEY = 'bugfix-users';
const SESSION_KEY = 'bugfix-session';

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MIN_PASSWORD_LENGTH = 8;

function normalizeEmail(email) {
  return email.trim().toLowerCase();
}

function bytesToHex(buffer) {
  return Array.from(new Uint8Array(buffer))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

function randomSaltHex() {
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  return bytesToHex(bytes.buffer);
}

async function hashPassword(password, saltHex) {
  const encoder = new TextEncoder();
  const digest = await crypto.subtle.digest('SHA-256', encoder.encode(saltHex + password));
  return bytesToHex(digest);
}

function getUsers() {
  return loadJSON(USERS_KEY, []);
}

function saveUsers(users) {
  saveJSON(USERS_KEY, users);
}

function toPublicUser(user) {
  if (!user) return null;
  const { id, name, email, avatarUrl, identities } = user;
  return {
    id,
    name,
    email,
    avatarUrl: avatarUrl || null,
    providers: identities.map((i) => i.provider),
  };
}

export function validateRegistration({ name, email, password, confirmPassword }) {
  const errors = {};
  if (!name.trim()) errors.name = 'Enter your name.';
  if (!email.trim()) errors.email = 'Enter an email address.';
  else if (!EMAIL_RE.test(email.trim())) errors.email = 'Enter a valid email address.';
  if (!password) errors.password = 'Enter a password.';
  else if (password.length < MIN_PASSWORD_LENGTH) {
    errors.password = `Password must be at least ${MIN_PASSWORD_LENGTH} characters.`;
  }
  if (confirmPassword !== password) errors.confirmPassword = "Passwords don't match.";
  return errors;
}

export async function registerUser({ name, email, password }) {
  const normalizedEmail = normalizeEmail(email);
  const users = getUsers();
  const salt = randomSaltHex();
  const passwordHash = await hashPassword(password, salt);
  const localIdentity = { provider: 'local', salt, passwordHash };

  const existing = users.find((u) => u.email === normalizedEmail);
  if (existing) {
    if (existing.identities.some((i) => i.provider === 'local')) {
      throw new Error('An account with that email already exists.');
    }
    // They previously signed up with Google only — add a password to that same account.
    existing.identities.push(localIdentity);
    saveUsers(users);
    saveJSON(SESSION_KEY, { userId: existing.id });
    return toPublicUser(existing);
  }

  const user = {
    id: makeId(),
    name: name.trim(),
    email: normalizedEmail,
    avatarUrl: null,
    identities: [localIdentity],
  };
  saveUsers([...users, user]);
  saveJSON(SESSION_KEY, { userId: user.id });
  return toPublicUser(user);
}

export async function loginUser({ email, password }) {
  const normalizedEmail = normalizeEmail(email);
  const users = getUsers();
  const user = users.find((u) => u.email === normalizedEmail);
  const localIdentity = user?.identities.find((i) => i.provider === 'local');

  // Same error for "no such user", "no password on this account", and
  // "wrong password" so login can't be used to enumerate accounts.
  const genericError = 'Incorrect email or password.';
  if (!user || !localIdentity) throw new Error(genericError);

  const attemptedHash = await hashPassword(password, localIdentity.salt);
  if (attemptedHash !== localIdentity.passwordHash) throw new Error(genericError);

  saveJSON(SESSION_KEY, { userId: user.id });
  return toPublicUser(user);
}

/**
 * Creates or updates the local account behind a social sign-in (e.g. Google).
 * @param {string} provider
 * @param {{providerId: string, name: string, email: string, avatarUrl?: string}} profile
 */
export async function upsertSocialUser(provider, profile) {
  const { providerId, name, avatarUrl } = profile;
  const normalizedEmail = normalizeEmail(profile.email || '');
  if (!normalizedEmail) {
    throw new Error(`Your ${provider} account has no accessible email address.`);
  }

  const users = getUsers();

  let user = users.find((u) =>
    u.identities.some((i) => i.provider === provider && i.providerId === providerId)
  );

  if (!user) {
    user = users.find((u) => u.email === normalizedEmail);
    if (user) {
      user.identities.push({ provider, providerId });
      if (!user.avatarUrl && avatarUrl) user.avatarUrl = avatarUrl;
    }
  }

  if (!user) {
    user = {
      id: makeId(),
      name: name || normalizedEmail,
      email: normalizedEmail,
      avatarUrl: avatarUrl || null,
      identities: [{ provider, providerId }],
    };
    users.push(user);
  }

  saveUsers(users);
  saveJSON(SESSION_KEY, { userId: user.id });
  return toPublicUser(user);
}

export function logoutUser() {
  saveJSON(SESSION_KEY, null);
}

export function getCurrentUser() {
  const session = loadJSON(SESSION_KEY, null);
  if (!session?.userId) return null;
  const user = getUsers().find((u) => u.id === session.userId);
  if (!user) {
    // Session pointed at a user that no longer exists — clear the stale session.
    logoutUser();
    return null;
  }
  return toPublicUser(user);
}
