// src/components/AgentWorkflow.js
import { useState } from 'react';
import { SparklesIcon, CheckIcon, SpinnerIcon, ChevronDownIcon } from './Icons';

const AGENT_SUBTEXTS = {
  'Triage Agent': 'Evaluating defect severity, priority & component mapping',
  'Log Analysis Agent': 'Extracting stack trace failure points & call tree',
  'Historical Retrieval': 'Searching vector database for similar historical defect chunks',
  'Root Cause Agent': 'Synthesizing evidence-backed hypothesis & confidence',
  'Duplicate Detection Agent': 'Cross-referencing historical bug resolutions & duplicates',
  'Remediation Agent': 'Drafting actionable fix recommendations & patch strategy',
  'Report Generation': 'Consolidating findings into structured report',
};

function AgentWorkflow({ agents, isLoading }) {
  const [expanded, setExpanded] = useState(true);

  // Render ONLY when an agent pipeline is actively working in the background
  if (!isLoading || !agents || agents.length === 0) return null;

  const activeAgentIndex = agents.findIndex((item) => item.status.includes('In Progress'));
  const activeAgent = activeAgentIndex !== -1 ? agents[activeAgentIndex] : null;
  const completedCount = agents.filter((item) => item.status.includes('Completed')).length;
  const totalCount = agents.length;
  const progressPercent = Math.min(100, Math.round(((completedCount + (activeAgent ? 0.5 : 0)) / totalCount) * 100));

  const activeAgentName = activeAgent ? activeAgent.agent : 'Report Generation';
  const activeSubtext = AGENT_SUBTEXTS[activeAgentName] || 'Processing software defect signals...';

  return (
    <div className="agent-pipeline-card" role="status" aria-live="polite">
      {/* Top Shimmer Progress Accent Bar */}
      <div className="agent-pipeline-progress-bar">
        <div
          className="agent-pipeline-progress-fill"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* Main Status Header */}
      <div className="agent-pipeline-header">
        <div className="agent-pipeline-brand">
          <div className="agent-spark-icon-wrapper">
            <SparklesIcon size={16} className="agent-spark-icon" />
          </div>
          <div className="agent-headline-text">
            <div className="agent-title-row">
              <span className="agent-main-title">Autonomous Reasoning Pipeline</span>
              <span className="agent-step-counter">Step {completedCount + (activeAgent ? 1 : 0)} of {totalCount}</span>
            </div>
            <p className="agent-active-subtext">{activeSubtext}</p>
          </div>
        </div>

        <button
          type="button"
          className={`agent-expand-toggle ${expanded ? 'open' : ''}`}
          onClick={() => setExpanded((prev) => !prev)}
          aria-expanded={expanded}
          title="Toggle stage details"
        >
          <span>Details</span>
          <ChevronDownIcon size={13} />
        </button>
      </div>

      {/* Expandable Agent Stage List */}
      {expanded && (
        <div className="agent-pipeline-stages">
          {agents.map((item) => {
            const isDone = item.status.includes('Completed');
            const isWorking = item.status.includes('In Progress');

            return (
              <div
                key={item.agent}
                className={`agent-stage-row ${isDone ? 'completed' : isWorking ? 'active' : 'pending'}`}
              >
                <div className="agent-stage-left">
                  <div className="agent-stage-indicator">
                    {isDone ? (
                      <CheckIcon size={11} className="check-mark" />
                    ) : isWorking ? (
                      <SpinnerIcon size={11} className="working-spinner" />
                    ) : (
                      <span className="pending-dot" />
                    )}
                  </div>
                  <span className="agent-stage-name">{item.agent}</span>
                </div>

                <div className="agent-stage-right">
                  <span className="agent-stage-badge">
                    {isDone ? 'Done' : isWorking ? 'Running' : 'Queued'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default AgentWorkflow;
