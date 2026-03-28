import React from "react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { SynthesisAnalysis } from "@/lib/types";

interface SynthesisViewProps {
  analysis: SynthesisAnalysis;
  sourcesCount: number;
  onClose?: () => void;
}

export const SynthesisView: React.FC<SynthesisViewProps> = ({
  analysis,
  sourcesCount,
  onClose,
}) => {
  const sections = [
    {
      title: "Common Themes",
      items: analysis.common_themes,
      icon: "🎯",
      color: "blue",
      description: "Consistent insights across sources",
    },
    {
      title: "Unique Insights",
      items: analysis.unique_insights,
      icon: "✨",
      color: "purple",
      description: "What's unique to individual sources",
    },
    {
      title: "Contradictions",
      items: analysis.contradictions,
      icon: "⚡",
      color: "amber",
      description: "Where sources disagree",
    },
    {
      title: "Knowledge Gaps",
      items: analysis.knowledge_gaps,
      icon: "🔍",
      color: "red",
      description: "What wasn't covered",
    },
  ];

  const colorClasses = {
    blue: "bg-blue-50 border-blue-200 text-blue-800",
    purple: "bg-purple-50 border-purple-200 text-purple-800",
    amber: "bg-amber-50 border-amber-200 text-amber-800",
    red: "bg-red-50 border-red-200 text-red-800",
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Cross-Source Analysis</h2>
          <p className="text-sm text-gray-500 mt-1">
            Synthesized from {sourcesCount} source{sourcesCount !== 1 ? "s" : ""}
          </p>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl"
          >
            ✕
          </button>
        )}
      </div>

      {/* Synthesis Summary */}
      <Card className="p-6 bg-white border border-gray-200 rounded-lg">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Synthesis Summary</h3>
        <p className="text-gray-700 leading-relaxed">{analysis.synthesis_summary}</p>
      </Card>

      {/* Recommended Reading Order */}
      {analysis.recommended_order && analysis.recommended_order.length > 0 && (
        <Card className="p-6 bg-white border border-gray-200 rounded-lg">
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <span>📋</span> Recommended Reading Order
          </h3>
          <div className="flex flex-wrap gap-2">
            {analysis.recommended_order.map((index, pos) => (
              <div key={pos} className="flex items-center">
                <Badge className="bg-blue-100 text-blue-800 font-semibold px-3 py-1 rounded-full">
                  {pos + 1}. Source {index + 1}
                </Badge>
                {pos < analysis.recommended_order.length - 1 && (
                  <span className="mx-2 text-gray-400">→</span>
                )}
              </div>
            ))}
          </div>
          <p className="text-sm text-gray-500 mt-3">
            This order helps build knowledge progressively
          </p>
        </Card>
      )}

      {/* Main Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {sections.map((section) => (
          <Card
            key={section.title}
            className={`p-6 border rounded-lg ${
              colorClasses[section.color as keyof typeof colorClasses]
            }`}
          >
            <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
              <span className="text-2xl">{section.icon}</span>
              {section.title}
            </h3>
            <p className="text-sm opacity-75 mb-3">{section.description}</p>

            {section.items && section.items.length > 0 ? (
              <ul className="space-y-2">
                {section.items.map((item, idx) => (
                  <li
                    key={idx}
                    className="flex gap-2 text-sm leading-relaxed"
                  >
                    <span className="font-bold min-w-fit">•</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm opacity-60 italic">None identified</p>
            )}
          </Card>
        ))}
      </div>

      {/* Export Section */}
      <Card className="p-6 bg-gradient-to-r from-blue-50 to-purple-50 border border-gray-200 rounded-lg">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">📤 Export Synthesis</h3>
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => {
              const text = formatSynthesisAsText(analysis, sourcesCount);
              const blob = new Blob([text], { type: "text/plain" });
              downloadFile(blob, "synthesis.txt");
            }}
            className="px-4 py-2 bg-white hover:bg-gray-100 border border-gray-300 rounded-lg text-sm font-medium transition"
          >
            📝 Text
          </button>
          <button
            onClick={() => {
              const md = formatSynthesisAsMarkdown(analysis, sourcesCount);
              const blob = new Blob([md], { type: "text/markdown" });
              downloadFile(blob, "synthesis.md");
            }}
            className="px-4 py-2 bg-white hover:bg-gray-100 border border-gray-300 rounded-lg text-sm font-medium transition"
          >
            📘 Markdown
          </button>
          <button
            onClick={() => {
              const json = JSON.stringify(analysis, null, 2);
              const blob = new Blob([json], { type: "application/json" });
              downloadFile(blob, "synthesis.json");
            }}
            className="px-4 py-2 bg-white hover:bg-gray-100 border border-gray-300 rounded-lg text-sm font-medium transition"
          >
            🔗 JSON
          </button>
        </div>
      </Card>
    </div>
  );
};

// Helper Functions
function formatSynthesisAsText(analysis: SynthesisAnalysis, sourcesCount: number): string {
  const lines: string[] = [
    "=".repeat(60),
    "CROSS-SOURCE SYNTHESIS",
    `Synthesized from ${sourcesCount} sources`,
    "=".repeat(60),
    "",
    "SYNTHESIS SUMMARY",
    "-".repeat(60),
    analysis.synthesis_summary,
    "",
    "COMMON THEMES",
    "-".repeat(60),
    analysis.common_themes.map((t) => `• ${t}`).join("\n"),
    "",
    "UNIQUE INSIGHTS",
    "-".repeat(60),
    analysis.unique_insights.map((u) => `• ${u}`).join("\n"),
    "",
    "CONTRADICTIONS",
    "-".repeat(60),
    analysis.contradictions.length > 0
      ? analysis.contradictions.map((c) => `• ${c}`).join("\n")
      : "[None identified]",
    "",
    "KNOWLEDGE GAPS",
    "-".repeat(60),
    analysis.knowledge_gaps.length > 0
      ? analysis.knowledge_gaps.map((g) => `• ${g}`).join("\n")
      : "[None identified]",
    "",
    "RECOMMENDED READING ORDER",
    "-".repeat(60),
    analysis.recommended_order
      .map((idx, pos) => `${pos + 1}. Source ${idx + 1}`)
      .join(" → "),
    "",
  ];

  return lines.join("\n");
}

function formatSynthesisAsMarkdown(analysis: SynthesisAnalysis, sourcesCount: number): string {
  const sections: string[] = [
    "# Cross-Source Synthesis",
    `*Synthesized from ${sourcesCount} sources*`,
    "",
    "## Synthesis Summary",
    analysis.synthesis_summary,
    "",
    "## Common Themes",
    analysis.common_themes.map((t) => `- ${t}`).join("\n"),
    "",
    "## Unique Insights",
    analysis.unique_insights.map((u) => `- ${u}`).join("\n"),
    "",
    "## Contradictions",
    analysis.contradictions.length > 0
      ? analysis.contradictions.map((c) => `- ${c}`).join("\n")
      : "*None identified*",
    "",
    "## Knowledge Gaps",
    analysis.knowledge_gaps.length > 0
      ? analysis.knowledge_gaps.map((g) => `- ${g}`).join("\n")
      : "*None identified*",
    "",
    "## Recommended Reading Order",
    analysis.recommended_order
      .map((idx, pos) => `${pos + 1}. Source ${idx + 1}`)
      .join(" → "),
    "",
  ];

  return sections.join("\n");
}

function downloadFile(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
