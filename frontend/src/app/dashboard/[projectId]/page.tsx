// src/app/dashboard/[projectId]/page.tsx
'use client';

import { useEffect, useState } from 'react';
import { ProjectHeader } from '@/components/project-header';
import { ProjectStats } from '@/components/project-stats';
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import { 
  fetchProject, 
  getProjectElements, 
  getProjectPoms, 
  getProjectTests, 
  getProjectExecutions,
  scanProject,
  generatePom,
  generateTests
} from '@/lib/api';
import { Project, Element, Pom, TestCase, Execution } from '@/types';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { FileCode, Download, Code, Clock } from 'lucide-react';

export default function ProjectDashboard({ params }: { params: { projectId: string } }) {
  const [project, setProject] = useState<Project | null>(null);
  const [elements, setElements] = useState<Element[]>([]);
  const [poms, setPoms] = useState<Pom[]>([]);
  const [tests, setTests] = useState<TestCase[]>([]);
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const { projectId } = params;

  useEffect(() => {
    const fetchData = async () => {
      try {
        const projectData = await fetchProject(projectId);
        setProject(projectData);

        const elementsData = await getProjectElements(projectId);
        setElements(elementsData);

        const pomsData = await getProjectPoms(projectId);
        setPoms(pomsData);

        const testsData = await getProjectTests(projectId);
        setTests(testsData);

        const executionsData = await getProjectExecutions(projectId);
        setExecutions(executionsData);
     // src/app/dashboard/[projectId]/page.tsx (continued)
    } catch (error) {
      console.error('Error fetching project data:', error);
      toast.error('Failed to load project data');
    }
  };

  fetchData();
}, [projectId]);

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

const handleGenerateTests = async () => {
  if (!poms.length) return;
  
  setLoading(true);
  try {
    await generateTests(projectId, poms[0].id);
    const testsData = await getProjectTests(projectId);
    setTests(testsData);
    toast.success('Test cases generated successfully');
  } catch (error) {
    console.error('Error generating tests:', error);
    toast.error('Failed to generate test cases');
  } finally {
    setLoading(false);
  }
};

if (!project) {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-pulse flex flex-col items-center">
        <div className="h-12 w-12 bg-primary/30 rounded-full mb-4"></div>
        <div className="h-4 w-48 bg-primary/30 rounded mb-2"></div>
        <div className="h-3 w-32 bg-primary/20 rounded"></div>
      </div>
    </div>
  );
}

return (
  <div className="space-y-6">
    <ProjectHeader project={project} />

    <ProjectStats
      elementCount={elements.length}
      pomCount={poms.length}
      testCount={tests.length}
      onScanElements={handleScanElements}
      onGeneratePom={handleGeneratePom}
      onGenerateTests={handleGenerateTests}
      loading={loading}
    />

    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <Card className="shadow-md border-2 border-primary/10 hover-lift">
        <CardHeader className="bg-primary/10 rounded-t-lg">
          <CardTitle className="text-lg flex items-center">
            <FileCode className="mr-2 h-5 w-5 text-primary" />
            Recent Tests
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-4">
          {tests.length > 0 ? (
            <div className="space-y-3">
              {tests.slice(0, 3).map((test) => (
                <div key={test.id} className="p-3 border border-primary/10 rounded-lg bg-white shadow-sm hover:shadow-md transition-shadow">
                  <div className="flex justify-between">
                    <h3 className="font-medium text-primary">{test.name}</h3>
                    <span className="text-xs text-muted-foreground">
                      {new Date(test.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground mt-1">{test.description}</p>
                  <Link 
                    href={`/api/tests/${test.id}/code`} 
                    target="_blank"
                    className="inline-flex items-center mt-2 text-sm text-primary hover:underline"
                  >
                    <Code className="h-4 w-4 mr-1" />
                    View Code
                  </Link>
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-muted/30 p-6 rounded-lg text-center">
              <p className="text-muted-foreground">No test cases generated yet.</p>
            </div>
          )}
        </CardContent>
        {tests.length > 0 && (
          <CardFooter className="bg-gray-50 rounded-b-lg border-t">
            <Button 
              variant="outline" 
              className="w-full" 
              onClick={() => router.push(`/dashboard/${projectId}/tests`)}
            >
              View All Tests
            </Button>
          </CardFooter>
        )}
      </Card>

      <Card className="shadow-md border-2 border-primary/10 hover-lift">
        <CardHeader className="bg-primary/10 rounded-t-lg">
          <CardTitle className="text-lg flex items-center">
            <Clock className="mr-2 h-5 w-5 text-primary" />
            Recent Executions
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-4">
          {executions.length > 0 ? (
            <div className="space-y-3">
              {executions.slice(0, 3).map((execution) => (
                <div key={execution.id} className="p-3 border border-primary/10 rounded-lg bg-white shadow-sm hover:shadow-md transition-shadow">
                  <div className="flex justify-between items-center">
                    <h3 className="font-medium text-primary">Test Execution</h3>
                    <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                      execution.status === 'SUCCESS' 
                        ? 'bg-green-100 text-green-800' 
                        : execution.status === 'FAILURE' 
                        ? 'bg-red-100 text-red-800' 
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {execution.status}
                    </div>
                  </div>
                  <p className="text-sm text-muted-foreground mt-1">
                    Executed: {new Date(execution.executed_at).toLocaleString()}
                  </p>
                  <Link 
                    href={`/api/download/${encodeURIComponent(execution.log_path)}`}
                    className="inline-flex items-center mt-2 text-sm text-primary hover:underline"
                  >
                    <Download className="h-4 w-4 mr-1" />
                    Download Log
                  </Link>
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-muted/30 p-6 rounded-lg text-center">
              <p className="text-muted-foreground">No test executions yet.</p>
            </div>
          )}
        </CardContent>
        {executions.length > 0 && (
          <CardFooter className="bg-gray-50 rounded-b-lg border-t">
            <Button 
              variant="outline" 
              className="w-full" 
              onClick={() => router.push(`/dashboard/${projectId}/executions`)}
            >
              View All Executions
            </Button>
          </CardFooter>
        )}
      </Card>
    </div>
  </div>
);
}