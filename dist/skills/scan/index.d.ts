import type { Entity } from '../../db/index.js';
export interface ScanResult {
    id: string;
    entity: Entity;
    promise_text: string;
    source_url: string;
    promise_date: string;
    expiry_date: string | null;
    verifiable_metric: string | null;
    data_source_for_verification: string | null;
    is_verifiable: boolean;
    extracted_by: string;
    soul_md_hash: string;
}
declare class ScanSkill {
    private soulMdHash;
    setSoulHash(hash: string): void;
    extractTimeAnchor(text: string): {
        found: boolean;
        months?: number;
    };
    extractNumericMetrics(text: string): {
        found: boolean;
        metrics: string[];
    };
    analyzeVerifiability(text: string): Promise<{
        is_verifiable: boolean;
        score: number;
    }>;
    calculateExpiryDate(promiseDate: string, months: number): string;
    extractVerifiableMetric(text: string): string | null;
    scanStatement(entity: Entity, content: string, sourceUrl: string, timestamp: string): Promise<ScanResult | null>;
    scanManual(entity: Entity, quote: string, sourceUrl?: string): Promise<ScanResult | null>;
    getRecommendedDataSource(promiseText: string): string | null;
}
export default ScanSkill;
