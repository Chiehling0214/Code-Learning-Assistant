import { useParams } from "react-router-dom";

import { PagePlaceholder } from "@/components/PagePlaceholder";

export function LessonPage() {
  const { id } = useParams<{ id: string }>();
  return (
    <PagePlaceholder
      title="Lesson"
      description={`AI-taught lesson content${id ? ` (id: ${id})` : ""}.`}
      sprint={2}
    />
  );
}
