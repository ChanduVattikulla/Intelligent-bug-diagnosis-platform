// src/pages/ChatPage.js
import { useState, useEffect, useRef, useCallback } from 'react';
import Sidebar from '../components/Sidebar';
import ChatArea from '../components/ChatArea';
import SettingsPage from './SettingsPage';
import HistoryPage from './HistoryPage';
import { loadJSON, saveJSON, makeId } from '../utils/storage';
import { runDiagnosis, runFollowUp, validateBugInput } from '../utils/diagnosisAgent';
import { useAuth } from '../contexts/AuthContext';
import { MenuIcon } from '../components/Icons';

const THEME_KEY = 'bugfix-theme';

function ChatPage() {
  const { user, logout } = useAuth();
  // Each account gets its own chat history so users sharing a browser don't see each other's data.
  const chatsKey = `bugfix-chats:${user.id}`;

  // --- THEME STATE ---
  const [theme, setTheme] = useState(() => loadJSON(THEME_KEY, 'dark'));

  useEffect(() => {
    document.body.setAttribute('data-theme', theme);
    saveJSON(THEME_KEY, theme);
  }, [theme]);

  const toggleTheme = () => setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));

  // --- CHAT STATE (loaded lazily so a single JSON.parse failure can't wipe data) ---
  const [chats, setChats] = useState(() => loadJSON(chatsKey, []));
  const [currentChatId, setCurrentChatId] = useState(() => {
    const initial = loadJSON(chatsKey, []);
    return initial.length > 0 ? initial[0].id : null;
  });
  const [input, setInput] = useState('');
  const [bugFields, setBugFields] = useState({
    title: '',
    description: '',
    stack_trace: '',
    error_log: '',
  });
  const [attachedFileName, setAttachedFileName] = useState('');
  const [attachedFile, setAttachedFile] = useState(null);
  const [diagnosisSessionId, setDiagnosisSessionId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [agentStatus, setAgentStatus] = useState([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [activePage, setActivePage] = useState('diagnoses');
  const messagesEndRef = useRef(null);
  const abortControllerRef = useRef(null);

  // Persist chats whenever they change (including going down to zero chats).
  useEffect(() => {
    saveJSON(chatsKey, chats);
  }, [chats, chatsKey]);

  const currentChat = chats.find((c) => c.id === currentChatId);
  const messages = currentChat?.messages || [];

  // Auto-scroll to latest message or anchor to top of expanding diagnosis report
  useEffect(() => {
    if (!messages.length) return;
    const lastMsg = messages[messages.length - 1];
    if (lastMsg.role === 'assistant' && lastMsg.content?.type === 'diagnosis') {
      const diagnosisEl = document.querySelector('.diagnosis-report-container') || document.querySelector('.diagnosis-report');
      if (diagnosisEl) {
        diagnosisEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
        return;
      }
    }
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chats, currentChatId, isLoading, agentStatus]);

  // Stops a running diagnosis so it never resolves against the wrong chat.
  const cancelActiveDiagnosis = useCallback(() => {
    abortControllerRef.current?.abort();
    setIsLoading(false);
    setAgentStatus([]);
  }, []);

  const createNewChat = () => {
    cancelActiveDiagnosis();
    setDiagnosisSessionId(null);
    setActivePage('diagnoses');
    const newChat = { id: makeId(), title: 'New Diagnosis', messages: [] };
    setChats((prev) => [newChat, ...prev]);
    setCurrentChatId(newChat.id);
    setIsSidebarOpen(true);
  };

  const selectChat = (id) => {
    if (id === currentChatId) return;
    cancelActiveDiagnosis();
    const selectedChat = chats.find((chat) => chat.id === id);
    setDiagnosisSessionId(selectedChat?.diagnosisSessionId || null);
    setCurrentChatId(id);
  };

  const deleteChat = (id) => {
    if (id === currentChatId) cancelActiveDiagnosis();
    setChats((prev) => {
      const next = prev.filter((c) => c.id !== id);
      if (currentChatId === id) {
        setCurrentChatId(next.length > 0 ? next[0].id : null);
      }
      return next;
    });
  };

  const handleNavigate = (page) => {
    setActivePage(page);
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setAttachedFile(file);
      setAttachedFileName(file.name);
      setBugFields((current) => ({ ...current, error_log: '' }));
    }
    e.target.value = ''; // allow re-selecting the same file later
  };

  const handleSend = async () => {
    const trimmed = input.trim();
    // For follow-up, require input text. For initial diagnosis, allow any bug field or attached file.
    const hasInitialContent = Boolean(
      Object.values(bugFields).some((v) => v.trim()) || attachedFile
    );
    if (isLoading) return;
    if (diagnosisSessionId ? !trimmed : !hasInitialContent) return;

    const prospectiveReport = {
      ...bugFields,
      file: attachedFile,
      description: bugFields.description || trimmed,
      error_log: attachedFileName
        ? `${bugFields.error_log}\n[File: ${attachedFileName}]`.trim()
        : bugFields.error_log,
    };
    // Ensure a chat exists.
    let chatId = currentChatId;
    if (!chatId) {
      const newChat = {
        id: makeId(),
        title: trimmed.slice(0, 30) + (trimmed.length > 30 ? '...' : ''),
        messages: [],
      };
      setChats((prev) => [newChat, ...prev]);
      chatId = newChat.id;
      setCurrentChatId(chatId);
    }

    if (!diagnosisSessionId) {
      const validationError = validateBugInput(prospectiveReport);
      if (validationError && !attachedFile) {
        setAgentStatus([]);
        setChats((prev) => prev.map((c) => (
          c.id === chatId
            ? { ...c, messages: [...c.messages, { id: makeId(), role: 'assistant', content: validationError }] }
            : c
        )));
        return;
      }
    }

    const report = prospectiveReport;
    const fullContent = [
      report.title && `Title: ${report.title}`,
      report.description && `Description: ${report.description}`,
      report.stack_trace && `Stack trace:\n${report.stack_trace}`,
      report.error_log && `Logs:\n${report.error_log}`,
    ].filter(Boolean).join('\n\n');
    const userMsg = { id: makeId(), role: 'user', content: fullContent };

    setChats((prev) =>
      prev.map((c) => (c.id === chatId ? { ...c, messages: [...c.messages, userMsg] } : c))
    );
    setInput('');
    setBugFields({ title: '', description: '', stack_trace: '', error_log: '' });
    setAttachedFileName('');
    setAttachedFile(null);
    setIsLoading(true);
    setAgentStatus([]);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      let assistantMsg;
      if (diagnosisSessionId) {
        // runFollowUp returns a message object { id, role, content }
        const followUpMsg = await runFollowUp(diagnosisSessionId, trimmed, controller.signal);
        assistantMsg = typeof followUpMsg === 'object' && followUpMsg.role
          ? followUpMsg
          : { id: makeId(), role: 'assistant', content: followUpMsg };
      } else {
        const diagnosisResult = await runDiagnosis(report, controller.signal, setAgentStatus);
        assistantMsg = { id: makeId(), role: 'assistant', content: diagnosisResult };
      }
      const newSessionId = !diagnosisSessionId ? assistantMsg.content?.sessionId : null;
      if (newSessionId) setDiagnosisSessionId(newSessionId);
      setChats((prev) =>
        prev.map((c) => (c.id === chatId
          ? { ...c, ...(newSessionId ? { diagnosisSessionId: newSessionId } : {}), messages: [...c.messages, assistantMsg] }
          : c))
      );
    } catch (err) {
      if (err.name !== 'AbortError') {
        if (err.status === 404 && diagnosisSessionId) {
          // A browser chat can outlive a database session after test cleanup
          // or a database reset. Stop retrying the dead session ID.
          setDiagnosisSessionId(null);
          setChats((prev) => prev.map((c) => (
            c.id === chatId ? { ...c, diagnosisSessionId: null } : c
          )));
        }
        const errorMsg = {
          id: makeId(),
          role: 'assistant',
            content: err.status === 404 && diagnosisSessionId
            ? "This diagnosis session is no longer available. Submit the bug again to start a new session."
            : err.message || "Something went wrong while diagnosing that bug. Please try again.",
        };
        setChats((prev) =>
          prev.map((c) => (c.id === chatId ? { ...c, messages: [...c.messages, errorMsg] } : c))
        );
      }
    } finally {
      if (abortControllerRef.current === controller) {
        setIsLoading(false);
        setAgentStatus([]);
        abortControllerRef.current = null;
      }
    }
  };

  return (
    <div className="chat-container">
      <button
        className="hamburger-btn"
        onClick={() => setIsSidebarOpen(true)}
        style={{ display: isSidebarOpen ? 'none' : 'flex' }}
        aria-label="Open sidebar"
      >
        <MenuIcon size={20} />
      </button>

      <Sidebar
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen((prev) => !prev)}
        onNewChat={createNewChat}
        onNavigate={handleNavigate}
        activePage={activePage}
        chats={chats}
        currentChatId={currentChatId}
        onSelectChat={selectChat}
        onDeleteChat={deleteChat}
        user={user}
        onLogout={logout}
      />

      {activePage === 'settings' ? (
        <SettingsPage
          theme={theme}
          toggleTheme={toggleTheme}
          onNavigate={handleNavigate}
          user={user}
          onLogout={logout}
        />
      ) : activePage === 'history' ? (
        <HistoryPage onBack={() => setActivePage('diagnoses')} />
      ) : (
        <ChatArea
          messages={messages}
          agentStatus={agentStatus}
          isLoading={isLoading}
          input={input}
          setInput={setInput}
          bugFields={bugFields}
          setBugFields={setBugFields}
          isFollowUp={Boolean(diagnosisSessionId)}
          onSend={handleSend}
          attachedFileName={attachedFileName}
          onFileSelect={handleFileSelect}
          onRemoveFile={() => setAttachedFileName('')}
          messagesEndRef={messagesEndRef}
          marginLeft={isSidebarOpen ? '260px' : '0'}
        />
      )}
    </div>
  );
}

export default ChatPage;
