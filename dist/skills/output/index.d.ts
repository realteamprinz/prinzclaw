import type { Strike } from '../../db/index.js';
interface ReviewItem {
    strike: Strike;
    evidenceChain: any[];
    createdAt: string;
}
declare class OutputSkill {
    private db;
    private pendingQueue;
    constructor(db: any);
    addToQueue(strike: Strike): Promise<void>;
    getPendingReviews(): ReviewItem[];
    getAllPendingFromDB(): Strike[];
    approve(strikeId: string, channel?: string): Promise<{
        success: boolean;
        error?: string;
    }>;
    reject(strikeId: string, reason?: string): Promise<{
        success: boolean;
        error?: string;
    }>;
    getApprovedStrikes(): Strike[];
    getAllStrikes(): Strike[];
    getQueueStats(): {
        pending: number;
        approved: number;
        rejected: number;
        published: number;
    };
}
export default OutputSkill;
