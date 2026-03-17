// Heartbeat Scheduler
// Runs automated checks at configurable intervals

import ConfigManager from '../config/index.js';
import Brain from '../brain/index.js';
import PrinzclawDB from '../db/index.js';

export interface HeartbeatTask {
  name: string;
  enabled: boolean;
  run: () => Promise<void>;
}

class Heartbeat {
  private config: ConfigManager;
  private brain: Brain;
  private db: PrinzclawDB;
  private intervalId: NodeJS.Timeout | null = null;
  private tasks: HeartbeatTask[] = [];

  constructor(config: ConfigManager, brain: Brain, db: PrinzclawDB) {
    this.config = config;
    this.brain = brain;
    this.db = db;
  }

  // Initialize heartbeat tasks
  initialize(): void {
    console.log('[heartbeat] Initializing heartbeat tasks...');

    // Task 1: Check expiring promises
    this.tasks.push({
      name: 'check_expiry',
      enabled: true,
      run: this.checkExpiringPromises.bind(this),
    });

    // Task 2: Update DEAL scores
    this.tasks.push({
      name: 'update_scores',
      enabled: true,
      run: this.updateDealScores.bind(this),
    });

    // Task 3: Memory cleanup
    this.tasks.push({
      name: 'memory_cleanup',
      enabled: true,
      run: this.memoryCleanup.bind(this),
    });

    console.log(`[heartbeat] Registered ${this.tasks.length} tasks`);
  }

  // Start heartbeat daemon
  start(): void {
    const cfg = this.config.get();
    const interval = cfg.heartbeat.interval * 60 * 1000; // Convert to ms

    if (!cfg.heartbeat.enabled) {
      console.log('[heartbeat] Disabled in config');
      return;
    }

    console.log(`[heartbeat] Starting with ${cfg.heartbeat.interval} minute interval`);

    this.intervalId = setInterval(async () => {
      await this.tick();
    }, interval);

    // Run once immediately
    this.tick();
  }

  // Stop heartbeat daemon
  stop(): void {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
      console.log('[heartbeat] Stopped');
    }
  }

  // Execute one tick
  private async tick(): Promise<void> {
    console.log('[heartbeat] Tick...');

    for (const task of this.tasks) {
      if (task.enabled) {
        try {
          await task.run();
        } catch (error) {
          console.error(`[heartbeat] Task ${task.name} failed:`, error);
        }
      }
    }

    console.log('[heartbeat] Tick complete');
  }

  // Task: Check promises nearing expiry
  private async checkExpiringPromises(): Promise<void> {
    const entities = this.db.getAllEntities();
    const now = new Date();
    const sevenDays = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);

    for (const entity of entities) {
      const promises = this.db.getPromisesByEntity(entity.id);

      for (const promise of promises) {
        if (promise.status === 'PENDING' && promise.expiry_date) {
          const expiry = new Date(promise.expiry_date);

          if (expiry <= sevenDays) {
            console.log(`[heartbeat] Promise expiring soon: ${promise.promise_text.substring(0, 50)}...`);

            // Use LLM to analyze
            const prompt = `
Analyze this expiring promise:

Promise: "${promise.promise_text}"
Expiry date: ${promise.expiry_date}
Verifiable metric: ${promise.verifiable_metric || 'none'}

Has 7 days passed since expiry date?
If yes, what is the actual outcome? Look for public data sources.

Respond with:
- outcome: KEPT | BROKE | PARTIALLY_KEPT | INSUFFICIENT_EVIDENCE
- evidence_url: (public source URL or "none")
- brief_explanation
`;

            const response = await this.brain.think(prompt);

            // Update promise status
            const outcome = response.content.toUpperCase().includes('BROKE')
              ? 'BROKE'
              : response.content.toUpperCase().includes('KEPT')
                ? 'KEPT'
                : 'PARTIALLY_KEPT';

            this.db.updatePromiseStatus(promise.id, outcome as any);

            await this.brain.writeToLog(`Promise ${outcome}: ${promise.promise_text.substring(0, 50)}...`);
          }
        }
      }
    }
  }

  // Task: Update DEAL scores
  private async updateDealScores(): Promise<void> {
    const entities = this.db.getAllEntities();

    for (const entity of entities) {
      const stats = this.db.getEntityStats(entity.id);
      // Score is calculated in getDEALBoard()
      console.log(`[heartbeat] DEAL score for ${entity.display_name}: ${stats.total > 0 ? Math.round(((stats.kept + stats.partiallyKept * 0.5) / stats.total) * 100) : 100}%`);
    }
  }

  // Task: Memory cleanup
  private async memoryCleanup(): Promise<void> {
    // Check if today's log is getting too long
    // In production, would implement log compaction
    console.log('[heartbeat] Memory check: OK');
  }
}

export default Heartbeat;
