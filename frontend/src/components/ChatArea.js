// src/components/ChatArea.js
import { useEffect, useRef, useState } from 'react';
import MessageBubble from './MessageBubble';
import AgentWorkflow from './AgentWorkflow';
import {
  BugIcon,
  UploadIcon,
  SendIcon,
  CloseIcon,
  PaperclipIcon,
  SpinnerIcon,
} from './Icons';

function ChatArea({
  messages,
  agentStatus,
  isLoading,
  input,
  setInput,
  bugFields,
  setBugFields,
  isFollowUp,
  onSend,
  attachedFileName,
  onFileSelect,
  onRemoveFile,
  messagesEndRef,
  marginLeft,
}) {
  const isEmpty = messages.length === 0 && agentStatus.length === 0;
  const [activeField, setActiveField] = useState('description');
  const fieldRefs = useRef({});

  const fields = [
    { key: 'title', label: 'Title', icon: 'T', required: true },
    { key: 'description', label: 'Description', icon: 'D', required: true },
    { key: 'stack_trace', label: 'Stack trace', icon: '⌁' },
    { key: 'error_log', label: 'Logs', icon: '≡' },
  ];

  const hasComposerContent = isFollowUp
    ? Boolean(input.trim())
    : Boolean(Object.values(bugFields).some((value) => value.trim()) || attachedFileName);

  const updateField = (value) => {
    setBugFields((current) => ({ ...current, [activeField]: value }));
  };

  useEffect(() => {
    if (!isFollowUp) fieldRefs.current[activeField]?.focus();
  }, [activeField, isFollowUp]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  return (
    <div className="chat-area" style={{ marginLeft }}>
      <div className="messages-container">
        {isEmpty ? (
          <div className="empty-state">
            <div className="empty-state-badge">
              <BugIcon size={38} className="empty-state-icon" />
            </div>
            <h1>BugFix AI Assistant</h1>
            <p>Describe your software bug, paste a stack trace, or upload a log file.</p>
          </div>
        ) : (
          <>
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            <AgentWorkflow agents={agentStatus} isLoading={isLoading} />
            {isLoading && agentStatus.length === 0 && (
              <div className="follow-up-thinking" role="status" aria-live="polite">
                <SpinnerIcon size={16} className="thinking-spinner" />
                <span>Thinking through the diagnosis...</span>
              </div>
            )}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-area">
        <div className="composer-box">
          {isFollowUp ? (
            <div className="follow-up-label">
              <span className="follow-up-dot" /> Continue this diagnosis
            </div>
          ) : (
            <div className="bug-field-pills" aria-label="Bug report fields">
              {fields.map((field) => (
                <button
                  key={field.key}
                  type="button"
                  className={`bug-field-pill ${activeField === field.key ? 'active' : ''}`}
                  onClick={() => setActiveField(field.key)}
                >
                  <span className="field-icon" aria-hidden="true">{field.icon}</span>
                  {field.label}{field.required ? ' *' : ''}
                </button>
              ))}
            </div>
          )}
          {!isFollowUp && attachedFileName && (
            <div className="attachment-chip">
              <PaperclipIcon size={15} className="attachment-icon" />
              <span>{attachedFileName}</span>
              <button onClick={onRemoveFile} aria-label="Remove attachment" type="button">
                <CloseIcon size={14} />
              </button>
            </div>
          )}
          <div className="composer-row">
            {!isFollowUp && (
              <label className="file-label" title="Upload log or bug report file">
                <input
                  type="file"
                  style={{ display: 'none' }}
                  onChange={onFileSelect}
                  accept=".log,.txt,.json"
                />
                <UploadIcon size={18} className="upload-icon" />
              </label>
            )}
            {isFollowUp ? (
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask a follow-up question about this diagnosis..."
                rows="2"
                aria-label="Follow-up question"
              />
            ) : activeField === 'title' ? (
              <input
                ref={(element) => { fieldRefs.current.title = element; }}
                value={bugFields.title}
                onChange={(e) => updateField(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Short bug title (required)"
                aria-label="Bug title"
              />
            ) : (
              <textarea
                ref={(element) => { fieldRefs.current[activeField] = element; }}
                value={activeField === 'description' ? (bugFields.description || input) : bugFields[activeField]}
                onChange={(e) => {
                  updateField(e.target.value);
                  if (activeField === 'description') setInput(e.target.value);
                }}
                onKeyDown={handleKeyDown}
                placeholder={`Add ${fields.find((field) => field.key === activeField)?.label.toLowerCase()}${activeField === 'description' ? ' (required)' : ''}...`}
                rows="2"
                aria-label={`${activeField} field`}
              />
            )}
            <button
              className="send-btn"
              onClick={onSend}
              disabled={isLoading || !hasComposerContent}
            >
              <span>{isLoading ? 'Working' : 'Send'}</span>
              <SendIcon size={16} className="send-icon" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ChatArea;
