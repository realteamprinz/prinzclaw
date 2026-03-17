import ConfigManager from '../config/index.js';
import Brain from '../brain/index.js';
import PrinzclawDB from '../db/index.js';
export interface HeartbeatTask {
    name: string;
    enabled: boolean;
    run: () => Promise<void>;
}
declare class Heartbeat {
    private config;
    private brain;
    private db;
    private intervalId;
    private tasks;
    constructor(config: ConfigManager, brain: Brain, db: PrinzclawDB);
    initialize(): void;
    start(): void;
    stop(): void;
    private tick;
    private checkExpiringPromises;
    private updateDealScores;
    private memoryCleanup;
}
export default Heartbeat;
