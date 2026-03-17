import type { Strike } from '../../db/index.js';
import type { AnalysisOutput } from '../analyze/index.js';
interface EvidenceItem {
    type: 'promise' | 'outcome' | 'contradiction';
    text: string;
    source_url: string;
    date: string;
}
interface CraftOutput {
    strike: Strike;
    ruleZeroPassed: boolean;
    ruleZeroErrors: string[];
}
declare class CraftSkill {
    private soulMdHash;
    setSoulHash(hash: string): void;
    getTemplate(verdict: string): string;
    generateCounterText(analysis: AnalysisOutput): string;
    generateEvidenceChain(analysis: AnalysisOutput): EvidenceItem[];
    generateSummary(analysis: AnalysisOutput): string;
    verifyRuleZero(strike: Partial<Strike>, evidenceChain: EvidenceItem[]): Promise<{
        passed: boolean;
        errors: string[];
    }>;
    craft(analysis: AnalysisOutput): Promise<CraftOutput>;
}
export default CraftSkill;
