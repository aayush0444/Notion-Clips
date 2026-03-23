import { Send } from "lucide-react";
import { useState } from "react";

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (!input.trim()) return;

    const userMessage: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);

    // Simulate AI response
    setTimeout(() => {
      const responses = [
        'Based on the transcript, this concept is covered around the 12:30 mark. The speaker emphasizes that understanding the fundamentals is crucial before moving to advanced implementations.',
        'That\'s a great question. The video mentions three main approaches: direct implementation, using a library, and building a custom solution. Each has trade-offs in terms of flexibility and complexity.',
        'Yes, this is discussed in detail. The key difference lies in how data is processed before rendering—one happens on the server, reducing client-side work, while the other provides more interactivity.'
      ];
      const randomResponse = responses[Math.floor(Math.random() * responses.length)];
      const aiMessage: Message = { role: 'assistant', content: randomResponse };
      setMessages(prev => [...prev, aiMessage]);
    }, 800);

    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t border-white/5 pt-6 mt-6">
      <div className="text-xs text-white/40 mb-3 uppercase tracking-wider">Ask Follow-up Questions</div>
      
      {messages.length > 0 && (
        <div className="mb-4 space-y-3 max-h-[200px] overflow-y-auto">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`text-sm ${
                msg.role === 'user'
                  ? 'text-white/90 bg-white/5 border border-white/10 rounded-lg px-3 py-2'
                  : 'text-white/70 pl-3 border-l-2 border-purple-500/30'
              }`}
            >
              {msg.content}
            </div>
          ))}
        </div>
      )}

      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about the video content..."
          className="flex-1 bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white/90 placeholder:text-white/30 focus:outline-none focus:border-white/20 focus:bg-white/[0.07] transition-colors"
        />
        <button
          onClick={handleSend}
          disabled={!input.trim()}
          className="px-4 py-2.5 bg-white/10 hover:bg-white/15 disabled:opacity-40 disabled:cursor-not-allowed border border-white/10 rounded-lg transition-all"
        >
          <Send className="w-4 h-4 text-white/70" />
        </button>
      </div>
    </div>
  );
}
