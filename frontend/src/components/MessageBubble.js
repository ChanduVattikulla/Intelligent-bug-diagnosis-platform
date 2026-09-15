// src/components/MessageBubble.js
import '../styles/MessageBubble.css';
import { useState } from 'react';
import { ChevronDownIcon } from './Icons';

// Splits a line on **bold** markers and renders alternating text/strong nodes.
function renderInline(line, lineKey) {
  const parts = line.split(/\*\*(.*?)\*\*/g);
  return parts.map((part, i) =>
    i % 2 === 1 ? (
      <strong key={`${lineKey}-${i}`}>{part}</strong>
    ) : (
      <span key={`${lineKey}-${i}`}>{part}</span>
    )
  );
}

function renderContent(content) {
  const lines = content.split('\n').filter((line) => line.trim() !== '');
  return lines.map((line, idx) => {
    const key = `line-${idx}`;
    if (line.startsWith('•')) {
      return (
        <div key={key} className="message-line message-bullet">
          {renderInline(line, key)}
        </div>
      );
    }
    if (line.includes('**')) {
      return (
        <div key={key} className="message-line message-bold">
          {renderInline(line, key)}
        </div>
      );
    }
    return (
      <div key={key} className="message-line">
        {line}
      </div>
    );
  });
}

function FindingSection({ number, title, status, children, delay = 0 }) {
  const [isOpen, setIsOpen] = useState(true);
  return (
    <section
      className={`diagnosis-card finding-section ${isOpen ? 'open' : 'closed'}`}
      style={{ '--reveal-delay': `${delay}ms` }}
    >
      <button
        className="finding-toggle"
        type="button"
        onClick={() => setIsOpen((open) => !open)}
        aria-expanded={isOpen}
      >
        <span className="finding-number">{number}</span>
        <h3>{title}</h3>
        {status && <b className="finding-status-badge">{status}</b>}
        <span className={`finding-arrow ${isOpen ? 'open' : 'closed'}`} aria-hidden="true">
          <ChevronDownIcon size={18} />
        </span>
      </button>
      <div className={`finding-body-container ${isOpen ? 'expanded' : 'collapsed'}`}>
        <div className="finding-body">{children}</div>
      </div>
    </section>
  );
}

