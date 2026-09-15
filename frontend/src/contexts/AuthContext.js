// src/contexts/AuthContext.js
import { createContext, useContext, useEffect, useState, useCallback } from 'react';
import * as auth from '../utils/auth';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    let mounted = true;
    auth.verifyBackendSession().then((verifiedUser) => {
      if (mounted) {
        setUser(verifiedUser || auth.getCurrentUser());
        setIsReady(true);
      }
    });
    return () => {
      mounted = false;
    };
  }, []);

  const register = useCallback(async (fields) => {
    const newUser = await auth.registerUser(fields);
    setUser(newUser);
    return newUser;
  }, []);

  const login = useCallback(async (fields) => {
    const loggedInUser = await auth.loginUser(fields);
    setUser(loggedInUser);
    return loggedInUser;
  }, []);

  const logout = useCallback(() => {
    auth.logoutUser();
    setUser(null);
  }, []);

  const loginWithGoogle = useCallback(async (profile) => {
    const loggedInUser = await auth.upsertSocialUser('google', profile);
    setUser(loggedInUser);
    return loggedInUser;
  }, []);

  return (
    <AuthContext.Provider value={{ user, isReady, register, login, logout, loginWithGoogle }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
}
