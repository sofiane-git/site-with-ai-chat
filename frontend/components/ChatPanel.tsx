"use client";

import { useEffect, useState } from "react";
import { sendChat, LLMProvider, getProvidersHealth, ProvidersHealth } from "@/lib/api";

type Message = { role: "user" | "assistant"; content: string };

const STORAGE_KEY = "llm_provider";

function getInitialProvider(): LLMProvider {
  if (typeof window === "undefined") return "ollama";
  const stored = localStorage.getItem(STORAGE_KEY);
  return stored === "ollama" || stored === "azure" ? stored : "ollama";
}

function statusDotClass(health: ProvidersHealth | null, p: LLMProvider): string {
  if (health === null) return "bg-gray-300";
  return health[p] ? "bg-green-400" : "bg-red-400";
}

export default function ChatPanel({ onMutation }: { onMutation?: () => void }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [provider, setProvider] = useState<LLMProvider>(getInitialProvider);
  const [health, setHealth] = useState<ProvidersHealth | null>(null);

  useEffect(() => {
    getProvidersHealth()
      .then(setHealth)
      .catch(() => setHealth({ ollama: false, azure: false }));
  }, []);

  function handleProviderChange(p: LLMProvider) {
    setProvider(p);
    localStorage.setItem(STORAGE_KEY, p);
  }

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || loading) return;
    const userMsg: Message = { role: "user", content: input };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setLoading(true);
    try {
      const { reply } = await sendChat(userMsg.content, provider);
      setMessages((m) => [...m, { role: "assistant", content: reply }]);
      onMutation?.();
    } catch (e) {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: `Erreur : ${(e as Error).message}` },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="border rounded p-3 flex flex-col h-full">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-xl font-semibold">Chat IA</h2>
        <div className="flex gap-1">
          {(["ollama", "azure"] as LLMProvider[]).map((p) => (
            <button
              key={p}
              onClick={() => handleProviderChange(p)}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors flex items-center gap-1.5 ${
                provider === p
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              <span className={`w-2 h-2 rounded-full ${statusDotClass(health, p)}`} />
              {p === "ollama" ? "Ollama" : "Azure"}
            </button>
          ))}
        </div>
      </div>
      <div className="flex-1 overflow-y-auto space-y-2 min-h-[300px]">
        {messages.length === 0 && (
          <p className="text-gray-500 text-sm">
            Demande-moi par exemple : « Quelles recettes j'ai ? » ou « Ajoute une tarte aux fraises ».
          </p>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            className={`p-2 rounded ${m.role === "user" ? "bg-blue-50 ml-8" : "bg-gray-50 mr-8"}`}
          >
            <div className="text-xs text-gray-500">
              {m.role === "user" ? "Toi" : "Assistant"}
            </div>
            <div className="whitespace-pre-wrap">{m.content}</div>
          </div>
        ))}
        {loading && <div className="text-sm text-gray-500">…</div>}
      </div>
      <form onSubmit={handleSend} className="mt-3 flex gap-2">
        <input
          className="border p-2 flex-1 rounded"
          placeholder="Écris un message…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
        />
        <button
          className="bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-50"
          disabled={loading}
        >
          Envoyer
        </button>
      </form>
    </div>
  );
}
