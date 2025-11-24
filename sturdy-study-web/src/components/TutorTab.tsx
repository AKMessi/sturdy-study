"use client";

import { useState, useEffect, useRef } from "react";
import { Send, Loader2, X, GraduationCap } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { startGuidedSession, guidedChat, GuidedChatResponse } from "@/lib/api";
import { cn } from "@/lib/utils";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface TutorTabProps {
  userId: string;
}

export function TutorTab({ userId }: TutorTabProps) {
  const [topic, setTopic] = useState<string | null>(null);
  const [topicInput, setTopicInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [inputValue]);

  const handleStartSession = async () => {
    if (!topicInput.trim() || !userId) return;

    const selectedTopic = topicInput.trim();
    setTopic(selectedTopic);
    setTopicInput("");
    setIsLoading(true);

    try {
      const response: GuidedChatResponse = await startGuidedSession(userId, selectedTopic);
      
      // Add the AI's initial message
      setMessages([
        {
          role: "assistant",
          content: response.ai_message,
        },
      ]);
    } catch (error) {
      setTopic(null);
      alert(`Error starting session: ${error instanceof Error ? error.message : "Failed to start session"}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSend = async () => {
    if (!inputValue.trim() || isLoading || !userId || !topic) return;

    const userMessage: Message = {
      role: "user",
      content: inputValue.trim(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);

    try {
      // Convert messages to chat_history format
      const chatHistory = messages.map((msg) => ({
        role: msg.role,
        content: msg.content,
      }));

      const response: GuidedChatResponse = await guidedChat({
        user_id: userId,
        topic: topic,
        chat_history: chatHistory,
        user_question: userMessage.content,
      });

      const assistantMessage: Message = {
        role: "assistant",
        content: response.ai_message,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        role: "assistant",
        content: `Error: ${error instanceof Error ? error.message : "Failed to get response"}`,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleEndSession = () => {
    setTopic(null);
    setMessages([]);
    setInputValue("");
    setIsLoading(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (topic) {
        handleSend();
      } else {
        handleStartSession();
      }
    }
  };

  // UI State 1: No Topic
  if (!topic) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Card className="w-full max-w-md border-border/50">
          <CardHeader className="text-center">
            <div className="flex justify-center mb-4">
              <div className="rounded-full bg-primary/10 p-4">
                <GraduationCap className="h-8 w-8 text-primary" />
              </div>
            </div>
            <CardTitle>Start a Guided Learning Session</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="topic-input" className="text-sm font-medium">
                What topic do you want to master?
              </label>
              <Input
                id="topic-input"
                placeholder="e.g., Machine Learning, Calculus, Quantum Physics..."
                value={topicInput}
                onChange={(e) => setTopicInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={isLoading || !userId}
                className="w-full"
              />
            </div>
            <Button
              onClick={handleStartSession}
              disabled={!topicInput.trim() || isLoading || !userId}
              className="w-full"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Starting Session...
                </>
              ) : (
                "Start Learning"
              )}
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // UI State 2: Active Session
  return (
    <div className="flex flex-col h-full">
      {/* Top Bar */}
      <div className="flex items-center justify-between p-4 border-b border-border bg-card">
        <div className="flex items-center gap-2">
          <GraduationCap className="h-5 w-5 text-primary" />
          <div>
            <span className="text-sm text-muted-foreground">Current Topic:</span>
            <span className="ml-2 font-semibold">{topic}</span>
          </div>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={handleEndSession}
          disabled={isLoading}
        >
          <X className="h-4 w-4 mr-2" />
          End Session
        </Button>
      </div>

      {/* Messages Area */}
      <ScrollArea className="flex-1 px-1">
        <div className="space-y-4 p-4">
          {messages.length === 0 && (
            <div className="flex items-center justify-center h-full text-muted-foreground text-sm min-h-[200px]">
              Your tutor will guide you through learning {topic}
            </div>
          )}
          {messages.map((message, index) => (
            <div
              key={index}
              className={cn(
                "flex",
                message.role === "user" ? "justify-end" : "justify-start"
              )}
            >
              <div
                className={cn(
                  "max-w-[80%] rounded-lg px-4 py-3",
                  message.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-foreground"
                )}
              >
                <div className="prose prose-sm dark:prose-invert max-w-none [&_p]:my-2 [&_ul]:my-2 [&_ol]:my-2 [&_h1]:text-lg [&_h2]:text-base [&_h3]:text-sm [&_code]:bg-muted [&_code]:px-1 [&_code]:rounded [&_pre]:bg-muted [&_pre]:p-2 [&_pre]:rounded [&_pre]:overflow-x-auto">
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                </div>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-muted text-foreground rounded-lg px-4 py-3 flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm">Tutor is thinking...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="border-t border-border p-4">
        <div className="flex gap-2 items-end">
          <textarea
            ref={textareaRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Answer the tutor's question or ask your own..."
            disabled={isLoading || !userId}
            className={cn(
              "flex-1 min-h-[44px] max-h-[120px] resize-none rounded-md border border-input bg-background px-3 py-2 text-sm",
              "placeholder:text-muted-foreground",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
              "disabled:cursor-not-allowed disabled:opacity-50"
            )}
            rows={1}
          />
          <Button
            onClick={handleSend}
            disabled={!inputValue.trim() || isLoading || !userId}
            size="icon"
            className="shrink-0 h-[44px] w-[44px]"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}

