import ConfigManager from '../config/index.js';
import Brain from '../brain/index.js';
import PrinzclawDB from '../db/index.js';
import Heartbeat from '../heartbeat/index.js';
declare class Gateway {
    private app;
    private server;
    private wss;
    private config;
    private brain;
    private db;
    private heartbeat;
    private clients;
    constructor(config: ConfigManager, brain: Brain, db: PrinzclawDB, heartbeat: Heartbeat);
    private initializeRoutes;
    start(): Promise<void>;
    stop(): void;
    private broadcast;
}
export default Gateway;
