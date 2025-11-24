"use client";

import { useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ChatTab } from "@/components/ChatTab";
import { ExamTab } from "@/components/ExamTab";
import { SearchTab } from "@/components/SearchTab";
import { TutorTab } from "@/components/TutorTab";
import { Sidebar } from "@/components/Sidebar";

type TabType = "chat" | "search" | "exams" | "tutor";

export default function Dashboard() {
  const { userId, isLoaded } = useAuth();
  const [activeTab, setActiveTab] = useState<TabType>("chat");
  const [courseName, setCourseName] = useState("General");

  const effectiveId = (isLoaded && userId) 
    ? `${userId}--${courseName}` 
    : "demo_mode";

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* Sidebar */}
      <Sidebar 
        effectiveId={effectiveId}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        courseName={courseName}
        setCourseName={setCourseName}
        onUploadSuccess={() => {}}
      />

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col h-full overflow-hidden">
        
        {/* Context Bar */}
        <div className="px-6 pt-4 pb-2 shrink-0">
           <div className="text-sm text-muted-foreground flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
              Context: <span className="font-bold text-primary">{courseName}</span> 
           </div>
        </div>

        <div className="flex-1 p-6 pt-4 overflow-hidden flex flex-col">
          
          {activeTab === "chat" && (
            <Card className="h-full flex flex-col border-border/50 shadow-sm">
              <CardHeader className="border-b border-border py-3 shrink-0">
                <CardTitle>AI Chat Assistant</CardTitle>
                <CardDescription>Chatting with your <strong>{courseName}</strong> materials</CardDescription>
              </CardHeader>
              <CardContent className="flex-1 p-0 overflow-hidden min-h-0">
                <ChatTab userId={effectiveId} />
              </CardContent>
            </Card>
          )}

          {activeTab === "search" && (
            <Card className="h-full flex flex-col border-border/50 shadow-sm">
              <CardHeader className="shrink-0">
                <CardTitle>Find Practice Problems</CardTitle>
                <CardDescription>External resources for {courseName}</CardDescription>
              </CardHeader>
              {/* Search needs its own scrollbar */}
              <CardContent className="flex-1 overflow-y-auto min-h-0">
                <SearchTab userId={effectiveId} />
              </CardContent>
            </Card>
          )}

          {activeTab === "exams" && (
            <Card className="h-full flex flex-col border-border/50 shadow-sm">
              <CardHeader className="shrink-0">
                <CardTitle>Generate Practice Exams</CardTitle>
                <CardDescription>Create exams based on {courseName}</CardDescription>
              </CardHeader>
              <CardContent className="flex-1 overflow-y-auto min-h-0">
                <ExamTab userId={effectiveId} />
              </CardContent>
            </Card>
          )}

          {activeTab === "tutor" && (
            <Card className="h-full flex flex-col border-border/50 shadow-sm">
              <CardHeader className="border-b border-border py-3 shrink-0">
                <CardTitle>Guided Learning Session</CardTitle>
                <CardDescription>Master topics in {courseName}</CardDescription>
              </CardHeader>
              <CardContent className="flex-1 p-0 overflow-hidden min-h-0">
                <TutorTab userId={effectiveId} />
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  );
}