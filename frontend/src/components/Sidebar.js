// src/components/Sidebar.js
import { useState } from 'react';
import '../styles/Sidebar.css';
import {
  BugIcon,
  ChatIcon,
  HistoryIcon,
  KnowledgeIcon,
  SettingsIcon,
  SearchIcon,
  TrashIcon,
  LogoutIcon,
  PlusIcon,
  CloseIcon,
} from './Icons';

const MENU_ITEMS = [
  { id: 'diagnoses', icon: <ChatIcon size={18} />, label: 'Diagnoses' },
  { id: 'history', icon: <HistoryIcon size={18} />, label: 'Bug History' },
  { id: 'knowledge', icon: <KnowledgeIcon size={18} />, label: 'Knowledge Base' },
];

const FOOTER_ITEMS = [{ id: 'settings', icon: <SettingsIcon size={18} />, label: 'Settings' }];

function Sidebar({
  isOpen,
  onToggle,
  onNewChat,
  onNavigate,
  activePage,
  chats,
  currentChatId,
  onSelectChat,
  onDeleteChat,
  user,
  onLogout,
}) {
  const [query, setQuery] = useState('');

  const filteredChats = chats.filter((chat) =>
    chat.title.toLowerCase().includes(query.trim().toLowerCase())
  );

  const handleDelete = (e, chatId, title) => {
    e.stopPropagation(); // don't also trigger onSelectChat
    if (window.confirm(`Delete "${title}"? This can't be undone.`)) {
      onDeleteChat(chatId);
    }
  };

  return (
    <>
      <div
        className={`sidebar-overlay ${isOpen ? 'show' : ''}`}
        onClick={onToggle}
        aria-hidden="true"
      />

      <div className={`sidebar ${isOpen ? '' : 'closed'}`}>
        <div className="sidebar-header">
          <div className="brand">
            <BugIcon size={22} className="brand-icon" />
            <span>BugFix AI</span>
          </div>
          <button className="close-btn" onClick={onToggle} aria-label="Close sidebar">
            <CloseIcon size={18} />
          </button>
        </div>

        <button className="new-diagnosis-btn" onClick={onNewChat}>
          <PlusIcon size={18} />
          <span>New Diagnosis</span>
        </button>

        <div className="search-box-wrapper">
          <SearchIcon size={16} className="search-icon" />
          <input
            type="text"
            className="search-box"
            placeholder="Search diagnoses..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label="Search diagnoses"
          />
        </div>

        <nav className="nav-menu">
          {MENU_ITEMS.map((item) => (
            <div
              key={item.id}
              role="button"
              tabIndex={0}
              className={`nav-item ${activePage === item.id ? 'active' : ''}`}
              onClick={() => onNavigate(item.id)}
              onKeyDown={(e) => e.key === 'Enter' && onNavigate(item.id)}
            >
              <span className="icon">{item.icon}</span>
              <span className="label">{item.label}</span>
            </div>
          ))}
        </nav>

        {activePage === 'diagnoses' && (
          <div className="chat-list">
            {chats.length === 0 ? (
              <div className="chat-list-empty">No diagnoses yet</div>
            ) : filteredChats.length === 0 ? (
              <div className="chat-list-empty">No matches for "{query}"</div>
            ) : (
              filteredChats.map((chat) => (
                <div
                  key={chat.id}
                  role="button"
                  tabIndex={0}
                  className={`chat-item ${chat.id === currentChatId ? 'active' : ''}`}
                  onClick={() => onSelectChat(chat.id)}
                  onKeyDown={(e) => e.key === 'Enter' && onSelectChat(chat.id)}
                  title={chat.title}
                >
                  <span className="chat-item-title">{chat.title}</span>
                  <button
                    className="chat-item-delete"
                    onClick={(e) => handleDelete(e, chat.id, chat.title)}
                    aria-label={`Delete "${chat.title}"`}
                  >
                    <TrashIcon size={15} />
                  </button>
                </div>
              ))
            )}
          </div>
        )}

        <hr className="divider" />

        <div className="sidebar-footer">
          {FOOTER_ITEMS.map((item) => (
            <div
              key={item.id}
              role="button"
              tabIndex={0}
              className={`nav-item ${activePage === item.id ? 'active' : ''}`}
              onClick={() => onNavigate(item.id)}
              onKeyDown={(e) => e.key === 'Enter' && onNavigate(item.id)}
            >
              <span className="icon">{item.icon}</span>
              <span className="label">{item.label}</span>
            </div>
          ))}

          {user && (
            <div className="account-row">
              {user.avatarUrl ? (
                <img className="account-avatar" src={user.avatarUrl} alt="" referrerPolicy="no-referrer" />
              ) : (
                <div className="account-avatar account-avatar-fallback" aria-hidden="true">
                  {user.name.trim().charAt(0).toUpperCase() || '?'}
                </div>
              )}
              <div className="account-info">
                <div className="account-name">{user.name}</div>
                <div className="account-email">{user.email}</div>
              </div>
              <button className="logout-btn" onClick={onLogout} aria-label="Log out">
                <LogoutIcon size={16} />
              </button>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

export default Sidebar;
