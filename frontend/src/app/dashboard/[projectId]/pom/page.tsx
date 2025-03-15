'use client';

import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { 
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger
} from '@/components/ui/accordion';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { ProjectHeader } from '@/components/project-header';
import { 
  fetchProject, 
  getProjectPoms, 
  getProjectElements, 
  generatePom, 
  generateTests 
} from '@/lib/api';
import { Project, Pom } from '@/types';
import { toast } from 'sonner';
import { Layers, FileCode, Download, FileSpreadsheet } from 'lucide-react';
import Link from 'next/link';

export default function PomPage({ params }: { params: { projectId: string } }) {
  const [project, setProject] = useState<Project | null>(null);
  const [poms, setPoms] = useState<Pom[]>([]);
  const [elementCount, setElementCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const { projectId } = params;

  useEffect(() => {
    const fetchData = async () => {
      try {
        const projectData = await fetchProject(projectId);
        setProject(projectData);

        const pomsData = await getProjectPoms(projectId);
        setPoms(pomsData);

        const elementsData = await getProjectElements(projectId);
        setElementCount(elementsData.length);
      } catch (error) {
        console.error('Error fetching data:', error);
        toast.error('Failed to load data');
      }
    };

    fetchData();
  }, [projectId]);

  const handleGeneratePom = async () => {
    setLoading(true);
    try {
      await generatePom(projectId);
      const pomsData = await getProjectPoms(projectId);
      setPoms(pomsData);
      toast.success('Page Object Model generated successfully');
    } catch (error) {
      console.error('Error generating POM:', error);
      toast.error('Failed to generate Page Object Model');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateTests = async (pomId: string) => {
    setLoading(true);
    try {
      await generateTests(projectId, pomId);
      toast.success('Test cases generated successfully');
    } catch (error) {
      console.error('Error generating tests:', error);
      toast.error('Failed to generate test cases');
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
        <h2 className="text-2xl font-bold">Page Object Models ({poms.length})</h2>
        <Button 
          onClick={handleGeneratePom}
          disabled={elementCount === 0 || loading}
        >
          <Layers className="mr-2 h-4 w-4" />
          Generate POM
        </Button>
      </div>

      {poms.length > 0 ? (
        <Accordion type="single" collapsible className="space-y-4">
          {poms.map((pom, index) => (
            <AccordionItem 
              key={pom.id} 
              value={pom.id}
              className="border rounded-lg overflow-hidden shadow-sm"
            >
              <AccordionTrigger className="px-4 py-2 hover:no-underline hover:bg-muted">
                <div className="flex justify-between items-center w-full pr-4">
                  <span>Page Object Model {index + 1}</span>
                  <span className="text-sm text-muted-foreground">
                    {new Date(pom.created_at).toLocaleString()}
                  </span>
                </div>
              </AccordionTrigger>
              <AccordionContent className="px-4 py-2">
                <div className="mb-4">
                  <h4 className="font-medium mb-2">Page Classes:</h4>
                  <div className="grid gap-2">
                    {pom.elements
                      .filter(element => element.type === 'page')
                      .map(page => (
                        <Card key={page.id} className="bg-muted/50">
                          <CardContent className="p-3 flex justify-between items-center">
                            <span className="font-medium">{page.name}</span>
                            <Badge variant="secondary">
                              {page.children?.length || 0} elements
                            </Badge>
                          </CardContent>
                        </Card>
                      ))
                    }
                  </div>
                </div>

                <div className="flex flex-wrap gap-2 justify-between">
                  <Link 
                    href={`/api/download/${encodeURIComponent(pom.file_path)}`}
                    className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-9 px-4 py-2"
                  >
                    <Download className="mr-2 h-4 w-4" />
                    Download POM JSON
                  </Link>
                  
                  <Link 
                    href={`/api/projects/${projectId}/poms/${pom.id}/csv`}
                    className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-9 px-4 py-2"
                  >
                    <FileSpreadsheet className="mr-2 h-4 w-4" />
                    Export as CSV
                  </Link>
                  
                  <Button
                    onClick={() => handleGenerateTests(pom.id)}
                    disabled={loading}
                  >
                    <FileCode className="mr-2 h-4 w-4" />
                    Generate Tests
                  </Button>
                </div>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      ) : (
        <div className="bg-muted p-8 rounded-lg text-center">
          <p className="text-muted-foreground mb-4">
            No Page Object Models generated yet. Click the "Generate POM" button to create page objects from your UI elements.
          </p>
          <Button 
            onClick={handleGeneratePom}
            disabled={elementCount === 0 || loading}
          >
            <Layers className="mr-2 h-4 w-4" />
            Generate POM
          </Button>
        </div>
      )}
    </div>
  );
}