'use client';

import { useEffect, useState } from 'react';
import { 
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger
} from '@/components/ui/accordion';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Table, 
  TableHeader, 
  TableBody, 
  TableHead, 
  TableRow, 
  TableCell 
} from '@/components/ui/table';
import { ProjectHeader } from '@/components/project-header';
import { fetchProject, getProjectExecutions, getProjectTests } from '@/lib/api';
import { Project, Execution, TestCase } from '@/types';
import { toast } from 'sonner';
import { FileText, Download } from 'lucide-react';
import Link from 'next/link';

export default function ExecutionsPage({ params }: { params: { projectId: string } }) {
  const [project, setProject] = useState<Project | null>(null);
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [testCases, setTestCases] = useState<Record<string, TestCase>>({});
  const { projectId } = params;

  useEffect(() => {
    const fetchData = async () => {
      try {
        const projectData = await fetchProject(projectId);
        setProject(projectData);

        const executionsData = await getProjectExecutions(projectId);
        setExecutions(executionsData);

        const testsData = await getProjectTests(projectId);
        const testsMap: Record<string, TestCase> = {};
        testsData.forEach(test => {
          testsMap[test.id] = test;
        });
        setTestCases(testsMap);
      } catch (error) {
        console.error('Error fetching data:', error);
        toast.error('Failed to load data');
      }
    };

    fetchData();
  }, [projectId]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'SUCCESS':
      case 'PASSED':
        return 'bg-green-100 text-green-800';
      case 'FAILURE':
      case 'FAILED':
      case 'ERROR':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-yellow-100 text-yellow-800';
    }
  };

  if (!project) {
    return <div className="flex items-center justify-center h-full">Loading project...</div>;
  }

  return (
    <div className="space-y-6">
      <ProjectHeader project={project} />

      <h2 className="text-2xl font-bold mb-4">Test Executions ({executions.length})</h2>

      {executions.length > 0 ? (
        <Accordion type="single" collapsible className="space-y-4">
          {executions.map((execution, index) => (
            <AccordionItem 
              key={execution.id} 
              value={execution.id}
              className="border rounded-lg overflow-hidden shadow-sm"
            >
              <AccordionTrigger className="px-4 py-2 hover:no-underline hover:bg-muted">
                <div className="flex justify-between items-center w-full pr-4">
                  <div className="flex items-center">
                    <span className="font-medium">Execution #{executions.length - index}</span>
                    <Badge className={`ml-3 ${getStatusColor(execution.status)}`}>
                      {execution.status}
                    </Badge>
                  </div>
                  <span className="text-sm text-muted-foreground">
                    {new Date(execution.executed_at).toLocaleString()}
                  </span>
                </div>
              </AccordionTrigger>
              <AccordionContent className="px-4 py-3">
                <div className="mb-4">
                  <p>
                    <strong>Test:</strong> {testCases[execution.test_id]?.name || 'Unknown Test'}
                  </p>
                  <p>
                    <strong>Executed:</strong> {new Date(execution.executed_at).toLocaleString()}
                  </p>
                </div>

                <div className="space-y-4">
                  <div>
                    <h4 className="font-medium mb-2">Execution Log:</h4>
                    <div className="bg-muted p-3 rounded-md max-h-64 overflow-auto">
                      <pre className="text-xs whitespace-pre-wrap">
                        <code>{execution.result.log}</code>
                      </pre>
                    </div>
                  </div>

                  {execution.result.tests && execution.result.tests.length > 0 && (
                    <div>
                      <h4 className="font-medium mb-2">Test Results:</h4>
                      <Table>
                        <TableHeader>
                          <TableRow className="bg-muted/50">
                            <TableHead>Test</TableHead>
                            <TableHead>Status</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {execution.result.tests.map((result, i) => (
                            <TableRow key={i}>
                              <TableCell>{result.name}</TableCell>
                              <TableCell>
                                <Badge className={getStatusColor(result.status)}>
                                  {result.status}
                                </Badge>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  )}

                  <div className="flex justify-end">
                    <Link 
                      href={`/api/download/${encodeURIComponent(execution.log_path)}`}
                      className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-9 px-4 py-2"
                    >
                      <Download className="mr-2 h-4 w-4" />
                      Download Complete Log
                    </Link>
                  </div>
                </div>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      ) : (
        <div className="bg-muted p-8 rounded-lg text-center">
          <p className="text-muted-foreground">
            No test executions yet. Go to the "Tests" tab to execute your test cases.
          </p>
          <Link 
            href={`/dashboard/${projectId}/tests`}
            className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-9 px-4 py-2 mt-4"
          >
            <FileText className="mr-2 h-4 w-4" />
            Go to Tests
          </Link>
        </div>
      )}
    </div>
  );
}