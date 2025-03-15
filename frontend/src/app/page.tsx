// src/app/page.tsx
'use client';

import { useState, useEffect } from 'react';
import { fetchProjects } from '@/lib/api';
import { Project } from '@/types';
import { CreateProjectDialog } from '@/components/create-project-dialog';
import Link from 'next/link';
import { PlusCircle, Bot, Search, Layers, Cpu, ArrowRight } from 'lucide-react';

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
    <div className="min-h-screen bg-white">
      {/* Hero Section with Purple Gradient */}
      <section 
        className="relative" 
        style={{ 
          background: 'linear-gradient(135deg, #8626c3, #a64ced)',
          color: 'white'
        }}
      >
        <div className="container mx-auto px-4 py-20 text-center">
          <Bot className="h-20 w-20 mx-auto mb-8" />
          <h1 className="text-4xl md:text-5xl font-bold mb-6">UI Test Generator</h1>
          <p className="text-xl md:text-2xl max-w-2xl mx-auto mb-10 opacity-90">
            Generate automated tests from your UI source code with AI assistance
          </p>
          <button 
            onClick={() => setIsDialogOpen(true)}
            className="bg-white text-[#8626c3] px-8 py-3 rounded-lg font-medium shadow-lg hover:bg-gray-50 transition-all flex items-center mx-auto"
          >
            <PlusCircle className="mr-2 h-5 w-5" />
            Create Project
          </button>
        </div>
        
        {/* Wave Separator */}
        <div className="absolute bottom-0 left-0 right-0">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 100" fill="white">
            <path d="M0,64L80,58.7C160,53,320,43,480,53.3C640,64,800,96,960,96C1120,96,1280,64,1360,48L1440,32L1440,100L1360,100C1280,100,1120,100,960,100C800,100,640,100,480,100C320,100,160,100,80,100L0,100Z"></path>
          </svg>
        </div>
      </section>

      {/* Projects Section */}
      {projects.length > 0 && (
        <section className="py-16 bg-white">
          <div className="container mx-auto px-4">
            <h2 className="text-3xl font-bold mb-10 text-center text-gray-800">Your Projects</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
              {projects.map((project) => (
                <Link 
                  key={project.id} 
                  href={`/dashboard/${project.id}`}
                  className="block"
                >
                  <div className="h-full rounded-xl shadow-md border border-gray-100 bg-white p-6 hover:shadow-lg transition-all duration-300 flex flex-col">
                    <div className="w-12 h-12 rounded-full bg-[#8626c3]/10 flex items-center justify-center mb-4">
                      <Bot className="h-6 w-6 text-[#8626c3]" />
                    </div>
                    <h3 className="text-xl font-semibold mb-2 text-[#8626c3]">{project.name}</h3>
                    <p className="text-sm text-gray-500 mb-4 flex-grow">
                      {project.description || 'No description'}
                    </p>
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-gray-400">
                        Created: {new Date(project.created_at).toLocaleDateString()}
                      </span>
                      <div className="text-[#8626c3] text-sm font-medium flex items-center">
                        View Project <ArrowRight className="ml-1 h-4 w-4" />
                      </div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Features Section */}
      <section className="py-16 bg-gray-50">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold mb-16 text-center text-gray-800">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-10 max-w-6xl mx-auto">
            <div className="text-center">
              <div className="w-20 h-20 mx-auto rounded-full bg-[#8626c3] text-white flex items-center justify-center mb-6 shadow-lg">
                <Search className="h-8 w-8" />
              </div>
              <h3 className="text-xl font-semibold mb-3 text-[#8626c3]">Element Discovery</h3>
              <p className="text-gray-600">
                Automatically scan and identify UI components from HTML, JSX, TSX, and Vue files
              </p>
            </div>
            
            <div className="text-center">
              <div className="w-20 h-20 mx-auto rounded-full bg-[#8626c3] text-white flex items-center justify-center mb-6 shadow-lg">
                <Layers className="h-8 w-8" />
              </div>
              <h3 className="text-xl font-semibold mb-3 text-[#8626c3]">POM Generation</h3>
              <p className="text-gray-600">
                Create structured Page Object Models with selectors and methods for test automation
              </p>
            </div>
            
            <div className="text-center">
              <div className="w-20 h-20 mx-auto rounded-full bg-[#8626c3] text-white flex items-center justify-center mb-6 shadow-lg">
                <Cpu className="h-8 w-8" />
              </div>
              <h3 className="text-xl font-semibold mb-3 text-[#8626c3]">AI-Powered Tests</h3>
              <p className="text-gray-600">
                Generate comprehensive test cases using Gemini 1.5 Flash API
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-white">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto rounded-2xl p-12 text-center shadow-xl" 
               style={{ 
                 background: 'linear-gradient(135deg, rgba(134,38,195,0.1), rgba(166,76,237,0.1))',
                 borderTop: '1px solid rgba(134,38,195,0.2)',
                 borderLeft: '1px solid rgba(134,38,195,0.2)',
               }}>
            <h2 className="text-3xl font-bold mb-4 text-[#8626c3]">Ready to get started?</h2>
            <p className="text-lg mb-8 text-gray-700 max-w-2xl mx-auto">
              Upload your UI source files and let AI generate comprehensive test cases that save you time and improve coverage.
            </p>
            <button 
              className="bg-[#8626c3] text-white hover:bg-[#8626c3]/90 font-medium px-8 py-3 rounded-lg inline-flex items-center shadow-md hover:shadow-lg transition-all"
              onClick={() => setIsDialogOpen(true)}
            >
              <PlusCircle className="mr-2 h-5 w-5" />
              Create Your First Project
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-10" style={{ background: 'linear-gradient(135deg, #8626c3, #a64ced)', color: 'white' }}>
        <div className="container mx-auto px-4 text-center">
          <Bot className="h-10 w-10 mx-auto mb-4" />
          <p className="mb-2">© 2025 UI Test Generator</p>
          <p className="text-sm opacity-70">Powered by Gemini 1.5 Flash</p>
        </div>
      </footer>

      <CreateProjectDialog 
        open={isDialogOpen} 
        onOpenChange={setIsDialogOpen} 
      />
    </div>
  );
}