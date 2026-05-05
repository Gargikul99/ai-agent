import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { Send, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { api } from "@/lib/api";
import type { ChatMessage } from "@/lib/types";
import { cn } from "@/lib/utils";

export function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "Hi — I'm your supply chain assistant. Ask me about inventory, shipments, suppliers, or any custom query against your data.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;
    const next: ChatMessage[] = [...messages, { role: "user", content: text }];
    setMessages(next);
    setInput("");
    setLoading(true);
    try {
      const reply = await api.chat(next);
      setMessages([...next, { role: "assistant", content: reply }]);
    } catch (e) {
      setMessages([
        ...next,
        { role: "assistant", content: `⚠️ Failed to reach AI agent: ${(e as Error).message}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="flex flex-col h-full bg-card text-card-foreground border-border/40 p-0 overflow-hidden">
      <div className="px-4 py-3 border-b border-border/40 flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-primary" />
        <h2 className="font-semibold">AI Assistant</h2>
      </div>
      <div ref={scrollRef} className="flex-1 overflow-auto p-4 space-y-3">
        {messages.map((m, i) => (
          <div
            key={i}
            className={cn(
              "rounded-lg px-3 py-2 text-sm max-w-[90%]",
              m.role === "user"
                ? "ml-auto bg-primary text-primary-foreground"
                : "bg-background/40",
            )}
          >
            <div className="prose prose-sm prose-invert max-w-none prose-p:my-1 prose-ul:my-1">
              <ReactMarkdown>{m.content}</ReactMarkdown>
            </div>
          </div>
        ))}
        {loading && (
          <div className="bg-background/40 rounded-lg px-3 py-2 text-sm w-fit">
            <span className="inline-flex gap-1">
              <span className="h-1.5 w-1.5 bg-muted-foreground rounded-full animate-bounce" />
              <span className="h-1.5 w-1.5 bg-muted-foreground rounded-full animate-bounce [animation-delay:120ms]" />
              <span className="h-1.5 w-1.5 bg-muted-foreground rounded-full animate-bounce [animation-delay:240ms]" />
            </span>
          </div>
        )}
      </div>
      <form
        onSubmit={(e) => { e.preventDefault(); send(); }}
        className="border-t border-border/40 p-3 flex gap-2"
      >
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about your supply chain…"
          className="bg-background/40 border-border/40"
        />
        <Button type="submit" size="icon" disabled={loading || !input.trim()}>
          <Send className="h-4 w-4" />
        </Button>
      </form>
    </Card>
  );
}
