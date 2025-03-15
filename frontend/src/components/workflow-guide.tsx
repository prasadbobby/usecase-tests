// src/components/workflow-guide.tsx
import { useState, useEffect } from 'react';
import { usePathname } from 'next/navigation';
import { Upload, Search, Layers, Code, Play, Info, Check, X } from 'lucide-react';
import { 
  getProjectElements, 
  getProjectPoms, 
  getProjectTests, 
  getProjectExecutions 
} from '@/lib/api';

export function WorkflowGuide() {
  const pathname = usePathname();
  const projectId = pathname.split('/')[2]; // Extract project ID from URL
  
  const [elementsStatus, setElementsStatus] = useState({ complete: false, success: false });
  const [pomStatus, setPomStatus] = useState({ complete: false, success: false });
  const [testsStatus, setTestsStatus] = useState({ complete: false, success: false });
  const [executionsStatus, setExecutionsStatus] = useState({ complete: false, success: false });
  const [loading, setLoading] = useState(false);
  
  // Determine active step based on URL
  const getActiveStep = () => {
    if (pathname.includes('/elements')) return 2;
    if (pathname.includes('/pom')) return 3;
    if (pathname.includes('/tests')) return 4;
    if (pathname.includes('/executions')) return 5;
    return 1;
  };
  
  const activeStep = getActiveStep();
  
  // Fetch status data for the project
  useEffect(() => {
    if (!projectId) return;
    
    const fetchStatus = async () => {
      setLoading(true);
      try {
        // Check elements
        const elements = await getProjectElements(projectId);
        const hasElements = elements && elements.length > 0;
        setElementsStatus({ complete: true, success: hasElements });
        
        // Check POMs
        const poms = await getProjectPoms(projectId);
        const hasPoms = poms && poms.length > 0;
        setPomStatus({ complete: hasElements, success: hasPoms });
        
        // Check tests
        const tests = await getProjectTests(projectId);
        const hasTests = tests && tests.length > 0;
        setTestsStatus({ complete: hasPoms, success: hasTests });
        
        // Check executions
        const executions = await getProjectExecutions(projectId);
        if (executions && executions.length > 0) {
          const successfulExecution = executions.some(exec => exec.status === 'SUCCESS');
          setExecutionsStatus({ complete: true, success: successfulExecution });
        } else {
          setExecutionsStatus({ complete: false, success: false });
        }
      } catch (error) {
        console.error('Error fetching status:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchStatus();
  }, [projectId, pathname]);

  // Define steps with their statuses
  const steps = [
    { 
      id: 1, 
      title: 'Upload Source Code', 
      description: 'Upload your UI source files', 
      icon: <Upload size={16} />,
      active: activeStep >= 1,
      complete: true, // Always complete since project exists
      success: true
    },
    { 
      id: 2, 
      title: 'Scan UI Elements', 
      description: 'Extract interactive elements', 
      icon: <Search size={16} />,
      active: activeStep >= 2,
      complete: elementsStatus.complete,
      success: elementsStatus.success
    },
    { 
      id: 3, 
      title: 'Generate POM', 
      description: 'Create Page Object Models', 
      icon: <Layers size={16} />,
      active: activeStep >= 3,
      complete: pomStatus.complete,
      success: pomStatus.success
    },
    { 
      id: 4, 
      title: 'Generate Tests', 
      description: 'Create test scripts with AI', 
      icon: <Code size={16} />,
      active: activeStep >= 4,
      complete: testsStatus.complete,
      success: testsStatus.success
    },
    { 
      id: 5, 
      title: 'Execute Tests', 
      description: 'Run tests and view results', 
      icon: <Play size={16} />,
      active: activeStep >= 5,
      complete: executionsStatus.complete,
      success: executionsStatus.success
    },
  ];

  return (
    <div className="border rounded-lg overflow-hidden shadow-sm">
      <div className="purple-gradient p-3">
        <div className="flex items-center">
          <Info className="h-4 w-4 mr-2 text-white" />
          <h3 className="text-sm font-medium text-white">Workflow Guide</h3>
        </div>
      </div>
      
      <div className="p-3 bg-white">
        <div className="space-y-4">
          {steps.map((step, index) => (
            <div key={step.id} className="relative">
              {index < steps.length - 1 && (
                <div 
                  className={`absolute left-[11px] top-6 w-[2px] h-[calc(100%-12px)] ${
                    step.active 
                      ? step.complete 
                        ? step.success ? 'bg-green-500' : 'bg-red-500'
                        : 'bg-[#8626c3]' 
                      : 'bg-gray-200'
                  }`}
                />
              )}
              
              <div className="flex">
                <div 
                  className={`flex-shrink-0 flex items-center justify-center w-[22px] h-[22px] rounded-full z-10 ${
                    step.active 
                      ? step.complete 
                        ? step.success ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
                        : 'bg-[#8626c3] text-white' 
                      : 'bg-gray-200 text-gray-500'
                  } ${loading && step.id === activeStep ? 'animate-pulse' : ''}`}
                >
                  {step.complete ? (
                    step.success ? (
                      <Check size={12} />
                    ) : (
                      <X size={12} />
                    )
                  ) : (
                    <span className="text-xs">{step.id}</span>
                  )}
                </div>
                
                <div className="ml-3">
                  <div className="flex items-center">
                    {step.icon && <span className={`mr-1 ${
                      step.active 
                        ? step.complete 
                          ? step.success ? 'text-green-500' : 'text-red-500' 
                          : 'text-[#8626c3]' 
                        : 'text-gray-400'
                    }`}>{step.icon}</span>}
                    <h4 className={`text-xs font-medium ${
                      step.active 
                        ? step.complete 
                          ? step.success ? 'text-green-500' : 'text-red-500' 
                          : 'text-[#8626c3]' 
                        : 'text-gray-700'
                    }`}>
                      {step.title}
                    </h4>
                  </div>
                  <p className="text-xs text-gray-500">{step.description}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}