// Database module for prinzclaw
import Database from 'better-sqlite3';
import { v4 as uuidv4 } from 'uuid';
import * as path from 'path';
import * as fs from 'fs';

export interface Entity {
  id: string;
  handle: string;
  display_name: string;
  created_at: string;
}

export interface Promise {
  id: string;
  entity_id: string;
  promise_text: string;
  source_url: string | null;
  promise_date: string;
  expiry_date: string | null;
  verifiable_metric: string | null;
  data_source_for_verification: string | null;
  status: 'PENDING' | 'KEPT' | 'BROKE' | 'PARTIALLY_KEPT' | 'INSUFFICIENT_EVIDENCE';
  created_at: string;
  soul_md_hash: string | null;
}

export interface Strike {
  id: string;
  target: string;
  verdict: string;
  summary: string;
  evidence_chain: string;
  counter_text: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'PUBLISHED';
  created_at: string;
  published_at: string | null;
  forged_by: string;
  soul_md_hash: string | null;
  signature: string;
}

class PrinzclawDB {
  private db: Database.Database;

  constructor(dbPath: string = './prinzclaw.db') {
    const dir = path.dirname(dbPath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    this.db = new Database(dbPath);
    this.initialize();
  }

  private initialize() {
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS entities (
        id TEXT PRIMARY KEY,
        handle TEXT UNIQUE,
        display_name TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now'))
      )
    `);

    this.db.exec(`
      CREATE TABLE IF NOT EXISTS promises (
        id TEXT PRIMARY KEY,
        entity_id TEXT NOT NULL,
        promise_text TEXT NOT NULL,
        source_url TEXT,
        promise_date TEXT NOT NULL,
        expiry_date TEXT,
        verifiable_metric TEXT,
        data_source_for_verification TEXT,
        status TEXT DEFAULT 'PENDING',
        created_at TEXT DEFAULT (datetime('now')),
        soul_md_hash TEXT,
        FOREIGN KEY (entity_id) REFERENCES entities(id)
      )
    `);

    this.db.exec(`
      CREATE TABLE IF NOT EXISTS strikes (
        id TEXT PRIMARY KEY,
        target TEXT NOT NULL,
        verdict TEXT NOT NULL,
        summary TEXT NOT NULL,
        evidence_chain TEXT NOT NULL,
        counter_text TEXT NOT NULL,
        status TEXT DEFAULT 'PENDING',
        created_at TEXT DEFAULT (datetime('now')),
        published_at TEXT,
        forged_by TEXT,
        soul_md_hash TEXT,
        signature TEXT
      )
    `);

    this.db.exec(`
      CREATE INDEX IF NOT EXISTS idx_promises_entity ON promises(entity_id);
      CREATE INDEX IF NOT EXISTS idx_promises_status ON promises(status);
      CREATE INDEX IF NOT EXISTS idx_strikes_status ON strikes(status);
    `);
  }

  // Entity operations
  createEntity(handle: string, displayName: string): Entity {
    const id = uuidv4();
    const stmt = this.db.prepare('INSERT INTO entities (id, handle, display_name) VALUES (?, ?, ?)');
    stmt.run(id, handle, displayName);
    return this.getEntity(id)!;
  }

  getEntity(id: string): Entity | undefined {
    const stmt = this.db.prepare('SELECT * FROM entities WHERE id = ?');
    return stmt.get(id) as Entity | undefined;
  }

  getEntityByHandle(handle: string): Entity | undefined {
    const stmt = this.db.prepare('SELECT * FROM entities WHERE handle = ?');
    return stmt.get(handle) as Entity | undefined;
  }

  getAllEntities(): Entity[] {
    const stmt = this.db.prepare('SELECT * FROM entities ORDER BY display_name');
    return stmt.all() as Entity[];
  }

  // Promise operations
  createPromise(data: {
    entity_id: string;
    promise_text: string;
    source_url?: string;
    promise_date: string;
    expiry_date?: string;
    verifiable_metric?: string;
    data_source_for_verification?: string;
    soul_md_hash?: string;
  }): Promise {
    const id = uuidv4();
    const stmt = this.db.prepare(`
      INSERT INTO promises (id, entity_id, promise_text, source_url, promise_date, expiry_date, verifiable_metric, data_source_for_verification, soul_md_hash)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);
    stmt.run(id, data.entity_id, data.promise_text, data.source_url || null, data.promise_date, data.expiry_date || null, data.verifiable_metric || null, data.data_source_for_verification || null, data.soul_md_hash || null);
    return this.getPromise(id)!;
  }

