'use client';

import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardContent, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ProjectHeader } from '@/components/project-header';
import { 
  fetchProject, 
  getProjectTests, 
  getProjectPoms, 
  generateTests, 
  executeTest,
  getTestCode 
} from '@/lib/api';
import { Project, TestCase, Pom } from '@/types';
import { toast } from 'sonner';
import { FileCode, Play, Code, Download } from 'lucide-react';
import Link from 'next/link';

export default function TestsPage({ params }: { params: { projectId: string } }) {
  const [project, setProject] = useState<Project | null>(null);
  const [tests, setTests] = useState<TestCase[]>([]);
  const [poms, setPoms] = useState<Pom[]>([]);
  const [testCode, setTestCode] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [executingTest, setExecutingTest] = useState<string | null>(null);
  const { projectId } = params;

  useEffect(() => {
    const fetchData = async () => {
      try {
        const projectData = await fetchProject(projectId);
        setProject(projectData);

        const testsData = await getProjectTests(projectId);
        setTests(testsData);

        const pomsData = await getProjectPoms(projectId);
        setPoms(pomsData);
      } catch (error) {
        console.error('Error fetching data:', error);
        toast.error('Failed to load data');
      }
    };

    fetchData();
  }, [projectId]);

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

  const handleExecuteTest = async (testId: string) => {
    setExecutingTest(testId);
    try {
      await executeTest(projectId, testId);
      toast.success('Test execution started');
    } catch (error) {
      console.error('Error executing test:', error);
      toast.error('Failed to execute test');
    } finally {
      setExecutingTest(null);
    }
  };

  const handleViewCode = async (testId: string) => {
    if (testCode[testId]) {
      // Already loaded
      return;
    }
    
    try {
      const response = await getTestCode(testId);
      setTestCode(prev => ({
        ...prev,
        [testId]: response.code
      }));
    } catch (error) {
      console.error('Error fetching test code:', error);
      toast.error('Failed to load test code');
    }
  };

  if (!project) {
    return <div className="flex items-center justify-center h-full">Loading project...</div>;
  }

  return (
    <div className="space-y-6">
      <ProjectHeader project={project} />

      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">Test Cases ({tests.length})</h2>
        <div className="flex space-x-2">
          <Button 
            onClick={handleGenerateTests}
            disabled={poms.length === 0 || loading}
          >
            <FileCode className="mr-2 h-4 w-4" />
            Generate Tests
          </Button>
          {tests.length > 0 && (
            <Link 
              href={`/api/projects/${projectId}/tests/download`}
              className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-9 px-4 py-2"
            >
              <Download className="mr-2 h-4 w-4" />
              Download All Tests
            </Link>
          )}
        </div>
      </div>

      {tests.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {tests.map((test) => (
            <Card key={test.id} className="overflow-hidden shadow-sm">
              <CardHeader className="bg-muted p-4">
                <div className="flex justify-between items-start">
                  <h3 className="font-medium">{test.name}</h3>
                  <Badge variant="outline">
                    {new Date(test.created_at).toLocaleDateString()}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="p-4">
                <p className="text-sm text-muted-foreground">
                  {test.description}
                </p>
                
                {testCode[test.id] && (
                  <div className="mt-4 bg-muted p-3 rounded-md max-h-48 overflow-auto">
                    <pre className="text-xs">
                      <code>{testCode[test.id]}</code>
                    </pre>
                  </div>
                )}
              </CardContent>
              <CardFooter className="p-4 pt-0 flex justify-between">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => handleViewCode(test.id)}
                >
                  <Code className="mr-2 h-4 w-4" />
                  {testCode[test.id] ? 'Hide Code' : 'View Code'}
                </Button>
                <Button 
                  size="sm"
                  onClick={() => handleExecuteTest(test.id)}
                  disabled={executingTest === test.id}
                >
                  <Play className="mr-2 h-4 w-4" />
                  {executingTest === test.id ? 'Executing...' : 'Execute Test'}
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      ) : (
        <div className="bg-muted p-8 rounded-lg text-center">
          <p className="text-muted-foreground mb-4">
            No test cases generated yet. Click the "Generate Tests" button to create tests based on your Page Object Model.
          </p>
          <Button 
            onClick={handleGenerateTests}
            disabled={poms.length === 0 || loading}
          >
            <FileCode className="mr-2 h-4 w-4" />
            Generate Tests
          </Button>
        </div>
      )}
    </div>
  );
}