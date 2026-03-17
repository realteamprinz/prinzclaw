// Craft Skill - C (Curvature) - Strike Forging Engine
import * as crypto from 'crypto';
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

const STRIKE_TEMPLATES = {
  'BROKE PROMISE': [
    'You promised "{metric}" on {date}. The data shows otherwise. Which one is true?',
    'On {date}, you said {promise}. Now the numbers say something different. How do you explain?',
  ],
  'SPINNING': [
    'You said "{current}" on {current_date}. But {past_date} you said "{past}". Which position is real?',
    'Interesting how your tone changed from "{past}" to "{current}". What happened?',
  ],
  'CHERRY-PICKING': [
    'You highlight the wins but ignore the losses. Selective memory or deliberate spin?',
  ],
  'LYING': [
    'Your statement on {date} contradicts official records. Care to explain?',
  ],
};

class CraftSkill {
  private soulMdHash: string = '';

  setSoulHash(hash: string) {
    this.soulMdHash = hash;
  }

  getTemplate(verdict: string): string {
    const templates = STRIKE_TEMPLATES[verdict as keyof typeof STRIKE_TEMPLATES];
    if (!templates || templates.length === 0) {
      return 'Your record speaks for itself. Care to comment?';
    }
    return templates[Math.floor(Math.random() * templates.length)];
  }

  generateCounterText(analysis: AnalysisOutput): string {
    const template = this.getTemplate(analysis.verdict);
    let counterText = template
      .replace('{target}', analysis.newPromise.promise_text.substring(0, 50))
      .replace('{date}', analysis.newPromise.promise_date)
      .replace('{promise}', analysis.newPromise.promise_text.substring(0, 30))
      .replace('{metric}', analysis.newPromise.verifiable_metric || 'your promise');

    if (analysis.historicalPromise) {
      counterText = counterText
        .replace('{current}', analysis.newPromise.promise_text.substring(0, 30))
        .replace('{current_date}', analysis.newPromise.promise_date)
        .replace('{past}', analysis.historicalPromise.promise_text.substring(0, 30))
        .replace('{past_date}', analysis.historicalPromise.promise_date);
    }

    if (!counterText.endsWith('?')) counterText += ' Which one is true?';
    return counterText;
  }

  generateEvidenceChain(analysis: AnalysisOutput): EvidenceItem[] {
    const chain: EvidenceItem[] = [{
      type: 'promise',
      text: analysis.newPromise.promise_text,
      source_url: analysis.newPromise.source_url || '',
      date: analysis.newPromise.promise_date,
    }];

    if (analysis.historicalPromise) {
      chain.push({
        type: 'contradiction',
        text: analysis.historicalPromise.promise_text,
        source_url: analysis.historicalPromise.source_url || '',
        date: analysis.historicalPromise.promise_date,
      });
    }

    return chain;
  }

  generateSummary(analysis: AnalysisOutput): string {
    const target = analysis.newPromise.promise_text.substring(0, 40);
    switch (analysis.verdict) {
      case 'BROKE PROMISE': return `Broken promise: ${target}...`;
      case 'SPINNING': return `Spin detected: Contradiction in statements`;
      case 'CHERRY-PICKING': return `Cherry-picking: Selective data use`;
      default: return `Accountability: ${target}...`;
    }
  }

  async verifyRuleZero(strike: Partial<Strike>, evidenceChain: EvidenceItem[]): Promise<{ passed: boolean; errors: string[] }> {
    const errors: string[] = [];

    for (const evidence of evidenceChain) {
      if (!evidence.source_url || evidence.source_url === '') {
        errors.push('INSUFFICIENT EVIDENCE: No source URL');
      }
    }

    const insultPatterns = [/stupid|idiot|moron|imbecile|dumb/i, /liar|cheat|fraud/i, /corrupt|criminal/i];
    const counterText = strike.counter_text || '';
    for (const pattern of insultPatterns) {
      if (pattern.test(counterText)) {
        errors.push('RULE ZERO VIOLATION: Contains insults');
      }
    }

    if (!counterText.endsWith('?')) {
      errors.push('RULE ZERO VIOLATION: Must end with question');
    }

    return { passed: errors.length === 0, errors };
  }

  async craft(analysis: AnalysisOutput): Promise<CraftOutput> {
    const evidenceChain = this.generateEvidenceChain(analysis);
    const counterText = this.generateCounterText(analysis);
    const summary = this.generateSummary(analysis);

    let verdict = analysis.verdict;
    if (verdict === 'NO_CONTRADICTION') verdict = 'VERIFIED';

    const strike: Strike = {
      id: crypto.randomUUID(),
      target: analysis.newPromise.entity_id,
      verdict,
      summary,
      evidence_chain: JSON.stringify(evidenceChain),
      counter_text: counterText,
      status: 'PENDING',
      created_at: new Date().toISOString(),
      published_at: null,
      forged_by: 'prinzclaw@1.0.0',
      soul_md_hash: this.soulMdHash,
      signature: 'FORGED WITH PRINZCLAW',
    };

    const ruleZeroResult = await this.verifyRuleZero(strike, evidenceChain);

    return { strike, ruleZeroPassed: ruleZeroResult.passed, ruleZeroErrors: ruleZeroResult.errors };
  }
}

export default CraftSkill;
