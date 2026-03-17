import ConfigManager from '../config/index.js';
export interface LLMMessage {
    role: 'system' | 'user' | 'assistant';
    content: string;
}
export interface LLMResponse {
    content: string;
    usage?: {
        input_tokens: number;
        output_tokens: number;
    };
}
declare abstract class LLMProvider {
    abstract name: string;
    abstract chat(messages: LLMMessage[]): Promise<LLMResponse>;
}
declare class AnthropicProvider extends LLMProvider {
    name: string;
    private apiKey;
    private model;
    constructor(apiKey: string, model?: string);
    chat(messages: LLMMessage[]): Promise<LLMResponse>;
}
declare class OpenAIProvider extends LLMProvider {
    name: string;
    private apiKey;
    private model;
    constructor(apiKey: string, model?: string);
    chat(messages: LLMMessage[]): Promise<LLMResponse>;
}
declare class OllamaProvider extends LLMProvider {
    name: string;
    private endpoint;
    private model;
    constructor(model?: string, endpoint?: string);
    chat(messages: LLMMessage[]): Promise<LLMResponse>;
}
declare class DeepSeekProvider extends LLMProvider {
    name: string;
    private apiKey;
    private model;
    constructor(apiKey: string, model?: string);
    chat(messages: LLMMessage[]): Promise<LLMResponse>;
}
declare class Brain {
    private provider;
    private config;
    private workspace;
    private soulContext;
    private agentsContext;
    private skillsContext;
    private memoryContext;
    private todayLog;
    private yesterdayLog;
    constructor(config: ConfigManager);
    initialize(): Promise<void>;
    private loadContexts;
    private loadSkillsContext;
    private loadDailyLogs;
    private initializeProvider;
    private buildContext;
    think(prompt: string): Promise<LLMResponse>;
    thinkWithHistory(prompt: string, history: LLMMessage[]): Promise<LLMResponse>;
    writeToLog(content: string): Promise<void>;
    updateMemory(content: string): Promise<void>;
}
export default Brain;
export { LLMProvider, AnthropicProvider, OpenAIProvider, OllamaProvider, DeepSeekProvider };
