import { useState, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Send, Bot, User, Loader2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';

export default function Chat({ projectId }: { projectId: string }) {
  const queryClient = useQueryClient();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { data: messages = [] } = useQuery({
    queryKey: ['chat', projectId],
    queryFn: async () => {
      const res = await fetch(`http://localhost:8000/api/chat/project/${projectId}`);
      if (!res.ok) throw new Error('Failed to fetch chat history');
      return res.json();
    }
  });

  const sendMessage = useMutation({
    mutationFn: async (content: string) => {
      const res = await fetch(`http://localhost:8000/api/chat/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_id: projectId, content })
      });
      if (!res.ok) throw new Error('Failed to send message');
      return res.json();
    },
    onMutate: async (newContent) => {
      await queryClient.cancelQueries({ queryKey: ['chat', projectId] });
      const previousMessages = queryClient.getQueryData(['chat', projectId]);
      
      // Optimistically update UI
      queryClient.setQueryData(['chat', projectId], (old: any) => [
        ...(old || []), 
        { id: 'temp', role: 'user', content: newContent }
      ]);
      
      setInput('');
      return { previousMessages };
    },
    onError: (err, newContent, context) => {
      queryClient.setQueryData(['chat', projectId], context?.previousMessages);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['chat', projectId] });
    }
  });

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, sendMessage.isPending]);

  return (
    <div className="flex flex-col h-full bg-white relative">
      <div className="p-4 border-b border-slate-100 flex items-center bg-white/80 backdrop-blur-md sticky top-0 z-10">
        <h2 className="text-lg font-semibold text-slate-900">AI Assistant</h2>
      </div>

      <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6">
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-center text-slate-500 max-w-md mx-auto">
            <Bot className="w-12 h-12 text-slate-300 mb-4" />
            <h3 className="text-lg font-medium text-slate-900 mb-2">How can I help you today?</h3>
            <p className="text-sm">Ingest some documents on the left, and ask me any questions about them.</p>
          </div>
        )}

        {messages.map((msg: any, idx: number) => (
          <div key={msg.id || idx} className={`flex gap-4 max-w-3xl mx-auto ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${msg.role === 'user' ? 'bg-accent text-white' : 'bg-slate-100 text-slate-600'}`}>
              {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>
            
            <div className={`flex flex-col gap-2 ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
              <div className={`px-5 py-3 rounded-2xl max-w-2xl ${msg.role === 'user' ? 'bg-accent text-white rounded-tr-none' : 'bg-slate-50 text-slate-900 rounded-tl-none border border-slate-100'}`}>
                {msg.role === 'user' ? (
                  <p className="whitespace-pre-wrap text-sm">{msg.content}</p>
                ) : (
                  <div className="prose prose-sm prose-slate max-w-none">
                    <ReactMarkdown rehypePlugins={[rehypeRaw]}>{msg.content}</ReactMarkdown>
                  </div>
                )}
              </div>
              
            </div>
          </div>
        ))}

        {sendMessage.isPending && (
          <div className="flex gap-4 max-w-3xl mx-auto">
            <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 bg-slate-100 text-slate-600">
              <Bot className="w-4 h-4" />
            </div>
            <div className="px-5 py-4 rounded-2xl bg-slate-50 border border-slate-100 rounded-tl-none flex items-center gap-2 text-slate-500 text-sm">
              <Loader2 className="w-4 h-4 animate-spin" /> Thinking...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 bg-white border-t border-slate-100">
        <form 
          className="max-w-3xl mx-auto relative flex items-center"
          onSubmit={(e) => {
            e.preventDefault();
            if (input.trim() && !sendMessage.isPending) {
              sendMessage.mutate(input);
            }
          }}
        >
          <input 
            type="text" 
            placeholder="Ask a question about your documents..."
            className="w-full bg-slate-50 border border-slate-200 rounded-full pl-6 pr-14 py-4 text-sm focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-all shadow-sm"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={sendMessage.isPending}
          />
          <button 
            type="submit"
            disabled={!input.trim() || sendMessage.isPending}
            className="absolute right-2 p-2.5 bg-accent text-white rounded-full hover:bg-accent/90 disabled:opacity-50 disabled:hover:bg-accent transition-all shadow-md"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
        <p className="text-center text-xs text-slate-400 mt-3">
          AI can make mistakes. Consider verifying important information.
        </p>
      </div>
    </div>
  );
}
