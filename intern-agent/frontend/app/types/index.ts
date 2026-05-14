/**
 * 前端类型定义
 * 
 * 与后端 schemas.py 保持一致
 */

export interface Task {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed';
}

export interface Learning {
  id: string;
  content: string;
  category: 'tech' | 'business' | 'tool' | 'soft_skill';
  keywords: string[];
  source: string;
}

export interface DailyLog {
  id: string;
  date: string;
  tasks: Task[];
  learnings: Learning[];
  attachments: string[];
  tags: string[];
  ai_summary: string | null;
}

export interface ErrorResponse {
  error: string;
  status_code: number;
  detail?: string;
}

export interface StatsSummary {
  total_logs: number;
  tag_distribution: Record<string, number>;
}
