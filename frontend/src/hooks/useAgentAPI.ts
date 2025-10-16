/**
 * Custom Hook for Agent API Calls
 * 
 * This hook manages API state (loading, error, data) for agent operations.
 */

import { useState } from 'react';
import { invokeAgents, getAgentStatus } from '@/lib/api';
import type { AgentInvokeRequest, AgentInvokeResponse } from '@/types/agent';

/**
 * Hook return type.
 */
interface UseAgentAPIReturn {
  // State
  loading: boolean;
  error: string | null;
  response: AgentInvokeResponse | null;
  
  // Methods
  invoke: (request: AgentInvokeRequest) => Promise<void>;
  clearError: () => void;
}

/**
 * Custom hook for invoking agents.
 */
export function useAgentAPI(): UseAgentAPIReturn {
  // State for tracking API call status
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<AgentInvokeResponse | null>(null);
  
  /**
   * Invoke agents with user message.
   * 
   * This is an async function that:
   * 1. Sets loading to true
   * 2. Calls API
   * 3. Updates state with response or error
   * 4. Sets loading to false
   */
  const invoke = async (request: AgentInvokeRequest) => {
    try {
      setLoading(true);
      setError(null);
      
      // Call API (this waits for response)
      const result = await invokeAgents(request);
      
      // Update state with successful response
      setResponse(result);
      
    } catch (err) {
      // Handle error
      const errorMessage = err instanceof Error ? err.message : 'Failed to invoke agents';
      setError(errorMessage);
      
      // Clear response on error
      setResponse(null);
      
    } finally {
      // Always run this, whether success or error
      setLoading(false);
    }
  };
  
  /**
   * Clear error message.
   */
  const clearError = () => {
    setError(null);
  };
  
  return {
    loading,
    error,
    response,
    invoke,
    clearError,
  };
}
