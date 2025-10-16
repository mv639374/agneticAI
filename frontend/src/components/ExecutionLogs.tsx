// frontend/src/components/ExecutionLogs.tsx

/**
 * ExecutionLogs Component
 * 
 * Displays real-time execution logs from agents.
 * Shows which agents are running, their progress, and results.
 */

'use client';

import React, { useState, useEffect } from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import type { WebSocketMessage } from '@/types/agent';

interface ExecutionLogsProps {
  className?: string;
  clientId: string;  // Unique ID for WebSocket connection
}

/**
 * Log entry interface.
 */
interface LogEntry {
  id: string;
  timestamp: string;
  type: string;
  agentName?: string;
  message: string;
  data?: any;
}

export function ExecutionLogs({ className, clientId }: ExecutionLogsProps) {
  
  // ==========================================================================
  // STATE
  // ==========================================================================
  
  /**
   * Array of log entries.
   * We'll add new logs as WebSocket messages arrive.
   */
  const [logs, setLogs] = useState<LogEntry[]>([]);
  
  /**
   * Maximum number of logs to keep (prevent memory issues).
   */
  const MAX_LOGS = 100;
  
  // ==========================================================================
  // WEBSOCKET CONNECTION
  // ==========================================================================
  
  /**
   * Connect to WebSocket for real-time updates.
   * 
   * This uses our custom hook from earlier.
   */
  const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
  const { status, lastMessage } = useWebSocket(
    `${wsUrl}/ws/agents/${clientId}`,
    true // enabled
  );
  
  // ==========================================================================
  // HANDLE NEW WEBSOCKET MESSAGES
  // ==========================================================================
  
  /**
   * When a new WebSocket message arrives, add it to logs.
   */
  useEffect(() => {
    if (!lastMessage) return;
    
    // Create log entry from WebSocket message
    const logEntry: LogEntry = {
      id: `${Date.now()}-${Math.random()}`, // Unique ID
      timestamp: lastMessage.timestamp || new Date().toISOString(),
      type: lastMessage.type,
      agentName: lastMessage.agent_name,
      message: getLogMessage(lastMessage),
      data: lastMessage.data,
    };
    
    // Add to logs (keeping only MAX_LOGS entries)
    setLogs(prevLogs => {
      const newLogs = [...prevLogs, logEntry];
      
      // If too many logs, remove oldest ones
      if (newLogs.length > MAX_LOGS) {
        return newLogs.slice(-MAX_LOGS); // Keep last MAX_LOGS entries
      }
      
      return newLogs;
    });
    
  }, [lastMessage]); // Run when lastMessage changes
  
  // ==========================================================================
  // HELPER FUNCTIONS
  // ==========================================================================
  
  /**
   * Generate human-readable message from WebSocket data.
   * 
   * This converts technical WebSocket messages into user-friendly text.
   */
  function getLogMessage(wsMessage: WebSocketMessage): string {
    switch (wsMessage.type) {
      case 'connected':
        return 'Connected to agent system';
      
      case 'agent_started':
        return `${wsMessage.agent_name} started processing`;
      
      case 'agent_progress':
        return wsMessage.message || `${wsMessage.agent_name} in progress`;
      
      case 'agent_completed':
        return `${wsMessage.agent_name} completed successfully`;
      
      case 'error':
        return `Error: ${wsMessage.message || 'Unknown error'}`;
      
      case 'pong':
        return 'Connection alive';
      
      default:
        return wsMessage.message || 'Unknown event';
    }
  }
  
  /**
   * Get badge color based on message type.
   */
  function getBadgeVariant(type: string): "default" | "secondary" | "destructive" | "outline" {
    switch (type) {
      case 'agent_started':
        return 'secondary';  // Yellow
      case 'agent_completed':
        return 'default';    // Green
      case 'error':
        return 'destructive'; // Red
      default:
        return 'outline';    // Gray
    }
  }
  
  /**
   * Format timestamp for display.
   */
  function formatTime(timestamp: string): string {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit'
    });
  }
  
  // ==========================================================================
  // RENDER
  // ==========================================================================
  
  return (
    <Card className={className}>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Execution Logs</CardTitle>
        
        {/* WebSocket connection status indicator */}
        <div className="flex items-center space-x-2">
          <div 
            className={`w-2 h-2 rounded-full ${
              status === 'connected' ? 'bg-green-500' :
              status === 'connecting' ? 'bg-yellow-500' :
              'bg-red-500'
            }`}
          />
          <span className="text-sm text-muted-foreground">
            {status}
          </span>
        </div>
      </CardHeader>
      
      <CardContent>
        {/* Scrollable log area */}
        {/* 
          ScrollArea is a shadcn component that provides custom scrollbar.
          "h-[400px]" is Tailwind CSS for height: 400px
        */}
        <ScrollArea className="h-[400px] pr-4">
          {/* Show message if no logs */}
          {logs.length === 0 && (
            <div className="text-center text-muted-foreground py-8">
              <p>Waiting for agent activity...</p>
            </div>
          )}
          
          {/* Render all logs */}
          <div className="space-y-3">
            {/* 
              Reverse logs so newest appears at bottom (like a chat).
              If you want newest at top, remove .reverse()
            */}
            {logs.map((log) => (
              <div 
                key={log.id}
                className="flex flex-col space-y-1 p-3 border rounded-lg hover:bg-accent transition-colors"
              >
                {/* Header: timestamp and type badge */}
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground font-mono">
                    {formatTime(log.timestamp)}
                  </span>
                  
                  <Badge variant={getBadgeVariant(log.type)}>
                    {log.type}
                  </Badge>
                </div>
                
                {/* Agent name (if available) */}
                {log.agentName && (
                  <span className="text-sm font-medium">
                    {log.agentName.replace(/_/g, ' ')}
                  </span>
                )}
                
                {/* Log message */}
                <p className="text-sm">{log.message}</p>
                
                {/* Additional data (collapsible, if present) */}
                {log.data && (
                  <details className="text-xs">
                    <summary className="cursor-pointer text-muted-foreground hover:text-foreground">
                      Show details
                    </summary>
                    <pre className="mt-2 p-2 bg-muted rounded overflow-x-auto">
                      {JSON.stringify(log.data, null, 2)}
                    </pre>
                  </details>
                )}
              </div>
            ))}
          </div>
        </ScrollArea>
        
        {/* Clear logs button */}
        {logs.length > 0 && (
          <div className="mt-4 text-center">
            <button
              onClick={() => setLogs([])}
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              Clear logs ({logs.length})
            </button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
