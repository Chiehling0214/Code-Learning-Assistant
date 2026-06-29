import { useParams } from "react-router-dom";

import { PagePlaceholder } from "@/components/PagePlaceholder";

export function QuizPage() {
  const { id } = useParams<{ id: string }>();
  return (
    <PagePlaceholder
      title="Quiz"
      description={`Knowledge check${id ? ` (id: ${id})` : ""} with scored questions.`}
      sprint={5}
    />
  );
}
