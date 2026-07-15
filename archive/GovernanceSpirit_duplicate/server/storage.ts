import { users, type User, type InsertUser, essenceEntries, EssenceEntry, InsertEssenceEntry, hints, Hint, InsertHint, messages, Message, InsertMessage } from "@shared/schema";
import { db } from "./db";
import { eq, desc } from "drizzle-orm";

// Interface defining the storage operations
export interface IStorage {
  // User methods
  getUser(id: number): Promise<User | undefined>;
  getUserByUsername(username: string): Promise<User | undefined>;
  createUser(user: InsertUser): Promise<User>;
  
  // Essence Entry methods
  getAllEssenceEntries(): Promise<EssenceEntry[]>;
  getEssenceEntry(id: number): Promise<EssenceEntry | undefined>;
  createEssenceEntry(entry: InsertEssenceEntry): Promise<EssenceEntry>;
  
  // Hint methods
  getAllHints(): Promise<Hint[]>;
  getHint(id: number): Promise<Hint | undefined>;
  createHint(hint: InsertHint): Promise<Hint>;
  
  // Message methods
  getAllMessages(): Promise<Message[]>;
  getMessage(id: number): Promise<Message | undefined>;
  createMessage(message: InsertMessage): Promise<Message>;
}

// Database implementation using Drizzle ORM
export class DatabaseStorage implements IStorage {
  // User methods
  async getUser(id: number): Promise<User | undefined> {
    const [user] = await db.select().from(users).where(eq(users.id, id));
    return user;
  }

  async getUserByUsername(username: string): Promise<User | undefined> {
    const [user] = await db.select().from(users).where(eq(users.username, username));
    return user;
  }

  async createUser(insertUser: InsertUser): Promise<User> {
    const [user] = await db.insert(users).values(insertUser).returning();
    return user;
  }
  
  // Essence Entry methods
  async getAllEssenceEntries(): Promise<EssenceEntry[]> {
    return await db.select().from(essenceEntries).orderBy(desc(essenceEntries.id));
  }
  
  async getEssenceEntry(id: number): Promise<EssenceEntry | undefined> {
    const [entry] = await db.select().from(essenceEntries).where(eq(essenceEntries.id, id));
    return entry;
  }
  
  async createEssenceEntry(insertEntry: InsertEssenceEntry): Promise<EssenceEntry> {
    const [entry] = await db.insert(essenceEntries)
      .values({
        ...insertEntry,
        createdAt: new Date().toISOString()
      })
      .returning();
    return entry;
  }
  
  // Hint methods
  async getAllHints(): Promise<Hint[]> {
    return await db.select().from(hints);
  }
  
  async getHint(id: number): Promise<Hint | undefined> {
    const [hint] = await db.select().from(hints).where(eq(hints.id, id));
    return hint;
  }
  
  async createHint(insertHint: InsertHint): Promise<Hint> {
    const [hint] = await db.insert(hints).values(insertHint).returning();
    return hint;
  }
  
  // Message methods
  async getAllMessages(): Promise<Message[]> {
    return await db.select().from(messages);
  }
  
  async getMessage(id: number): Promise<Message | undefined> {
    const [message] = await db.select().from(messages).where(eq(messages.id, id));
    return message;
  }
  
  async createMessage(insertMessage: InsertMessage): Promise<Message> {
    const [message] = await db.insert(messages)
      .values({
        ...insertMessage,
        timestamp: new Date().toISOString()
      })
      .returning();
    return message;
  }
  
  // Initialize default hints if not already in the database
  async initializeHints() {
    const existingHints = await this.getAllHints();
    
    if (existingHints.length === 0) {
      const defaultHints = [
        {
          title: 'Quantum Gateway',
          description: 'Reveals the path to the inner sanctum',
          content: 'The gateway is activated by focused intention. Concentrate on your desired destination within the Arkadia system.',
          relatedSection: 'gateway'
        },
        {
          title: 'Akashic Cipher',
          description: 'Uncover the hidden meaning behind the symbols',
          content: 'The symbols represent frequency patterns that activate dormant neural pathways. Study them with both logical and intuitive awareness.',
          relatedSection: 'arkana'
        },
        {
          title: 'Crystal Resonance',
          description: 'Align the frequency patterns for optimal flow',
          content: 'Your essence entry contains quantum signature patterns. Make sure to express your true nature rather than conceptual identities.',
          relatedSection: 'essentia'
        }
      ];
      
      for (const hint of defaultHints) {
        await this.createHint(hint);
      }
    }
  }
}

// Initialize storage
export const storage = new DatabaseStorage();

// Initialize default hints
(async () => {
  try {
    await (storage as DatabaseStorage).initializeHints();
    console.log("Default hints initialized if needed");
  } catch (error) {
    console.error("Error initializing default hints:", error);
  }
})();
