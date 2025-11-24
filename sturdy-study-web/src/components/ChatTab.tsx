"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { chat, ChatResponse } from "@/lib/api";
import { cn } from "@/lib/utils";

interface Message {
  role: "user" | "assistant";
  content: string;
  isQuiz?: boolean;
  quizData?: QuizData;
}

interface QuizData {
  questions: Array<{
    question_text: string;
    options: string[];
    correct_answer: string;
  }>;
}

interface ChatTabProps {
  userId: string;
}

export function ChatTab({ userId }: ChatTabProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // --- NEW: Reset chat when course changes ---
  // This is the critical fix for the Composite Key update
  useEffect(() => {
    setMessages([]);
  }, [userId]);
  // --- END NEW SECTION ---

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

  const parseQuiz = (quizString: string): QuizData | null => {
    try {
      // Try to extract JSON from the string (in case there's extra text)
      const jsonMatch = quizString.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const parsed = JSON.parse(jsonMatch[0]);
        if (parsed.questions && Array.isArray(parsed.questions)) {
          return parsed as QuizData;
        }
      }
      return null;
    } catch {
      return null;
    }
  };

  const handleSend = async () => {
    if (!inputValue.trim() || isLoading || !userId) return;

    const userMessage: Message = {
      role: "user",
      content: inputValue.trim(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);

    try {
      const response: ChatResponse = await chat({
        question: userMessage.content,
        user_id: userId,
      });

      // Check if response contains a quiz
      if (response.quiz) {
        const quizData = parseQuiz(response.quiz);
        if (quizData) {
          const quizMessage: Message = {
            role: "assistant",
            content: response.quiz, // Keep content for debugging/fallback
            isQuiz: true,
            quizData,
          };
          setMessages((prev) => [...prev, quizMessage]);
        } else {
          // Quiz string exists but couldn't parse it, show as markdown
          const assistantMessage: Message = {
            role: "assistant",
            content: response.quiz,
          };
          setMessages((prev) => [...prev, assistantMessage]);
        }
      } else if (response.answer) {
        const assistantMessage: Message = {
          role: "assistant",
          content: response.answer,
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } else {
        const assistantMessage: Message = {
          role: "assistant",
          content: "I'm sorry, I couldn't generate a response. Please try again.",
        };
        setMessages((prev) => [...prev, assistantMessage]);
      }
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

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-12rem)]"> {/* Fixed height constraint */}
      
      {/* Messages Area */}
      <ScrollArea className="flex-1 px-1">
        <div className="space-y-4 p-4 pb-20"> {/* Added padding bottom */}
          {messages.length === 0 && (
            <div className="flex items-center justify-center h-full text-muted-foreground text-sm min-h-[200px]">
              Start a conversation by asking a question or requesting a quiz
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
                {message.isQuiz && message.quizData ? (
                  <QuizComponent quizData={message.quizData} />
                ) : (
                  <div className="prose prose-sm dark:prose-invert max-w-none [&_p]:my-2 [&_ul]:my-2 [&_ol]:my-2 [&_h1]:text-lg [&_h2]:text-base [&_h3]:text-sm [&_code]:bg-muted [&_code]:px-1 [&_code]:rounded [&_pre]:bg-muted [&_pre]:p-2 [&_pre]:rounded [&_pre]:overflow-x-auto">
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                  </div>
                )}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-muted text-foreground rounded-lg px-4 py-3 flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm">Thinking...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="mt-auto border-t border-border p-4 bg-background">
        <div className="flex gap-2 items-end">
          <textarea
            ref={textareaRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question or request a quiz..."
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

// Quiz Component (unchanged)
function QuizComponent({ quizData }: { quizData: QuizData }) {
  // ... (keep your existing QuizComponent code exactly as is) ...
  // I'm omitting it here to save space, but DO NOT DELETE IT.
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, string>>({});
  const [showResults, setShowResults] = useState(false);

  const handleAnswerSelect = (questionIndex: number, option: string) => {
    if (showResults) return;
    setSelectedAnswers((prev) => ({
      ...prev,
      [questionIndex]: option,
    }));
  };

  const handleSubmit = () => {
    setShowResults(true);
  };

  const getScore = () => {
    let correct = 0;
    quizData.questions.forEach((q, index) => {
      if (selectedAnswers[index] === q.correct_answer) {
        correct++;
      }
    });
    return { correct, total: quizData.questions.length };
  };

  const score = showResults ? getScore() : null;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold text-base">Quiz</h3>
        {showResults && score && (
          <div className="text-sm font-medium">
            Score: {score.correct}/{score.total}
          </div>
        )}
      </div>

      {quizData.questions.map((question, qIndex) => (
        <Card key={qIndex} className="p-4 border-border/50">
          <div className="space-y-3">
            <p className="font-medium text-sm">{question.question_text}</p>
            <div className="space-y-2">
              {question.options.map((option, oIndex) => {
                const isSelected = selectedAnswers[qIndex] === option;
                const isCorrect = option === question.correct_answer;
                const isWrong = showResults && isSelected && !isCorrect;

                return (
                  <button
                    key={oIndex}
                    onClick={() => handleAnswerSelect(qIndex, option)}
                    disabled={showResults}
                    className={cn(
                      "w-full text-left px-3 py-2 rounded-md border text-sm transition-colors",
                      "hover:bg-accent hover:text-accent-foreground",
                      "disabled:cursor-not-allowed",
                      isSelected && !showResults && "bg-primary/10 border-primary",
                      showResults && isCorrect && "bg-green-500/20 border-green-500",
                      showResults && isWrong && "bg-destructive/20 border-destructive"
                    )}
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-medium">
                        {String.fromCharCode(65 + oIndex)}.
                      </span>
                      <span>{option}</span>
                      {showResults && isCorrect && (
                        <span className="ml-auto text-green-600 dark:text-green-400 text-xs font-medium">
                          ✓ Correct
                        </span>
                      )}
                      {showResults && isWrong && (
                        <span className="ml-auto text-destructive text-xs font-medium">
                          ✗ Wrong
                        </span>
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </Card>
      ))}

      {!showResults && (
        <Button onClick={handleSubmit} className="w-full">
          Submit Quiz
        </Button>
      )}

      {showResults && (
        <div className="pt-2">
          <Button
            variant="outline"
            onClick={() => {
              setShowResults(false);
              setSelectedAnswers({});
            }}
            className="w-full"
          >
            Retake Quiz
          </Button>
        </div>
      )}
    </div>
  );
}