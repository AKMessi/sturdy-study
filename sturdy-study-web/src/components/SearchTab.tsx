"use client";

import { useState } from "react";
import { Search, Loader2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { findProblems } from "@/lib/api";
import { cn } from "@/lib/utils";

interface SearchTabProps {
  userId: string;
}

export function SearchTab({ userId }: SearchTabProps) {
  const [topic, setTopic] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastTopic, setLastTopic] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!topic.trim() || !userId) return;

    setIsSearching(true);
    setError(null);
    setResults(null);
    setLastTopic(topic.trim());

    try {
      const response = await findProblems({
        topic: topic.trim(),
        user_id: userId,
      });
      setResults(response.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to search for practice problems");
    } finally {
      setIsSearching(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !isSearching) {
      handleSearch();
    }
  };

  return (
    <div className="space-y-6">
      {/* Search Input Section */}
      <Card className="border-border/50">
        <CardHeader>
          <CardTitle>Find Practice Problems</CardTitle>
          <CardDescription>
            Search the web for relevant practice problems on any topic
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="topic-input">Topic</Label>
            <div className="flex gap-2">
              <Input
                id="topic-input"
                placeholder="e.g., Linear Algebra, Machine Learning, Calculus..."
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={isSearching}
                className="flex-1"
              />
              <Button
                onClick={handleSearch}
                disabled={!topic.trim() || isSearching || !userId}
                className="shrink-0"
              >
                {isSearching ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Searching...
                  </>
                ) : (
                  <>
                    <Search className="h-4 w-4 mr-2" />
                    Search
                  </>
                )}
              </Button>
            </div>
          </div>

          {error && (
            <div className="p-3 rounded-md bg-destructive/10 text-destructive border border-destructive/20 text-sm">
              {error}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Loading Skeleton */}
      {isSearching && (
        <Card className="border-border/50">
          <CardContent className="pt-6">
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <Loader2 className="h-5 w-5 animate-spin text-primary" />
                <div className="space-y-2 flex-1">
                  <div className="h-4 bg-muted rounded w-3/4 animate-pulse" />
                  <div className="h-4 bg-muted rounded w-1/2 animate-pulse" />
                </div>
              </div>
              <div className="space-y-2">
                <div className="h-3 bg-muted rounded w-full animate-pulse" />
                <div className="h-3 bg-muted rounded w-full animate-pulse" />
                <div className="h-3 bg-muted rounded w-5/6 animate-pulse" />
              </div>
              <div className="space-y-2 pt-4">
                <div className="h-3 bg-muted rounded w-full animate-pulse" />
                <div className="h-3 bg-muted rounded w-full animate-pulse" />
                <div className="h-3 bg-muted rounded w-4/5 animate-pulse" />
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Results Section */}
      {results && !isSearching && (
        <Card className="border-border/50">
          <CardHeader>
            <CardTitle>Search Results</CardTitle>
            {lastTopic && (
              <CardDescription>
                Practice problems for: <span className="font-medium">{lastTopic}</span>
              </CardDescription>
            )}
          </CardHeader>
          <CardContent>
            <div className="prose prose-sm dark:prose-invert max-w-none [&_p]:my-3 [&_ul]:my-3 [&_ol]:my-3 [&_h1]:text-xl [&_h1]:font-bold [&_h1]:mt-6 [&_h1]:mb-4 [&_h2]:text-lg [&_h2]:font-semibold [&_h2]:mt-5 [&_h2]:mb-3 [&_h3]:text-base [&_h3]:font-semibold [&_h3]:mt-4 [&_h3]:mb-2 [&_code]:bg-muted [&_code]:px-1.5 [&_code]:py-0.5 [&_code]:rounded [&_code]:text-sm [&_pre]:bg-muted [&_pre]:p-4 [&_pre]:rounded-lg [&_pre]:overflow-x-auto [&_pre]:my-4 [&_blockquote]:border-l-4 [&_blockquote]:border-muted [&_blockquote]:pl-4 [&_blockquote]:italic [&_blockquote]:my-4 [&_a]:text-primary [&_a]:underline [&_a]:hover:text-primary/80 [&_strong]:font-semibold [&_em]:italic">
              <ReactMarkdown>{results}</ReactMarkdown>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {!results && !isSearching && !error && (
        <Card className="border-border/50">
          <CardContent className="pt-6">
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Search className="h-12 w-12 text-muted-foreground mb-4 opacity-50" />
              <h3 className="font-semibold text-lg mb-2">No Search Results</h3>
              <p className="text-sm text-muted-foreground max-w-md">
                Enter a topic above and click Search to find relevant practice problems from the web.
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

