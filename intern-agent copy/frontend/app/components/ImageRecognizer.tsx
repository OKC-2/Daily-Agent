"use client";

import { useState, useRef, useCallback } from "react";

export default function ImageRecognizer() {
  const [image, setImage] = useState<string | null>(null);
  const [recognizedText, setRecognizedText] = useState("");
  const [isRecognizing, setIsRecognizing] = useState(false);
  const [copied, setCopied] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = (file: File) => {
    if (!file.type.startsWith("image/")) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      const result = e.target?.result as string;
      setImage(result);
      setRecognizedText("");
      setCopied(false);
    };
    reader.readAsDataURL(file);
  };

  const handlePaste = useCallback((e: React.ClipboardEvent) => {
    const items = e.clipboardData.items;
    for (let i = 0; i < items.length; i++) {
      if (items[i].type.startsWith("image/")) {
        const file = items[i].getAsFile();
        if (file) handleFile(file);
        break;
      }
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith("image/")) handleFile(file);
  }, []);

  const handleRecognize = async () => {
    if (!image) return;
    setIsRecognizing(true);
    try {
      const base64 = image.split(",")[1];
      const res = await fetch("http://localhost:8000/recognize-image", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image_base64: base64 }),
      });
      if (!res.ok) throw new Error("识别失败");
      const data = await res.json();
      setRecognizedText(data.text);
      setCopied(false);
    } catch (e) {
      alert("图片识别失败，请检查后端服务");
      console.error(e);
    } finally {
      setIsRecognizing(false);
    }
  };

  const handleCopy = async () => {
    if (!recognizedText) return;
    try {
      await navigator.clipboard.writeText(recognizedText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      alert("复制失败，请手动选择文本复制");
    }
  };

  return (
    <div className="border border-blue-200 rounded-lg p-4 bg-blue-50/50 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-blue-700">截图智能分析</span>
        <span className="text-xs text-gray-400">支持粘贴截图（Ctrl+V）</span>
      </div>

      {!image ? (
        <div
          onPaste={handlePaste}
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => fileInputRef.current?.click()}
          className="border-2 border-dashed border-blue-300 rounded-lg p-6 text-center cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition-colors focus:outline-none focus:border-blue-500"
          tabIndex={0}
        >
          <p className="text-sm text-gray-600">点击上传或粘贴截图</p>
          <p className="text-xs text-gray-400 mt-1">支持 PNG、JPG、GIF</p>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleFile(file);
            }}
          />
        </div>
      ) : (
        <div className="space-y-3">
          <div className="relative">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={image} alt="预览" className="max-h-48 mx-auto rounded-lg border border-gray-200" />
            <button
              type="button"
              onClick={() => { setImage(null); setRecognizedText(""); setCopied(false); }}
              className="absolute top-1 right-1 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs hover:bg-red-600"
            >
              x
            </button>
          </div>
          <button
            type="button"
            onClick={handleRecognize}
            disabled={isRecognizing}
            className="w-full bg-blue-600 text-white py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {isRecognizing ? "分析中..." : "开始分析"}
          </button>
        </div>
      )}

      {recognizedText && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-blue-600">分析结果</span>
            <div className="h-px flex-1 bg-blue-100" />
          </div>
          <div className="bg-white rounded-lg p-3 border border-gray-200">
            <textarea
              className="w-full text-sm text-gray-700 bg-transparent outline-none"
              rows={16}
              value={recognizedText}
              onChange={(e) => setRecognizedText(e.target.value)}
            />
          </div>
          <button
            type="button"
            onClick={handleCopy}
            className="w-full bg-green-600 text-white py-2 rounded-lg text-sm font-medium hover:bg-green-700 transition-colors"
          >
            {copied ? "已复制" : "复制分析结果"}
          </button>
        </div>
      )}
    </div>
  );
}
