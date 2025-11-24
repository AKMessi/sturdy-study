"use client";

import { useState, useRef } from "react";
import { Upload, File, Music, Settings, Loader2, MessageSquare, Search, GraduationCap, FileText } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { uploadPdf, uploadAudio } from "@/lib/api";
import { toast } from "sonner";

type TabType = "chat" | "search" | "exams" | "tutor";

interface SidebarProps {
  userId: string;
  setUserId: (userId: string) => void;
  activeTab: TabType;
  setActiveTab: (tab: TabType) => void;
  onUploadSuccess?: () => void;
}

export function Sidebar({ userId, setUserId, activeTab, setActiveTab, onUploadSuccess }: SidebarProps) {
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [uploadingPdf, setUploadingPdf] = useState(false);
  const [uploadingAudio, setUploadingAudio] = useState(false);
  const pdfInputRef = useRef<HTMLInputElement>(null);
  const audioInputRef = useRef<HTMLInputElement>(null);

  const handlePdfUpload = async () => {
    if (!pdfFile || !userId) return;

    setUploadingPdf(true);

    try {
      const response = await uploadPdf(userId, pdfFile);
      toast.success(
        `${response.filename} processed successfully!`,
        {
          description: `${response.documents_added} documents added to your knowledge base.`,
        }
      );
      setPdfFile(null);
      if (pdfInputRef.current) {
        pdfInputRef.current.value = "";
      }
      onUploadSuccess?.();
    } catch (error) {
      toast.error(
        "Failed to upload PDF",
        {
          description: error instanceof Error ? error.message : "An error occurred while uploading the PDF.",
        }
      );
    } finally {
      setUploadingPdf(false);
    }
  };

  const handleAudioUpload = async () => {
    if (!audioFile || !userId) return;

    setUploadingAudio(true);

    try {
      const response = await uploadAudio(userId, audioFile);
      toast.success(
        `${response.filename} transcribed successfully!`,
        {
          description: `${response.documents_added} documents added to your knowledge base.`,
        }
      );
      setAudioFile(null);
      if (audioInputRef.current) {
        audioInputRef.current.value = "";
      }
      onUploadSuccess?.();
    } catch (error) {
      toast.error(
        "Failed to upload audio",
        {
          description: error instanceof Error ? error.message : "An error occurred while uploading the audio file.",
        }
      );
    } finally {
      setUploadingAudio(false);
    }
  };

  return (
    <aside className="w-80 border-r border-border bg-card flex flex-col overflow-y-auto">
      <div className="p-6 border-b border-border">
        <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
          Sturdy Study
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          AI-Powered Learning Platform
        </p>
      </div>

      <div className="flex-1 p-6 space-y-6">
        {/* Navigation Section */}
        <Card className="border-border/50">
          <CardHeader className="pb-4">
            <CardTitle className="text-base">Navigation</CardTitle>
            <CardDescription className="text-xs">
              Switch between different features
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <Button
              variant={activeTab === "chat" ? "secondary" : "ghost"}
              className="w-full justify-start gap-2"
              onClick={() => setActiveTab("chat")}
            >
              <MessageSquare className="h-4 w-4" />
              Chat with Docs
            </Button>
            <Button
              variant={activeTab === "search" ? "secondary" : "ghost"}
              className="w-full justify-start gap-2"
              onClick={() => setActiveTab("search")}
            >
              <Search className="h-4 w-4" />
              Find Problems
            </Button>
            <Button
              variant={activeTab === "tutor" ? "secondary" : "ghost"}
              className="w-full justify-start gap-2"
              onClick={() => setActiveTab("tutor")}
            >
              <GraduationCap className="h-4 w-4" />
              Guided Tutor
            </Button>
            <Button
              variant={activeTab === "exams" ? "secondary" : "ghost"}
              className="w-full justify-start gap-2"
              onClick={() => setActiveTab("exams")}
            >
              <FileText className="h-4 w-4" />
              Generate Exam
            </Button>
          </CardContent>
        </Card>

        {/* Course Setup Section */}
        <Card className="border-border/50">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-2">
              <Settings className="h-4 w-4 text-primary" />
              <CardTitle className="text-base">Course Setup</CardTitle>
            </div>
            <CardDescription className="text-xs">
              Configure your learning environment
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2">
              <Label htmlFor="user-id" className="text-xs font-medium">
                User/Course ID
              </Label>
              <Input
                id="user-id"
                placeholder="demo_course_101"
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                className="h-9 text-sm"
              />
            </div>
          </CardContent>
        </Card>

        {/* Uploads Section */}
        <Card className="border-border/50">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-2">
              <Upload className="h-4 w-4 text-primary" />
              <CardTitle className="text-base">Uploads</CardTitle>
            </div>
            <CardDescription className="text-xs">
              Add study materials to your knowledge base
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* PDF Upload */}
            <div className="space-y-2">
              <Label htmlFor="pdf-upload" className="text-xs font-medium flex items-center gap-2">
                <File className="h-3.5 w-3.5" />
                PDF Documents
              </Label>
              <Input
                ref={pdfInputRef}
                id="pdf-upload"
                type="file"
                accept=".pdf"
                onChange={(e) => setPdfFile(e.target.files?.[0] || null)}
                className="h-9 text-xs file:mr-2 file:py-1 file:px-2 file:rounded-md file:border-0 file:text-xs file:font-medium file:bg-primary/10 file:text-primary hover:file:bg-primary/20"
                disabled={uploadingPdf}
              />
              {pdfFile && (
                <Button
                  size="sm"
                  onClick={handlePdfUpload}
                  disabled={uploadingPdf || !userId}
                  className="w-full"
                >
                  {uploadingPdf ? (
                    <>
                      <Loader2 className="h-3.5 w-3.5 mr-2 animate-spin" />
                      Uploading...
                    </>
                  ) : (
                    "Upload PDF"
                  )}
                </Button>
              )}
            </div>

            <Separator />

            {/* Audio Upload */}
            <div className="space-y-2">
              <Label htmlFor="audio-upload" className="text-xs font-medium flex items-center gap-2">
                <Music className="h-3.5 w-3.5" />
                Audio Files
              </Label>
              <Input
                ref={audioInputRef}
                id="audio-upload"
                type="file"
                accept=".mp3,.m4a,.wav"
                onChange={(e) => setAudioFile(e.target.files?.[0] || null)}
                className="h-9 text-xs file:mr-2 file:py-1 file:px-2 file:rounded-md file:border-0 file:text-xs file:font-medium file:bg-primary/10 file:text-primary hover:file:bg-primary/20"
                disabled={uploadingAudio}
              />
              {audioFile && (
                <Button
                  size="sm"
                  onClick={handleAudioUpload}
                  disabled={uploadingAudio || !userId}
                  className="w-full"
                >
                  {uploadingAudio ? (
                    <>
                      <Loader2 className="h-3.5 w-3.5 mr-2 animate-spin" />
                      Transcribing...
                    </>
                  ) : (
                    "Transcribe Audio"
                  )}
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </aside>
  );
}

