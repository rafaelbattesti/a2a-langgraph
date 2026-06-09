"use client";

import { useChat } from "@ai-sdk/react";
import { Workflow } from "lucide-react";
import {
  Conversation,
  ConversationContent,
  ConversationEmptyState,
  ConversationScrollButton
} from "@/components/ai-elements/conversation";
import {
  Message,
  MessageContent,
  MessageResponse
} from "@/components/ai-elements/message";
import {
  PromptInput,
  PromptInputBody,
  PromptInputFooter,
  type PromptInputMessage,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputTools
} from "@/components/ai-elements/prompt-input";
import { Suggestion, Suggestions } from "@/components/ai-elements/suggestion";
import { Shimmer } from "@/components/ai-elements/shimmer";
import { cn } from "@/lib/utils";

const STARTERS = [
  "What can you orchestrate?",
  "Which agents are available?",
  "Route a research task to the right agent",
  "Summarize the latest run"
];

const STATUS_META = {
  ready: { label: "Ready", dot: "bg-primary" },
  submitted: { label: "Thinking", dot: "bg-amber-400 animate-pulse" },
  streaming: { label: "Streaming", dot: "bg-primary animate-pulse" },
  error: { label: "Error", dot: "bg-destructive" }
} as const;

const ROLE_LABEL: Record<string, string> = {
  user: "You",
  assistant: "Orchestrator",
  system: "System"
};

export default function Chat() {
  const { messages, sendMessage, status, stop } = useChat();
  const meta = STATUS_META[status] ?? STATUS_META.ready;
  const isThinking =
    status === "submitted" && messages.at(-1)?.role === "user";

  function handleSubmit(message: PromptInputMessage) {
    const text = message.text.trim();
    if (!text) {
      return;
    }
    sendMessage({ text });
  }

  return (
    <main className="bg-console relative flex h-svh flex-col overflow-hidden bg-background">
      <div className="mx-auto flex h-full w-full max-w-3xl flex-col px-4 sm:px-6">
        <header className="flex items-center justify-between gap-4 border-b border-border/60 py-5">
          <div className="flex items-center gap-3.5">
            <span className="glow-primary flex size-11 items-center justify-center rounded-xl bg-gradient-to-br from-primary/25 to-primary/5 text-primary">
              <Workflow size={21} strokeWidth={2.1} />
            </span>
            <div className="min-w-0">
              <h1 className="font-display text-[1.6rem] font-semibold leading-none tracking-tight text-foreground">
                A2A Orchestrator
              </h1>
              <p className="mt-1.5 font-mono text-[0.7rem] uppercase tracking-[0.18em] text-muted-foreground">
                AI SDK · agentgateway
              </p>
            </div>
          </div>

          <span className="inline-flex shrink-0 items-center gap-2 rounded-full border border-border/70 bg-card/60 px-3 py-1.5 font-mono text-[0.7rem] uppercase tracking-[0.14em] text-muted-foreground backdrop-blur">
            <span className={cn("size-1.5 rounded-full", meta.dot)} />
            {meta.label}
          </span>
        </header>

        <Conversation className="scrollbar-subtle relative flex-1">
          <ConversationContent className="mx-auto w-full max-w-2xl gap-7 px-0 py-7">
            {messages.length === 0 ? (
              <ConversationEmptyState className="h-full justify-center gap-6">
                <span className="glow-primary flex size-16 items-center justify-center rounded-2xl bg-gradient-to-br from-primary/25 to-primary/5 text-primary">
                  <Workflow size={28} strokeWidth={1.9} />
                </span>
                <div className="space-y-2">
                  <h2 className="font-display text-2xl font-semibold tracking-tight text-foreground">
                    How can I orchestrate for you?
                  </h2>
                  <p className="mx-auto max-w-md text-sm text-muted-foreground">
                    Coordinate your agents through a single conversation. Ask
                    anything, or start with one of these.
                  </p>
                </div>
                <Suggestions className="mt-1 justify-center">
                  {STARTERS.map((starter) => (
                    <Suggestion
                      className="border-border/70 bg-card/50 text-foreground/90 backdrop-blur transition-colors hover:border-primary/40 hover:bg-accent hover:text-foreground"
                      key={starter}
                      onClick={(text) => sendMessage({ text })}
                      suggestion={starter}
                    />
                  ))}
                </Suggestions>
              </ConversationEmptyState>
            ) : (
              <>
                {messages.map((message) => (
                  <div
                    className={cn(
                      "flex flex-col gap-1.5",
                      message.role === "user" ? "items-end" : "items-start"
                    )}
                    key={message.id}
                  >
                    <span className="px-1 font-mono text-[0.62rem] uppercase tracking-[0.2em] text-muted-foreground/80">
                      {ROLE_LABEL[message.role] ?? message.role}
                    </span>
                    <Message className="max-w-full" from={message.role}>
                      <MessageContent>
                        {message.parts.map((part, index) =>
                          part.type === "text" ? (
                            <MessageResponse key={`${message.id}-${index}`}>
                              {part.text}
                            </MessageResponse>
                          ) : null
                        )}
                      </MessageContent>
                    </Message>
                  </div>
                ))}

                {isThinking ? (
                  <div className="flex flex-col items-start gap-1.5">
                    <span className="px-1 font-mono text-[0.62rem] uppercase tracking-[0.2em] text-muted-foreground/80">
                      Orchestrator
                    </span>
                    <Shimmer className="px-1 text-sm">Thinking…</Shimmer>
                  </div>
                ) : null}
              </>
            )}
          </ConversationContent>
          <ConversationScrollButton className="border-border/70 bg-card/80 backdrop-blur" />
        </Conversation>

        <div className="pb-6 pt-1">
          <PromptInput
            className="rounded-2xl border-border/70 bg-card/60 shadow-xl shadow-black/20 backdrop-blur transition-shadow focus-within:border-primary/40 focus-within:glow-primary"
            onSubmit={handleSubmit}
          >
            <PromptInputBody>
              <PromptInputTextarea
                className="placeholder:text-muted-foreground/70"
                placeholder="Message the orchestrator…"
              />
            </PromptInputBody>
            <PromptInputFooter className="justify-between border-transparent">
              <PromptInputTools>
                <span className="px-1 font-mono text-[0.66rem] uppercase tracking-[0.12em] text-muted-foreground/70">
                  ↵ send · ⇧↵ newline
                </span>
              </PromptInputTools>
              <PromptInputSubmit onStop={stop} status={status} />
            </PromptInputFooter>
          </PromptInput>
        </div>
      </div>
    </main>
  );
}
