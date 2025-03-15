// src/app/dashboard/layout.tsx
'use client';

import { useState, useEffect } from 'react';
import { fetchProjects } from '@/lib/api';
import { Project } from '@/types';
import { ProjectSidebar } from '@/components/project-sidebar';
import { CreateProjectDialog } from '@/components/create-project-dialog';
import { HelpDialog } from '@/components/help-dialog';
import { Header } from '@/components/header';

export default function DashboardLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: { projectId?: string };
}) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [helpDialogOpen, setHelpDialogOpen] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const projectsData = await fetchProjects();
        setProjects(projectsData);
        
        if (params.projectId) {
          const project = projectsData.find(p => p.id === params.projectId);
          if (project) {
            setSelectedProject(project);
          }
        }
      } catch (error) {
        console.error('Error fetching projects:', error);
      }
    };
    
    fetchData();
  }, [params.projectId]);

  return (
    <div className="min-h-screen bg-gray-50">
      <Header 
        openCreateProjectDialog={() => setCreateDialogOpen(true)}
        openHelpDialog={() => setHelpDialogOpen(true)}
      />
      
      <div className="container mx-auto px-4 py-6">
        <div className="flex flex-col lg:flex-row gap-6">
          <div className="w-full lg:w-1/4">
            <ProjectSidebar 
              projects={projects} 
              selectedProject={selectedProject} 
              openCreateProjectDialog={() => setCreateDialogOpen(true)} 
            />
          </div>
          
          <div className="w-full lg:w-3/4 fade-in">
            {children}
          </div>
        </div>
      </div>
      
      <CreateProjectDialog 
        open={createDialogOpen} 
        onOpenChange={setCreateDialogOpen} 
      />
      
      <HelpDialog 
        open={helpDialogOpen} 
        onOpenChange={setHelpDialogOpen} 
      />
    </div>
  );
}