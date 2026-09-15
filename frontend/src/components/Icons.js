// src/components/Icons.js
import React from 'react';

const defaultProps = {
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 2,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
  'aria-hidden': 'true',
};

export function BugIcon({ size = 20, className = '', ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...defaultProps} className={`icon icon-bug ${className}`} {...props}>
      <path d="m8 2 1.88 1.88" />
      <path d="M14.12 3.88 16 2" />
      <path d="M9 7.13v-1a3.003 3.003 0 1 1 6 0v1" />
      <path d="M12 20c-3.3 0-6-2.7-6-6v-3a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v3c0 3.3-2.7 6-6 6" />
      <path d="M12 20v-9" />
      <path d="M6.53 9C4.6 8.8 3 7.1 3 5" />
      <path d="M6 13H2" />
      <path d="M3 21c0-2.1 1.7-3.9 3.8-4" />
      <path d="M20.97 5c0 2.1-1.6 3.8-3.5 4" />
      <path d="M22 13h-4" />
      <path d="M17.2 17c2.1.1 3.8 1.9 3.8 4" />
    </svg>
  );
}

export function ChatIcon({ size = 20, className = '', ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...defaultProps} className={`icon icon-chat ${className}`} {...props}>
      <path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z" />
    </svg>
  );
}

export function HistoryIcon({ size = 20, className = '', ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...defaultProps} className={`icon icon-history ${className}`} {...props}>
      <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
      <path d="M3 3v5h5" />
      <path d="M12 7v5l4 2" />
    </svg>
  );
}

export function KnowledgeIcon({ size = 20, className = '', ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...defaultProps} className={`icon icon-knowledge ${className}`} {...props}>
      <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
      <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
    </svg>
  );
}

export function SettingsIcon({ size = 20, className = '', ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...defaultProps} className={`icon icon-settings ${className}`} {...props}>
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </svg>
  );
}

export function SearchIcon({ size = 18, className = '', ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...defaultProps} className={`icon icon-search ${className}`} {...props}>
      <circle cx="11" cy="11" r="8" />
      <path d="m21 21-4.3-4.3" />
    </svg>
  );
}

export function TrashIcon({ size = 16, className = '', ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...defaultProps} className={`icon icon-trash ${className}`} {...props}>
      <path d="M3 6h18" />
      <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
      <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
      <line x1="10" y1="11" x2="10" y2="17" />
      <line x1="14" y1="11" x2="14" y2="17" />
    </svg>
  );
}

export function LogoutIcon({ size = 16, className = '', ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...defaultProps} className={`icon icon-logout ${className}`} {...props}>
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <polyline points="16 17 21 12 16 7" />
      <line x1="21" y1="12" x2="9" y2="12" />
    </svg>
  );
}

export function PlusIcon({ size = 18, className = '', ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...defaultProps} className={`icon icon-plus ${className}`} {...props}>
      <path d="M5 12h14" />
      <path d="M12 5v14" />
    </svg>
  );
}

export function CloseIcon({ size = 18, className = '', ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...defaultProps} className={`icon icon-close ${className}`} {...props}>
      <path d="M18 6 6 18" />
      <path d="m6 6 12 12" />
    </svg>
  );
}

export function UploadIcon({ size = 18, className = '', ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...defaultProps} className={`icon icon-upload ${className}`} {...props}>
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="17 8 12 3 7 8" />
      <line x1="12" y1="3" x2="12" y2="15" />
    </svg>
  );
}

export function SendIcon({ size = 18, className = '', ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...defaultProps} className={`icon icon-send ${className}`} {...props}>
      <path d="m22 2-7 20-4-9-9-4Z" />
      <path d="M22 2 11 13" />
    </svg>
  );
}

export function PaperclipIcon({ size = 16, className = '', ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...defaultProps} className={`icon icon-paperclip ${className}`} {...props}>
      <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48" />
    </svg>
  );
}

export function MenuIcon({ size = 20, className = '', ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...defaultProps} className={`icon icon-menu ${className}`} {...props}>
      <line x1="4" y1="6" x2="20" y2="6" />
      <line x1="4" y1="12" x2="20" y2="12" />
      <line x1="4" y1="18" x2="20" y2="18" />
    </svg>
  );
}

export function ChevronDownIcon({ size = 18, className = '', ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...defaultProps} className={`icon icon-chevron-down ${className}`} {...props}>
      <path d="m6 9 6 6 6-6" />
    </svg>
  );
}

export function ChevronUpIcon({ size = 18, className = '', ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...defaultProps} className={`icon icon-chevron-up ${className}`} {...props}>
      <path d="m18 15-6-6-6 6" />
    </svg>
  );
}

export function SpinnerIcon({ size = 18, className = '', ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...defaultProps} className={`icon icon-spinner ${className}`} {...props}>
      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
    </svg>
  );
}

export function CheckIcon({ size = 16, className = '', ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...defaultProps} className={`icon icon-check ${className}`} {...props}>
      <path d="M20 6 9 17l-5-5" />
    </svg>
  );
}

export function SparklesIcon({ size = 18, className = '', ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...defaultProps} className={`icon icon-sparkles ${className}`} {...props}>
      <path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3Z" />
    </svg>
  );
}

export function CpuIcon({ size = 18, className = '', ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...defaultProps} className={`icon icon-cpu ${className}`} {...props}>
      <rect width="16" height="16" x="4" y="4" rx="2" />
      <rect width="6" height="6" x="9" y="9" rx="1" />
      <path d="M15 2v2" />
      <path d="M15 20v2" />
      <path d="M2 15h2" />
      <path d="M2 9h2" />
      <path d="M20 15h2" />
      <path d="M20 9h2" />
      <path d="M9 2v2" />
      <path d="M9 20v2" />
    </svg>
  );
}