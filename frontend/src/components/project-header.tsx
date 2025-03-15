// src/components/project-header.tsx
import { Project } from '@/types';
import { useRouter, usePathname } from 'next/navigation';
import { FileText, Search, Layers, Code, Play, Clock, Settings, MoreHorizontal, ExternalLink } from 'lucide-react';

interface ProjectHeaderProps {
  project: Project;
}

export function ProjectHeader({ project }: ProjectHeaderProps) {
  const router = useRouter();
  const pathname = usePathname();
  const projectId = project.id;
  const currentTab = pathname.split('/').pop() || 'dashboard';

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: <FileText className="h-4 w-4" /> },
    { id: 'elements', label: 'UI Elements', icon: <Search className="h-4 w-4" /> },
    { id: 'pom', label: 'Page Objects', icon: <Layers className="h-4 w-4" /> },
    { id: 'tests', label: 'Test Cases', icon: <Code className="h-4 w-4" /> },
    { id: 'executions', label: 'Executions', icon: <Play className="h-4 w-4" /> }
  ];

  const handleTabChange = (tabId: string) => {
    if (tabId === 'dashboard') {
      router.push(`/dashboard/${projectId}`);
    } else {
      router.push(`/dashboard/${projectId}/${tabId}`);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border mb-6 overflow-hidden">
      <div className="p-6 pb-4">
        <div className="flex justify-between items-start">
          <div>
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-800">{project.name}</h1>
              <span className="ml-3 px-2.5 py-1 text-xs bg-gray-100 text-gray-600 rounded-full flex items-center">
                <Clock className="h-3 w-3 mr-1" />
                Created {new Date(project.created_at).toLocaleDateString()}
              </span>
            </div>
            {project.description && (
              <p className="mt-1 text-gray-600">{project.description}</p>
            )}
            <div className="mt-3 flex items-center text-sm text-gray-500">
              <span className="mr-4">
                <strong>Source:</strong> {project.source_file}
              </span>
              <a href="#" className="text-[#8626c3] hover:underline flex items-center">
                <ExternalLink className="h-3.5 w-3.5 mr-1" />
                View Source
              </a>
            </div>
          </div>
          
          <div className="flex space-x-2">
            <button className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-full transition-colors">
              <Settings className="h-5 w-5" />
            </button>
            <button className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-full transition-colors">
              <MoreHorizontal className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
      
      <div className="border-t px-1">
        <div className="flex">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => handleTabChange(tab.id)}
              className={`flex items-center py-3 px-4 text-sm font-medium transition-colors border-b-2 ${
                currentTab === tab.id 
                  ? 'border-[#8626c3] text-[#8626c3]' 
                  : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
              }`}
            >
              {tab.icon}
              <span className="ml-2">{tab.label}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}