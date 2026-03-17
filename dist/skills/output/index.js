class OutputSkill {
    db;
    pendingQueue = [];
    constructor(db) {
        this.db = db;
    }
    async addToQueue(strike) {
        const reviewItem = {
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
    getPendingReviews() {
        return this.pendingQueue;
    }
    getAllPendingFromDB() {
        return this.db.getPendingStrikes();
    }
    async approve(strikeId, channel) {
        this.db.updateStrikeStatus(strikeId, 'APPROVED');
        const strike = this.db.getStrike(strikeId);
        if (!strike)
            return { success: false, error: 'Strike not found' };
        console.log(`[output] Published to ${channel || 'all channels'}: ${strikeId}`);
        this.db.updateStrikeStatus(strikeId, 'PUBLISHED');
        this.pendingQueue = this.pendingQueue.filter(item => item.strike.id !== strikeId);
        return { success: true };
    }
    async reject(strikeId, reason) {
        this.db.updateStrikeStatus(strikeId, 'REJECTED');
        this.pendingQueue = this.pendingQueue.filter(item => item.strike.id !== strikeId);
        console.log(`[output] Rejected: ${strikeId}${reason ? ` - Reason: ${reason}` : ''}`);
        return { success: true };
    }
    getApprovedStrikes() {
        return this.db.getApprovedStrikes();
    }
    getAllStrikes() {
        return this.db.getAllStrikes();
    }
    getQueueStats() {
        const allStrikes = this.db.getAllStrikes();
        return {
            pending: allStrikes.filter((s) => s.status === 'PENDING').length,
            approved: allStrikes.filter((s) => s.status === 'APPROVED').length,
            rejected: allStrikes.filter((s) => s.status === 'REJECTED').length,
            published: allStrikes.filter((s) => s.status === 'PUBLISHED').length,
        };
    }
}
export default OutputSkill;
//# sourceMappingURL=index.js.map