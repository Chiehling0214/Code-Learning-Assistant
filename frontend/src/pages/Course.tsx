import { useParams } from "react-router-dom";

import { PagePlaceholder } from "@/components/PagePlaceholder";

export function CoursePage() {
  const { slug } = useParams<{ slug: string }>();
  return (
    <PagePlaceholder
      title="Course"
      description={`Course overview${slug ? ` for "${slug}"` : ""} and its lessons.`}
      sprint={1}
    />
  );
}
