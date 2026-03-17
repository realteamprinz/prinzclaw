import type { Promise as PromiseType } from '../../db/index.js';
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
declare class AnalyzeSkill {
    private db;
    constructor(db: any);
    getCoherenceWindow(currentDate: string): {
        start: string;
        end: string;
    };
    isExpired(promise: PromiseType): boolean;
    checkDealExpiration(promise: PromiseType): Promise<{
        outcome: string;
        evidenceUrl: string | null;
        score: number;
    } | null>;
    detectContradiction(newPromise: PromiseType, historicalPromises: PromiseType[]): Promise<{
        historicalPromise: PromiseType;
        contradictionType: string;
        score: number;
    } | null>;
    analyze(scanResult: ScanResult): Promise<AnalysisOutput>;
}
export default AnalyzeSkill;
