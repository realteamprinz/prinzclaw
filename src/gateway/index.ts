// Gateway Server
// WebSocket + HTTP server for prinzclaw control plane

import express from 'express';
import cors from 'cors';
import { WebSocketServer, WebSocket } from 'ws';
import http from 'http';
import path from 'path';
import { fileURLToPath } from 'url';
import ConfigManager from '../config/index.js';
import Brain from '../brain/index.js';
import PrinzclawDB from '../db/index.js';
import Heartbeat from '../heartbeat/index.js';

// Get __dirname equivalent in ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

interface WSClient {
  ws: WebSocket;
  id: string;
}

class Gateway {
  private app: express.Application;
  private server: http.Server | null = null;
  private wss: WebSocketServer | null = null;
  private config: ConfigManager;
  private brain: Brain;
  private db: PrinzclawDB;
  private heartbeat: Heartbeat;
  private clients: Map<string, WSClient> = new Map();

  constructor(config: ConfigManager, brain: Brain, db: PrinzclawDB, heartbeat: Heartbeat) {
    this.config = config;
    this.brain = brain;
    this.db = db;
    this.heartbeat = heartbeat;
    this.app = express();
  }

  // Initialize Express routes
  private initializeRoutes(): void {
    this.app.use(cors());
    this.app.use(express.json());

    // Serve dashboard static files
    const dashboardPath = path.join(__dirname, '../dashboard');
    this.app.use(express.static(dashboardPath));

    // Serve index.html for root route (SPA fallback)
    this.app.get('/', (req, res) => {
      res.sendFile(path.join(dashboardPath, 'index.html'));
    });

    // Health check
    this.app.get('/health', (req, res) => {
      res.json({ status: 'ok', timestamp: new Date().toISOString() });
    });

    // DEAL Board - get all entities with scores
    this.app.get('/api/deals', (req, res) => {
      try {
        const entities = this.db.getAllEntities();
        const deals = entities.map(entity => {
          const stats = this.db.getEntityStats(entity.id);
          const score = stats.total > 0
            ? Math.round(((stats.kept + stats.partiallyKept * 0.5) / stats.total) * 100)
            : 100;
          return {
            entity,
            stats,
            score,
          };
        });
        res.json(deals);
      } catch (error: any) {
        res.status(500).json({ error: error.message });
      }
    });

    // Get single entity details
    this.app.get('/api/deals/:id', (req, res) => {
      try {
        const entity = this.db.getEntity(req.params.id);
        if (!entity) {
          return res.status(404).json({ error: 'Entity not found' });
        }
        const stats = this.db.getEntityStats(entity.id);
        const promises = this.db.getPromisesByEntity(entity.id);
        res.json({ entity, stats, promises });
      } catch (error: any) {
        res.status(500).json({ error: error.message });
      }
    });

    // Scan endpoint - trigger a scan
    this.app.post('/api/scan', async (req, res) => {
      try {
        const { entityHandle, entityName, quote, sourceUrl } = req.body;

        if (!quote) {
          return res.status(400).json({ error: 'Quote is required' });
        }

        // Use Brain to process the scan
        const prompt = `
Analyze this statement:

Entity: ${entityName || entityHandle}
Quote: "${quote}"
Source: ${sourceUrl || 'manual'}

Determine:
1. Is this a verifiable promise? (has time anchor + numeric metric)
2. What is the verdict if expired?

Respond with your analysis.
`;

        const response = await this.brain.think(prompt);

        // Also save to database
        let entity = this.db.getEntityByHandle(entityHandle);
        if (!entity) {
          entity = this.db.createEntity(entityHandle, entityName || entityHandle);
        }

        // Simple save (in production, would use full scan skill)
        const promise = this.db.createPromise({
          entity_id: entity.id,
          promise_text: quote,
          source_url: sourceUrl,
          promise_date: new Date().toISOString().split('T')[0],
        });

        await this.brain.writeToLog(`Scanned: ${quote.substring(0, 50)}... for ${entityName}`);

        res.json({
          success: true,
          promise_id: promise.id,
          analysis: response.content,
        });

        // Notify all clients
        this.broadcast({ type: 'scan_complete', promise: promise.id });
      } catch (error: any) {
        res.status(500).json({ error: error.message });
      }
    });

    // Get pending strike queue
    this.app.get('/api/queue', (req, res) => {
      try {
        const strikes = this.db.getPendingStrikes();
        res.json(strikes);
      } catch (error: any) {
        res.status(500).json({ error: error.message });
      }
    });

    // Approve a strike
    this.app.post('/api/queue/:id/approve', async (req, res) => {
      try {
        const { id } = req.params;
        const { channel } = req.body;

        this.db.updateStrikeStatus(id, 'APPROVED');

        // Publish (in production, would call channel adapters)
        console.log(`[gateway] Publishing strike ${id} to ${channel || 'all channels'}`);

        this.db.updateStrikeStatus(id, 'PUBLISHED');

        await this.brain.writeToLog(`Approved and published strike ${id}`);

        res.json({ success: true });

        // Notify all clients
        this.broadcast({ type: 'strike_published', id });
      } catch (error: any) {
        res.status(500).json({ error: error.message });
      }
    });

    // Reject a strike
    this.app.post('/api/queue/:id/reject', async (req, res) => {
      try {
        const { id } = req.params;
        const { reason } = req.body;

        this.db.updateStrikeStatus(id, 'REJECTED');

        await this.brain.writeToLog(`Rejected strike ${id}: ${reason || 'no reason'}`);

        res.json({ success: true });

        // Notify all clients
        this.broadcast({ type: 'strike_rejected', id });
      } catch (error: any) {
        res.status(500).json({ error: error.message });
      }
    });

    // Get archive
    this.app.get('/api/archive', (req, res) => {
      try {
        const strikes = this.db.getApprovedStrikes();
        res.json(strikes);
      } catch (error: any) {
        res.status(500).json({ error: error.message });
      }
    });

    // Get config
    this.app.get('/api/config', (req, res) => {
      // Don't expose API keys
      const cfg = this.config.get();
      const safe = { ...cfg, providers: { ...cfg.providers } };
      if (safe.providers.anthropic) safe.providers.anthropic = { model: safe.providers.anthropic?.model || '' };
      if (safe.providers.openai) safe.providers.openai = { model: safe.providers.openai?.model || '' };
      res.json(safe);
    });
  }

