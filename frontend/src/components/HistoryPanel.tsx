import React, { useEffect, useState } from "react";
import { getHistory, getFeedbackSummary } from "../api";
import type { HistoryEntry, FeedbackSummary } from "../types";

interface Props {
  sessionId: string;
  refreshKey: number;
  onSelectPrompt: (question: string, filename: string, sheet: string) => void;
}

export default function HistoryPanel({
  sessionId,
  refreshKey,
  onSelectPrompt,
}: Props) {
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [summary, setSummary] = useState<FeedbackSummary | null>(null);

  useEffect(() => {
    getHistory(sessionId).then((data) => setHistory(data.history));
    getFeedbackSummary(sessionId).then(setSummary).catch(() => {});
  }, [sessionId, refreshKey]);

  if (history.length === 0) {
    return (
      <p className="text-sm text-gray-400 italic">No prompts yet. Ask a question to get started.</p>
    );
  }

  return (
    <div className="space-y-2">
      {history
        .slice()
        .reverse()
        .map((entry, i) => {
          const realIndex = history.length - 1 - i;
          return (
            <button
              key={realIndex}
              onClick={() => onSelectPrompt(entry.question, entry.filename, entry.sheet)}
              className="w-full text-left p-3 rounded border hover:bg-blue-50 transition-colors cursor-pointer"
            >
              <p className="text-sm font-medium text-gray-800 truncate">
                {entry.question}
              </p>
              <p className="text-xs text-gray-400 mt-1">
                {entry.filename}
                {entry.sheet !== "Sheet1" ? ` / ${entry.sheet}` : ""} &middot;{" "}
                {new Date(entry.timestamp).toLocaleTimeString()}
                {entry.result.type === "chart" && " · 📊 Chart"}
              </p>
            </button>
          );
        })}

      {summary && summary.total > 0 && (
        <div className="pt-3 border-t text-xs text-gray-500 text-center">
          Feedback: {summary.percent_positive}% positive ({summary.positive}/
          {summary.total})
        </div>
      )}
    </div>
  );
}
