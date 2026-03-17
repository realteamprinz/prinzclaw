// Output Skill - O (Observer) - Review Queue & Publishing
import type { Strike } from '../../db/index.js';

interface ReviewItem {
  strike: Strike;
  evidenceChain: any[];
  createdAt: string;
}

class OutputSkill {
  private db: any;
  private pendingQueue: ReviewItem[] = [];

  constructor(db: any) {
    this.db = db;
  }

  async addToQueue(strike: Strike): Promise<void> {
    const reviewItem: ReviewItem = {
      strike,
      evidenceChain: JSON.parse(strike.evidence_chain),
      createdAt: new Date().toISOString(),
    };

    this.db.createStrike({
      target: strike.target,
      verdict: strike.verdict,
      summary: strike.summary,
      evidence_chain: reviewItem.evidenceChain,
      counter_text: strike.counter_text,
      forged_by: strike.forged_by,
      soul_md_hash: strike.soul_md_hash,
    });

    this.pendingQueue.push(reviewItem);
    console.log(`[output] Added to review queue: ${strike.id}`);
  }

  getPendingReviews(): ReviewItem[] {
    return this.pendingQueue;
  }

  getAllPendingFromDB(): Strike[] {
    return this.db.getPendingStrikes();
  }

  async approve(strikeId: string, channel?: string): Promise<{ success: boolean; error?: string }> {
    this.db.updateStrikeStatus(strikeId, 'APPROVED');
    const strike = this.db.getStrike(strikeId);
    if (!strike) return { success: false, error: 'Strike not found' };

    console.log(`[output] Published to ${channel || 'all channels'}: ${strikeId}`);
    this.db.updateStrikeStatus(strikeId, 'PUBLISHED');
    this.pendingQueue = this.pendingQueue.filter(item => item.strike.id !== strikeId);

    return { success: true };
  }

  async reject(strikeId: string, reason?: string): Promise<{ success: boolean; error?: string }> {
    this.db.updateStrikeStatus(strikeId, 'REJECTED');
    this.pendingQueue = this.pendingQueue.filter(item => item.strike.id !== strikeId);
    console.log(`[output] Rejected: ${strikeId}${reason ? ` - Reason: ${reason}` : ''}`);
    return { success: true };
  }

  getApprovedStrikes(): Strike[] {
    return this.db.getApprovedStrikes();
  }

  getAllStrikes(): Strike[] {
    return this.db.getAllStrikes();
  }

  getQueueStats(): { pending: number; approved: number; rejected: number; published: number } {
    const allStrikes = this.db.getAllStrikes();
    return {
      pending: allStrikes.filter((s: Strike) => s.status === 'PENDING').length,
      approved: allStrikes.filter((s: Strike) => s.status === 'APPROVED').length,
      rejected: allStrikes.filter((s: Strike) => s.status === 'REJECTED').length,
      published: allStrikes.filter((s: Strike) => s.status === 'PUBLISHED').length,
    };
  }
}

export default OutputSkill;
