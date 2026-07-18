import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { BookOpen, Search, MessageSquare, FileText, UploadCloud, Database, Loader2, ArrowRight } from 'lucide-react';

export default function Dashboard() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [isCreating, setIsCreating] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');

  const { data: projects = [], isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: async () => {
      const res = await fetch('http://localhost:8000/api/projects');
      if (!res.ok) throw new Error('Failed to fetch projects');
      return res.json();
    }
  });

  const createProject = useMutation({
    mutationFn: async (name: string) => {
      const res = await fetch('http://localhost:8000/api/projects/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
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

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2 text-primary">
            <Database className="h-6 w-6 text-accent" />
            <span className="font-bold text-xl tracking-tight">DocIntelli Platform</span>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/" className="text-sm font-medium text-primary transition-colors">Projects</Link>
            <button onClick={() => alert("Settings coming soon!")} className="text-sm font-medium text-slate-600 hover:text-primary transition-colors">Settings</button>
            <button onClick={() => alert("User Profile coming soon!")} className="h-8 w-8 rounded-full bg-accent/10 flex items-center justify-center text-accent font-bold hover:bg-accent/20 transition-colors">
              U
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Welcome back</h1>
            <p className="text-slate-500 mt-1">Manage your knowledge bases and explore documentation.</p>
          </div>
          <button 
            onClick={() => setIsCreating(true)}
            className="inline-flex items-center justify-center gap-2 bg-accent hover:bg-blue-600 text-white px-5 py-2.5 rounded-lg font-medium transition-all shadow-sm shadow-blue-500/20 active:scale-95"
          >
            <UploadCloud className="w-5 h-5" />
            New Project
          </button>
        </div>

        {isCreating && (
          <div className="mb-8 bg-white p-6 rounded-xl border border-blue-200 shadow-md">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Create New Knowledge Base</h3>
            <form onSubmit={handleCreate} className="flex gap-4">
              <input 
                type="text" 
                placeholder="Project Name (e.g., React Docs)" 
                autoFocus
                className="flex-1 bg-slate-50 border border-slate-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent"
                value={newProjectName}
                onChange={(e) => setNewProjectName(e.target.value)}
              />
              <button 
                type="button" 
                onClick={() => setIsCreating(false)}
                className="px-4 py-2 text-slate-600 font-medium hover:bg-slate-100 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button 
                type="submit" 
                disabled={!newProjectName.trim() || createProject.isPending}
                className="bg-accent text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-600 transition-colors disabled:opacity-50"
              >
                {createProject.isPending ? 'Creating...' : 'Create'}
              </button>
            </form>
          </div>
        )}

        <div className="mt-12">
          <h2 className="text-xl font-bold text-slate-900 mb-6">Recent Projects</h2>
          
          {isLoading ? (
            <div className="flex justify-center items-center py-20 text-slate-400">
              <Loader2 className="w-8 h-8 animate-spin" />
            </div>
          ) : projects.length === 0 ? (
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex items-center justify-center p-12 text-center">
              <div className="max-w-sm">
                <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Database className="w-8 h-8 text-slate-400" />
                </div>
                <h3 className="text-lg font-medium text-slate-900">No projects yet</h3>
                <p className="text-slate-500 mt-2 mb-6">Create your first project to start ingesting documentation and PDFs.</p>
                <button 
                  onClick={() => setIsCreating(true)}
                  className="text-accent font-medium hover:underline inline-flex items-center gap-1"
                >
                  Create Project <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {projects.map((project: any) => (
                <Link 
                  key={project.id || project._id} 
                  to={`/project/${project.id || project._id}`}
                  className="group bg-white p-6 rounded-xl border border-slate-200 shadow-sm hover:shadow-md hover:border-accent/50 transition-all cursor-pointer block"
                >
                  <div className="flex justify-between items-start mb-4">
                    <div className="w-12 h-12 rounded-lg bg-blue-50 flex items-center justify-center">
                      <Database className="w-6 h-6 text-accent" />
                    </div>
                    <ArrowRight className="w-5 h-5 text-slate-300 group-hover:text-accent group-hover:translate-x-1 transition-all" />
                  </div>
                  <h3 className="text-lg font-semibold text-slate-900 mb-1">{project.name}</h3>
                  <p className="text-slate-500 text-sm">Created {new Date(project.created_at).toLocaleDateString()}</p>
                </Link>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
