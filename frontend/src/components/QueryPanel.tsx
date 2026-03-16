import React, { useState } from "react";
import { queryData, submitFeedback } from "../api";
import type { FileEntry, QueryResult, TableData } from "../types";

interface Props {
  sessionId: string;
  files: FileEntry[];
  onQueryComplete: () => void;
  prefillQuestion?: string;
  prefillFile?: string;
  prefillSheet?: string;
}

export default function QueryPanel({
  sessionId,
  files,
  onQueryComplete,
  prefillQuestion,
  prefillFile,
  prefillSheet,
}: Props) {
  const [question, setQuestion] = useState(prefillQuestion || "");
  const [selectedFile, setSelectedFile] = useState(files[0]?.filename || "");
  const [selectedSheet, setSelectedSheet] = useState(files[0]?.sheets[0] || "");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<"up" | "down" | null>(null);

  React.useEffect(() => {
    if (prefillQuestion) setQuestion(prefillQuestion);
    if (prefillFile) setSelectedFile(prefillFile);
    if (prefillSheet) setSelectedSheet(prefillSheet);
  }, [prefillQuestion, prefillFile, prefillSheet]);

  React.useEffect(() => {
    if (files.length > 0 && !selectedFile) {
      setSelectedFile(files[0].filename);
      setSelectedSheet(files[0].sheets[0]);
    }
  }, [files, selectedFile]);

  const currentFile = files.find((f) => f.filename === selectedFile);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || !selectedFile) return;

    setLoading(true);
    setError(null);
    setResult(null);
    setFeedback(null);

    try {
      const res = await queryData(sessionId, question, selectedFile, selectedSheet);
      setResult(res);
      onQueryComplete();
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message || "Query failed");
    } finally {
      setLoading(false);
    }
  };

  const handleFeedback = async (rating: "up" | "down") => {
    if (result?.history_index == null || feedback) return;
    try {
      await submitFeedback(sessionId, result.history_index, rating);
      setFeedback(rating);
    } catch {}
  };

  const downloadChart = () => {
    if (result?.type !== "chart" || typeof result.data !== "string") return;
    const link = document.createElement("a");
    link.href = `data:image/png;base64,${result.data}`;
    link.download = "chart.png";
    link.click();
  };

  return (
    <div>
      <form onSubmit={handleSubmit} className="space-y-3">
        {/* File selector row */}
        <div className="flex flex-wrap items-center gap-2 p-3 bg-gray-50 rounded-lg border border-gray-100">
          <div className="flex items-center gap-2">
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              File
            </label>
            <select
              className="border border-gray-200 rounded-md px-3 py-1.5 text-sm bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent"
              value={selectedFile}
              onChange={(e) => {
                setSelectedFile(e.target.value);
                const f = files.find((f) => f.filename === e.target.value);
                if (f) setSelectedSheet(f.sheets[0]);
              }}
            >
              {files.map((f) => (
                <option key={f.filename} value={f.filename}>
                  {f.filename}
                </option>
              ))}
            </select>
          </div>

          {currentFile && currentFile.sheets.length > 1 && (
            <div className="flex items-center gap-2">
              <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                Sheet
              </label>
              <select
                className="border border-gray-200 rounded-md px-3 py-1.5 text-sm bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent"
                value={selectedSheet}
                onChange={(e) => setSelectedSheet(e.target.value)}
              >
                {currentFile.sheets.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {/* Question input */}
        <div className="relative">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g. What is the average age of passengers?"
            className="w-full border border-gray-200 rounded-lg px-4 py-3 pr-24 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent placeholder:text-gray-400"
          />
          <button
            type="submit"
            disabled={loading || !question.trim()}
            className="absolute right-1.5 top-1/2 -translate-y-1/2 px-4 py-1.5 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed text-sm font-medium cursor-pointer transition-colors"
          >
            {loading ? (
              <span className="flex items-center gap-1.5">
                <svg className="animate-spin h-3.5 w-3.5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Thinking...
              </span>
            ) : (
              "Ask"
            )}
          </button>
        </div>
      </form>

      {/* Error */}
      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 flex items-start gap-2">
          <svg className="h-4 w-4 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {error}
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="mt-4 flex items-center justify-center py-10">
          <div className="flex flex-col items-center gap-3 text-gray-400">
            <svg className="animate-spin h-6 w-6 text-blue-500" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <p className="text-sm">Analyzing your data...</p>
          </div>
        </div>
      )}

      {/* Result */}
      {result && !loading && (
        <div className="mt-4 rounded-lg border border-gray-200 overflow-hidden">
          {/* Result header */}
          <div className="px-4 py-2.5 bg-gradient-to-r from-gray-50 to-white border-b border-gray-100 flex items-center justify-between">
            <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              {result.type === "chart" ? "Chart" : result.type === "table" ? "Table" : result.type === "error" ? "Error" : "Answer"}
            </span>
            <div className="flex items-center gap-1">
              <button
                onClick={() => handleFeedback("up")}
                disabled={feedback !== null}
                className={`p-1.5 rounded-md text-sm transition-colors cursor-pointer ${
                  feedback === "up"
                    ? "bg-green-100 text-green-600"
                    : feedback === null
                    ? "hover:bg-green-50 text-gray-400 hover:text-green-600"
                    : "text-gray-200 cursor-default"
                }`}
                title="Helpful"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M14 9V5a3 3 0 00-3-3l-4 9v11h11.28a2 2 0 002-1.7l1.38-9a2 2 0 00-2-2.3H14z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M7 22H4a2 2 0 01-2-2v-7a2 2 0 012-2h3" />
                </svg>
              </button>
              <button
                onClick={() => handleFeedback("down")}
                disabled={feedback !== null}
                className={`p-1.5 rounded-md text-sm transition-colors cursor-pointer ${
                  feedback === "down"
                    ? "bg-red-100 text-red-600"
                    : feedback === null
                    ? "hover:bg-red-50 text-gray-400 hover:text-red-600"
                    : "text-gray-200 cursor-default"
                }`}
                title="Not helpful"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M10 15v4a3 3 0 003 3l4-9V2H5.72a2 2 0 00-2 1.7l-1.38 9a2 2 0 002 2.3H10z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M17 2h2.67A2.31 2.31 0 0122 4v7a2.31 2.31 0 01-2.33 2H17" />
                </svg>
              </button>
              {feedback && (
                <span className="text-xs text-gray-400 ml-1">Thanks!</span>
              )}
            </div>
          </div>

          {/* Result body */}
          <div className="p-4">
            {result.type === "error" && (
              <div className="text-red-600 text-sm">
                <p className="font-medium mb-1">Execution Error</p>
                <p className="text-red-500">{result.data as string}</p>
              </div>
            )}

            {result.type === "scalar" && (
              <p className="text-2xl font-bold text-gray-900">
                {result.data as string}
              </p>
            )}

            {result.type === "text" && (
              <p className="text-sm text-gray-700 leading-relaxed">{result.data as string}</p>
            )}

            {result.type === "table" && (() => {
              const table = result.data as TableData;
              return (
                <div className="overflow-x-auto rounded-md border border-gray-100">
                  <table className="min-w-full text-sm">
                    <thead>
                      <tr className="bg-gray-50 border-b border-gray-200">
                        {table.columns.map((col) => (
                          <th
                            key={col}
                            className="px-3 py-2 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap"
                          >
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                      {table.rows.map((row, i) => (
                        <tr key={i} className="hover:bg-blue-50/30">
                          {row.map((cell, j) => (
                            <td
                              key={j}
                              className="px-3 py-2 whitespace-nowrap text-gray-700"
                            >
                              {cell === null ? (
                                <span className="text-gray-300">--</span>
                              ) : (
                                String(cell)
                              )}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              );
            })()}

            {result.type === "chart" && (
              <div>
                {result.text && (
                  <p className="text-sm text-gray-700 mb-3 leading-relaxed">{result.text}</p>
                )}
                <img
                  src={`data:image/png;base64,${result.data}`}
                  alt="Generated chart"
                  className="max-w-full rounded-md border border-gray-100"
                />
                <button
                  onClick={downloadChart}
                  className="mt-3 inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md cursor-pointer transition-colors"
                >
                  <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  Download PNG
                </button>
              </div>
            )}
          </div>

          {/* Generated code toggle */}
          {result.code && (
            <details className="border-t border-gray-100">
              <summary className="px-4 py-2.5 text-xs text-gray-400 cursor-pointer hover:text-gray-600 hover:bg-gray-50 transition-colors">
                View generated code
              </summary>
              <pre className="px-4 py-3 bg-gray-900 text-gray-100 text-xs overflow-x-auto font-mono leading-relaxed">
                {result.code}
              </pre>
            </details>
          )}
        </div>
      )}
    </div>
  );
}
