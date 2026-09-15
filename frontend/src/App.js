import { useState } from 'react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import ChatPage from './pages/ChatPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';

function AuthGate() {
  const { user, isReady } = useAuth();
  const [authView, setAuthView] = useState('login'); // 'login' | 'register'

  if (!isReady) {
    // Avoids a login-screen flash while we check for an existing session.
    return null;
  }

  if (!user) {
    return authView === 'login' ? (
      <LoginPage onSwitchToRegister={() => setAuthView('register')} />
    ) : (
      <RegisterPage onSwitchToLogin={() => setAuthView('login')} />
    );
  }

  return <ChatPage />;
}

function App() {
  return (
    <AuthProvider>
      <AuthGate />
    </AuthProvider>
  );
}

export default App;
