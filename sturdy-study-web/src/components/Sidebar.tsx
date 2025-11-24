"use client";

import { useState, useRef } from "react";
import { UserButton } from "@clerk/nextjs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { 
  MessageSquare, Search, GraduationCap, FileText, 
  Upload, File, Music, Loader2, Library 
} from "lucide-react";
import { toast } from "sonner";
import { uploadPdf, uploadAudio } from "@/lib/api";

type TabType = "chat" | "search" | "exams" | "tutor";

interface SidebarProps {
  effectiveId: string; // The combined ID (User + Course)
  activeTab: TabType;
  setActiveTab: (tab: TabType) => void;
  courseName: string;
  setCourseName: (name: string) => void;
  onUploadSuccess?: () => void;
}

export function Sidebar({ 
  effectiveId, 
  activeTab, 
  setActiveTab, 
  courseName, 
  setCourseName, 
  onUploadSuccess 
}: SidebarProps) {
  
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [uploadingPdf, setUploadingPdf] = useState(false);
  const [uploadingAudio, setUploadingAudio] = useState(false);
  
  const pdfInputRef = useRef<HTMLInputElement>(null);
  const audioInputRef = useRef<HTMLInputElement>(null);

  const handlePdfUpload = async () => {
    if (!pdfFile || !effectiveId) return;
    setUploadingPdf(true);
    try {
      // Upload to the specific Course bucket
      const response = await uploadPdf(effectiveId, pdfFile);
      toast.success(`${response.filename} processed!`, { 
        description: `Added to ${courseName} notebook.` 
      });
      setPdfFile(null);
      if (pdfInputRef.current) pdfInputRef.current.value = "";
      onUploadSuccess?.();
    } catch (error) {
      toast.error("Upload Failed", { description: String(error) });
    } finally {
      setUploadingPdf(false);
    }
  };

  const handleAudioUpload = async () => {
    if (!audioFile || !effectiveId) return;
    setUploadingAudio(true);
    try {
      const response = await uploadAudio(effectiveId, audioFile);
      toast.success(`${response.filename} transcribed!`, { 
        description: `Added to ${courseName} notebook.` 
      });
      setAudioFile(null);
      if (audioInputRef.current) audioInputRef.current.value = "";
      onUploadSuccess?.();
    } catch (error) {
      toast.error("Upload Failed", { description: String(error) });
    } finally {
      setUploadingAudio(false);
    }
  };

  return (
    <aside className="w-80 border-r border-border bg-card flex flex-col overflow-y-auto h-full">
      <div className="p-6 border-b border-border">
        <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
          Sturdy Study
        </h1>
        <p className="text-xs text-muted-foreground mt-1">v1.0 Production</p>
      </div>

      <div className="flex-1 p-6 space-y-6">
        
        {/* Navigation */}
        <Card className="border-border/50">
          <CardHeader className="pb-3 pt-4 px-4">
            <CardTitle className="text-sm">Navigation</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 px-2 pb-2">
            <Button variant={activeTab === 'chat' ? 'secondary' : 'ghost'} className="w-full justify-start gap-2" onClick={() => setActiveTab('chat')}>
              <MessageSquare className="h-4 w-4" /> Chat
            </Button>
            <Button variant={activeTab === 'search' ? 'secondary' : 'ghost'} className="w-full justify-start gap-2" onClick={() => setActiveTab('search')}>
              <Search className="h-4 w-4" /> Web Search
            </Button>
            <Button variant={activeTab === 'tutor' ? 'secondary' : 'ghost'} className="w-full justify-start gap-2" onClick={() => setActiveTab('tutor')}>
              <GraduationCap className="h-4 w-4" /> Guided Tutor
            </Button>
            <Button variant={activeTab === 'exams' ? 'secondary' : 'ghost'} className="w-full justify-start gap-2" onClick={() => setActiveTab('exams')}>
              <FileText className="h-4 w-4" /> Generate Exam
            </Button>
          </CardContent>
        </Card>

        {/* COURSE SWITCHER (The New Feature) */}
        <Card className="border-primary/20 bg-primary/5">
          <CardHeader className="pb-2 pt-4 px-4">
            <div className="flex items-center gap-2">
              <Library className="h-4 w-4 text-primary" />
              <CardTitle className="text-sm">Current Course</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="px-4 pb-4 space-y-2">
            <Input 
              value={courseName}
              onChange={(e) => setCourseName(e.target.value)}
              className="h-8 bg-background"
              placeholder="e.g. Biology 101"
            />
            <p className="text-[10px] text-muted-foreground">
              Switching this name switches your notebook.
            </p>
          </CardContent>
        </Card>

        {/* Uploads */}
        <Card className="border-border/50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Upload to {courseName}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label className="text-xs">PDF Documents</Label>
              <Input ref={pdfInputRef} type="file" accept=".pdf" onChange={(e) => setPdfFile(e.target.files?.[0] || null)} className="h-8 text-xs" />
              {pdfFile && <Button size="sm" onClick={handlePdfUpload} disabled={uploadingPdf} className="w-full">{uploadingPdf ? <Loader2 className="animate-spin h-3 w-3" /> : "Upload"}</Button>}
            </div>
            <Separator />
            <div className="space-y-2">
              <Label className="text-xs">Audio Files</Label>
              <Input ref={audioInputRef} type="file" accept=".mp3,.m4a,.wav" onChange={(e) => setAudioFile(e.target.files?.[0] || null)} className="h-8 text-xs" />
              {audioFile && <Button size="sm" onClick={handleAudioUpload} disabled={uploadingAudio} className="w-full">{uploadingAudio ? <Loader2 className="animate-spin h-3 w-3" /> : "Transcribe"}</Button>}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="p-4 border-t border-border flex items-center justify-between bg-muted/30">
        <span className="text-sm font-medium">Account</span>
        <UserButton afterSignOutUrl="/" />
      </div>
    </aside>
  );
}