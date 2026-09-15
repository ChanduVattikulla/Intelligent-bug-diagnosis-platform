// src/utils/storage.js
// Thin wrapper around localStorage that never throws — private browsing modes,
// storage quota limits, and hand-edited/corrupted JSON all degrade gracefully
// instead of crashing the app.

export function loadJSON(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    if (raw === null) return fallback;
    return JSON.parse(raw);
  } catch (err) {
    console.warn(`Could not read "${key}" from storage, using fallback.`, err);
    return fallback;
  }
}

export function saveJSON(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch (err) {
    console.warn(`Could not write "${key}" to storage.`, err);
    return false;
  }
}

export function removeItem(key) {
  try {
    localStorage.removeItem(key);
    return true;
  } catch (err) {
    console.warn(`Could not remove "${key}" from storage.`, err);
    return false;
  }
}

// Monotonic-ish unique id generator — Date.now() alone can collide when two
// items are created in the same millisecond (e.g. React StrictMode double-invoke).
let counter = 0;
export function makeId() {
  counter += 1;
  return `${Date.now().toString(36)}-${counter.toString(36)}`;
}
