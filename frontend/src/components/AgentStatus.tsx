// frontend/src/components/AgentStatus.tsx

/**
 * AgentStatus Component
 * 
 * REACT COMPONENT BASICS:
 * - Components are reusable pieces of UI
 * - They can accept props (inputs) and maintain state
 * - They return JSX (looks like HTML, but it's JavaScript)
 * - Function components are the modern way (vs class components)
 */

'use client'; // Next.js directive: this component uses browser-only features

import React, { useEffect, useState } from 'react';
import { getAgentStatus } from '@/lib/api';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

/**
 * TypeScript interface for component props.
 * 
 * Props are like function parameters - they let parent components
 * pass data to child components.
 * 
 * Example usage:
 * <AgentStatus className="my-custom-class" />
 */
interface AgentStatusProps {
  className?: string;  // Optional CSS class for styling
}

/**
 * AgentStatus Component
 * 
 * Displays real-time status of all agents in the system.
 * 
 * @param props - Component props
 * @returns JSX element
 */
export function AgentStatus({ className }: AgentStatusProps) {
  
  // ==========================================================================
  // STATE MANAGEMENT
  // ==========================================================================
  
  /**
   * State for agent data fetched from API.
   * 
   * Initial value is null (no data yet).
   * Type annotation ensures type safety.
   */
  const [agents, setAgents] = useState<Array<{
    name: string;
    status: string;
    temperature: number;
  }> | null>(null);
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // ==========================================================================
  // DATA FETCHING
  // ==========================================================================
  
  /**
   * useEffect to fetch agent status when component mounts.
   * 
   * This runs once when the component first appears on screen.
   */
  useEffect(() => {
    async function fetchStatus() {
      try {
        setLoading(true);
        
        // Call API to get agent status
        const data = await getAgentStatus();
        
        // Update state with fetched data
        setAgents(data.agents);
        
      } catch (err) {
        // Handle error
        const message = err instanceof Error ? err.message : 'Failed to fetch agent status';
        setError(message);
        
      } finally {
        setLoading(false);
      }
    }
    
    // Call the async function
    fetchStatus();
    
    // Optional: Set up polling to refresh every 30 seconds
    const interval = setInterval(fetchStatus, 30000);
    
    // Cleanup: clear interval when component unmounts
    return () => clearInterval(interval);
    
  }, []); // Empty deps = run once on mount
  
  // ==========================================================================
  // HELPER FUNCTION FOR STATUS COLORS
  // ==========================================================================
  
  /**
   * Get color for status badge based on agent status.
   * 
   * This is a pure function (no side effects).
   */
  const getStatusColor = (status: string): "default" | "secondary" | "destructive" => {
    switch (status.toLowerCase()) {
      case 'ready':
        return 'default';    // Green/blue color
      case 'running':
        return 'secondary';  // Yellow color
      case 'error':
        return 'destructive'; // Red color
      default:
        return 'default';
    }
  };
  
  // ==========================================================================
  // CONDITIONAL RENDERING
  // ==========================================================================
  
  /**
   * Show loading state while fetching data.
   * 
   * In React, you can return different JSX based on conditions.
   */
  if (loading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Agent Status</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">Loading agent status...</p>
        </CardContent>
      </Card>
    );
  }
  
  /**
   * Show error state if fetch failed.
   */
  if (error) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Agent Status</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-destructive">Error: {error}</p>
        </CardContent>
      </Card>
    );
  }
  
  /**
   * Show message if no agents found.
   */
  if (!agents || agents.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Agent Status</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">No agents found</p>
        </CardContent>
      </Card>
    );
  }
  
  // ==========================================================================
  // MAIN RENDER
  // ==========================================================================
  
  /**
   * JSX SYNTAX GUIDE:
   * 
   * - <Component /> = React component
   * - {variable} = Insert JavaScript expression
   * - className = CSS class (not "class" because that's a JS keyword)
   * - {condition && <Element />} = Conditional rendering
   * - {array.map(item => <Element />)} = Render list
   * - onClick={handler} = Event handler
   */
  
  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Agent Status ({agents.length})</CardTitle>
      </CardHeader>
      <CardContent>
        {/* RENDERING LISTS WITH .map() */}
        {/* 
          .map() transforms an array into a new array.
          Here, we transform agent data into JSX elements.
          
          Key prop is required for lists - it helps React identify which items changed.
          Use a unique identifier (agent.name here).
        */}
        <div className="space-y-4">
          {agents.map((agent) => (
            <div 
              key={agent.name}  // Unique key for React list reconciliation
              className="flex items-center justify-between p-3 border rounded-lg"
            >
              {/* Agent name and metadata */}
              <div className="flex flex-col">
                <span className="font-medium">
                  {/* Format agent name: remove underscores, capitalize words */}
                  {agent.name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </span>
                <span className="text-sm text-muted-foreground">
                  Temperature: {agent.temperature}
                </span>
              </div>
              
              {/* Status badge with dynamic color */}
              <Badge variant={getStatusColor(agent.status)}>
                {agent.status}
              </Badge>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
