/**
 * API 客户端
 * 
 * 处理所有后端 API 请求，包括认证、错误处理等
 */

import type { DailyLog, ErrorResponse, StatsSummary } from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || '';

/**
 * API 请求封装
 */
class ApiClient {
  private baseUrl: string;
  private apiKey: string;

  constructor(baseUrl: string, apiKey: string) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
  }

  /**
   * 发送请求
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    // 添加认证头
    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      // 解析响应
      const data = await response.json();

      // 检查 HTTP 状态码
      if (!response.ok) {
        const error: ErrorResponse = data;
        throw new Error(error.error || `HTTP ${response.status}: ${response.statusText}`);
      }

      return data as T;
    } catch (error) {
      // 网络错误或其他异常
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('网络请求失败，请检查网络连接');
    }
  }

  /**
   * GET 请求
   */
  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  /**
   * POST 请求
   */
  async post<T>(endpoint: string, body: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  /**
   * PUT 请求
   */
  async put<T>(endpoint: string, body: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(body),
    });
  }

  /**
   * DELETE 请求
   */
  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  // API 端点方法

  /**
   * 获取学习记录列表
   */
  async getLogs(skip = 0, limit = 30): Promise<DailyLog[]> {
    return this.get<DailyLog[]>(`/logs?skip=${skip}&limit=${limit}`);
  }

  /**
   * 获取单条学习记录
   */
  async getLog(id: string): Promise<DailyLog> {
    return this.get<DailyLog>(`/logs/${id}`);
  }

  /**
   * 创建学习记录
   */
  async createLog(data: any): Promise<DailyLog> {
    return this.post<DailyLog>('/logs', data);
  }

  /**
   * 更新学习记录
   */
  async updateLog(id: string, data: any): Promise<DailyLog> {
    return this.put<DailyLog>(`/logs/${id}`, data);
  }

  /**
   * 删除学习记录
   */
  async deleteLog(id: string): Promise<{ message: string }> {
    return this.delete<{ message: string }>(`/logs/${id}`);
  }

  /**
   * 获取统计摘要
   */
  async getStats(): Promise<StatsSummary> {
    return this.get<StatsSummary>('/logs/stats/summary');
  }

  /**
   * 图片识别
   */
  async recognizeImage(imageBase64: string): Promise<{ text: string }> {
    return this.post<{ text: string }>('/recognize-image', {
      image_base64: imageBase64,
    });
  }

  /**
   * 健康检查
   */
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.get<{ status: string; timestamp: string }>('/health');
  }
}

// 导出单例
export const api = new ApiClient(API_BASE, API_KEY);

// 导出类型
export type { ApiClient };
