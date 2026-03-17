// Brain Module - LLM Integration
// Handles context assembly, model inference, and ReAct loop
import axios from 'axios';
import * as fs from 'fs';
import * as path from 'path';
// Abstract LLM Provider
class LLMProvider {
}
// Anthropic Provider
class AnthropicProvider extends LLMProvider {
    name = 'anthropic';
    apiKey;
    model;
    constructor(apiKey, model = 'claude-sonnet-4-20250514') {
        super();
        this.apiKey = apiKey;
        this.model = model;
    }
    async chat(messages) {
        const systemMessage = messages.find(m => m.role === 'system')?.content || '';
        const conversation = messages.filter(m => m.role !== 'system');
        const response = await axios.post('https://api.anthropic.com/v1/messages', {
            model: this.model,
            max_tokens: 4096,
            system: systemMessage,
            messages: conversation,
        }, {
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': this.apiKey,
                'anthropic-version': '2023-06-01',
            },
        });
        return {
            content: response.data.content[0].text,
            usage: {
                input_tokens: response.data.usage.input_tokens,
                output_tokens: response.data.usage.output_tokens,
            },
        };
    }
}
// OpenAI Provider
class OpenAIProvider extends LLMProvider {
    name = 'openai';
    apiKey;
    model;
    constructor(apiKey, model = 'gpt-4') {
        super();
        this.apiKey = apiKey;
        this.model = model;
    }
    async chat(messages) {
        const response = await axios.post('https://api.openai.com/v1/chat/completions', {
            model: this.model,
            messages: messages,
            temperature: 0.7,
        }, {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.apiKey}`,
            },
        });
        return {
            content: response.data.choices[0].message.content,
            usage: {
                input_tokens: response.data.usage.prompt_tokens,
                output_tokens: response.data.usage.completion_tokens,
            },
        };
    }
}
// Ollama Provider (local)
class OllamaProvider extends LLMProvider {
    name = 'ollama';
    endpoint;
    model;
    constructor(model = 'llama3', endpoint = 'http://localhost:11434') {
        super();
        this.model = model;
        this.endpoint = endpoint;
    }
    async chat(messages) {
        // Convert messages to Ollama format
        const ollamaMessages = messages.map(m => ({
            role: m.role,
            content: m.content,
        }));
        const response = await axios.post(`${this.endpoint}/api/chat`, {
            model: this.model,
            messages: ollamaMessages,
            stream: false,
        });
        return {
            content: response.data.message.content,
        };
    }
}
// DeepSeek Provider
class DeepSeekProvider extends LLMProvider {
    name = 'deepseek';
    apiKey;
    model;
    constructor(apiKey, model = 'deepseek-chat') {
        super();
        this.apiKey = apiKey;
        this.model = model;
    }
    async chat(messages) {
        const response = await axios.post('https://api.deepseek.com/v1/chat/completions', {
            model: this.model,
            messages: messages,
            temperature: 0.7,
        }, {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.apiKey}`,
            },
        });
        return {
            content: response.data.choices[0].message.content,
            usage: {
                input_tokens: response.data.usage.prompt_tokens,
                output_tokens: response.data.usage.completion_tokens,
            },
        };
    }
}
// Brain - Main orchestrator
class Brain {
    provider = null;
    config;
    workspace;
    // Context files
    soulContext = '';
    agentsContext = '';
    skillsContext = '';
    memoryContext = '';
    todayLog = '';
    yesterdayLog = '';
    constructor(config) {
        this.config = config;
        this.workspace = config.getWorkspace();
    }
    // Initialize the Brain - load all contexts
    async initialize() {
        console.log('[brain] Initializing Brain module...');
        // Ensure workspace exists
        if (!fs.existsSync(this.workspace)) {
            fs.mkdirSync(this.workspace, { recursive: true });
        }
        // Load contexts in order (OpenClaw priority)
        await this.loadContexts();
        // Initialize LLM provider
        this.initializeProvider();
        console.log('[brain] Brain initialized');
    }
    // Load all context files
    async loadContexts() {
        // 1. SOUL.md - loaded FIRST (most important)
        const soulPath = path.join(this.workspace, 'SOUL.md');
        if (fs.existsSync(soulPath)) {
            this.soulContext = fs.readFileSync(soulPath, 'utf-8');
            console.log('[brain] Loaded SOUL.md');
        }
        else {
            // Fallback to bundled SOUL.md
            const bundledSoul = path.join(__dirname, '../../soul/SOUL.md');
            if (fs.existsSync(bundledSoul)) {
                this.soulContext = fs.readFileSync(bundledSoul, 'utf-8');
                console.log('[brain] Loaded bundled SOUL.md');
            }
        }
        // 2. AGENTS.md
        const agentsPath = path.join(this.workspace, 'AGENTS.md');
        if (fs.existsSync(agentsPath)) {
            this.agentsContext = fs.readFileSync(agentsPath, 'utf-8');
            console.log('[brain] Loaded AGENTS.md');
        }
        // 3. SKILLS - load all skill descriptions
        await this.loadSkillsContext();
        // 4. MEMORY.md (long-term)
        const memoryPath = path.join(this.workspace, 'MEMORY.md');
        if (fs.existsSync(memoryPath)) {
            this.memoryContext = fs.readFileSync(memoryPath, 'utf-8');
            console.log('[brain] Loaded MEMORY.md');
        }
        // 5. Daily logs
        await this.loadDailyLogs();
    }
    // Load skills context
    async loadSkillsContext() {
        const skillsDir = path.join(this.workspace, 'skills');
        let skillsContent = '# Available Skills\n\n';
        if (fs.existsSync(skillsDir)) {
            const skillDirs = fs.readdirSync(skillsDir);
            for (const skillDir of skillDirs) {
                const skillPath = path.join(skillsDir, skillDir, 'SKILL.md');
                if (fs.existsSync(skillPath)) {
                    const skillDoc = fs.readFileSync(skillPath, 'utf-8');
                    skillsContent += `## ${skillDir}\n${skillDoc}\n\n`;
                }
            }
        }
        this.skillsContext = skillsContent;
    }
    // Load daily logs
    async loadDailyLogs() {
        const memoryDir = path.join(this.workspace, 'memory');
        const today = new Date();
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);
        const todayStr = today.toISOString().split('T')[0];
        const yesterdayStr = yesterday.toISOString().split('T')[0];
        // Load today's log
        const todayPath = path.join(memoryDir, `${todayStr}.md`);
        if (fs.existsSync(todayPath)) {
            this.todayLog = fs.readFileSync(todayPath, 'utf-8');
        }
        // Load yesterday's log
        const yesterdayPath = path.join(memoryDir, `${yesterdayStr}.md`);
        if (fs.existsSync(yesterdayPath)) {
            this.yesterdayLog = fs.readFileSync(yesterdayPath, 'utf-8');
        }
    }
    // Initialize LLM provider based on config
    initializeProvider() {
        const cfg = this.config.get();
        const providerName = cfg.providers.primary;
        let apiKey = this.config.getApiKey(providerName);
        if (!apiKey) {
            console.warn(`[brain] WARNING: No API key for ${providerName}, using mock mode`);
            // Use mock provider for testing
            this.provider = new MockProvider();
            return;
        }
        switch (providerName) {
            case 'anthropic':
                this.provider = new AnthropicProvider(apiKey, cfg.providers.anthropic?.model);
                break;
            case 'openai':
                this.provider = new OpenAIProvider(apiKey, cfg.providers.openai?.model);
                break;
            case 'ollama':
                this.provider = new OllamaProvider(cfg.providers.ollama?.model, cfg.providers.ollama?.endpoint);
                break;
            case 'deepseek':
                this.provider = new DeepSeekProvider(apiKey, cfg.providers.deepseek?.model);
                break;
            default:
                console.warn(`[brain] Unknown provider ${providerName}, using mock mode`);
                this.provider = new MockProvider();
        }
        console.log(`[brain] Using LLM provider: ${providerName}`);
    }
    // Build full context for a prompt
    buildContext(userPrompt) {
        const messages = [];
        // System prompt (order matters!)
        let systemContent = '';
        if (this.soulContext) {
            systemContent += `# IDENTITY\n${this.soulContext}\n\n`;
        }
        if (this.agentsContext) {
            systemContent += `# OPERATING RULES\n${this.agentsContext}\n\n`;
        }
        if (this.skillsContext) {
            systemContent += `# CAPABILITIES\n${this.skillsContext}\n\n`;
        }
        if (this.memoryContext) {
            systemContent += `# LONG-TERM MEMORY\n${this.memoryContext}\n\n`;
        }
        if (this.yesterdayLog) {
            systemContent += `# YESTERDAY'S LOG\n${this.yesterdayLog}\n\n`;
        }
        if (this.todayLog) {
            systemContent += `# TODAY'S LOG\n${this.todayLog}\n\n`;
        }
        messages.push({
            role: 'system',
            content: systemContent,
        });
        // User prompt
        messages.push({
            role: 'user',
            content: userPrompt,
        });
        return messages;
    }
    // Main think method - send prompt to LLM and get response
    async think(prompt) {
        if (!this.provider) {
            await this.initialize();
        }
        const messages = this.buildContext(prompt);
        try {
            const response = await this.provider.chat(messages);
            console.log(`[brain] LLM response received (${response.usage?.output_tokens || '?'} tokens)`);
            return response;
        }
        catch (error) {
            console.error('[brain] LLM error:', error.message);
            return {
                content: `Error: ${error.message}`,
            };
        }
    }
    // Think with conversation history
    async thinkWithHistory(prompt, history) {
        if (!this.provider) {
            await this.initialize();
        }
        const messages = this.buildContext('');
        // Add history (excluding system as we rebuild it)
        const conversationHistory = history.filter(m => m.role !== 'system');
        messages.push(...conversationHistory);
        // Add new prompt
        messages.push({ role: 'user', content: prompt });
        try {
            const response = await this.provider.chat(messages);
            return response;
        }
        catch (error) {
            console.error('[brain] LLM error:', error.message);
            return {
                content: `Error: ${error.message}`,
            };
        }
    }
    // Write to daily log
    async writeToLog(content) {
        const memoryDir = path.join(this.workspace, 'memory');
        if (!fs.existsSync(memoryDir)) {
            fs.mkdirSync(memoryDir, { recursive: true });
        }
        const today = new Date().toISOString().split('T')[0];
        const logPath = path.join(memoryDir, `${today}.md`);
        const timestamp = new Date().toISOString();
        const entry = `\n## ${timestamp}\n${content}\n`;
        fs.appendFileSync(logPath, entry);
        this.todayLog += entry;
    }
    // Update memory
    async updateMemory(content) {
        const memoryPath = path.join(this.workspace, 'MEMORY.md');
        fs.appendFileSync(memoryPath, `\n${content}`);
        this.memoryContext += `\n${content}`;
    }
}
// Mock Provider for testing without API keys
class MockProvider extends LLMProvider {
    name = 'mock';
    async chat(messages) {
        const userMsg = messages.find(m => m.role === 'user')?.content || '';
        return {
            content: `[MOCK RESPONSE] I processed your request: "${userMsg.substring(0, 50)}..."`,
        };
    }
}
export default Brain;
export { LLMProvider, AnthropicProvider, OpenAIProvider, OllamaProvider, DeepSeekProvider };
//# sourceMappingURL=index.js.map