"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import ImageRecognizer from "./components/ImageRecognizer";

const API_BASE = "http://localhost:8000";

interface Task {
  id: string;
  title: string;
  description: string;
  status: string;
}

interface Learning {
  id: string;
  content: string;
  category: string;
  keywords: string[];
  source: string;
}

interface DailyLog {
  id: string;
  date: string;
  tasks: Task[];
  learnings: Learning[];
  attachments: string[];
  tags: string[];
  ai_summary: string | null;
}

function getDateKey(date: Date | string): string {
  const d = typeof date === "string" ? new Date(date) : date;
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function getMonthData(year: number, month: number) {
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  const daysInMonth = lastDay.getDate();
  const startWeekday = firstDay.getDay();
  const prevMonthLastDay = new Date(year, month, 0).getDate();

  const days: { date: Date; day: number; isCurrentMonth: boolean }[] = [];

  for (let i = startWeekday - 1; i >= 0; i--) {
    days.push({
      date: new Date(year, month - 1, prevMonthLastDay - i),
      day: prevMonthLastDay - i,
      isCurrentMonth: false,
    });
  }

  for (let i = 1; i <= daysInMonth; i++) {
    days.push({
      date: new Date(year, month, i),
      day: i,
      isCurrentMonth: true,
    });
  }

  const remaining = 42 - days.length;
  for (let i = 1; i <= remaining; i++) {
    days.push({
      date: new Date(year, month + 1, i),
      day: i,
      isCurrentMonth: false,
    });
  }

  return days;
}

const WEEKDAYS = ["日", "一", "二", "三", "四", "五", "六"];

export default function Home() {
  const [logs, setLogs] = useState<DailyLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [stats, setStats] = useState<{ total_logs: number; tag_distribution: Record<string, number> } | null>(null);

  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [selectedDateKey, setSelectedDateKey] = useState<string>(getDateKey(new Date()));

  const [taskText, setTaskText] = useState("");
  const [learnings, setLearnings] = useState<Learning[]>([
    { id: "business", content: "", category: "business", keywords: [], source: "" },
  ]);
  const [attachments, setAttachments] = useState<string[]>([""]);

  const [editingLogId, setEditingLogId] = useState<string | null>(null);
  const [editTaskText, setEditTaskText] = useState("");
  const [editLearnings, setEditLearnings] = useState<Learning[]>([]);
  const [editAttachments, setEditAttachments] = useState<string[]>([]);
  const [editSubmitting, setEditSubmitting] = useState(false);

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/logs`);
      if (!res.ok) throw new Error("获取记录失败");
      const data = await res.json();
      setLogs(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchStats = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/logs/stats/summary`);
      if (!res.ok) throw new Error("获取统计失败");
      const data = await res.json();
      setStats(data);
    } catch (e) {
      console.error(e);
    }
  }, []);

  useEffect(() => {
    fetchLogs();
    fetchStats();
  }, [fetchLogs, fetchStats]);

  const logsByDate = useMemo(() => {
    const map: Record<string, DailyLog[]> = {};
    for (const log of logs) {
      const key = getDateKey(log.date);
      if (!map[key]) map[key] = [];
      map[key].push(log);
    }
    return map;
  }, [logs]);

  const selectedLogs = logsByDate[selectedDateKey] || [];

  const calendarDays = useMemo(() => {
    return getMonthData(currentMonth.getFullYear(), currentMonth.getMonth());
  }, [currentMonth]);

  const renumberLines = (text: string): string => {
    return text
      .split("\n")
      .map((line, i) => {
        const content = line.replace(/^\d+\.\s*/, "");
        return `${i + 1}. ${content}`;
      })
      .join("\n");
  };

  const parseTasks = (text: string): Task[] => {
    return text
      .split("\n")
      .map((line, i) => ({
        id: String(i),
        title: line.replace(/^\d+\.\s*/, "").trim(),
        description: "",
        status: "completed",
      }))
      .filter((t) => t.title);
  };

  const handleTaskKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key !== "Enter") return;
    e.preventDefault();
    const target = e.currentTarget;
    const cursor = target.selectionStart || 0;
    const before = taskText.slice(0, cursor);
    const after = taskText.slice(cursor);
    const currentLineNum = before.split("\n").length;
    const nextLine = `${currentLineNum + 1}. `;
    const newText = renumberLines(before + "\n" + nextLine + after);
    setTaskText(newText);
    setTimeout(() => {
      const pos = before.length + 1 + nextLine.length;
      target.setSelectionRange(pos, pos);
    }, 0);
  };

  const addLearning = () => {
    const name = prompt("请输入新模块名称（如：项目收获）");
    if (!name || !name.trim()) return;
    setLearnings([...learnings, { id: String(Date.now()), content: "", category: name.trim(), keywords: [], source: "" }]);
  };

  const updateLearning = (index: number, field: keyof Learning, value: string) => {
    const newLearnings = [...learnings];
    newLearnings[index] = { ...newLearnings[index], [field]: value };
    setLearnings(newLearnings);
  };

  const removeLearning = (index: number) => {
    setLearnings(learnings.filter((_, i) => i !== index));
  };

  const addAttachment = () => {
    setAttachments([...attachments, ""]);
  };

  const updateAttachment = (index: number, value: string) => {
    const newAttachments = [...attachments];
    newAttachments[index] = value;
    setAttachments(newAttachments);
  };

  const removeAttachment = (index: number) => {
    setAttachments(attachments.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);

    const payload = {
      date: selectedDateKey,
      tasks: parseTasks(taskText).map((t) => ({ ...t, description: t.description || null })),
      learnings: learnings.filter((l) => l.content.trim()).map((l) => ({ ...l, keywords: l.keywords || [] })),
      attachments: attachments.filter((a) => a.trim()),
    };

    try {
      const res = await fetch(`${API_BASE}/logs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error("提交失败");
      await fetchLogs();
      setTaskText("");
      setLearnings([
        { id: "business", content: "", category: "business", keywords: [], source: "" },
      ]);
      setAttachments([""]);
      setSelectedDateKey(getDateKey(new Date()));
    } catch (e) {
      console.error(e);
      alert("提交失败，请检查后端服务是否正常运行");
    } finally {
      setSubmitting(false);
    }
  };

  const deleteLog = async (id: string) => {
    if (!confirm("确定要删除这条记录吗？")) return;
    try {
      const res = await fetch(`${API_BASE}/logs/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error("删除失败");
      await fetchLogs();
      await fetchStats();
    } catch (e) {
      console.error(e);
      alert("删除失败");
    }
  };

  const tasksToText = (tasks: Task[]): string => {
    return tasks.map((t, i) => `${i + 1}. ${t.title}`).join("\n");
  };

  const startEditing = (log: DailyLog) => {
    setEditingLogId(log.id);
    setEditTaskText(tasksToText(log.tasks));
    setEditLearnings(log.learnings.length > 0 ? log.learnings.map((l) => ({ ...l })) : [{ id: "business", content: "", category: "business", keywords: [], source: "" }]);
    setEditAttachments(log.attachments.length > 0 ? [...log.attachments] : [""]);
  };

  const cancelEditing = () => {
    setEditingLogId(null);
    setEditTaskText("");
    setEditLearnings([]);
    setEditAttachments([]);
  };

  const updateLog = async (logId: string) => {
    setEditSubmitting(true);
    const payload = {
      tasks: parseTasks(editTaskText).map((t) => ({ ...t, description: t.description || null })),
      learnings: editLearnings.filter((l) => l.content.trim()).map((l) => ({ ...l, keywords: l.keywords || [] })),
      attachments: editAttachments.filter((a) => a.trim()),
    };

    try {
      const res = await fetch(`${API_BASE}/logs/${logId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error("更新失败");
      await fetchLogs();
      await fetchStats();
      cancelEditing();
    } catch (e) {
      console.error(e);
      alert("更新失败，请检查后端服务是否正常运行");
    } finally {
      setEditSubmitting(false);
    }
  };

  const addEditLearning = () => {
    const name = prompt("请输入新模块名称（如：项目收获）");
    if (!name || !name.trim()) return;
    setEditLearnings([...editLearnings, { id: String(Date.now()), content: "", category: name.trim(), keywords: [], source: "" }]);
  };

  const updateEditLearning = (index: number, field: keyof Learning, value: string) => {
    const newLearnings = [...editLearnings];
    newLearnings[index] = { ...newLearnings[index], [field]: value };
    setEditLearnings(newLearnings);
  };

  const removeEditLearning = (index: number) => {
    setEditLearnings(editLearnings.filter((_, i) => i !== index));
  };

  const addEditAttachment = () => {
    setEditAttachments([...editAttachments, ""]);
  };

  const updateEditAttachment = (index: number, value: string) => {
    const newAttachments = [...editAttachments];
    newAttachments[index] = value;
    setEditAttachments(newAttachments);
  };

  const removeEditAttachment = (index: number) => {
    setEditAttachments(editAttachments.filter((_, i) => i !== index));
  };

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr);
    return d.toLocaleDateString("zh-CN", { year: "numeric", month: "long", day: "numeric", weekday: "long" });
  };

  const handleDateClick = (dateKey: string) => {
    if (dateKey > todayKey) {
      alert("还没到这一天，不能写入");
      return;
    }
    setSelectedDateKey(dateKey);
  };

  const prevMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1));
  };

  const nextMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1));
  };

  const todayKey = getDateKey(new Date());

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900">日报记录agent</h1>
            <p className="text-sm text-gray-500 mt-0.5">记录每日任务与学习收获，AI 自动生成摘要</p>
          </div>
          <div className="flex items-center gap-3">
            {stats && (
              <span className="bg-blue-50 text-blue-700 px-3 py-1 rounded-full font-medium text-sm">
                共 {stats.total_logs} 条记录
              </span>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left: Form */}
          <div className="lg:col-span-1 space-y-6">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 sticky top-20">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">新建日报记录</h2>
              <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                  <label className="text-sm font-medium text-gray-700 mb-2 block">
                    {(() => {
                      const [y, m, d] = selectedDateKey.split("-").map(Number);
                      return `${y}年${m}月${d}日实习工作`;
                    })()}
                  </label>
                  <textarea
                    value={taskText}
                    onChange={(e) => setTaskText(e.target.value)}
                    placeholder="工作内容"
                    rows={3}
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none resize-y"
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium text-gray-700 block">学习收获（可选）</label>
                    <button type="button" onClick={addLearning} className="text-xs text-blue-600 hover:text-blue-800 font-medium">
                      + 添加模块
                    </button>
                  </div>
                  <div className="space-y-3">
                    {learnings.map((learning, i) => {
                      const labels: Record<string, string> = {
                        tech: "技术收获",
                        business: "业务收获",
                        tool: "工具收获",
                        soft_skill: "软技能收获",
                      };
                      const label = labels[learning.category] || learning.category;
                      return (
                        <div key={learning.id} className="space-y-1.5">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-medium text-blue-600">{label}</span>
                            {learnings.length > 1 && learning.category !== "business" && (
                              <button
                                type="button"
                                onClick={() => removeLearning(i)}
                                className="text-xs text-red-500 hover:text-red-700"
                              >
                                删除
                              </button>
                            )}
                          </div>
                          <div className="flex gap-2">
                            <textarea
                              placeholder={`${label}内容（可选）`}
                              value={learning.content}
                              onChange={(e) => updateLearning(i, "content", e.target.value)}
                              rows={8}
                              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none resize-y min-h-[200px]"
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium text-gray-700">附件链接</label>
                    <button type="button" onClick={addAttachment} className="text-xs text-blue-600 hover:text-blue-800 font-medium">
                      + 添加链接
                    </button>
                  </div>
                  <div className="space-y-2">
                    {attachments.map((attachment, i) => (
                      <div key={i} className="flex gap-2">
                        <input
                          type="text"
                          placeholder="https://..."
                          value={attachment}
                          onChange={(e) => updateAttachment(i, e.target.value)}
                          className="flex-1 min-w-0 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                        />
                        {attachments.length > 1 && (
                          <button type="button" onClick={() => removeAttachment(i)} className="text-red-500 hover:text-red-700 text-sm px-2">
                            ✕
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                <ImageRecognizer />

                <button
                  type="submit"
                  disabled={submitting}
                  className="w-full bg-blue-600 text-white py-2.5 px-4 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {submitting ? "AI 生成摘要中..." : "提交记录"}
                </button>
              </form>
            </div>
          </div>

          {/* Right: Calendar + Detail */}
          <div className="lg:col-span-2 space-y-6">
            {/* Calendar */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-6">
                <button
                  onClick={prevMonth}
                  className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-100 text-gray-600 transition-colors"
                >
                  ‹
                </button>
                <h2 className="text-lg font-semibold text-gray-900">
                  {currentMonth.getFullYear()}年{currentMonth.getMonth() + 1}月
                </h2>
                <button
                  onClick={nextMonth}
                  className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-100 text-gray-600 transition-colors"
                >
                  ›
                </button>
              </div>

              <div className="grid grid-cols-7 gap-1 mb-2">
                {WEEKDAYS.map((w) => (
                  <div key={w} className="text-center text-xs font-medium text-gray-400 py-2">
                    {w}
                  </div>
                ))}
              </div>

              <div className="grid grid-cols-7 gap-1">
                {calendarDays.map((dayInfo, idx) => {
                  const dateKey = getDateKey(dayInfo.date);
                  const hasLogs = !!logsByDate[dateKey];
                  const logCount = logsByDate[dateKey]?.length || 0;
                  const isSelected = dateKey === selectedDateKey;
                  const isToday = dateKey === todayKey;

                  return (
                    <button
                      key={idx}
                      onClick={() => handleDateClick(dateKey)}
                      disabled={dateKey > todayKey}
                      className={`
                        relative h-14 rounded-lg flex flex-col items-center justify-center text-sm transition-all
                        ${dayInfo.isCurrentMonth ? "text-gray-900" : "text-gray-300"}
                        ${isSelected ? "bg-blue-600 text-white shadow-md" : dateKey > todayKey ? "opacity-40 cursor-not-allowed" : "hover:bg-gray-50"}
                        ${isToday && !isSelected ? "ring-2 ring-blue-400 bg-blue-50" : ""}
                      `}
                    >
                      <span className="font-medium">{dayInfo.day}</span>
                      {hasLogs && (
                        <span
                          className={`mt-0.5 text-[10px] font-medium px-1.5 py-0 rounded-full ${
                            isSelected ? "bg-white/30 text-white" : "bg-green-100 text-green-700"
                          }`}
                        >
                          {logCount}条
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>

              <div className="flex items-center gap-4 mt-4 text-xs text-gray-500">
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-full bg-blue-50 ring-2 ring-blue-400"></span>
                  <span>今天</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-full bg-green-100"></span>
                  <span>有记录</span>
                </div>
              </div>
            </div>

            {/* Selected date detail */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900">
                  {(() => {
                    const [y, m, d] = selectedDateKey.split("-").map(Number);
                    return `${y}年${m}月${d}日 记录`;
                  })()}
                </h2>
                {selectedLogs.length > 0 && (
                  <span className="text-sm text-gray-500">{selectedLogs.length} 条记录</span>
                )}
              </div>

              {selectedLogs.length === 0 ? (
                <div className="text-center py-8 text-gray-400">
                  <p>这一天还没有记录</p>
                  <p className="text-sm mt-1">在左侧表单中添加新记录吧</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {selectedLogs.map((log) => (
                    <div key={log.id} className="border border-gray-100 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                      <div className="flex items-start justify-between mb-3">
                        <span className="text-sm font-medium text-gray-500">{formatDate(log.date)}</span>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => startEditing(log)}
                            className="flex items-center gap-1 text-xs font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-md px-2.5 py-1 transition-colors"
                            title="修改"
                          >
                            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                            修改
                          </button>
                          <button
                            onClick={() => deleteLog(log.id)}
                            className="flex items-center gap-1 text-xs font-medium text-red-600 bg-red-50 hover:bg-red-100 border border-red-200 rounded-md px-2.5 py-1 transition-colors"
                            title="删除"
                          >
                            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                            删除
                          </button>
                        </div>
                      </div>

                      {editingLogId === log.id ? (
                        <div className="space-y-4">
                          <div>
                            <label className="text-sm font-medium text-gray-700 mb-2 block">
                              {(() => {
                                const dateStr = log.date.split("T")[0];
                                const [y, m, d] = dateStr.split("-").map(Number);
                                return `${y}年${m}月${d}日实习工作`;
                              })()}
                            </label>
                            <textarea
                              value={editTaskText}
                              onChange={(e) => setEditTaskText(e.target.value)}
                              placeholder="工作内容"
                              rows={3}
                              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none resize-y"
                            />
                          </div>

                          <div>
                            <div className="flex items-center justify-between mb-2">
                              <label className="text-sm font-medium text-gray-700 block">学习收获</label>
                              <button type="button" onClick={addEditLearning} className="text-xs text-blue-600 hover:text-blue-800 font-medium">
                                + 添加模块
                              </button>
                            </div>
                            <div className="space-y-3">
                              {editLearnings.map((learning, i) => {
                                const labels = {
                                  tech: "技术收获",
                                  business: "业务收获",
                                  tool: "工具收获",
                                  soft_skill: "软技能收获",
                                };
                                const label = labels[learning.category] || learning.category;
                                return (
                                  <div key={learning.id} className="space-y-1.5">
                                    <div className="flex items-center justify-between">
                                      <span className="text-xs font-medium text-blue-600">{label}</span>
                                      {editLearnings.length > 1 && learning.category !== "business" && (
                                        <button
                                          type="button"
                                          onClick={() => removeEditLearning(i)}
                                          className="text-xs text-red-500 hover:text-red-700"
                                        >
                                          删除
                                        </button>
                                      )}
                                    </div>
                                    <div className="flex gap-2">
                                      <textarea
                                        placeholder={`${label}内容（可选）`}
                                        value={learning.content}
                                        onChange={(e) => updateEditLearning(i, "content", e.target.value)}
                                        rows={4}
                                        className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none resize-y"
                                      />
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          </div>

                          <div>
                            <div className="flex items-center justify-between mb-2">
                              <label className="text-sm font-medium text-gray-700">附件链接</label>
                              <button type="button" onClick={addEditAttachment} className="text-xs text-blue-600 hover:text-blue-800 font-medium">
                                + 添加链接
                              </button>
                            </div>
                            <div className="space-y-2">
                              {editAttachments.map((attachment, i) => (
                                <div key={i} className="flex gap-2">
                                  <input
                                    type="text"
                                    placeholder="https://..."
                                    value={attachment}
                                    onChange={(e) => updateEditAttachment(i, e.target.value)}
                                    className="flex-1 min-w-0 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                                  />
                                  {editAttachments.length > 1 && (
                                    <button type="button" onClick={() => removeEditAttachment(i)} className="text-red-500 hover:text-red-700 text-sm px-2">
                                      ✕
                                    </button>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>

                          <div className="flex items-center gap-2 pt-2">
                            <button
                              onClick={() => updateLog(log.id)}
                              disabled={editSubmitting}
                              className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            >
                              {editSubmitting ? "保存中..." : "保存修改"}
                            </button>
                            <button
                              onClick={cancelEditing}
                              disabled={editSubmitting}
                              className="flex-1 bg-gray-100 text-gray-700 py-2 px-4 rounded-lg text-sm font-medium hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            >
                              取消
                            </button>
                          </div>
                        </div>
                      ) : (
                        <>
                          {log.ai_summary && (
                            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4 mb-4 border border-blue-100">
                              <div className="flex items-center gap-2 mb-1.5">
                                <span className="text-sm font-semibold text-blue-700">AI 摘要</span>
                              </div>
                              <p className="text-sm text-gray-700 leading-relaxed">{log.ai_summary}</p>
                            </div>
                          )}

                          {log.tasks.length > 0 && (
                            <div className="mb-4">
                              <h3 className="text-sm font-semibold text-gray-900 mb-2">
                                {(() => {
                                  const dateStr = log.date.split("T")[0];
                                  const [y, m, d] = dateStr.split("-").map(Number);
                                  return `${y}年${m}月${d}日实习工作`;
                                })()}
                              </h3>
                              <ol className="list-decimal list-inside space-y-1 text-sm text-gray-700">
                                {log.tasks.map((task, idx) => (
                                  <li key={task.id}>{task.title}</li>
                                ))}
                              </ol>
                            </div>
                          )}

                          {log.learnings.length > 0 && (
                            <div className="mb-4">
                              <h3 className="text-sm font-semibold text-gray-900 mb-2">学习收获</h3>
                              <div className="space-y-2">
                                {log.learnings.map((learning) => (
                                  <div key={learning.id} className="bg-gray-50 rounded-lg p-3 text-sm">
                                    <p className="text-gray-700 whitespace-pre-line">{learning.content}</p>
                                    <div className="flex items-center gap-2 mt-1.5">
                                      <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 font-medium">
                                        {learning.category === "tech" && "技术"}
                                        {learning.category === "business" && "业务"}
                                        {learning.category === "tool" && "工具"}
                                        {learning.category === "soft_skill" && "软技能"}
                                        {!["tech", "business", "tool", "soft_skill"].includes(learning.category) && learning.category}
                                      </span>
                                      {learning.source && null}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {log.attachments.length > 0 && (
                            <div className="mb-3">
                              <h3 className="text-sm font-semibold text-gray-900 mb-1.5">附件</h3>
                              <div className="flex flex-wrap gap-2">
                                {log.attachments.map((url, i) => (
                                  <a
                                    key={i}
                                    href={url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-xs text-blue-600 hover:text-blue-800 underline break-all"
                                  >
                                    {url}
                                  </a>
                                ))}
                              </div>
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
