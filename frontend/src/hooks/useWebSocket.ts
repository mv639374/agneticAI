// frontend/src/hooks/useWebSocket.ts

/**
 * Custom WebSocket Hook
 * 
 * REACT HOOKS BASICS:
 * - Hooks are functions that let you "hook into" React features
 * - They start with "use" (useState, useEffect, useWebSocket)
 * - Custom hooks let you reuse stateful logic between components
 * 
 * This hook manages WebSocket connection for real-time agent updates.
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import type { WebSocketMessage } from '@/types/agent';

/**
 * WebSocket connection states.
 */
type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

/**
 * Hook return type (what this hook gives back to components).
 */
interface UseWebSocketReturn {
  // Connection state
  status: ConnectionStatus;
  
  // Latest message received
  lastMessage: WebSocketMessage | null;
  
  // Function to send messages to server
  sendMessage: (message: any) => void;
  
  // Function to manually reconnect
  reconnect: () => void;
}

/**
 * Custom hook for WebSocket connection.
 * 
 * @param url - WebSocket URL (ws://localhost:8000/ws/agents/client_id)
 * @param enabled - Whether to connect (default: true)
 * @returns WebSocket connection state and methods
 */
export function useWebSocket(
  url: string,
  enabled: boolean = true
): UseWebSocketReturn {
  
  // ==========================================================================
  // STATE MANAGEMENT WITH useState
  // ==========================================================================
  
  /**
   * useState creates reactive state in React.
   * 
   * When state changes, React automatically re-renders the component.
   * 
   * Syntax: const [value, setValue] = useState(initialValue)
   * - value: current state value
   * - setValue: function to update state
   * - initialValue: starting value
   */
  
  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  
  // ==========================================================================
  // REF FOR WEBSOCKET INSTANCE
  // ==========================================================================
  
  /**
   * useRef creates a mutable reference that persists across re-renders.
   * 
   * Unlike useState, changing a ref does NOT trigger re-render.
   * Use refs for:
   * - Storing WebSocket/interval IDs
   * - Accessing DOM elements
   * - Keeping mutable values that don't affect UI
   * 
   * Access value with: wsRef.current
   */
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  // ==========================================================================
  // WEBSOCKET CONNECTION LOGIC
  // ==========================================================================
  
  /**
   * useCallback memoizes functions to prevent unnecessary re-creations.
   * 
   * Without useCallback, this function would be recreated on every render.
   * Dependencies array [] means: "never recreate this function"
   * 
   * Why use it?
   * - Performance optimization
   * - Prevents infinite loops in useEffect dependencies
   */
  const connect = useCallback(() => {
    // Don't connect if disabled or already connecting
    if (!enabled || wsRef.current?.readyState === WebSocket.CONNECTING) {
      return;
    }
    
    // Close existing connection if any
    if (wsRef.current) {
      wsRef.current.close();
    }
    
    try {
      setStatus('connecting');
      
      // Create new WebSocket connection
      const ws = new WebSocket(url);
      wsRef.current = ws;
      
      // =======================================================================
      // WEBSOCKET EVENT HANDLERS
      // =======================================================================
      
      /**
       * onopen: Called when connection successfully established.
       */
      ws.onopen = () => {
        console.log('WebSocket connected');
        setStatus('connected');
        
        // Clear any pending reconnect attempts
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
      };
      
      /**
       * onmessage: Called when server sends data.
       */
      ws.onmessage = (event) => {
        try {
          // Parse incoming JSON message
          const message: WebSocketMessage = JSON.parse(event.data);
          console.log('WebSocket message received:', message);
          
          // Update state with new message (triggers re-render)
          setLastMessage(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };
      
      /**
       * onerror: Called when error occurs.
       */
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setStatus('error');
      };
      
      /**
       * onclose: Called when connection closes.
       */
      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setStatus('disconnected');
        
        // Auto-reconnect after 3 seconds
        if (enabled) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('Attempting to reconnect...');
            connect();
          }, 3000);
        }
      };
      
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      setStatus('error');
    }
  }, [url, enabled]); // Dependencies: recreate if url or enabled changes
  
  // ==========================================================================
  // SEND MESSAGE FUNCTION
  // ==========================================================================
  
  /**
   * Send message to WebSocket server.
   */
  const sendMessage = useCallback((message: any) => {
    // Check if connection is open
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      // Convert object to JSON string and send
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, cannot send message');
    }
  }, []); // No dependencies - function never changes
  
  // ==========================================================================
  // RECONNECT FUNCTION
  // ==========================================================================
  
  const reconnect = useCallback(() => {
    connect();
  }, [connect]);
  
  // ==========================================================================
  // SIDE EFFECTS WITH useEffect
  // ==========================================================================
  
  /**
   * useEffect runs side effects in function components.
   * 
   * Side effects are operations that affect things outside the component:
   * - Fetching data
   * - Setting up subscriptions (like WebSocket)
   * - Timers
   * - Manually changing the DOM
   * 
   * Syntax: useEffect(() => { ... }, [dependencies])
   * 
   * Dependencies control when effect runs:
   * - [] = run once on mount
   * - [value] = run when value changes
   * - No array = run on every render (usually wrong!)
   * 
   * Return function = cleanup (runs before next effect and on unmount)
   */
  useEffect(() => {
    // Connect to WebSocket when component mounts
    if (enabled) {
      connect();
    }
    
    // Cleanup function: runs when component unmounts or dependencies change
    return () => {
      console.log('Cleaning up WebSocket connection');
      
      // Close WebSocket
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      
      // Clear reconnect timeout
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };
  }, [enabled, connect]); // Re-run if enabled or connect changes
  
  // ==========================================================================
  // RETURN HOOK API
  // ==========================================================================
  
  /**
   * Return object that components can use.
   * 
   * Components call this hook like:
   * const { status, lastMessage, sendMessage } = useWebSocket(url);
   */
  return {
    status,
    lastMessage,
    sendMessage,
    reconnect,
  };
}
