// frontend/src/components/Dashboard.tsx

/**
 * Dashboard Component
 * 
 * Main dashboard that combines all components into a cohesive UI.
 * This is the "page" that users see.
 */

'use client';

import React, { useState } from 'react';
import { AgentStatus } from './AgentStatus';
import { ChatInterface } from './ChatInterface';
import { ExecutionLogs } from './ExecutionLogs';

/**
 * Generate unique client ID for WebSocket.
 * 
 * This ensures each browser tab gets its own WebSocket connection.
 */
function generateClientId(): string {
  return `client-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

export function Dashboard() {
  
  // ==========================================================================
  // STATE
  // ==========================================================================
  
  /**
   * Client ID for WebSocket connection.
   * 
   * We use useState with function initializer to generate ID only once.
   * Without this, ID would regenerate on every render.
   */
  const [clientId] = useState(() => generateClientId());
  
  // ==========================================================================
  // RENDER
  // ==========================================================================
  
  /**
   * LAYOUT EXPLANATION:
   * 
   * We use CSS Grid for responsive layout:
   * - Desktop: 2 columns (sidebar + main content)
   * - Mobile: 1 column (stack vertically)
   * 
   * Tailwind CSS classes:
   * - min-h-screen: minimum height = full viewport
   * - bg-background: background color from theme
   * - grid: CSS Grid layout
   * - grid-cols-1: 1 column on mobile
   * - lg:grid-cols-4: 4 columns on large screens
   * - gap-4: spacing between grid items
   * - p-4: padding on all sides
   */
  
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto p-4">
          <h1 className="text-3xl font-bold">
            Multi-Agent AI System
          </h1>
          <p className="text-muted-foreground mt-1">
            Autonomous enterprise intelligence powered by 5 specialized agents
          </p>
        </div>
      </header>
      
      {/* Main content grid */}
      <main className="container mx-auto p-4">
        {/* 
          Grid layout:
          - AgentStatus: 1 column on mobile, spans left column on desktop
          - ChatInterface: Full width on mobile, spans 2 middle columns on desktop
          - ExecutionLogs: Full width on mobile, spans right column on desktop
        */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          
          {/* Left sidebar: Agent Status */}
          {/* lg:col-span-1 means "take 1 column on large screens" */}
          <aside className="lg:col-span-1">
            <AgentStatus />
          </aside>
          
          {/* Center: Chat Interface */}
          {/* lg:col-span-2 means "take 2 columns on large screens" */}
          <section className="lg:col-span-2">
            <ChatInterface />
          </section>
          
          {/* Right sidebar: Execution Logs */}
          {/* lg:col-span-1 means "take 1 column on large screens" */}
          <aside className="lg:col-span-1">
            <ExecutionLogs clientId={clientId} />
          </aside>
        </div>
        
        {/* Footer with instructions */}
        <footer className="mt-8 text-center text-sm text-muted-foreground">
          <p>
            Ask questions, analyze data, generate reports - the agents will collaborate to help you.
          </p>
        </footer>
      </main>
    </div>
  );
}