  getPromise(id: string): Promise | undefined {
    const stmt = this.db.prepare('SELECT * FROM promises WHERE id = ?');
    return stmt.get(id) as Promise | undefined;
  }

  getPromisesByEntity(entityId: string): Promise[] {
    const stmt = this.db.prepare('SELECT * FROM promises WHERE entity_id = ? ORDER BY promise_date DESC');
    return stmt.all(entityId) as Promise[];
  }

  getPendingPromises(entityId?: string): Promise[] {
    let query = "SELECT * FROM promises WHERE status = 'PENDING'";
    if (entityId) {
      query += ' AND entity_id = ?';
      const stmt = this.db.prepare(query + ' ORDER BY promise_date ASC');
      return stmt.all(entityId) as Promise[];
    }
    const stmt = this.db.prepare(query + ' ORDER BY promise_date ASC');
    return stmt.all() as Promise[];
  }

  getPromisesInWindow(entityId: string, startDate: string, endDate: string): Promise[] {
    const stmt = this.db.prepare('SELECT * FROM promises WHERE entity_id = ? AND promise_date >= ? AND promise_date <= ? ORDER BY promise_date DESC');
    return stmt.all(entityId, startDate, endDate) as Promise[];
  }

  updatePromiseStatus(id: string, status: Promise['status']): void {
    const stmt = this.db.prepare('UPDATE promises SET status = ? WHERE id = ?');
    stmt.run(status, id);
  }

  // Strike operations
  createStrike(data: {
    target: string;
    verdict: string;
    summary: string;
    evidence_chain: any[];
    counter_text: string;
    forged_by?: string;
    soul_md_hash?: string;
  }): Strike {
    const id = uuidv4();
    const signature = 'FORGED WITH PRINZCLAW';
    const evidenceChainJson = JSON.stringify(data.evidence_chain);

    const stmt = this.db.prepare(`
      INSERT INTO strikes (id, target, verdict, summary, evidence_chain, counter_text, forged_by, soul_md_hash, signature)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);
    stmt.run(id, data.target, data.verdict, data.summary, evidenceChainJson, data.counter_text, data.forged_by || 'prinzclaw@1.0.0', data.soul_md_hash || null, signature);
    return this.getStrike(id)!;
  }

  getStrike(id: string): Strike | undefined {
    const stmt = this.db.prepare('SELECT * FROM strikes WHERE id = ?');
    return stmt.get(id) as Strike | undefined;
  }

  getPendingStrikes(): Strike[] {
    const stmt = this.db.prepare("SELECT * FROM strikes WHERE status = 'PENDING' ORDER BY created_at DESC");
    return stmt.all() as Strike[];
  }

  getApprovedStrikes(): Strike[] {
    const stmt = this.db.prepare("SELECT * FROM strikes WHERE status = 'APPROVED' OR status = 'PUBLISHED' ORDER BY published_at DESC");
    return stmt.all() as Strike[];
  }

  getAllStrikes(): Strike[] {
    const stmt = this.db.prepare('SELECT * FROM strikes ORDER BY created_at DESC');
    return stmt.all() as Strike[];
  }

  updateStrikeStatus(id: string, status: Strike['status']): void {
    const publishedAt = status === 'PUBLISHED' ? new Date().toISOString() : null;
    const stmt = this.db.prepare('UPDATE strikes SET status = ?, published_at = ? WHERE id = ?');
    stmt.run(status, publishedAt, id);
  }

  // Statistics
  getEntityStats(entityId: string): { total: number; pending: number; kept: number; broke: number; partiallyKept: number } {
    const promises = this.getPromisesByEntity(entityId);
    return {
      total: promises.length,
      pending: promises.filter(p => p.status === 'PENDING').length,
      kept: promises.filter(p => p.status === 'KEPT').length,
      broke: promises.filter(p => p.status === 'BROKE').length,
      partiallyKept: promises.filter(p => p.status === 'PARTIALLY_KEPT').length,
    };
  }

  close() {
    this.db.close();
  }
}

export default PrinzclawDB;
