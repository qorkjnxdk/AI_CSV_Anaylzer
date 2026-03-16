import React, { useCallback, useRef } from "react";
import { uploadFiles } from "../api";
import type { UploadedFile } from "../types";

interface Props {
  onUpload: (files: UploadedFile[]) => void;
  sessionId: string | null;
  setSessionId: (id: string) => void;
}

export default function FileUploader({
  onUpload,
  sessionId,
  setSessionId,
}: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const handleUpload = useCallback(
    async (fileList: FileList | null) => {
      if (!fileList || fileList.length === 0) return;
      setLoading(true);
      setError(null);

      try {
        const result = await uploadFiles(
          Array.from(fileList),
          sessionId || undefined
        );
        setSessionId(result.session_id);
        onUpload(result.files);

        const failed = result.files.filter((f) => !f.success);
        if (failed.length > 0) {
          setError(
            failed.map((f) => `${f.filename}: ${f.error}`).join("; ")
          );
        }
      } catch (e: any) {
        setError(e?.response?.data?.detail || e.message || "Upload failed");
      } finally {
        setLoading(false);
        if (inputRef.current) inputRef.current.value = "";
      }
    },
    [sessionId, setSessionId, onUpload]
  );

  return (
    <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-400 transition-colors">
      <input
        ref={inputRef}
        type="file"
        multiple
        accept=".csv,.xls,.xlsx"
        className="hidden"
        onChange={(e) => handleUpload(e.target.files)}
      />
      <button
        onClick={() => inputRef.current?.click()}
        disabled={loading}
        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 cursor-pointer"
      >
        {loading ? "Uploading..." : "Upload CSV / Excel Files"}
      </button>
      <p className="mt-2 text-sm text-gray-500">
        Accepts .csv, .xls, .xlsx — max 10MB per file
      </p>
      {error && (
        <p className="mt-2 text-sm text-red-600">{error}</p>
      )}
    </div>
  );
}
