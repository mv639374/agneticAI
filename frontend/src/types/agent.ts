// frontend/src/types/agent.ts

/**
 * TypeScript Type Definitions
 * 
 * Types define the "shape" of data in TypeScript.
 * They help catch errors at compile-time (before running code).
 * 
 * Think of types as contracts: "This variable MUST look like this"
 */

// ============================================================================
// AGENT STATUS TYPES
// ============================================================================

/**
 * AgentStatus represents the current state of an agent.
 * 
 * TypeScript union types (|) mean "one of these values"
 * This prevents typos like "idel" instead of "idle"
 */
export type AgentStatus = 'idle' | 'running' | 'completed' | 'error';

/**
 * Interface defines the structure of an object.
 * 
 * "?" means optional (might not exist)
 * Without "?" means required (must exist)
 */
export interface Agent {
  name: string;              // Required: agent identifier
  status: AgentStatus;       // Required: current status
  temperature: number;       // Required: LLM creativity (0-1)
  lastRun?: string;         // Optional: timestamp of last execution
  errorMessage?: string;    // Optional: error details if failed
}

// ============================================================================
// MESSAGE TYPES
// ============================================================================

/**
 * Messages are the conversation history.
 * Each message has a role (who sent it) and content (what they said).
 */
export interface Message {
  role: 'user' | 'assistant' | 'system';  // Who sent this message
  content: string;                         // Message text
  timestamp?: string;                      // When it was sent
  agentName?: string;                      // Which agent responded (if assistant)
}

// ============================================================================
// API REQUEST/RESPONSE TYPES
// ============================================================================

/**
 * When we call the backend API to invoke agents,
 * we need to send data in this format.
 */
export interface AgentInvokeRequest {
  message: string;              // User's question/command
  conversation_id?: string;     // To continue existing conversation
  user_id?: string;            // User identifier
}

/**
 * The backend API responds with this format.
 * We use this type to safely access response data.
 */
export interface AgentInvokeResponse {
  success: boolean;            // Did the request succeed?
  conversation_id: string;     // Conversation identifier
  response: string;            // Agent's answer
  message_count: number;       // Total messages in conversation
  error?: string;             // Error message if failed
}

// ============================================================================
// WEBSOCKET MESSAGE TYPES
// ============================================================================

/**
 * Real-time updates from WebSocket come in this format.
 */
export interface WebSocketMessage {
  type: 'connected' | 'agent_started' | 'agent_progress' | 'agent_completed' | 'error' | 'pong';
  agent_name?: string;
  data?: any;                  // Flexible data payload
  timestamp?: string;
  message?: string;
}

// ============================================================================
// CONVERSATION TYPES
// ============================================================================

/**
 * Summary of a conversation (for list view).
 */
export interface ConversationSummary {
  id: string;
  title: string;
  user_id?: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}