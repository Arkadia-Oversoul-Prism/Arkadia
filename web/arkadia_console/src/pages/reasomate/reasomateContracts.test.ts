import { describe, expect, it } from "vitest";
import {
  formatTimestamp,
  isDirectMessage,
  isInbox,
  isInboxEntry,
  isSentMessage,
  isThread,
  messageDirection,
  peerLabel,
  recipientField,
  type DirectMessage,
} from "./reasomateContracts";

const MESSAGE: DirectMessage = {
  id: "m-1",
  sender_uid: "peer-uid",
  recipient_uid: "me-uid",
  content: "hello",
  timestamp: 1_700_000_000_000,
};

describe("ReasoMate contract guards", () => {
  it("accepts the shape the thread handler returns", () => {
    expect(isThread({ peer_uid: "peer-uid", messages: [MESSAGE] })).toBe(true);
    expect(isThread({ peer_uid: "peer-uid", messages: [], peer_handle: "peer" })).toBe(true);
  });

  it("accepts the shape the inbox handler returns", () => {
    const payload = {
      conversations: [{ peer_uid: "peer-uid", last_message: MESSAGE, count: 1 }],
    };
    expect(isInbox(payload)).toBe(true);
    expect(isInboxEntry(payload.conversations[0])).toBe(true);
  });

  it("rejects a payload that would render as an empty conversation", () => {
    // A handler failure envelope must not be read as "no messages".
    expect(isInbox({ detail: "Authentication required" })).toBe(false);
    expect(isThread({ status: "error", detail: "vault unavailable" })).toBe(false);
    expect(isThread({ peer_uid: "peer-uid", messages: [{ id: "x" }] })).toBe(false);
    expect(isInbox({ conversations: [{ peer_uid: "peer-uid", count: 1 }] })).toBe(false);
  });

  it("rejects a non-record and an array at the top level", () => {
    expect(isInbox([])).toBe(false);
    expect(isThread(null)).toBe(false);
    expect(isDirectMessage("message")).toBe(false);
    expect(isSentMessage({ message: MESSAGE })).toBe(true);
    expect(isSentMessage({})).toBe(false);
  });
});

describe("ReasoMate thread semantics", () => {
  it("attributes a message by its sender, not by arrival order", () => {
    expect(messageDirection(MESSAGE, "peer-uid")).toBe("in");
    expect(messageDirection(MESSAGE, "someone-else")).toBe("out");
  });

  it("prefers a resolved handle and falls back to the uid", () => {
    expect(peerLabel({ peer_uid: "uid-1", peer_handle: "aurora" })).toBe("@aurora");
    expect(peerLabel({ peer_uid: "uid-1" })).toBe("uid-1");
  });

  it("addresses a handle only when the recipient is written as one", () => {
    expect(recipientField("@aurora")).toEqual({ recipient_handle: "aurora" });
    expect(recipientField("  uid-1  ")).toEqual({ recipient_uid: "uid-1" });
    expect(recipientField("   ")).toEqual({});
  });

  it("formats a millisecond instant and refuses a non-date", () => {
    expect(formatTimestamp(1_700_000_000_000)).toBe("2023-11-14 22:13:20Z");
    expect(formatTimestamp(Number.NaN)).toBe("unknown");
  });
});
