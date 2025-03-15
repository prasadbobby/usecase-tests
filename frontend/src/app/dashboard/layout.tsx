// src/app/dashboard/layout.tsx
'use client';

import { useState, useEffect } from 'react';
import { fetchProjects } from '@/lib/api';
import { CreateProjectDialog } from '@/components/create-project-dialog';
import { HelpDialog } from '@/components/help-dialog';
import { Header } from '@/components/header';
import { ProjectSidebar } from '@/components/project-sidebar';

export default function DashboardLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: { projectId?: string };
}) {
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
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
    <>
      <Header 
        openCreateProjectDialog={() => setCreateDialogOpen(true)}
        openHelpDialog={() => setHelpDialogOpen(true)}
      />
      
      <div className="flex bg-gray-50 min-h-[calc(100vh-64px)]">
        <ProjectSidebar 
          projects={projects}
          selectedProject={selectedProject}
          openCreateProjectDialog={() => setCreateDialogOpen(true)}
        />
        
        <main className="flex-1 p-6 overflow-auto">
          <div className="max-w-6xl mx-auto">
            {children}
          </div>
        </main>
      </div>
      
      <CreateProjectDialog 
        open={createDialogOpen} 
        onOpenChange={setCreateDialogOpen} 
      />
      
      <HelpDialog 
        open={helpDialogOpen} 
        onOpenChange={setHelpDialogOpen} 
      />
    </>
  );
}