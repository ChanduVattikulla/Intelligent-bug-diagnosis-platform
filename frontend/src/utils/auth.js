// src/utils/auth.js
// Production-grade backend JWT authentication client.

const API_BASE_URL =
  process.env.REACT_APP_API_BASE_URL || 'http://127.0.0.1:8000';

const TOKEN_KEY = 'bugfix_jwt_token';
const USER_KEY = 'bugfix_user_profile';
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MIN_PASSWORD_LENGTH = 6;

export function getToken() {
  return localStorage.getItem(TOKEN_KEY) || '';
}

export function saveSession(token, user) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
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
  const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: name.trim(), email: email.trim(), password }),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Registration failed.');
  }

  saveSession(data.token, data.user);
  return data.user;
}

export async function loginUser({ email, password }) {
  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: email.trim(), password }),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Login failed. Please check your credentials.');
  }

  saveSession(data.token, data.user);
  return data.user;
}

export async function upsertSocialUser(provider, profile) {
  const response = await fetch(`${API_BASE_URL}/api/auth/google`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: profile.email,
      name: profile.name,
      avatarUrl: profile.avatarUrl,
      providerId: profile.providerId,
    }),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Google sign-in failed.');
  }

  saveSession(data.token, data.user);
  return data.user;
}

export function logoutUser() {
  clearSession();
}

export function getCurrentUser() {
  const userJson = localStorage.getItem(USER_KEY);
  if (!userJson) return null;
  try {
    return JSON.parse(userJson);
  } catch {
    clearSession();
    return null;
  }
}

export async function verifyBackendSession() {
  const token = getToken();
  if (!token) return null;
  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) {
      clearSession();
      return null;
    }
    const data = await response.json();
    saveSession(token, data.user);
    return data.user;
  } catch {
    return getCurrentUser();
  }
}