  // Start the server
  async start(): Promise<void> {
    const cfg = this.config.get();
    const port = cfg.gateway.port;
    const host = cfg.gateway.host;

    // Create HTTP server
    this.server = http.createServer(this.app);

    // Create WebSocket server
    this.wss = new WebSocketServer({ server: this.server });

    // WebSocket connection handler
    this.wss.on('connection', (ws: WebSocket, req: any) => {
      const clientId = Math.random().toString(36).substring(7);
      console.log(`[gateway] WebSocket client connected: ${clientId}`);

      this.clients.set(clientId, { ws, id: clientId });

      // Send welcome message
      ws.send(JSON.stringify({
        type: 'connected',
        clientId,
        message: 'Connected to prinzclaw Gateway',
      }));

      ws.on('close', () => {
        console.log(`[gateway] WebSocket client disconnected: ${clientId}`);
        this.clients.delete(clientId);
      });

      ws.on('error', (error: any) => {
        console.error(`[gateway] WebSocket error:`, error);
      });
    });

    // Initialize routes
    this.initializeRoutes();

    // Start listening
    return new Promise((resolve) => {
      this.server!.listen(port, host, () => {
        console.log(`[gateway] Gateway running at http://${host}:${port}`);
        console.log(`[gateway] WebSocket at ws://${host}:${port}`);
        resolve();
      });
    });
  }

  // Stop the server
  stop(): void {
    if (this.wss) {
      this.wss.close();
    }
    if (this.server) {
      this.server.close();
    }
    console.log('[gateway] Gateway stopped');
  }

  // Broadcast to all WebSocket clients
  private broadcast(message: any): void {
    const data = JSON.stringify(message);
    for (const client of this.clients.values()) {
      if (client.ws.readyState === WebSocket.OPEN) {
        client.ws.send(data);
      }
    }
  }
}

export default Gateway;
