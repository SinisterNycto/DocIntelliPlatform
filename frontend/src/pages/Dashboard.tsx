import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Database, FolderGit2, PlusSquare, ArrowRight, Activity, Terminal, Trash2 } from 'lucide-react';
import { UserButton, useAuth } from '@clerk/clerk-react';
import { ThemeToggle } from '../components/ThemeToggle';

export default function Dashboard() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [isCreating, setIsCreating] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const { getToken } = useAuth();

  const { data: projects = [], isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: async () => {
      const token = await getToken();
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiUrl}/api/projects/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to fetch projects');
      return res.json();
    }
  });

  const createProject = useMutation({
    mutationFn: async (name: string) => {
      const token = await getToken();
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiUrl}/api/projects/`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ name, description: '' })
      });
      if (!res.ok) throw new Error('Failed to create project');
      return res.json();
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setIsCreating(false);
      setNewProjectName('');
      navigate(`/project/${data.id || data._id}`);
    }
  });

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (newProjectName.trim()) {
      createProject.mutate(newProjectName);
    }
  };

  const deleteProject = useMutation({
    mutationFn: async (projectId: string) => {
      const token = await getToken();
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiUrl}/api/projects/${projectId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to delete project');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    }
  });

  const handleDelete = (e: React.MouseEvent, projectId: string) => {
    e.preventDefault();
    e.stopPropagation();
    if (window.confirm("Are you sure you want to delete this project and all its vector data?")) {
      deleteProject.mutate(projectId);
    }
  };

  return (
    <div className="min-h-screen bg-void/80 backdrop-blur-md flex flex-col font-sans text-text-data">
      {/* Infrastructure Header */}
      <header className="border-b border-grid bg-surface/50">
        <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
            <Terminal className="h-5 w-5 text-accent" />
            <span className="font-mono font-semibold tracking-wide text-sm">DocIntelliPlatform<span className="text-grid ml-2">|</span><span className="text-primary ml-2 uppercase text-xs tracking-widest">RAG Engine</span></span>
          </Link>
          <div className="flex items-center gap-6 font-mono text-xs uppercase tracking-widest text-text-data/70">
            <ThemeToggle />
            <Link to="/" className="hover:text-primary transition-colors">Home</Link>
            <Link to="/dashboard" className="text-primary hover:text-accent transition-colors">Projects</Link>
            <UserButton afterSignOutUrl="/" />
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-12">
        <div className="flex items-end justify-between border-b border-grid pb-6 mb-10">
          <div>
            <h1 className="text-3xl font-mono font-medium text-text-data tracking-tight">Active Workspaces</h1>
            <p className="text-text-data/60 mt-2 font-mono text-sm">Select a knowledge base to initialize vector retrieval.</p>
          </div>
          <button 
            onClick={() => setIsCreating(true)}
            className="flex items-center gap-2 bg-primary hover:bg-primary/90 text-void px-4 py-2 rounded-sm font-mono text-sm font-medium transition-colors"
          >
            <PlusSquare className="w-4 h-4" />
            Initialize Project
          </button>
        </div>

        {isCreating && (
          <div className="mb-10 bg-surface border border-grid p-6 rounded-sm">
            <h3 className="text-sm font-mono uppercase tracking-widest text-text-data/80 mb-4">Create New Knowledge Base</h3>
            <form onSubmit={handleCreate} className="flex gap-4">
              <input 
                type="text" 
                placeholder="namespace_id (e.g. React_Docs)" 
                autoFocus
                className="flex-1 bg-void border border-grid rounded-sm px-4 py-2 font-mono text-sm focus:outline-none focus:border-primary transition-colors"
                value={newProjectName}
                onChange={(e) => setNewProjectName(e.target.value)}
              />
              <button 
                type="button" 
                onClick={() => setIsCreating(false)}
                className="px-4 py-2 font-mono text-sm text-text-data/60 hover:text-text-data transition-colors"
              >
                Cancel
              </button>
              <button 
                type="submit" 
                disabled={!newProjectName.trim() || createProject.isPending}
                className="bg-primary text-void px-6 py-2 rounded-sm font-mono text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
              >
                {createProject.isPending ? 'Processing...' : 'Execute'}
              </button>
            </form>
          </div>
        )}

        {isLoading ? (
          <div className="flex justify-center items-center py-20 text-primary">
            <Activity className="w-6 h-6 animate-spin" />
            <span className="ml-3 font-mono text-sm">Querying active namespaces...</span>
          </div>
        ) : projects.length === 0 ? (
          <div className="border border-dashed border-grid rounded-sm flex flex-col items-center justify-center p-16 text-center bg-surface/30">
            <Database className="w-8 h-8 text-grid mb-4" />
            <h3 className="font-mono text-text-data/80 mb-2">No namespaces found.</h3>
            <p className="text-text-data/50 text-sm mb-6 max-w-sm">Initialize a project to start ingesting documentation into the vector space.</p>
            <button onClick={() => setIsCreating(true)} className="text-primary font-mono text-sm hover:underline">
              [ Initialize Now ]
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project: any) => (
              <Link 
                key={project.id || project._id} 
                to={`/project/${project.id || project._id}`}
                className="group bg-surface border border-grid p-6 rounded-sm hover:border-primary transition-colors block relative overflow-hidden"
              >
                <div className="absolute top-0 left-0 w-1 h-full bg-grid group-hover:bg-primary transition-colors"></div>
                <div className="flex justify-between items-start mb-4">
                  <FolderGit2 className="w-5 h-5 text-primary" />
                  <div className="flex items-center gap-3">
                    <button 
                      onClick={(e) => handleDelete(e, project.id || project._id)}
                      className="text-text-data/40 hover:text-red-500 transition-colors z-10"
                      title="Delete Project"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                    <ArrowRight className="w-4 h-4 text-grid group-hover:text-primary transition-colors" />
                  </div>
                </div>
                <h3 className="text-lg font-mono font-medium text-text-data mb-2 truncate">{project.name}</h3>
                <div className="flex items-center gap-4 mt-6 border-t border-grid pt-4">
                  <div className="text-xs font-mono text-text-data/50">
                    <span className="uppercase tracking-wider block mb-1">Created</span>
                    <span className="text-text-data">{new Date(project.created_at).toISOString().split('T')[0]}</span>
                  </div>
                  <div className="text-xs font-mono text-text-data/50">
                    <span className="uppercase tracking-wider block mb-1">ID</span>
                    <span className="text-text-data truncate w-24 inline-block">{project.id || project._id}</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
