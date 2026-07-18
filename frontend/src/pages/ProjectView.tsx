import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Upload, Link as LinkIcon, FileText } from 'lucide-react';
import Chat from '../components/Chat';

export default function ProjectView() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [urlInput, setUrlInput] = useState('');
  
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
    refetchInterval: 5000 // Refetch every 5s to update statuses
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

  if (!project) return <div className="p-12 text-center text-slate-500">Loading project...</div>;

  return (
    <div className="flex h-screen bg-slate-50">
      {/* Sidebar - Document Management */}
      <div className="w-1/3 min-w-[320px] max-w-md border-r border-slate-200 bg-white flex flex-col">
        <div className="p-6 border-b border-slate-100">
          <Link to="/" className="inline-flex items-center text-sm font-medium text-slate-500 hover:text-slate-900 mb-4 transition-colors">
            <ArrowLeft className="w-4 h-4 mr-1" />
            Back to Dashboard
          </Link>
          <h1 className="text-2xl font-bold text-slate-900">{project.name}</h1>
          <p className="text-sm text-slate-500 mt-1">{project.description}</p>
        </div>

        <div className="p-6 border-b border-slate-100 space-y-4 bg-slate-50/50">
          <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider">Ingest Data</h3>
          
          <div className="flex gap-2">
            <input 
              type="url" 
              placeholder="https://docs.example.com"
              className="flex-1 bg-white border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-all"
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
            />
            <button 
              onClick={() => uploadUrl.mutate(urlInput)}
              disabled={!urlInput || uploadUrl.isPending}
              className="bg-slate-900 text-white px-3 py-2 rounded-lg text-sm font-medium hover:bg-slate-800 disabled:opacity-50 transition-colors flex items-center justify-center"
            >
              {uploadUrl.isPending ? '...' : <LinkIcon className="w-4 h-4" />}
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
            <div className="border-2 border-dashed border-slate-200 rounded-lg p-4 text-center hover:border-accent hover:bg-accent/5 transition-colors">
              <Upload className="w-5 h-5 text-slate-400 mx-auto mb-1" />
              <span className="text-sm text-slate-600 font-medium">Click to upload PDF</span>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-4">Ingested Documents</h3>
          {documents.length === 0 ? (
            <div className="text-center py-8 text-slate-500 text-sm border border-slate-100 rounded-xl bg-slate-50">
              No documents ingested yet.
            </div>
          ) : (
            <ul className="space-y-3">
              {documents.map((doc: any) => (
                <li key={doc._id} className="flex items-start gap-3 p-3 rounded-lg border border-slate-100 bg-white shadow-sm hover:shadow-md transition-shadow group">
                  <div className={`p-2 rounded-md ${doc.status === 'completed' ? 'bg-emerald-50 text-emerald-600' : doc.status === 'failed' ? 'bg-red-50 text-red-600' : 'bg-amber-50 text-amber-600'}`}>
                    <FileText className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-900 truncate">{doc.filename}</p>
                    <p className="text-xs text-slate-500 capitalize">{doc.status}</p>
                  </div>
                  <button 
                    onClick={() => deleteDocument.mutate(doc._id)}
                    className="opacity-0 group-hover:opacity-100 p-2 text-slate-400 hover:text-red-600 transition-all rounded-md hover:bg-red-50"
                    title="Delete document"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col bg-white">
        <Chat projectId={id!} />
      </div>
    </div>
  );
}
