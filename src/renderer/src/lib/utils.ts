/**
 * Utility functions for Open Stream
 */

import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge class names with Tailwind CSS conflict resolution
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Debounce function for optimizing frequent calls
 */
export function debounce<T extends (...args: any[]) => void>(
  func: T,
  wait: number
): T {
  let timeout: ReturnType<typeof setTimeout> | null = null;
  return ((...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  }) as T;
}

/**
 * Throttle function for rate limiting calls
 */
export function throttle<T extends (...args: any[]) => void>(
  func: T,
  delay: number
): T {
  let lastCall = 0;
  return ((...args: Parameters<T>) => {
    const now = new Date().getTime();
    if (now - lastCall < delay) return;
    lastCall = now;
    return func(...args);
  }) as T;
}

/**
 * Format number as percentage
 */
export function formatPercentage(value: number, precision = 1): string {
  return `${(value * 100).toFixed(precision)}%`;
}

/**
 * Format processing time in milliseconds
 */
export function formatProcessingTime(ms: number): string {
  if (ms < 1000) return `${ms.toFixed(1)}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

/**
 * Clamp value between min and max
 */
export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

/**
 * Check if value is empty (null, undefined, empty string, empty array)
 */
export function isEmpty(value: unknown): boolean {
  if (value == null) return true;
  if (typeof value === "string") return value.trim().length === 0;
  if (Array.isArray(value)) return value.length === 0;
  if (typeof value === "object") return Object.keys(value).length === 0;
  return false;
}

/**
 * Generate unique ID
 */
export function generateId(): string {
  return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
}

/**
 * Safe JSON parse with fallback
 */
export function safeJsonParse<T>(json: string, fallback: T): T {
  try {
    return JSON.parse(json) as T;
  } catch {
    return fallback;
  }
}

/**
 * Format text length for display
 */
export function formatTextLength(text: string): { characters: number; words: number } {
  return {
    characters: text.length,
    words: text.trim().split(/\s+/).filter(word => word.length > 0).length
  };
}

/**
 * Validate text for analysis
 */
export function validateText(text: string, maxLength = 10000): {
  isValid: boolean;
  errors: string[];
  characterCount: number;
  wordCount: number;
} {
  const errors: string[] = [];
  const trimmedText = text.trim();
  const characterCount = text.length;
  const wordCount = trimmedText.length > 0 ? trimmedText.split(/\s+/).length : 0;

  if (trimmedText.length === 0) {
    errors.push("Text cannot be empty");
  }

  if (characterCount > maxLength) {
    errors.push(`Text exceeds maximum length of ${maxLength} characters`);
  }

  return {
    isValid: errors.length === 0,
    errors,
    characterCount,
    wordCount,
  };
}

/**
 * Get text metadata for display
 */
export function getTextMetadata(text: string) {
  const characterCount = text.length;
  const wordCount = text.trim().length > 0 ? text.trim().split(/\s+/).length : 0;
  return {
    characterCount,
    wordCount,
    isValid: text.trim().length > 0 && text.trim().length <= 10000,
  };
}

/**
 * Simple hash function for text caching
 */
export function hashText(text: string): string {
  let hash = 0;
  for (let i = 0; i < text.length; i++) {
    const char = text.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return hash.toString();
}