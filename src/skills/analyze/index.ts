// Analyze Skill - A (Acceleration) - Contradiction Detection
import * as crypto from 'crypto';
import type { Entity, Promise as PromiseType } from '../../db/index.js';
import type { ScanResult } from '../scan/index.js';

export interface AnalysisOutput {
  id: string;
  newPromise: PromiseType;
  historicalPromise: PromiseType | null;
  contradictionType: string | null;
  contradictionScore: number | null;
  outcome: string | null;
  evidenceUrl: string | null;
  verdict: string;
  shouldCraft: boolean;
}

const COHERENCE_MONTHS = 11;

const CONTRADICTION_PATTERNS = {
  SPINNING: [
    { current: /minimal/i, historical: /catastrophic|disaster|devastating/i },
    { current: /no impact|very little impact/i, historical: /significant impact|major impact/i },
    { current: /great success|tremendous success/i, historical: /failure|failed|disaster/i },
    { current: /nothing to worry about/i, historical: /serious concern|grave concern/i },
  ],
};

class AnalyzeSkill {
  private db: any;

  constructor(db: any) {
    this.db = db;
  }

  getCoherenceWindow(currentDate: string): { start: string; end: string } {
    const end = new Date(currentDate);
    const start = new Date(end);
    start.setMonth(start.getMonth() - COHERENCE_MONTHS);
    return { start: start.toISOString().split('T')[0], end: end.toISOString().split('T')[0] };
  }

  isExpired(promise: PromiseType): boolean {
    if (!promise.expiry_date) return false;
    return new Date(promise.expiry_date) < new Date();
  }

  async checkDealExpiration(promise: PromiseType): Promise<{ outcome: string; evidenceUrl: string | null; score: number } | null> {
    if (!this.isExpired(promise)) return null;
    if (!promise.verifiable_metric) {
      return { outcome: 'INSUFFICIENT_EVIDENCE', evidenceUrl: null, score: 0 };
    }
    return null;
  }

  async detectContradiction(newPromise: PromiseType, historicalPromises: PromiseType[]): Promise<{ historicalPromise: PromiseType; contradictionType: string; score: number } | null> {
    if (historicalPromises.length === 0) return null;

    for (const historical of historicalPromises) {
      for (const pattern of CONTRADICTION_PATTERNS.SPINNING) {
        if (pattern.current.test(newPromise.promise_text) && pattern.historical.test(historical.promise_text)) {
          return { historicalPromise: historical, contradictionType: 'SPINNING', score: 0.9 };
        }
      }

      const currentWords = new Set(newPromise.promise_text.toLowerCase().split(/\s+/));
      const historicalWords = new Set(historical.promise_text.toLowerCase().split(/\s+/));
      const opposites: [string, string][] = [['success', 'failure'], ['good', 'bad'], ['minimal', 'massive'], ['increase', 'decrease']];

      for (const [word1, word2] of opposites) {
        if (currentWords.has(word1) && historicalWords.has(word2)) {
          return { historicalPromise: historical, contradictionType: 'SPINNING', score: 0.75 };
        }
      }
    }
    return null;
  }

  async analyze(scanResult: ScanResult): Promise<AnalysisOutput> {
    const { start, end } = this.getCoherenceWindow(scanResult.promise_date);
    const historicalPromises = this.db.getPromisesInWindow(scanResult.entity.id, start, end);

    const promiseData = {
      id: scanResult.id,
      entity_id: scanResult.entity.id,
      promise_text: scanResult.promise_text,
      source_url: scanResult.source_url,
      promise_date: scanResult.promise_date,
      expiry_date: scanResult.expiry_date,
      verifiable_metric: scanResult.verifiable_metric,
      data_source_for_verification: scanResult.data_source_for_verification,
      status: 'PENDING' as const,
      created_at: new Date().toISOString(),
      soul_md_hash: scanResult.soul_md_hash,
    };

    const expirationResult = await this.checkDealExpiration(promiseData);
    if (expirationResult && expirationResult.outcome) {
      return {
        id: crypto.randomUUID(),
        newPromise: promiseData,
        historicalPromise: null,
        contradictionType: expirationResult.outcome === 'BROKE' ? 'BROKE PROMISE' : null,
        contradictionScore: expirationResult.score,
        outcome: expirationResult.outcome,
        evidenceUrl: expirationResult.evidenceUrl,
        verdict: expirationResult.outcome,
        shouldCraft: expirationResult.outcome === 'BROKE',
      };
    }

    const contradictionResult = await this.detectContradiction(promiseData, historicalPromises);
    if (contradictionResult) {
      return {
        id: crypto.randomUUID(),
        newPromise: promiseData,
        historicalPromise: contradictionResult.historicalPromise,
        contradictionType: contradictionResult.contradictionType,
        contradictionScore: contradictionResult.score,
        outcome: null,
        evidenceUrl: scanResult.source_url,
        verdict: contradictionResult.contradictionType,
        shouldCraft: contradictionResult.score >= 0.7,
      };
    }

    return {
      id: crypto.randomUUID(),
      newPromise: promiseData,
      historicalPromise: null,
      contradictionType: null,
      contradictionScore: null,
      outcome: null,
      evidenceUrl: null,
      verdict: 'NO_CONTRADICTION',
      shouldCraft: false,
    };
  }
}

export default AnalyzeSkill;
