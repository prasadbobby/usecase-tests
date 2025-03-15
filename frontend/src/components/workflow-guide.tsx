// src/components/workflow-guide.tsx
import { useState, useEffect } from 'react';
import { Upload, Search, Layers, Code, Play, Info, Check, X } from 'lucide-react';
import { usePathname } from 'next/navigation';
import { 
  getProjectElements, 
  getProjectPoms, 
  getProjectTests, 
  getProjectExecutions 
} from '@/lib/api';

export function WorkflowGuide() {
  const pathname = usePathname();
  const [activeStep, setActiveStep] = useState(1);
  const [elementsGenerated, setElementsGenerated] = useState(false);
  const [pomGenerated, setPomGenerated] = useState(false);
  const [testsGenerated, setTestsGenerated] = useState(false);
  const [executionsCompleted, setExecutionsCompleted] = useState(false);
  const [executionsSuccess, setExecutionsSuccess] = useState(false);
  const [loading, setLoading] = useState(true);

  const projectId = pathname.split('/')[2]; // Get project ID from URL

  // Determine the active step based on the current path
  useEffect(() => {
    if (pathname.includes('/elements')) {
      setActiveStep(2);
    } else if (pathname.includes('/pom')) {
      setActiveStep(3);
    } else if (pathname.includes('/tests')) {
      setActiveStep(4);
    } else if (pathname.includes('/executions')) {
      setActiveStep(5);
    } else {
      setActiveStep(1);
    }
  }, [pathname]);

  // Check project status
  useEffect(() => {
    if (!projectId) return;
    
    const checkProjectStatus = async () => {
      try {
        setLoading(true);
        // Check elements
        const elements = await getProjectElements(projectId);
        setElementsGenerated(elements && elements.length > 0);
        
        // Check POMs
        const poms = await getProjectPoms(projectId);
        setPomGenerated(poms && poms.length > 0);
        
        // Check tests
        const tests = await getProjectTests(projectId);
        setTestsGenerated(tests && tests.length > 0);
        
        // Check executions
        const executions = await getProjectExecutions(projectId);
        if (executions && executions.length > 0) {
          setExecutionsCompleted(true);
          // Check if any successful executions
          const successfulExecution = executions.some(exec => exec.status === 'SUCCESS');
          setExecutionsSuccess(successfulExecution);
        }
      } catch (error) {
        console.error('Error checking project status:', error);
      } finally {
        setLoading(false);
      }
    };
    
    checkProjectStatus();
  }, [projectId, pathname]);

  return (
    <div className="border rounded-lg shadow-sm overflow-hidden">
      <div className="purple-gradient p-4">
        <h3 className="text-lg font-semibold flex items-center">
          <Info className="mr-2 h-5 w-5" />
          Workflow Guide
        </h3>
      </div>
      <div className="p-4">
        <div className="space-y-6">
          <WorkflowStep
            number={1}
            title="Upload Source Code"
            description="Upload your UI source code files"
            icon={<Upload className="h-4 w-4" />}
            isActive={activeStep >= 1}
            isCompleted={true} // Always completed since project exists
            status="success"
          />
          
          <WorkflowStep
            number={2}
            title="Scan UI Elements"
            description="Extract interactive elements from source"
            icon={<Search className="h-4 w-4" />}
            isActive={activeStep >= 2}
            isCompleted={elementsGenerated}
            status={elementsGenerated ? "success" : activeStep > 2 ? "error" : "pending"}
            loading={loading && activeStep === 2}
          />
          
          <WorkflowStep
            number={3}
            title="Generate POM"
            description="Create Page Object Models"
            icon={<Layers className="h-4 w-4" />}
            isActive={activeStep >= 3}
            isCompleted={pomGenerated}
            status={pomGenerated ? "success" : activeStep > 3 ? "error" : "pending"}
            loading={loading && activeStep === 3}
          />
          
          <WorkflowStep
            number={4}
            title="Generate Tests"
            description="Create test scripts using Gemini AI"
            icon={<Code className="h-4 w-4" />}
            isActive={activeStep >= 4}
            isCompleted={testsGenerated}
            status={testsGenerated ? "success" : activeStep > 4 ? "error" : "pending"}
            loading={loading && activeStep === 4}
          />
          
          <WorkflowStep
            number={5}
            title="Execute Tests"
            description="Run tests and view results"
            icon={<Play className="h-4 w-4" />}
            isActive={activeStep >= 5}
            isCompleted={executionsCompleted}
            status={
              executionsCompleted 
                ? executionsSuccess ? "success" : "error" 
                : "pending"
            }
            loading={loading && activeStep === 5}
            isLast
          />
        </div>
      </div>
    </div>
  );
}

interface WorkflowStepProps {
  number: number;
  title: string;
  description: string;
  icon: React.ReactNode;
  isActive: boolean;
  isCompleted: boolean;
  status: "success" | "error" | "pending";
  loading?: boolean;
  isLast?: boolean;
}

function WorkflowStep({ 
  number, 
  title, 
  description, 
  icon, 
  isActive, 
  isCompleted, 
  status,
  loading = false,
  isLast = false 
}: WorkflowStepProps) {
  return (
    <div className="relative">
      {!isLast && (
        <div 
          className={`absolute left-5 top-10 w-[2px] h-[calc(100%-20px)] transition-all duration-500 ${
            isActive 
              ? status === "success" 
                ? "bg-green-500" 
                : status === "error" 
                  ? "bg-red-500" 
                  : "bg-[#8626c3]" 
              : "bg-gray-200"
          }`}
        />
      )}
      <div className="flex">
        <div 
          className={`flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-full z-10 transition-all duration-500 ${
            isActive 
              ? isCompleted 
                ? status === "success" 
                  ? "bg-green-500 text-white" 
                  : "bg-red-500 text-white" 
                : "bg-[#8626c3] text-white ring-4 ring-[#8626c3]/20" 
              : "bg-gray-200 text-gray-500"
          } ${loading ? "animate-pulse" : ""}`}
        >
          {isCompleted ? (
            status === "success" ? (
              <Check className="h-5 w-5" />
            ) : (
              <X className="h-5 w-5" />
            )
          ) : (
            number
          )}
        </div>
        <div className={isActive ? "opacity-100" : "opacity-70"}>
          <h3 className={`font-medium flex items-center ${
            isActive 
              ? status === "success" 
                ? "text-green-600" 
                : status === "error" 
                  ? "text-red-600" 
                  : "text-[#8626c3]" 
              : "text-gray-500"
          }`}>
            {icon} <span className="ml-2">{title}</span>
          </h3>
          <p className={`text-sm ${isActive ? "text-gray-700" : "text-gray-400"}`}>{description}</p>
        </div>
      </div>
    </div>
  );
}