function renderDiagnosis(report) {
  const triage = report.triage?.result;
  const log = report.logAnalysis?.result;
  const rootCause = report.rootCause?.result;
  const duplicates = report.duplicateDetection?.result;
  const remediation = report.remediation?.result;
  const matches = report.matches || [];
  const statusLabel = (status) => (status || 'insufficient_evidence').replaceAll('_', ' ');

  return (
    <div className="diagnosis-report-container">
      <div className="diagnosis-report">
        <div className="diagnosis-heading">
          <span className="diagnosis-kicker">Analysis complete</span>
          <h2>Bug Diagnosis Report</h2>
          {report.bugId && <span className="diagnosis-id">{report.bugId}</span>}
          <span className="diagnosis-mode">
            {report.reasoningMode === 'hosted_model' ? 'Hosted model reasoning' : 'Local evidence reasoning'}
          </span>
        </div>
        <FindingSection number="01" title="Triage" delay={0}>
          {triage ? (
            <div className="triage-grid">
              <div>
                <small>Severity</small>
                <strong className={`severity-${triage.severity?.toLowerCase()}`}>{triage.severity}</strong>
              </div>
              <div>
                <small>Priority</small>
                <strong>{triage.priority}</strong>
              </div>
              <div>
                <small>Component</small>
                <strong>{triage.component}</strong>
              </div>
              <div>
                <small>Confidence</small>
                <strong>{Math.round((triage.confidence_score || 0) * 100)}%</strong>
              </div>
            </div>
          ) : (
            <p>Not available.</p>
          )}
          {triage?.reasoning && <p className="diagnosis-note">{triage.reasoning}</p>}
        </FindingSection>

        <FindingSection number="02" title="Log Analysis" delay={120}>
          {log && log.format_detected !== 'none' ? (
            <div className="fact-list">
              {log.exception_type && (
                <div>
                  <small>Exception</small>
                  <strong>{log.exception_type}</strong>
                </div>
              )}
              {log.error_message && (
                <div>
                  <small>Message</small>
                  <strong>{log.error_message}</strong>
                </div>
              )}
              {log.failure_point && (
                <div>
                  <small>Failure point</small>
                  <strong>{[log.failure_point.file, log.failure_point.line].filter(Boolean).join(':')}</strong>
                </div>
              )}
              <div>
                <small>Format</small>
                <strong>{log.format_detected}</strong>
              </div>
              <div>
                <small>Confidence</small>
                <strong>{Math.round((log.confidence_score || 0) * 100)}%</strong>
              </div>
            </div>
          ) : (
            <p className="diagnosis-note">No recognizable stack trace was found.</p>
          )}
        </FindingSection>

        <FindingSection number="03" title="Historical Evidence" status={`${matches.length} matches`} delay={240}>
          {matches.length ? (
            matches.slice(0, 5).map((match, index) => (
              <div className="evidence-row" key={`${match.source_bug_id}-${index}`}>
                <span className="evidence-rank">{index + 1}</span>
                <div>
                  <strong>{match.source_bug_id}</strong>
                  <small>{match.source} · {match.chunk_type}</small>
                  <p>{(match.text || '').slice(0, 150)}</p>
                </div>
                <b>{Math.round((match.similarity_score || 0) * 100)}%</b>
              </div>
            ))
          ) : (
            <p className="diagnosis-note">No similar historical bugs were found.</p>
          )}
        </FindingSection>

        <FindingSection number="04" title="Root Cause" status={statusLabel(rootCause?.status)} delay={360}>
          {rootCause?.hypothesis ? (
            <>
              <div className="finding-callout">
                <strong>{rootCause.hypothesis}</strong>
                <span>{Math.round((rootCause.confidence_score || 0) * 100)}% confidence</span>
              </div>
              {rootCause.reasoning && <p className="diagnosis-note">{rootCause.reasoning}</p>}
              {rootCause.supporting_evidence?.slice(0, 3).map((item) => (
                <div className="supporting-evidence" key={`${item.bug_id}-${item.chunk_type}`}>
                  <strong>{item.bug_id}</strong>
                  <small>{item.chunk_type} · {Math.round((item.similarity_score || 0) * 100)}% match</small>
                  <p>{item.text}</p>
                </div>
              ))}
            </>
          ) : (
            <p className="diagnosis-note">Insufficient Evidence: no historical defect strongly supports a root-cause hypothesis.</p>
          )}
        </FindingSection>

        <FindingSection number="05" title="Duplicate Detection" status={statusLabel(duplicates?.status)} delay={480}>
          <p className="diagnosis-note">{duplicates?.reasoning || 'No duplicate analysis is available.'}</p>
          {duplicates?.matches?.slice(0, 3).map((match) => (
            <div className="duplicate-row" key={match.bug_id}>
              <div>
                <strong>{match.bug_id}</strong>
                <small>{match.source} · {match.chunk_type}</small>
              </div>
              <b>{Math.round((match.similarity_score || 0) * 100)}%</b>
              {match.resolution_summary && <p>{match.resolution_summary}</p>}
            </div>
          ))}
        </FindingSection>

        <FindingSection number="06" title="Recommended Fix" status={statusLabel(remediation?.status)} delay={600}>
          {remediation?.recommendations?.length ? (
            remediation.recommendations.map((item, index) => (
              <div className="recommendation" key={`${item.supporting_bug_id}-${index}`}>
                <strong>{item.recommendation}</strong>
                <small>{item.basis.replaceAll('_', ' ')} · {Math.round((item.confidence_score || 0) * 100)}% confidence</small>
                {item.supporting_evidence && <p>{item.supporting_evidence}</p>}
              </div>
            ))
          ) : (
            <p className="diagnosis-note">Insufficient Evidence: no historical resolution was available for a specific recommendation.</p>
          )}
          <p className="diagnosis-note">{report.nextSteps}</p>
        </FindingSection>
      </div>
    </div>
  );
}

function MessageBubble({ message }) {
  const isUser = message.role === 'user';
  return (
    <div className={`message-bubble ${isUser ? 'user' : 'assistant'}`}>
      {isUser ? message.content : message.content?.type === 'diagnosis' ? renderDiagnosis(message.content) : renderContent(message.content)}
    </div>
  );
}

export default MessageBubble;
