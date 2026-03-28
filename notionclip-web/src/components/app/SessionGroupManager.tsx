import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { useAppStore } from "@/lib/store";

interface Session {
  id: string;
  title: string;
  type: "study" | "work" | "quick";
  created_at: string;
}

interface SessionGroupManagerProps {
  onSynthesisRequest: (sessionIds: string[], userQuestion?: string) => void;
  isLoading?: boolean;
}

export const SessionGroupManager: React.FC<SessionGroupManagerProps> = ({
  onSynthesisRequest,
  isLoading = false,
}) => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [userQuestion, setUserQuestion] = useState("");
  const [loadingSessions, setLoadingSessions] = useState(true);

  useEffect(() => {
    // Load sessions from browser storage or API
    // For now, we'll use a simple localStorage approach
    loadSessions();
  }, []);

  const loadSessions = () => {
    try {
      const stored = localStorage.getItem("notionclips_sessions");
      if (stored) {
        const parsedSessions: Session[] = JSON.parse(stored);
        // Sort by most recent first
        parsedSessions.sort(
          (a, b) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
        setSessions(parsedSessions);
      }
    } catch (e) {
      console.error("Failed to load sessions:", e);
    } finally {
      setLoadingSessions(false);
    }
  };

  const toggleSession = (id: string) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedIds(newSelected);
  };

  const handleSynthesize = () => {
    if (selectedIds.size < 2) {
      alert("Please select at least 2 sessions to synthesize");
      return;
    }
    onSynthesisRequest(Array.from(selectedIds), userQuestion || undefined);
  };

  const modeEmoji = {
    study: "📚",
    work: "💼",
    quick: "⚡",
  };

  if (loadingSessions) {
    return (
      <Card className="p-6 bg-white border border-gray-200 rounded-lg">
        <p className="text-gray-500">Loading sessions...</p>
      </Card>
    );
  }

  if (sessions.length === 0) {
    return (
      <Card className="p-6 bg-white border border-gray-200 rounded-lg text-center">
        <p className="text-gray-500 mb-2">No sessions found</p>
        <p className="text-sm text-gray-400">
          Process some content first to enable synthesis
        </p>
      </Card>
    );
  }

  return (
    <Card className="p-6 bg-white border border-gray-200 rounded-lg">
      <h3 className="text-lg font-semibold mb-4">Select Sessions to Synthesize</h3>

      {/* Session Selection */}
      <div className="grid grid-cols-1 gap-2 mb-6 max-h-64 overflow-y-auto">
        {sessions.map((session) => (
          <label
            key={session.id}
            className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-blue-50 cursor-pointer transition"
          >
            <input
              type="checkbox"
              checked={selectedIds.has(session.id)}
              onChange={() => toggleSession(session.id)}
              className="w-4 h-4 text-blue-600 rounded"
            />
            <div className="ml-3 flex-1">
              <div className="flex items-center gap-2">
                <span className="text-lg">{modeEmoji[session.type]}</span>
                <span className="font-medium text-gray-900">{session.title}</span>
              </div>
              <p className="text-xs text-gray-500">
                {new Date(session.created_at).toLocaleDateString()} at{" "}
                {new Date(session.created_at).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </p>
            </div>
          </label>
        ))}
      </div>

      {/* User Question (Optional) */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Focus Question (Optional)
        </label>
        <textarea
          value={userQuestion}
          onChange={(e) => setUserQuestion(e.target.value)}
          placeholder="Ask a question to guide the synthesis (e.g., 'How do these sources explain machine learning?')"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          rows={2}
        />
      </div>

      {/* Selection Summary */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-6">
        <p className="text-sm text-gray-700">
          {selectedIds.size === 0
            ? "Select at least 2 sessions to begin"
            : `${selectedIds.size} session${selectedIds.size !== 1 ? "s" : ""} selected`}
        </p>
      </div>

      {/* Synthesize Button */}
      <Button
        onClick={handleSynthesize}
        disabled={selectedIds.size < 2 || isLoading}
        className={`w-full py-2 px-4 rounded-lg font-medium transition ${
          selectedIds.size < 2 || isLoading
            ? "bg-gray-300 text-gray-500 cursor-not-allowed"
            : "bg-blue-600 text-white hover:bg-blue-700"
        }`}
      >
        {isLoading && <span className="mr-2">🔄</span>}
        {isLoading ? "Synthesizing..." : "Synthesize Sessions"}
      </Button>

      <p className="text-xs text-gray-500 mt-3">
        💡 Synthesis uses AI to compare insights across multiple sources and
        identify themes, contradictions, and gaps.
      </p>
    </Card>
  );
};
