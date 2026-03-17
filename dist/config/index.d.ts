export interface ProviderConfig {
    model: string;
    api_key?: string;
    endpoint?: string;
}
export interface GatewayConfig {
    port: number;
    host: string;
}
export interface HeartbeatConfig {
    interval: number;
    enabled: boolean;
}
export interface ChannelsConfig {
    telegram?: {
        enabled: boolean;
        token?: string;
    };
    discord?: {
        enabled: boolean;
        token?: string;
    };
}
export interface PrinzclawConfig {
    providers: {
        primary: string;
        anthropic?: ProviderConfig;
        openai?: ProviderConfig;
        deepseek?: ProviderConfig;
        ollama?: ProviderConfig;
    };
    gateway: GatewayConfig;
    heartbeat: HeartbeatConfig;
    workspace: string;
    database: string;
    channels?: ChannelsConfig;
}
declare const DEFAULT_CONFIG: PrinzclawConfig;
declare class ConfigManager {
    private config;
    private configPath;
    constructor(configPath?: string);
    load(): PrinzclawConfig;
    get(): PrinzclawConfig;
    save(config?: Partial<PrinzclawConfig>): void;
    getApiKey(provider: string): string | undefined;
    getWorkspace(): string;
    getDatabase(): string;
    private mergeDeep;
    private isObject;
}
export default ConfigManager;
export { DEFAULT_CONFIG };
