// src/components/header.tsx
import Link from 'next/link';
import { Bot, PlusCircle, HelpCircle } from 'lucide-react';

interface HeaderProps {
  openCreateProjectDialog: () => void;
  openHelpDialog: () => void;
}

export function Header({ openCreateProjectDialog, openHelpDialog }: HeaderProps) {
  return (
    <header className="purple-gradient shadow-md">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center">
            <Link href="/" className="flex items-center mr-6">
              <Bot className="h-6 w-6 mr-2 text-white" />
              <span className="text-lg font-bold text-white">UI Test Generator</span>
            </Link>
          </div>
          
          <div className="flex items-center space-x-2">
            <button 
              className="flex items-center px-3 py-1.5 text-sm font-medium text-white rounded-md border border-white/20 bg-white/10 hover:bg-white/20"
              onClick={openCreateProjectDialog}
            >
              <PlusCircle className="h-4 w-4 mr-1" />
              New Project
            </button>
            <button 
              className="flex items-center px-3 py-1.5 text-sm font-medium text-white rounded-md border border-white/20 bg-white/10 hover:bg-white/20"
              onClick={openHelpDialog}
            >
              <HelpCircle className="h-4 w-4 mr-1" />
              Help
            </button>
            <div className="bg-white/20 rounded-full px-3 py-1 text-xs font-medium text-white">
              Using Gemini 1.5 Flash
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}