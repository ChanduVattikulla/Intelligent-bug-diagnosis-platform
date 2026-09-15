// src/utils/diagnosisAgent.js

export const AGENT_NAMES = [
  'Triage Agent',
  'Log Analysis Agent',
  'Historical Retrieval',
  'Root Cause Agent',
  'Duplicate Detection Agent',
  'Remediation Agent',
  'Report Generation',
];

const PLACEHOLDER_VALUES = new Set(['asdf', 'asdfgh', 'asdfghjkl', 'qwerty', 'test', 'testing', 'hello', 'blah', 'none', 'null']);

export function validateBugInput(bugReport) {
  const combined = [bugReport.title, bugReport.description, bugReport.stack_trace, bugReport.error_log]
    .filter((value) => value && value.trim())
    .join(' ')
    .trim();
  if (!combined) return 'Please describe the bug or provide a log before submitting.';
  const normalized = combined.toLowerCase().replace(/[^a-z0-9\s]/g, '').trim();
  const placeholderWords = normalized.split(/\s+/).filter(Boolean);
  if (PLACEHOLDER_VALUES.has(normalized) || (placeholderWords.length > 0 && placeholderWords.every((word) => PLACEHOLDER_VALUES.has(word)))) {
    return 'Please provide real bug details instead of placeholder text.';
  }
  const letters = (normalized.match(/[a-z]/g) || []);
  const words = combined.match(/[a-z0-9_./:-]+/gi) || [];
  if (letters.length < 4) return 'Please provide a little more detail so the agents can analyze the problem.';
  if (words.length === 1 && letters.length < 6 && !/(error|exception|trace|failed|crash)/i.test(combined)) {
    return 'Please describe what failed, where it failed, and what you expected to happen.';
  }
  if (letters.length >= 8 && (new Set(letters).size < 3 || (letters.length <= 30 && new Set(letters).size / letters.length < 0.25))) return 'The submission looks like placeholder text. Please provide real bug details.';
  if (letters.length >= 8 && !/[aeiou]/i.test(normalized) && !/(exception|error)/i.test(normalized)) return 'The submission does not look like a readable bug report. Please add a description or log.';
  return null;
}

const API_BASE_URL =
  process.env.REACT_APP_API_BASE_URL || 'http://127.0.0.1:8000';

function checkAbort(signal) {
  if (signal?.aborted) {
    throw new DOMException('Aborted', 'AbortError');
  }
}

async function apiRequest(url, options = {}, signal) {
  checkAbort(signal);

  const response = await fetch(url, {
    ...options,
    signal,
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;

    try {
      const errorData = await response.json();
      if (errorData.detail) {
        message = errorData.detail;
      }
    } catch {
      // Keep the default error message.
    }

    const error = new Error(message);
    error.status = response.status;
    throw error;
  }

  return response.json();
}

function updateAgent(onAgentUpdate, completedAgents, currentAgent) {
  const updates = AGENT_NAMES.map((agent) => {
    if (agent === currentAgent) {
      return { agent, status: 'In Progress' };
    }
    if (completedAgents.includes(agent)) {
      return { agent, status: 'Completed' };
    }
    return { agent, status: 'Waiting' };
  });

  onAgentUpdate(updates);
}

function updateAgentFromJob(onAgentUpdate, stages) {
  const knownStages = new Map(stages.map((stage) => [stage.agent, stage.status]));
  onAgentUpdate(AGENT_NAMES.map((agent) => {
    const status = knownStages.get(agent);
    return {
      agent,
      status: status === 'completed' ? 'Completed' : status === 'working' ? 'In Progress' : status === 'error' ? 'Error' : 'Waiting',
    };
  }));
}

async function waitForDiagnosisJob(jobId, signal, onAgentUpdate) {
  while (true) {
    checkAbort(signal);
    const job = await apiRequest(`${API_BASE_URL}/api/diagnoses/jobs/${jobId}`, {}, signal);
    updateAgentFromJob(onAgentUpdate, job.stages || []);
    if (job.status === 'completed') return job.result;
    if (job.status === 'failed') throw new Error(job.error || 'The diagnosis could not be completed.');
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
}

/**
 * Sends the submitted bug to the backend, which runs the complete diagnosis
 * pipeline and returns the structured Milestone 3 findings report.
 *
 * @param {string} userText
 * @param {AbortSignal} signal
 * @param {(agents: {agent: string, status: string}[]) => void} onAgentUpdate
 * @returns {Promise<string>}
 */
export async function runDiagnosis(bugReport, signal, onAgentUpdate) {
  checkAbort(signal);

  const validationError = validateBugInput(bugReport);
  if (validationError) throw new Error(validationError);
    const title = (bugReport.title || '').trim() || (bugReport.description || '').trim().slice(0, 80) || 'Bug Report';

  // --------------------------------------------------
  // 1. SUBMIT — this alone triggers Triage + Log Analysis on the backend.
  // --------------------------------------------------
  updateAgent(onAgentUpdate, [], 'Triage Agent');

  if (!bugReport.file) {
    const started = await apiRequest(
      `${API_BASE_URL}/api/diagnoses/start`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title,
          description: (bugReport.description || '').trim(),
          stack_trace: (bugReport.stack_trace || '').trim(),
          error_log: (bugReport.error_log || '').trim(),
        }),
      },
      signal
    );
    const created = await waitForDiagnosisJob(started.job_id, signal, onAgentUpdate);
    return { ...created.report, sessionId: created.session_id };
  }

  const formData = new FormData();
  formData.append('file', bugReport.file);
  formData.append('title', title);
  formData.append('description', (bugReport.description || '').trim());
  const submittedBug = await apiRequest(
    `${API_BASE_URL}/api/diagnoses/upload`,
    { method: 'POST', body: formData },
    signal
  );

  updateAgent(onAgentUpdate, AGENT_NAMES, null);
  return { ...submittedBug.report, sessionId: submittedBug.session_id };
}

export async function runFollowUp(sessionId, content, signal) {
  const result = await apiRequest(
    `${API_BASE_URL}/api/diagnoses/${sessionId}/messages`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }),
    },
    signal
  );
  return result.message;
}
