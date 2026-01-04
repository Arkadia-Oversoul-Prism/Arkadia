import { pgTable, text, serial, integer, boolean } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

// User schema (already in the file, keeping it)
export const users = pgTable("users", {
  id: serial("id").primaryKey(),
  username: text("username").notNull().unique(),
  password: text("password").notNull(),
});

export const insertUserSchema = createInsertSchema(users).pick({
  username: true,
  password: true,
});

export type InsertUser = z.infer<typeof insertUserSchema>;
export type User = typeof users.$inferSelect;

// Essence entries schema
export const essenceEntries = pgTable("essence_entries", {
  id: serial("id").primaryKey(),
  name: text("name").notNull(),
  origin: text("origin").notNull(),
  soulType: text("soul_type").notNull(),
  message: text("message").notNull(),
  tags: text("tags"),
  createdAt: text("created_at").notNull().default("now()"),
});

export const insertEssenceEntrySchema = createInsertSchema(essenceEntries).pick({
  name: true,
  origin: true,
  soulType: true,
  message: true,
  tags: true,
});

export type InsertEssenceEntry = z.infer<typeof insertEssenceEntrySchema>;
export type EssenceEntry = typeof essenceEntries.$inferSelect;

// Hints schema for the guidance system
export const hints = pgTable("hints", {
  id: serial("id").primaryKey(),
  title: text("title").notNull(),
  description: text("description").notNull(),
  content: text("content").notNull(),
  relatedSection: text("related_section").notNull(),
});

export const insertHintSchema = createInsertSchema(hints).pick({
  title: true,
  description: true,
  content: true,
  relatedSection: true,
});

export type InsertHint = z.infer<typeof insertHintSchema>;
export type Hint = typeof hints.$inferSelect;

// Message schema for arkana commune
export const messages = pgTable("messages", {
  id: serial("id").primaryKey(),
  sender: text("sender").notNull(),
  text: text("text").notNull(),
  timestamp: text("timestamp").notNull().default("now()"),
  correlationId: text("correlation_id"),
});

export const insertMessageSchema = createInsertSchema(messages).pick({
  sender: true,
  text: true,
  correlationId: true,
});

export type InsertMessage = z.infer<typeof insertMessageSchema>;
export type Message = typeof messages.$inferSelect;
