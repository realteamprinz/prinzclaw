export interface Entity {
    id: string;
    handle: string;
    display_name: string;
    created_at: string;
}
export interface Promise {
    id: string;
    entity_id: string;
    promise_text: string;
    source_url: string | null;
    promise_date: string;
    expiry_date: string | null;
    verifiable_metric: string | null;
    data_source_for_verification: string | null;
    status: 'PENDING' | 'KEPT' | 'BROKE' | 'PARTIALLY_KEPT' | 'INSUFFICIENT_EVIDENCE';
    created_at: string;
    soul_md_hash: string | null;
}
export interface Strike {
    id: string;
    target: string;
    verdict: string;
    summary: string;
    evidence_chain: string;
    counter_text: string;
    status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'PUBLISHED';
    created_at: string;
    published_at: string | null;
    forged_by: string;
    soul_md_hash: string | null;
    signature: string;
}
declare class PrinzclawDB {
    private db;
    constructor(dbPath?: string);
    private initialize;
    createEntity(handle: string, displayName: string): Entity;
    getEntity(id: string): Entity | undefined;
    getEntityByHandle(handle: string): Entity | undefined;
    getAllEntities(): Entity[];
    createPromise(data: {
        entity_id: string;
        promise_text: string;
        source_url?: string;
        promise_date: string;
        expiry_date?: string;
        verifiable_metric?: string;
        data_source_for_verification?: string;
        soul_md_hash?: string;
    }): Promise;
    getPromise(id: string): Promise | undefined;
    getPromisesByEntity(entityId: string): Promise[];
    getPendingPromises(entityId?: string): Promise[];
    getPromisesInWindow(entityId: string, startDate: string, endDate: string): Promise[];
    updatePromiseStatus(id: string, status: Promise['status']): void;
    createStrike(data: {
        target: string;
        verdict: string;
        summary: string;
        evidence_chain: any[];
        counter_text: string;
        forged_by?: string;
        soul_md_hash?: string;
    }): Strike;
    getStrike(id: string): Strike | undefined;
    getPendingStrikes(): Strike[];
    getApprovedStrikes(): Strike[];
    getAllStrikes(): Strike[];
    updateStrikeStatus(id: string, status: Strike['status']): void;
    getEntityStats(entityId: string): {
        total: number;
        pending: number;
        kept: number;
        broke: number;
        partiallyKept: number;
    };
    close(): void;
}
export default PrinzclawDB;
