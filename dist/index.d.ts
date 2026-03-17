declare class Prinzclaw {
    private db;
    private scan;
    private analyze;
    private craft;
    private output;
    private soulHash;
    constructor(dbPath?: string);
    runPipeline(entityHandle: string, entityName: string, quote: string, sourceUrl?: string): Promise<{
        success: boolean;
        stage: string;
        result?: any;
        error?: string;
    }>;
    getQueue(): any[];
    approveStrike(strikeId: string, channel?: string): Promise<{
        success: boolean;
        error?: string;
    }>;
    rejectStrike(strikeId: string, reason?: string): Promise<{
        success: boolean;
        error?: string;
    }>;
    getDEALBoard(): {
        entity: import("./db/index.js").Entity;
        stats: {
            total: number;
            pending: number;
            kept: number;
            broke: number;
            partiallyKept: number;
        };
        score: number;
        promises: import("./db/index.js").Promise[];
    }[];
    getArchive(): import("./db/index.js").Strike[];
    close(): void;
}
export default Prinzclaw;
