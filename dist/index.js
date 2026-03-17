// Main entry point for prinzclaw CLI
import * as fs from 'fs';
import * as path from 'path';
import * as crypto from 'crypto';
import { fileURLToPath } from 'url';
import PrinzclawDB from './db/index.js';
import ScanSkill from './skills/scan/index.js';
import AnalyzeSkill from './skills/analyze/index.js';
import CraftSkill from './skills/craft/index.js';
import OutputSkill from './skills/output/index.js';
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
function getSoulHash() {
    const soulPath = path.join(__dirname, '../soul/SOUL.md');
    if (!fs.existsSync(soulPath)) {
        console.error('[prinzclaw] ERROR: SOUL.md not found!');
        process.exit(1);
    }
    const soulContent = fs.readFileSync(soulPath, 'utf-8');
    return crypto.createHash('sha256').update(soulContent).digest('hex');
}
class Prinzclaw {
    db;
    scan;
    analyze;
    craft;
    output;
    soulHash;
    constructor(dbPath) {
        this.db = new PrinzclawDB(dbPath);
        this.scan = new ScanSkill();
        this.analyze = new AnalyzeSkill(this.db);
        this.craft = new CraftSkill();
        this.output = new OutputSkill(this.db);
        this.soulHash = getSoulHash();
        this.scan.setSoulHash(this.soulHash);
        this.craft.setSoulHash(this.soulHash);
    }
    async runPipeline(entityHandle, entityName, quote, sourceUrl) {
        try {
            console.log('[prinzclaw] Stage 1: Scanning...');
            let entity = this.db.getEntityByHandle(entityHandle);
            if (!entity) {
                entity = this.db.createEntity(entityHandle, entityName);
                console.log(`[prinzclaw] Created entity: ${entityName} (@${entityHandle})`);
            }
            const scanResult = await this.scan.scanManual(entity, quote, sourceUrl);
            if (!scanResult) {
                return { success: false, stage: 'scan', error: 'Statement is not verifiable - filtered out' };
            }
            // Save to database
            this.db.createPromise({
                entity_id: entity.id,
                promise_text: scanResult.promise_text,
                source_url: scanResult.source_url,
                promise_date: scanResult.promise_date,
                expiry_date: scanResult.expiry_date || undefined,
                verifiable_metric: scanResult.verifiable_metric || undefined,
                soul_md_hash: this.soulHash,
            });
            console.log('[prinzclaw] Scan complete - verifiable promise detected');
            console.log('[prinzclaw] Stage 2: Analyzing...');
            const analysis = await this.analyze.analyze(scanResult);
            console.log(`[prinzclaw] Analysis result: ${analysis.verdict}`);
            if (!analysis.shouldCraft && !analysis.contradictionType) {
                return { success: true, stage: 'analyze', result: { verdict: 'NO_CONTRADICTION', message: 'No contradiction detected' } };
            }
            console.log('[prinzclaw] Stage 3: Crafting...');
            const crafted = await this.craft.craft(analysis);
            console.log(`[prinzclaw] Strike forged: ${crafted.strike.id}`);
            if (!crafted.ruleZeroPassed) {
                console.log('[prinzclaw] Rule Zero warnings:', crafted.ruleZeroErrors);
            }
            console.log('[prinzclaw] Stage 4: Output - adding to review queue');
            await this.output.addToQueue(crafted.strike);
            return {
                success: true,
                stage: 'output',
                result: {
                    strikeId: crafted.strike.id,
                    verdict: crafted.strike.verdict,
                    summary: crafted.strike.summary,
                    counterText: crafted.strike.counter_text,
                },
            };
        }
        catch (error) {
            return { success: false, stage: 'unknown', error: error.message };
        }
    }
    getQueue() {
        return this.output.getAllPendingFromDB();
    }
    async approveStrike(strikeId, channel) {
        return this.output.approve(strikeId, channel);
    }
    async rejectStrike(strikeId, reason) {
        return this.output.reject(strikeId, reason);
    }
    getDEALBoard() {
        const entities = this.db.getAllEntities();
        return entities.map(entity => {
            const stats = this.db.getEntityStats(entity.id);
            const promises = this.db.getPromisesByEntity(entity.id);
            const score = stats.total > 0 ? Math.round(((stats.kept + stats.partiallyKept * 0.5) / stats.total) * 100) : 100;
            return { entity, stats, score, promises: promises.slice(0, 5) };
        });
    }
    getArchive() {
        return this.output.getApprovedStrikes();
    }
    close() {
        this.db.close();
    }
}
export default Prinzclaw;
//# sourceMappingURL=index.js.map