import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { createProject } from '@/lib/api';
import { PlusCircle, Upload, FileText, Bot } from 'lucide-react';

interface CreateProjectDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CreateProjectDialog({ open, onOpenChange }: CreateProjectDialogProps) {
  const [loading, setLoading] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);

    try {
      const formData = new FormData(e.currentTarget);
      const response = await createProject(formData);
      toast.success('Project created successfully');
      onOpenChange(false);
      router.push(`/dashboard/${response.id}`);
      router.refresh();
    } catch (error) {
      console.error('Error creating project:', error);
      toast.error('Failed to create project');
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      if (e.target.files.length === 1) {
        setFileName(e.target.files[0].name);
      } else {
        setFileName(`${e.target.files.length} files selected`);
      }
    } else {
      setFileName(null);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const fileInput = document.getElementById('file') as HTMLInputElement;
      if (fileInput) {
        fileInput.files = e.dataTransfer.files;
        
        if (e.dataTransfer.files.length === 1) {
          setFileName(e.dataTransfer.files[0].name);
        } else {
          setFileName(`${e.dataTransfer.files.length} files selected`);
        }
        
        // Trigger a change event on the file input for form validation
        const event = new Event('change', { bubbles: true });
        fileInput.dispatchEvent(event);
      }
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[550px] p-0 overflow-hidden rounded-xl">
        <div className="purple-gradient p-6 text-white flex items-center">
          <Bot className="h-8 w-8 mr-3" />
          <DialogHeader className="text-white p-0">
            <DialogTitle className="text-xl text-white">Create New Project</DialogTitle>
            <p className="text-white/80 text-sm mt-1">Get started by uploading your UI source files</p>
          </DialogHeader>
        </div>
        
        <form onSubmit={handleSubmit} className="px-6 py-4">
          <div className="grid gap-5">
            <div>
              <Label htmlFor="name" className="text-sm font-medium mb-1.5 block">
                Project Name
              </Label>
              <Input
                id="name"
                name="name"
                placeholder="Enter project name"
                required
                className="border border-gray-200 focus-visible:ring-[#8626c3]"
              />
            </div>
            
            <div>
              <Label htmlFor="description" className="text-sm font-medium mb-1.5 block">
                Description
              </Label>
              <Textarea
                id="description"
                name="description"
                placeholder="Describe your project (optional)"
                rows={3}
                className="border border-gray-200 resize-none focus-visible:ring-[#8626c3]"
              />
            </div>
            
            <div>
              <Label htmlFor="file" className="text-sm font-medium mb-1.5 block">
                Source Files
              </Label>
              <div 
                className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
                  dragActive ? 'border-[#8626c3] bg-[#8626c3]/5' : 'border-gray-200 hover:border-[#8626c3]/50'
                }`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                <Input
                  id="file"
                  name="file"
                  type="file"
                  multiple
                  required
                  accept=".html,.js,.jsx,.tsx,.vue,.zip"
                  className="hidden"
                  onChange={handleFileChange}
                />
                
                {fileName ? (
                  <div className="py-2">
                    <FileText className="h-8 w-8 text-[#8626c3] mx-auto mb-2" />
                    <p className="text-[#8626c3] font-medium">{fileName}</p>
                    <button 
                      type="button"
                      className="text-sm text-gray-500 mt-2 hover:text-[#8626c3]"
                      onClick={() => {
                        setFileName(null);
                        const fileInput = document.getElementById('file') as HTMLInputElement;
                        if (fileInput) fileInput.value = '';
                      }}
                    >
                      Remove
                    </button>
                  </div>
                ) : (
                  <div>
                    <Upload className="h-10 w-10 text-gray-400 mx-auto mb-3" />
                    <label 
                      htmlFor="file" 
                      className="block cursor-pointer"
                    >
                      <p className="text-sm text-gray-500 mb-1">
                        Drag and drop your files here, or 
                        <span className="text-[#8626c3] font-medium"> browse</span>
                      </p>
                      <p className="text-xs text-gray-400">
                        HTML, JSX, TSX, Vue, JS or ZIP archives (max 256MB)
                      </p>
                    </label>
                  </div>
                )}
              </div>
            </div>
          </div>
          
          <DialogFooter className="mt-6 gap-2 flex sm:justify-between">
            <Button 
              type="button" 
              variant="outline" 
              onClick={() => onOpenChange(false)}
              className="border-gray-200 text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </Button>
            
            <Button 
              type="submit" 
              disabled={loading}
              className="bg-[#8626c3] hover:bg-[#8626c3]/90 text-white"
            >
              {loading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Creating...
                </>
              ) : (
                <>
                  <PlusCircle className="mr-2 h-4 w-4" />
                  Create Project
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}