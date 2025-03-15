// src/components/project-sidebar.tsx
import Link from 'next/link';
import { Bot, PlusCircle, Search } from 'lucide-react';
import { WorkflowGuide } from './workflow-guide';
import { useState } from 'react';

export function ProjectSidebar({ 
  projects, 
  selectedProject, 
  openCreateProjectDialog 
}) {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredProjects = searchQuery.trim() 
    ? projects.filter(p => 
        p.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
        (p.description && p.description.toLowerCase().includes(searchQuery.toLowerCase()))
      )
    : projects;

  return (
    <div className="w-64 border-r bg-white min-h-full flex-shrink-0 overflow-auto">
      <div className="p-4">
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search projects..."
            className="w-full pl-9 pr-3 py-2 rounded-md border border-gray-200 text-sm"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        
        <div className="mb-2">
          <h3 className="text-xs uppercase text-gray-500 font-semibold px-2">
            My Projects
          </h3>
        </div>
        
        <div className="space-y-1 mb-4">
          {filteredProjects && filteredProjects.length > 0 ? (
            filteredProjects.map((project) => (
              <Link
                key={project.id}
                href={`/dashboard/${project.id}`}
                className={`block px-3 py-2 rounded-md text-sm ${
                  selectedProject?.id === project.id 
                    ? 'bg-[#8626c3]/10 text-[#8626c3] font-medium' 
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                <div className="flex items-center">
                  <Bot className={`h-4 w-4 mr-2 ${
                    selectedProject?.id === project.id ? 'text-[#8626c3]' : 'text-gray-400'
                  }`} />
                  <span className="truncate">{project.name}</span>
                </div>
              </Link>
            ))
          ) : (
            <p className="text-sm text-gray-500 px-3 py-2">
              {searchQuery ? 'No matching projects found' : 'No projects yet'}
            </p>
          )}
        </div>
        
        <button
          onClick={openCreateProjectDialog}
          className="w-full text-sm py-2 px-3 rounded-md bg-[#8626c3] text-white flex items-center justify-center"
        >
          <PlusCircle className="h-4 w-4 mr-2" />
          New Project
        </button>
      </div>
      
      <div className="px-4 pb-4">
        <WorkflowGuide />
      </div>
    </div>
  );
}