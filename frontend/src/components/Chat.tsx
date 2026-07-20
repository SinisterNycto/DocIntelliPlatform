import { useState, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Terminal, Code2, Loader2, Send } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';

interface ChatProps {
  projectId: string;
  onTraceUpdate?: (status: string) => void;
  onContextUpdate?: (context: any[]) => void;
}

export default function Chat({ projectId, onTraceUpdate, onContextUpdate }: ChatProps) {
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
      // 1. Simulate Vectorizing
      onTraceUpdate?.('Vectorizing query (3072d)...');
      await new Promise(r => setTimeout(r, 600));
      
      // 2. Simulate Pinecone query
      onTraceUpdate?.('Querying Pinecone index...');
      await new Promise(r => setTimeout(r, 800));

      const res = await fetch(`http://localhost:8000/api/chat/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_id: projectId, content })
      });
      if (!res.ok) throw new Error('Failed to send message');
      
      const data = await res.json();
      
      // 3. Update Trace and Context with actual sources
      onTraceUpdate?.('Retrieved chunks. LLM generating response...');
      onContextUpdate?.(data.sources || []);
      await new Promise(r => setTimeout(r, 800));
      
      onTraceUpdate?.('IDLE');
      return data;
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
      onTraceUpdate?.('ERROR: Retrieval Failed');
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
    <div className="flex flex-col flex-1 min-h-0 bg-transparent relative">
      <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6">
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-center text-text-data/40 max-w-md mx-auto border border-grid border-dashed rounded-sm p-8 bg-surface/30">
            <Terminal className="w-12 h-12 mb-4 opacity-50" />
            <h3 className="text-sm font-mono tracking-widest uppercase mb-2 text-text-data/80">System Ready</h3>
            <p className="text-xs font-mono">Awaiting query input to initiate vector space retrieval.</p>
          </div>
        )}

        {messages.map((msg: any, idx: number) => (
          <div key={msg.id || idx} className={`flex max-w-4xl mx-auto w-full ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`flex flex-col max-w-[85%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
              
              <div className="flex items-center gap-2 mb-1 text-[10px] font-mono uppercase tracking-widest text-text-data/50">
                {msg.role === 'user' ? (
                  <><span>USER_QUERY</span><Terminal className="w-3 h-3" /></>
                ) : (
                  <><Code2 className="w-3 h-3 text-accent" /><span className="text-accent">RAG_OUTPUT</span></>
                )}
              </div>

              <div className={`p-4 rounded-sm border ${msg.role === 'user' ? 'bg-primary/10 border-primary/30 text-text-data' : 'bg-surface border-grid text-text-data'}`}>
                {msg.role === 'user' ? (
                  <p className="whitespace-pre-wrap text-sm font-mono">{msg.content}</p>
                ) : (
                  <div className="prose prose-sm prose-invert prose-p:font-sans prose-headings:font-sans prose-code:font-mono prose-a:text-primary max-w-none">
                    <ReactMarkdown rehypePlugins={[rehypeRaw]}>{msg.content}</ReactMarkdown>
                  </div>
                )}
              </div>
              
            </div>
          </div>
        ))}

        {sendMessage.isPending && (
          <div className="flex max-w-4xl mx-auto w-full justify-start">
            <div className="flex flex-col items-start max-w-[85%]">
              <div className="flex items-center gap-2 mb-1 text-[10px] font-mono uppercase tracking-widest text-accent">
                <Code2 className="w-3 h-3" /> PIPELINE_ACTIVE
              </div>
              <div className="p-4 rounded-sm border bg-surface border-accent/50 text-accent flex items-center gap-3">
                <Loader2 className="w-4 h-4 animate-spin" /> 
                <span className="text-xs font-mono uppercase">Streaming Response...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 bg-surface/50 border-t border-grid">
        <form 
          className="max-w-4xl mx-auto relative flex items-center"
          onSubmit={(e) => {
            e.preventDefault();
            if (input.trim() && !sendMessage.isPending) {
              sendMessage.mutate(input);
            }
          }}
        >
          <div className="absolute left-4 text-primary font-mono text-sm">{'>'}</div>
          <input 
            type="text" 
            placeholder="Enter search query..."
            className="w-full bg-void border border-grid rounded-sm pl-10 pr-14 py-3 text-sm font-mono text-text-data focus:outline-none focus:border-primary transition-colors placeholder:text-text-data/30"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={sendMessage.isPending}
          />
          <button 
            type="submit"
            disabled={!input.trim() || sendMessage.isPending}
            className="absolute right-2 p-1.5 bg-primary/20 text-primary hover:bg-primary hover:text-void rounded-sm disabled:opacity-50 disabled:hover:bg-primary/20 transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
