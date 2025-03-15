// src/components/project-sidebar.tsx
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Project } from '@/types';
import { PlusCircle, Folder } from 'lucide-react';
import { WorkflowGuide } from './workflow-guide';

interface ProjectSidebarProps {
  projects: Project[];
  selectedProject?: Project | null;
  openCreateProjectDialog: () => void;
}

export function ProjectSidebar({ 
  projects, 
  selectedProject, 
  openCreateProjectDialog 
}: ProjectSidebarProps) {
  const router = useRouter();

  return (
    <div className="flex flex-col gap-4">
      <div className="border rounded-lg shadow-sm overflow-hidden">
        {/* Change this div to use purple-gradient class */}
        <div className="purple-gradient p-4">
          <h3 className="text-lg font-semibold flex items-center">
            <Folder className="mr-2 h-5 w-5" />
            Projects
          </h3>
        </div>
        <div className="divide-y">
          {projects?.length > 0 ? (
            projects.map((project) => (
              <Link
                key={project.id}
                href={`/dashboard/${project.id}`}
                className={`block p-4 transition-all duration-200 hover-lift ${
                  selectedProject?.id === project.id 
                    ? 'border-l-4 border-[#8626c3] bg-[#8626c3]/5' 
                    : 'border-l-4 border-transparent'
                }`}
              >
                <div className="flex justify-between items-start">
                  <h3 className="font-medium">{project.name}</h3>
                  <span className="text-xs text-gray-500">
                    {new Date(project.created_at).toLocaleDateString()}
                  </span>
                </div>
                <p className="text-sm text-gray-500 truncate mt-1">
                  {project.description || 'No description'}
                </p>
              </Link>
            ))
          ) : (
            <div className="p-4 text-center text-gray-500">
              No projects yet. Create one to get started!
            </div>
          )}
        </div>
        <div className="p-3 bg-gray-50">
          <button 
            onClick={openCreateProjectDialog} 
            className="w-full bg-[#8626c3] text-white py-2 px-4 rounded-md flex items-center justify-center hover:bg-[#8626c3]/90"
          >
            <PlusCircle className="mr-2 h-4 w-4" />
            Create Project
          </button>
        </div>
      </div>

      <WorkflowGuide />
    </div>
  );
}