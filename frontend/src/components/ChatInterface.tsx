// frontend/src/components/ChatInterface.tsx

/**
 * ChatInterface Component
 * 
 * Main chat interface for interacting with the multi-agent system.
 * This is where users send messages and see responses.
 */

'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useAgentAPI } from '@/hooks/useAgentAPI';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import type { Message } from '@/types/agent';

interface ChatInterfaceProps {
  className?: string;
}

export function ChatInterface({ className }: ChatInterfaceProps) {
  
  // ==========================================================================
  // STATE & HOOKS
  // ==========================================================================
  
  // Current message being typed
  const [message, setMessage] = useState('');
  
  // Conversation history (all messages)
  const [messages, setMessages] = useState<Message[]>([]);
  
  // Current conversation ID
  const [conversationId, setConversationId] = useState<string | undefined>();
  
  // Use our custom hook for API calls
  const { loading, error, response, invoke, clearError } = useAgentAPI();
  
  // Ref for auto-scrolling to bottom of chat
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // ==========================================================================
  // AUTO-SCROLL TO BOTTOM
  // ==========================================================================
  
  /**
   * Scroll to bottom when new messages arrive.
   * 
   * This provides a smooth chat experience - new messages always visible.
   */
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]); // Run when messages change
  
  // ==========================================================================
  // HANDLE NEW RESPONSES
  // ==========================================================================
  
  /**
   * When API returns a response, add it to messages.
   */
  useEffect(() => {
    if (response) {
      // Update conversation ID
      setConversationId(response.conversation_id);
      
      // Add assistant's response to messages
      const assistantMessage: Message = {
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toISOString(),
      };
      
      // Update messages array
      // Spread operator [...messages, newMessage] creates new array with new item
      setMessages(prev => [...prev, assistantMessage]);
    }
  }, [response]); // Run when response changes
  
  // ==========================================================================
  // EVENT HANDLERS
  // ==========================================================================
  
  /**
   * Handle form submission.
   * 
   * Event handlers in React:
   * - onClick for buttons
   * - onChange for inputs
   * - onSubmit for forms
   * 
   * @param e - Form event (from <form onSubmit={...}>)
   */
  const handleSubmit = async (e: React.FormEvent) => {
    // Prevent default form behavior (page reload)
    e.preventDefault();
    
    // Don't submit if message is empty
    if (!message.trim()) return;
    
    // Add user message to chat
    const userMessage: Message = {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    
    // Clear input field
    setMessage('');
    
    // Clear any previous errors
    clearError();
    
    // Invoke agents with user message
    await invoke({
      message: message,
      conversation_id: conversationId,
      user_id: 'demo_user', // In production, use actual user ID
    });
  };
  
  /**
   * Handle input change.
   * 
   * Controlled components: React controls the input value.
   * - Value comes from state: value={message}
   * - Changes update state: onChange={handleInputChange}
   */
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setMessage(e.target.value);
  };
  
  /**
   * Handle Enter key press (submit on Enter).
   */
  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };
  
  // ==========================================================================
  // HELPER FUNCTIONS
  // ==========================================================================
  
  /**
   * Format timestamp for display.
   */
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };
  
  // ==========================================================================
  // RENDER
  // ==========================================================================
  
  return (
    <Card className={className}>
      <CardContent className="p-0">
        {/* Messages container */}
        <div className="h-[500px] overflow-y-auto p-4 space-y-4">
          {/* Show welcome message if no messages */}
          {messages.length === 0 && (
            <div className="text-center text-muted-foreground py-8">
              <p className="text-lg font-medium">Welcome to Multi-Agent AI System</p>
              <p className="text-sm mt-2">Ask a question to get started</p>
            </div>
          )}
          
          {/* Render all messages */}
          {messages.map((msg, index) => (
            <div
              key={index}  // Index as key is okay here (messages don't reorder)
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-lg p-3 ${
                  msg.role === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted'
                }`}
              >
                {/* Message content */}
                <p className="whitespace-pre-wrap">{msg.content}</p>
                
                {/* Timestamp */}
                {msg.timestamp && (
                  <p className="text-xs mt-1 opacity-70">
                    {formatTime(msg.timestamp)}
                  </p>
                )}
                
                {/* Agent name (for assistant messages) */}
                {msg.role === 'assistant' && msg.agentName && (
                  <p className="text-xs mt-1 opacity-70">
                    via {msg.agentName}
                  </p>
                )}
              </div>
            </div>
          ))}
          
          {/* Loading indicator */}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-muted rounded-lg p-3">
                <div className="flex items-center space-x-2">
                  <div className="animate-pulse">●</div>
                  <div className="animate-pulse animation-delay-200">●</div>
                  <div className="animate-pulse animation-delay-400">●</div>
                  <span className="text-sm ml-2">Agents processing...</span>
                </div>
              </div>
            </div>
          )}
          
          {/* Error alert */}
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          
          {/* Invisible div for auto-scroll */}
          <div ref={messagesEndRef} />
        </div>
        
        {/* Input form */}
        <div className="border-t p-4">
          <form onSubmit={handleSubmit} className="flex space-x-2">
            {/* Text input */}
            <Input
              type="text"
              placeholder="Ask a question..."
              value={message}
              onChange={handleInputChange}
              onKeyPress={handleKeyPress}
              disabled={loading}
              className="flex-1"
            />
            
            {/* Submit button */}
            <Button 
              type="submit" 
              disabled={loading || !message.trim()}
            >
              {loading ? 'Sending...' : 'Send'}
            </Button>
          </form>
        </div>
      </CardContent>
    </Card>
  );
}
