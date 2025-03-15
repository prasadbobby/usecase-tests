// src/app/page.tsx
'use client';

import { useState, useEffect } from 'react';
import { fetchProjects } from '@/lib/api';
import { Project } from '@/types';
import { CreateProjectDialog } from '@/components/create-project-dialog';
import Link from 'next/link';
import { PlusCircle, Bot, Search, Layers, Cpu } from 'lucide-react';

export default function Home() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  useEffect(() => {
    const getProjects = async () => {
      try {
        const data = await fetchProjects();
        setProjects(data);
      } catch (error) {
        console.error('Failed to fetch projects', error);
      }
    };

    getProjects();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="purple-gradient py-16">
        <div className="container mx-auto px-4 text-center">
          <Bot className="h-20 w-20 mx-auto mb-6" />
          <h1 className="text-4xl md:text-5xl font-bold mb-4">UI Test Generator</h1>
          <p className="text-xl md:text-2xl max-w-2xl mx-auto mb-8 opacity-90">
            Generate automated tests from your UI source code with AI assistance
          </p>
          <button 
            className="bg-white text-[#8626c3] hover:bg-white/90 font-medium px-6 py-3 rounded-md shadow-xl inline-flex items-center"
            onClick={() => setIsDialogOpen(true)}
          >
            <PlusCircle className="mr-2 h-5 w-5" />
            Create Project
          </button>
        </div>
      </header>

      <div className="container mx-auto py-16 px-4 max-w-7xl">
        {projects.length > 0 && (
          <div className="mb-16">
            <h2 className="text-3xl font-bold mb-8 text-center text-gray-800">Your Projects</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {projects.map((project) => (
                <Link 
                  key={project.id} 
                  href={`/dashboard/${project.id}`}
                  className="block"
                >
                  <div className="h-full hover-lift border rounded-lg shadow-sm bg-white p-6">
                    <div className="w-10 h-10 rounded-full bg-[#8626c3]/10 flex items-center justify-center mb-4">
                      <Bot className="h-5 w-5 text-[#8626c3]" />
                    </div>
                    <h3 className="text-xl font-semibold mb-2 text-[#8626c3]">{project.name}</h3>
                    <p className="text-sm text-gray-500 mb-4 line-clamp-2">
                      {project.description || 'No description'}
                    </p>
                    <div className="text-sm text-gray-500">
                      Created: {new Date(project.created_at).toLocaleDateString()}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}

        <div className="py-10">
          <h2 className="text-3xl font-bold mb-12 text-center text-gray-800">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 mx-auto rounded-full bg-[#8626c3] text-white flex items-center justify-center mb-4 shadow-lg">
                <Search className="h-8 w-8" />
              </div>
              <h3 className="text-xl font-semibold mb-3 text-[#8626c3]">Element Discovery</h3>
              <p className="text-gray-600">
                Automatically scan and identify UI components from HTML, JSX, TSX, and Vue files
              </p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 mx-auto rounded-full bg-[#8626c3] text-white flex items-center justify-center mb-4 shadow-lg">
                <Layers className="h-8 w-8" />
              </div>
              <h3 className="text-xl font-semibold mb-3 text-[#8626c3]">POM Generation</h3>
              <p className="text-gray-600">
                Create structured Page Object Models with selectors and methods for test automation
              </p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 mx-auto rounded-full bg-[#8626c3] text-white flex items-center justify-center mb-4 shadow-lg">
                <Cpu className="h-8 w-8" />
              </div>
              <h3 className="text-xl font-semibold mb-3 text-[#8626c3]">AI-Powered Tests</h3>
              <p className="text-gray-600">
                Generate comprehensive test cases using Gemini 1.5 Flash API
              </p>
            </div>
          </div>
        </div>

        <div className="mt-16 bg-[#8626c3]/10 rounded-2xl p-8 text-center shadow-lg border">
          <h2 className="text-2xl font-bold mb-4 text-[#8626c3]">Ready to get started?</h2>
          <p className="text-lg mb-6 text-gray-700">
            Upload your UI source files and let AI generate comprehensive test cases for you.
          </p>
          <button 
            className="bg-[#8626c3] text-white hover:bg-[#8626c3]/90 font-medium px-6 py-3 rounded-md inline-flex items-center"
            onClick={() => setIsDialogOpen(true)}
          >
            <PlusCircle className="mr-2 h-5 w-5" />
            Create Your First Project
          </button>
        </div>
      </div>

      <footer className="purple-gradient py-8 mt-20">
        <div className="container mx-auto px-4 text-center">
          <p className="text-white">© 2025 UI Test Generator. Powered by Gemini 1.5 Flash.</p>
        </div>
      </footer>

      <CreateProjectDialog 
        open={isDialogOpen} 
        onOpenChange={setIsDialogOpen} 
      />
    </div>
  );
}