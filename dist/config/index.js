// Configuration module for prinzclaw
// Loads and manages prinzclaw.json configuration
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
const DEFAULT_CONFIG = {
    providers: {
        primary: 'anthropic',
        anthropic: { model: 'claude-sonnet-4-20250514' },
        openai: { model: 'gpt-4' },
        ollama: { model: 'llama3', endpoint: 'http://localhost:11434' },
    },
    gateway: {
        port: 18789,
        host: '127.0.0.1',
    },
    heartbeat: {
        interval: 30,
        enabled: true,
    },
    workspace: '~/.prinzclaw/workspace',
    database: '~/.prinzclaw/prinzclaw.db',
};
class ConfigManager {
    config = null;
    configPath;
    constructor(configPath) {
        // Default to ~/.prinzclaw/prinzclaw.json
        const homeDir = os.homedir();
        this.configPath = configPath || path.join(homeDir, '.prinzclaw', 'prinzclaw.json');
    }
    // Load configuration from file
    load() {
        if (this.config) {
            return this.config;
        }
        // Check if config file exists
        if (!fs.existsSync(this.configPath)) {
            console.log(`[config] No config found at ${this.configPath}, using defaults`);
            this.config = DEFAULT_CONFIG;
            return this.config;
        }
        try {
            const content = fs.readFileSync(this.configPath, 'utf-8');
            const loaded = JSON.parse(content);
            // Merge with defaults
            this.config = this.mergeDeep(DEFAULT_CONFIG, loaded);
            console.log(`[config] Loaded config from ${this.configPath}`);
            return this.config;
        }
        catch (error) {
            console.error(`[config] Error loading config:`, error);
            this.config = DEFAULT_CONFIG;
            return this.config;
        }
    }
    // Get current config
    get() {
        if (!this.config) {
            return this.load();
        }
        return this.config;
    }
    // Save configuration to file
    save(config) {
        const toSave = config ? this.mergeDeep(this.get(), config) : this.get();
        // Ensure directory exists
        const dir = path.dirname(this.configPath);
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }
        fs.writeFileSync(this.configPath, JSON.stringify(toSave, null, 2));
        this.config = toSave;
        console.log(`[config] Saved config to ${this.configPath}`);
    }
    // Get API key from environment or config
    getApiKey(provider) {
        const config = this.get();
        // First check environment variables
        const envKey = `${provider.toUpperCase()}_API_KEY`;
        if (process.env[envKey]) {
            return process.env[envKey];
        }
        // Then check config
        const providerConfig = config.providers[provider];
        if (providerConfig && 'api_key' in providerConfig) {
            return providerConfig.api_key;
        }
        return undefined;
    }
    // Get workspace directory (expand ~)
    getWorkspace() {
        const workspace = this.get().workspace;
        return workspace.replace(/^~/, os.homedir());
    }
    // Get database path (expand ~)
    getDatabase() {
        const database = this.get().database;
        return database.replace(/^~/, os.homedir());
    }
    // Merge deep objects
    mergeDeep(target, source) {
        const output = { ...target };
        if (this.isObject(target) && this.isObject(source)) {
            Object.keys(source).forEach(key => {
                if (this.isObject(source[key])) {
                    if (!(key in target)) {
                        output[key] = source[key];
                    }
                    else {
                        output[key] = this.mergeDeep(target[key], source[key]);
                    }
                }
                else {
                    output[key] = source[key];
                }
            });
        }
        return output;
    }
    isObject(item) {
        return item && typeof item === 'object' && !Array.isArray(item);
    }
}
export default ConfigManager;
export { DEFAULT_CONFIG };
//# sourceMappingURL=index.js.map