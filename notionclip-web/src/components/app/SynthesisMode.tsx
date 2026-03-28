import React, { useState } from "react";
import { useAppStore } from "@/lib/store";
import { SynthesisAnalysis } from "@/lib/types";
import { api } from "@/lib/api";
import { SessionGroupManager } from "./SessionGroupManager";
import { SynthesisView } from "../SynthesisView";
import { Card } from "@/components/ui/Card";

export const SynthesisMode: React.FC = () => {
  const { setResults } = useAppStore();
  const [synthesisResult, setSynthesisResult] = useState<{
    analysis: SynthesisAnalysis;
    sourcesCount: number;
  } | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSynthesisRequest = async (
    sessionIds: string[],
    userQuestion?: string
  ) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.synthesiseSessions(sessionIds, userQuestion);
      
      setSynthesisResult({
        analysis: response.analysis,
        sourcesCount: response.sources_count,
      });

      // Also update the main app store to show results
      setResults({
        mode: "synthesis" as any,
        word_count: 0,
        insights: response.analysis as any,
        cache_hit: response.synthesis_cache_used,
      });
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to synthesize sessions";
      setError(errorMessage);
      console.error("Synthesis error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setSynthesisResult(null);
    setError(null);
  };

  return (
    <div className="w-full space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">
          🔗 Cross-Source Synthesis
        </h1>
        <p className="text-gray-600 mt-2">
          Compare and synthesize insights from multiple sessions to identify patterns,
          contradictions, and unified knowledge.
        </p>
      </div>

      {/* Error Message */}
      {error && (
        <Card className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800 font-medium">⚠️ Error</p>
          <p className="text-red-600 text-sm mt-1">{error}</p>
        </Card>
      )}

      {/* Main Content */}
      {!synthesisResult ? (
        <SessionGroupManager
          onSynthesisRequest={handleSynthesisRequest}
          isLoading={isLoading}
        />
      ) : (
        <div>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Results</h2>
            <button
              onClick={handleReset}
              className="text-blue-600 hover:text-blue-800 text-sm font-medium"
            >
              ← Back to Selection
            </button>
          </div>
          <SynthesisView
            analysis={synthesisResult.analysis}
            sourcesCount={synthesisResult.sourcesCount}
            onClose={handleReset}
          />
        </div>
      )}

      {/* Info Section */}
      <Card className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <h3 className="font-semibold text-blue-900 mb-2">💡 How It Works</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>
            • Select 2 or more sessions you have previously created across any modes
          </li>
          <li>• Optionally ask a question to guide the synthesis</li>
          <li>
            • AI analyzes all sources to find common themes and contradictions
          </li>
          <li>• Get a comprehensive overview with recommended reading order</li>
        </ul>
      </Card>
    </div>
  );
};
