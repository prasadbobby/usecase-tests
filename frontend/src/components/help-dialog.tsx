import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
    DialogFooter,
  } from '@/components/ui/dialog';
  import { Button } from '@/components/ui/button';
  import { Alert, AlertDescription } from '@/components/ui/alert';
  import { InfoIcon } from 'lucide-react';
  
  interface HelpDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
  }
  
  export function HelpDialog({ open, onOpenChange }: HelpDialogProps) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle className="text-xl">Help & Documentation</DialogTitle>
            <DialogDescription>
              Learn how to use the UI Test Generator effectively
            </DialogDescription>
          </DialogHeader>
          
          <div className="py-4 space-y-6">
            <div>
              <h3 className="text-lg font-semibold mb-2">How to Use UI Test Generator</h3>
              <p className="text-muted-foreground">
                This tool helps you automatically generate test cases from your UI source code using AI assistance.
              </p>
            </div>
  
            <div>
              <h4 className="text-md font-semibold mb-2">1. Create a Project</h4>
              <p className="text-muted-foreground mb-2">
                Start by creating a new project and uploading your UI source code. You can upload individual
                HTML, JSX, TSX, or Vue files, or a ZIP archive containing multiple files.
              </p>
            </div>
  
            <div>
              <h4 className="text-md font-semibold mb-2">2. Scan UI Elements</h4>
              <p className="text-muted-foreground mb-2">
                Once your project is created, go to the dashboard and click "Scan UI Elements" to analyze your
                source code. The scanner will identify interactive elements like buttons, inputs, links, and forms.
              </p>
            </div>
  
            <div>
              <h4 className="text-md font-semibold mb-2">3. Generate Page Object Model (POM)</h4>
              <p className="text-muted-foreground mb-2">
                After scanning, click "Generate POM" to create a structured representation of your UI elements.
                This will group elements by page and create appropriate selectors for each element.
              </p>
            </div>
  
            <div>
              <h4 className="text-md font-semibold mb-2">4. Generate Test Cases</h4>
              <p className="text-muted-foreground mb-2">
                With the POM in place, click "Generate Tests" to create Python test scripts using Selenium WebDriver.
                The Gemini 1.5 Flash API is used to intelligently design test cases based on your UI components.
              </p>
            </div>
  
            <div>
              <h4 className="text-md font-semibold mb-2">5. Execute Tests</h4>
              <p className="text-muted-foreground mb-2">
                Finally, you can execute the generated tests and view the results. The system will show you
                which tests passed or failed, and provide detailed logs for debugging.
              </p>
            </div>
            
            <Alert>
              <InfoIcon className="h-4 w-4 mr-2" />
              <AlertDescription>
                For test execution to work properly, make sure you have Chrome and the appropriate
                WebDriver installed on your system. The tests use the webdriver-manager package to handle
                WebDriver installation.
              </AlertDescription>
            </Alert>
          </div>
          
          <DialogFooter>
            <Button onClick={() => onOpenChange(false)}>Got it!</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    );
  }