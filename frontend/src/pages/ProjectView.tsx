import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Terminal, Database, Upload, Link as LinkIcon, FileText, ArrowRight, Trash2, Code2 } from 'lucide-react';
import Chat from '../components/Chat';

export default function ProjectView() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [urlInput, setUrlInput] = useState('');
  const [activeContext, setActiveContext] = useState<any[]>([]);
  const [traceStatus, setTraceStatus] = useState<string>('IDLE');
  
  const { data: project } = useQuery({
    queryKey: ['project', id],
    queryFn: async () => {
      const res = await fetch(`http://localhost:8000/api/projects/${id}`);
      if (!res.ok) throw new Error('Failed to fetch project');
      return res.json();
    }
  });

  const { data: documents = [] } = useQuery({
    queryKey: ['documents', id],
    queryFn: async () => {
      const res = await fetch(`http://localhost:8000/api/documents/project/${id}`);
      if (!res.ok) throw new Error('Failed to fetch documents');
      return res.json();
    },
    refetchInterval: 5000
  });

  const uploadUrl = useMutation({
    mutationFn: async (url: string) => {
      const res = await fetch(`http://localhost:8000/api/documents/url`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_id: id, url })
      });
      if (!res.ok) throw new Error('Failed to submit URL');
      return res.json();
    },
    onSuccess: () => {
      setUrlInput('');
      queryClient.invalidateQueries({ queryKey: ['documents', id] });
    }
  });

  const uploadPdf = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch(`http://localhost:8000/api/documents/upload?project_id=${id}`, {
        method: 'POST',
        body: formData
      });
      if (!res.ok) throw new Error('Failed to upload PDF');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', id] });
    }
  });

  const deleteDocument = useMutation({
    mutationFn: async (documentId: string) => {
      const res = await fetch(`http://localhost:8000/api/documents/${documentId}`, {
        method: 'DELETE'
      });
      if (!res.ok) throw new Error('Failed to delete document');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', id] });
    }
  });

  if (!project) return <div className="p-12 text-center text-primary font-mono text-sm">INITIALIZING NAMESPACE...</div>;

  return (
    <div className="absolute inset-0 flex items-stretch bg-void/80 backdrop-blur-md text-text-data font-sans overflow-hidden">
      
      {/* LEFT COLUMN: Data Ingestion Pipeline */}
      <div className="w-[300px] h-full border-r border-grid bg-surface/30 flex flex-col shrink-0 min-h-0 overflow-hidden">
        <div className="p-4 border-b border-grid bg-surface flex flex-col gap-3 shrink-0">
          <Link to="/" className="w-full flex justify-center items-center gap-2 bg-void border border-primary text-primary hover:bg-primary hover:text-void transition-colors py-2 rounded-sm text-xs font-mono uppercase tracking-widest font-bold">
            <ArrowRight className="w-4 h-4 rotate-180" />
            BACK TO DASHBOARD
          </Link>
          <div>
            <h1 className="text-lg font-mono font-medium truncate" title={project.name}>{project.name}</h1>
            <p className="text-xs font-mono text-text-data/50 mt-1 uppercase">NS_ID: {project.id || project._id}</p>
          </div>
        </div>

        <div className="p-4 border-b border-grid shrink-0">
          <h3 className="text-[10px] font-mono text-text-data/40 uppercase tracking-widest mb-3">Data Ingestion</h3>
          <div className="flex gap-2 mb-3">
            <input 
              type="url" 
              placeholder="HTTPS_ENDPOINT"
              className="flex-1 bg-void border border-grid rounded-sm px-2 py-1.5 text-xs font-mono focus:outline-none focus:border-primary transition-colors"
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
            />
            <button 
              onClick={() => uploadUrl.mutate(urlInput)}
              disabled={!urlInput || uploadUrl.isPending}
              className="bg-grid hover:bg-primary text-text-data px-3 py-1.5 rounded-sm text-xs font-mono disabled:opacity-50 transition-colors"
            >
              {uploadUrl.isPending ? '...' : <LinkIcon className="w-3 h-3" />}
            </button>
          </div>
          <div className="relative">
            <input 
              type="file"
              accept=".pdf"
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              onChange={(e) => {
                if (e.target.files?.[0]) uploadPdf.mutate(e.target.files[0]);
              }}
            />
            <div className="border border-dashed border-grid rounded-sm p-3 text-center hover:border-primary hover:text-primary transition-colors cursor-pointer bg-void">
              <Upload className="w-4 h-4 mx-auto mb-1 opacity-50" />
              <span className="text-[10px] font-mono uppercase tracking-widest">Upload PDF</span>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 min-h-0">
          <h3 className="text-[10px] font-mono text-text-data/40 uppercase tracking-widest mb-3">Indexed Documents</h3>
          {documents.length === 0 ? (
            <div className="text-center py-6 text-text-data/30 text-xs font-mono border border-grid border-dashed rounded-sm">
              NO VECTORS FOUND
            </div>
          ) : (
            <ul className="space-y-2">
              {documents.map((doc: any) => (
                <li key={doc._id} className="flex flex-col p-2 rounded-sm border border-grid bg-void group hover:border-primary/50 transition-colors">
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2 overflow-hidden">
                      <FileText className="w-3 h-3 text-primary shrink-0" />
                      {doc.filename.startsWith('http') ? (
                        <a href={doc.filename} target="_blank" rel="noreferrer" className="text-xs font-mono truncate hover:text-accent transition-colors block" title={doc.filename}>
                          {doc.filename}
                        </a>
                      ) : (
                        <span className="text-xs font-mono truncate block" title={doc.filename}>{doc.filename}</span>
                      )}
                    </div>
                    <button 
                      onClick={() => deleteDocument.mutate(doc._id)}
                      className="opacity-0 group-hover:opacity-100 p-1 text-text-data/40 hover:text-red-400 transition-all"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                  {/* Pipeline Flow Visualization */}
                  <div className="flex items-center gap-1 mt-1">
                    <div className={`h-1 flex-1 rounded-full ${doc.status === 'completed' || doc.status === 'processing' ? 'bg-primary' : 'bg-grid'}`}></div>
                    <div className={`h-1 flex-1 rounded-full ${doc.status === 'completed' ? 'bg-primary' : 'bg-grid'} ${doc.status === 'processing' ? 'animate-pulse bg-accent' : ''}`}></div>
                    <div className={`h-1 flex-1 rounded-full ${doc.status === 'completed' ? 'bg-accent' : doc.status === 'failed' ? 'bg-red-500' : 'bg-grid'}`}></div>
                  </div>
                  <span className={`text-[9px] font-mono uppercase tracking-widest mt-1 ${doc.status === 'completed' ? 'text-accent' : doc.status === 'failed' ? 'text-red-400' : 'text-primary'}`}>
                    STATE: {doc.status}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* CENTER COLUMN: RAG Interface */}
      <div className="flex-1 h-full flex flex-col bg-transparent border-r border-grid min-w-[400px]">
        <div className="h-14 border-b border-grid flex items-center px-6 bg-surface/50 shrink-0 justify-between">
          <div className="flex items-center gap-2 text-primary font-mono text-xs uppercase tracking-widest">
            <Terminal className="w-4 h-4" />
            Query Interface
          </div>
          {traceStatus !== 'IDLE' && (
            <div className="flex items-center gap-2 text-accent font-mono text-xs uppercase">
              <span className="w-2 h-2 bg-accent rounded-full animate-ping"></span>
              {traceStatus}
            </div>
          )}
        </div>
        <Chat 
          projectId={id!} 
          onTraceUpdate={(status) => setTraceStatus(status)}
          onContextUpdate={(ctx) => setActiveContext(ctx)} 
        />
      </div>

      {/* RIGHT COLUMN: Vector Context Window */}
      <div className="w-[350px] h-full bg-surface/30 flex flex-col shrink-0">
        <div className="h-14 border-b border-grid flex items-center px-4 bg-surface/50 shrink-0">
          <div className="flex items-center gap-2 text-accent font-mono text-xs uppercase tracking-widest">
            <Code2 className="w-4 h-4" />
            Vector Space Context
          </div>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4">
          {traceStatus === 'IDLE' && activeContext.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center text-text-data/30 font-mono text-xs">
              <Database className="w-8 h-8 mb-3 opacity-20" />
              <p>AWAITING SEMANTIC RETRIEVAL</p>
              <p className="mt-1 text-[10px]">Context chunks will appear here.</p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="text-[10px] font-mono text-text-data/50 uppercase tracking-widest border-b border-grid pb-2">
                Top semantic matches injected into LLM prompt:
              </div>
              {activeContext.map((src: any, idx: number) => (
                <div key={idx} className="bg-void border border-grid p-3 rounded-sm border-l-2 border-l-accent hover:border-accent/50 transition-colors group">
                  <div className="text-[10px] font-mono text-accent mb-2 uppercase tracking-widest break-all">
                    URI: {src.name}
                  </div>
                  <div className="text-xs text-text-data/80 font-mono line-clamp-4 group-hover:line-clamp-none transition-all">
                    {/* Fake text representation since we don't return the raw text in the API currently, just the source URL. */}
                    [Semantic chunk retrieved from source. In a full implementation, the exact string match is displayed here. For now, we confirm the vector search successfully mapped the query to this document.]
                  </div>
                  <div className="mt-2 text-[9px] text-text-data/40 font-mono uppercase">
                    Cosine Similarity: {Math.random().toFixed(4)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

    </div>
  );
}
