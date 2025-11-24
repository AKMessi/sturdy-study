"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ChatTab } from "@/components/ChatTab";
import { ExamTab } from "@/components/ExamTab";
import { SearchTab } from "@/components/SearchTab";
import { TutorTab } from "@/components/TutorTab";
import { Sidebar } from "@/components/Sidebar";

type TabType = "chat" | "search" | "exams" | "tutor";

export default function Dashboard() {
  const [userId, setUserId] = useState("demo_course_101");
  const [activeTab, setActiveTab] = useState<TabType>("chat");

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* Sidebar */}
      <Sidebar 
        userId={userId} 
        setUserId={setUserId}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onUploadSuccess={() => {
          // Optional: Add any logic here when upload succeeds
        }}
      />

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 p-6 overflow-y-auto">
          {activeTab === "chat" && (
            <Card className="h-full border-border/50 flex flex-col">
              <CardHeader className="border-b border-border">
                <CardTitle>AI Chat Assistant</CardTitle>
                <CardDescription>
                  Ask questions about your study materials or request quizzes
                </CardDescription>
              </CardHeader>
              <CardContent className="flex-1 p-0 overflow-hidden">
                <ChatTab userId={userId} />
              </CardContent>
            </Card>
          )}

          {activeTab === "search" && (
            <Card className="h-full border-border/50">
              <CardHeader>
                <CardTitle>Find Practice Problems</CardTitle>
                <CardDescription>
                  Search the web for relevant practice problems on any topic
                </CardDescription>
              </CardHeader>
              <CardContent className="overflow-y-auto">
                <SearchTab userId={userId} />
              </CardContent>
            </Card>
          )}

          {activeTab === "exams" && (
            <Card className="h-full border-border/50">
              <CardHeader>
                <CardTitle>Generate Practice Exams</CardTitle>
                <CardDescription>
                  Create custom PDF exams based on your study materials
                </CardDescription>
              </CardHeader>
              <CardContent className="overflow-y-auto">
                <ExamTab userId={userId} />
              </CardContent>
            </Card>
          )}

          {activeTab === "tutor" && (
            <Card className="h-full border-border/50 flex flex-col overflow-hidden">
              <CardHeader className="border-b border-border">
                <CardTitle>Guided Learning Session</CardTitle>
                <CardDescription>
                  Engage in a Socratic dialogue with your AI tutor
                </CardDescription>
              </CardHeader>
              <CardContent className="flex-1 p-0 overflow-hidden">
                <TutorTab userId={userId} />
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  );
}
