import Editor from "@monaco-editor/react";
import { useState } from "react";
import { useParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const STARTER_CODE = `# Coding exercise editor
# Code execution via Judge0 arrives in Sprint 2.

def solution():
    return "Hello, CodePath!"


print(solution())
`;

export function CodingExercisePage() {
  const { id } = useParams<{ id: string }>();
  const [code, setCode] = useState(STARTER_CODE);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Coding Exercise</h1>
          <p className="text-muted-foreground">{id ? `Exercise ${id}` : "Practice editor"}</p>
        </div>
        {/* Execution is wired in Sprint 2 (Judge0); the button stays disabled until then. */}
        <Button disabled title="Code execution arrives in Sprint 2">
          Run (Sprint 2)
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Editor</CardTitle>
          <CardDescription>Monaco editor mounted and ready.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-hidden rounded-md border">
            <Editor
              height="420px"
              defaultLanguage="python"
              theme="vs-dark"
              value={code}
              onChange={(value) => setCode(value ?? "")}
              options={{ minimap: { enabled: false }, fontSize: 14 }}
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
