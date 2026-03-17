// Scan Skill - T (Tension) - Scanning Engine
import * as crypto from 'crypto';
const TIME_ANCHORS = [
    { pattern: /within\s+(\d+)\s+months?/i, months: (m) => parseInt(m[1]) },
    { pattern: /by\s+(\d{4})/i, months: () => 12 },
    { pattern: /by\s+end\s+of\s+(\d{4})/i, months: () => 12 },
    { pattern: /next\s+quarter/i, months: () => 3 },
    { pattern: /in\s+(\d+)\s+days?/i, months: (m) => Math.ceil(parseInt(m[1]) / 30) },
    { pattern: /in\s+(\d+)\s+weeks?/i, months: (m) => Math.ceil(parseInt(m[1]) / 4) },
];
const NUMERIC_PATTERNS = [
    /\$\d+(?:\.\d+)?/,
    /\d+(?:,\d{3})*(?:\.\d+)?%/,
    /reduce.*?to\s+\$?\d+/i,
    /increase.*?to\s+\$?\d+/i,
    /create\s+\d+.*?jobs/i,
    /under\s+\$\d+/i,
    /below\s+\$\d+/i,
];
class ScanSkill {
    soulMdHash = '';
    setSoulHash(hash) {
        this.soulMdHash = hash;
    }
    extractTimeAnchor(text) {
        for (const anchor of TIME_ANCHORS) {
            const match = text.match(anchor.pattern);
            if (match) {
                return { found: true, months: anchor.months(match) };
            }
        }
        return { found: false };
    }
    extractNumericMetrics(text) {
        const metrics = [];
        for (const pattern of NUMERIC_PATTERNS) {
            const match = text.match(pattern);
            if (match)
                metrics.push(match[0]);
        }
        return { found: metrics.length > 0, metrics: [...new Set(metrics)] };
    }
    async analyzeVerifiability(text) {
        const timeAnchor = this.extractTimeAnchor(text);
        const numeric = this.extractNumericMetrics(text);
        let score = 0;
        if (timeAnchor.found)
            score += 1;
        if (numeric.found)
            score += 1;
        return { is_verifiable: score >= 2, score };
    }
    calculateExpiryDate(promiseDate, months) {
        const date = new Date(promiseDate);
        date.setMonth(date.getMonth() + months);
        return date.toISOString().split('T')[0];
    }
    extractVerifiableMetric(text) {
        const numeric = this.extractNumericMetrics(text);
        return numeric.found ? numeric.metrics.join(', ') : null;
    }
    async scanStatement(entity, content, sourceUrl, timestamp) {
        const analysis = await this.analyzeVerifiability(content);
        if (!analysis.is_verifiable)
            return null;
        let expiryDate = null;
        if (this.extractTimeAnchor(content).found) {
            const timeAnchor = this.extractTimeAnchor(content);
            if (timeAnchor.months) {
                expiryDate = this.calculateExpiryDate(timestamp, timeAnchor.months);
            }
        }
        const dealId = crypto.createHash('sha256').update(`${entity.id}:${content}:${timestamp}`).digest('hex').substring(0, 16);
        return {
            id: dealId,
            entity,
            promise_text: content,
            source_url: sourceUrl,
            promise_date: timestamp,
            expiry_date: expiryDate,
            verifiable_metric: this.extractVerifiableMetric(content),
            data_source_for_verification: null,
            is_verifiable: analysis.is_verifiable,
            extracted_by: 'prinzclaw@1.0.0',
            soul_md_hash: this.soulMdHash,
        };
    }
    async scanManual(entity, quote, sourceUrl) {
        const timestamp = new Date().toISOString().split('T')[0];
        return this.scanStatement(entity, quote, sourceUrl || 'manual', timestamp);
    }
    getRecommendedDataSource(promiseText) {
        const lower = promiseText.toLowerCase();
        if (lower.includes('gas') || lower.includes('oil') || lower.includes('energy'))
            return 'https://www.eia.gov/petroleum/gasdiesel/';
        if (lower.includes('job') || lower.includes('employment'))
            return 'https://www.bls.gov/';
        if (lower.includes('gdp') || lower.includes('economy'))
            return 'https://www.bea.gov/';
        if (lower.includes('tax'))
            return 'https://www.irs.gov/';
        return null;
    }
}
export default ScanSkill;
//# sourceMappingURL=index.js.map