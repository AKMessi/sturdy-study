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
  // 1. Get the secure User ID from Clerk
  const { userId, isLoaded } = useAuth();
  
  // 2. UI State
  const [activeTab, setActiveTab] = useState<TabType>("chat");
  const [courseName, setCourseName] = useState("General");

  // 3. The Secret Sauce: Create the Composite ID
  // Format: "user_2b...--General"
  // If not logged in yet, fallback to "demo_mode"
  const effectiveId = (isLoaded && userId) 
    ? `${userId}--${courseName}` 
    : "demo_mode";

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* Sidebar controls the Course Name */}
      <Sidebar 
        effectiveId={effectiveId}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        courseName={courseName}
        setCourseName={setCourseName}
        onUploadSuccess={() => {
          // Optional: trigger any refresh logic here
        }}
      />

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col overflow-hidden">
        
        {/* Context Bar (Shows what course you are in) */}
        <div className="px-6 pt-4 pb-0">
           <div className="text-sm text-muted-foreground flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
              Context: <span className="font-bold text-primary">{courseName}</span> 
           </div>
        </div>

        <div className="flex-1 p-6 pt-4 overflow-y-auto">
          {activeTab === "chat" && (
            <Card className="h-full border-border/50 flex flex-col">
              <CardHeader className="border-b border-border py-4">
                <CardTitle>AI Chat Assistant</CardTitle>
                <CardDescription>
                  Chatting with your <strong>{courseName}</strong> materials
                </CardDescription>
              </CardHeader>
              <CardContent className="flex-1 p-0 overflow-hidden">
                {/* Pass effectiveId so the chat knows which bucket to look in */}
                <ChatTab userId={effectiveId} />
              </CardContent>
            </Card>
          )}

          {activeTab === "search" && (
            <Card className="h-full border-border/50">
              <CardHeader>
                <CardTitle>Find Practice Problems</CardTitle>
                <CardDescription>Find external resources for {courseName}</CardDescription>
              </CardHeader>
              <CardContent className="overflow-y-auto">
                <SearchTab userId={effectiveId} />
              </CardContent>
            </Card>
          )}

          {activeTab === "exams" && (
            <Card className="h-full border-border/50">
              <CardHeader>
                <CardTitle>Generate Practice Exams</CardTitle>
                <CardDescription>Create exams based on {courseName} notes</CardDescription>
              </CardHeader>
              <CardContent className="overflow-y-auto">
                <ExamTab userId={effectiveId} />
              </CardContent>
            </Card>
          )}

          {activeTab === "tutor" && (
            <Card className="h-full border-border/50 flex flex-col overflow-hidden">
              <CardHeader className="border-b border-border py-4">
                <CardTitle>Guided Learning Session</CardTitle>
                <CardDescription>Master topics in {courseName}</CardDescription>
              </CardHeader>
              <CardContent className="flex-1 p-0 overflow-hidden">
                <TutorTab userId={effectiveId} />
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  );
}