'use client';

import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { 
  Table, 
  TableHeader, 
  TableBody, 
  TableHead, 
  TableRow, 
  TableCell 
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { ProjectHeader } from '@/components/project-header';
import { getProjectElements, fetchProject, scanProject, generatePom } from '@/lib/api';
import { Project, Element } from '@/types';
import { toast } from 'sonner';
import { Search, Layers } from 'lucide-react';

export default function ElementsPage({ params }: { params: { projectId: string } }) {
  const [project, setProject] = useState<Project | null>(null);
  const [elements, setElements] = useState<Element[]>([]);
  const [loading, setLoading] = useState(false);
  const { projectId } = params;

  useEffect(() => {
    const fetchData = async () => {
      try {
        const projectData = await fetchProject(projectId);
        setProject(projectData);

        const elementsData = await getProjectElements(projectId);
        setElements(elementsData);
      } catch (error) {
        console.error('Error fetching data:', error);
        toast.error('Failed to load data');
      }
    };

    fetchData();
  }, [projectId]);

  // src/app/dashboard/[projectId]/elements/page.tsx (continued)
  const handleScanElements = async () => {
    setLoading(true);
    try {
      await scanProject(projectId);
      const elementsData = await getProjectElements(projectId);
      setElements(elementsData);
      toast.success('UI elements scanned successfully');
    } catch (error) {
      console.error('Error scanning elements:', error);
      toast.error('Failed to scan UI elements');
    } finally {
      setLoading(false);
    }
  };

  const handleGeneratePom = async () => {
    setLoading(true);
    try {
      await generatePom(projectId);
      toast.success('Page Object Model generated successfully');
    } catch (error) {
      console.error('Error generating POM:', error);
      toast.error('Failed to generate Page Object Model');
    } finally {
      setLoading(false);
    }
  };

  if (!project) {
    return <div className="flex items-center justify-center h-full">Loading project...</div>;
  }

  return (
    <div className="space-y-6">
      <ProjectHeader project={project} />

      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">UI Elements ({elements.length})</h2>
        <div className="flex space-x-2">
          <Button 
            onClick={handleScanElements}
            disabled={loading}
          >
            <Search className="mr-2 h-4 w-4" />
            Scan Source Code
          </Button>
          {elements.length > 0 && (
            <Button 
              onClick={handleGeneratePom}
              disabled={loading}
              variant="outline"
            >
              <Layers className="mr-2 h-4 w-4" />
              Generate POM
            </Button>
          )}
        </div>
      </div>

      {elements.length > 0 ? (
        <div className="border rounded-lg overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted">
                <TableHead>Name</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Selector</TableHead>
                <TableHead>Text</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {elements.map((element) => (
                <TableRow key={element.id}>
                  <TableCell className="font-medium">{element.name}</TableCell>
                  <TableCell>
                    <Badge variant="secondary">{element.type}</Badge>
                  </TableCell>
                  <TableCell>
                    <code className="bg-muted text-xs p-1 rounded">{element.selector}</code>
                  </TableCell>
                  <TableCell>
                    {element.properties.text.substring(0, 30)}
                    {element.properties.text.length > 30 && '...'}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      ) : (
        <div className="bg-muted p-8 rounded-lg text-center">
          <p className="text-muted-foreground mb-4">
            No UI elements found. Click the "Scan Source Code" button to extract elements from your source files.
          </p>
          <Button 
            onClick={handleScanElements}
            disabled={loading}
          >
            <Search className="mr-2 h-4 w-4" />
            Scan Source Code
          </Button>
        </div>
      )}
    </div>
  );
}