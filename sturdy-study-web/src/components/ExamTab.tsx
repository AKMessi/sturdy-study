"use client";

import { useState, useEffect, useRef } from "react";
import { Loader2, FileText, Download, CheckCircle2, AlertCircle } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { startExamGeneration, getExamJobStatus, ExamJob } from "@/lib/api";
import { cn } from "@/lib/utils";

interface ExamTabProps {
  userId: string;
}

export function ExamTab({ userId }: ExamTabProps) {
  const [numQuestions, setNumQuestions] = useState<number>(20);
  const [isGenerating, setIsGenerating] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<ExamJob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

  // Polling effect
  useEffect(() => {
    if (!jobId || !isGenerating) {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
      return;
    }

    // Poll immediately, then every 3 seconds
    const pollStatus = async () => {
      try {
        const status = await getExamJobStatus(jobId);
        setJobStatus(status);

        if (status.status === "complete" || status.status === "error") {
          setIsGenerating(false);
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
          if (status.status === "error") {
            setError(status.error || "An error occurred during exam generation");
          }
        }
      } catch (err) {
        setIsGenerating(false);
        setError(err instanceof Error ? err.message : "Failed to check exam status");
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
      }
    };

    pollStatus();
    pollingIntervalRef.current = setInterval(pollStatus, 3000);

    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, [jobId, isGenerating]);

  const handleGenerate = async () => {
    if (!userId || numQuestions < 1 || numQuestions > 50) {
      setError("Number of questions must be between 1 and 50");
      return;
    }

    setError(null);
    setJobStatus(null);
    setIsGenerating(true);

    try {
      const job = await startExamGeneration({
        user_id: userId,
        num_questions: numQuestions,
      });
      setJobId(job.job_id);
      setJobStatus(job);
    } catch (err) {
      setIsGenerating(false);
      setError(err instanceof Error ? err.message : "Failed to start exam generation");
    }
  };

  const handleReset = () => {
    setJobId(null);
    setJobStatus(null);
    setIsGenerating(false);
    setError(null);
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  };

  return (
    <div className="space-y-6">
      {/* Input Section */}
      <Card className="border-border/50">
        <CardHeader>
          <CardTitle>Generate Practice Exam</CardTitle>
          <CardDescription>
            Create a custom PDF exam based on your study materials
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="num-questions">Number of Questions</Label>
            <Input
              id="num-questions"
              type="number"
              min={1}
              max={50}
              value={numQuestions}
              onChange={(e) => {
                const value = parseInt(e.target.value, 10);
                if (!isNaN(value)) {
                  setNumQuestions(Math.max(1, Math.min(50, value)));
                } else if (e.target.value === "") {
                  setNumQuestions(20);
                }
              }}
              disabled={isGenerating}
              className="w-full max-w-xs"
            />
            <p className="text-xs text-muted-foreground">
              Enter a number between 1 and 50 (default: 20)
            </p>
          </div>

          {error && !isGenerating && (
            <div className="flex items-center gap-2 p-3 rounded-md bg-destructive/10 text-destructive border border-destructive/20">
              <AlertCircle className="h-4 w-4" />
              <span className="text-sm">{error}</span>
            </div>
          )}

          <Button
            onClick={handleGenerate}
            disabled={isGenerating || !userId || numQuestions < 1 || numQuestions > 50}
            className="w-full sm:w-auto"
          >
            {isGenerating ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <FileText className="h-4 w-4 mr-2" />
                Generate Exam
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Progress Section */}
      {isGenerating && jobStatus && jobStatus.status === "running" && (
        <Card className="border-border/50">
          <CardContent className="pt-6">
            <div className="flex flex-col items-center justify-center space-y-4 py-8">
              <Loader2 className="h-12 w-12 animate-spin text-primary" />
              <div className="text-center space-y-2">
                <h3 className="font-semibold text-lg">Generating Your Exam</h3>
                <p className="text-sm text-muted-foreground">
                  This may take a few moments. Please wait...
                </p>
                {jobId && (
                  <p className="text-xs text-muted-foreground mt-2">
                    Job ID: {jobId}
                  </p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Success Section */}
      {jobStatus && jobStatus.status === "complete" && jobStatus.download_url && (
        <Card className="border-green-500/50 bg-green-500/5">
          <CardContent className="pt-6">
            <div className="flex flex-col items-center justify-center space-y-4 py-8">
              <div className="rounded-full bg-green-500/20 p-4">
                <CheckCircle2 className="h-12 w-12 text-green-600 dark:text-green-400" />
              </div>
              <div className="text-center space-y-2">
                <h3 className="font-semibold text-lg">Exam Generated Successfully!</h3>
                <p className="text-sm text-muted-foreground">
                  Your practice exam is ready to download
                </p>
              </div>
              <div className="flex gap-3 pt-2">
                <Button
                  asChild
                  size="lg"
                  className="bg-green-600 hover:bg-green-700 dark:bg-green-500 dark:hover:bg-green-600"
                >
                  <a href={`http://localhost:8000${jobStatus.download_url}`} target="_blank" rel="noopener noreferrer">
                    <Button>Download PDF</Button>
                  </a>
                </Button>
                <Button
                  variant="outline"
                  size="lg"
                  onClick={handleReset}
                >
                  Generate Another
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Error Section */}
      {jobStatus && jobStatus.status === "error" && (
        <Card className="border-destructive/50 bg-destructive/5">
          <CardContent className="pt-6">
            <div className="flex flex-col items-center justify-center space-y-4 py-8">
              <div className="rounded-full bg-destructive/20 p-4">
                <AlertCircle className="h-12 w-12 text-destructive" />
              </div>
              <div className="text-center space-y-2">
                <h3 className="font-semibold text-lg">Generation Failed</h3>
                <p className="text-sm text-muted-foreground">
                  {jobStatus.error || "An error occurred during exam generation"}
                </p>
              </div>
              <Button variant="outline" onClick={handleReset}>
                Try Again
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

