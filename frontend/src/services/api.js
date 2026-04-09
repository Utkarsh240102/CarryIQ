/**
 * API Service Layer (Substep 5.1)
 * Central HTTP client for all CarryIQ backend calls.
 * All components import from here — never fetch() directly.
 */

const ENV_URL = import.meta.env.VITE_API_URL;
// Ensure Render injected URL has /api suffixed to match FastAPI routes
const BASE_URL = ENV_URL 
  ? (ENV_URL.endsWith('/api') ? ENV_URL : `${ENV_URL}/api`) 
  : 'http://localhost:8000/api';

async function request(endpoint) {
  const res = await fetch(`${BASE_URL}${endpoint}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

async function post(endpoint, body) {
  const res = await fetch(`${BASE_URL}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  /** Check if server is alive and data is available */
  health: ()    => request('/health'),

  /** Get list of all brand names */
  brands: ()    => request('/brands'),

  /** Get full intelligence metrics leaderboard */
  metrics: ()   => request('/metrics'),

  /** Get LLM sentiment analysis for all brands */
  sentiment: () => request('/sentiment'),

  /** Get executive AI market insights */
  insights: ()  => request('/insights'),

  /** Trigger the full pipeline (mock=true for synthetic data) */
  runPipeline: (mock = false) => post('/run-pipeline', { mock }),
};
