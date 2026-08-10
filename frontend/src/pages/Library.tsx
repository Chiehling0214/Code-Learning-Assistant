import { BookOpen, Search } from "lucide-react";
import { useMemo, useState } from "react";

import { CourseCard } from "@/components/CourseCard";
import { SkeletonCards } from "@/components/Skeleton";
import { Card, CardContent } from "@/components/ui/card";
import { useLanguages } from "@/features/content/hooks";
import { useMyCourses } from "@/features/curriculum/hooks";
import { useProgress } from "@/features/progress/hooks";

type StatusFilter = "all" | "not-started" | "in-progress" | "completed";
type SortOption = "recent" | "progress" | "name";

const fieldClass =
  "h-10 rounded-lg border border-input bg-card px-3 text-sm outline-none transition-colors focus:border-primary/40 focus:ring-2 focus:ring-primary/10";

export function LibraryPage() {
  const { data: courses = [], isLoading } = useMyCourses();
  const { data: progress } = useProgress();
  const { data: languages = [] } = useLanguages();
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<StatusFilter>("all");
  const [languageId, setLanguageId] = useState("all");
  const [sort, setSort] = useState<SortOption>("recent");

  const progressByCourse = useMemo(
    () => new Map(progress?.courses.map((item) => [item.course_id, item])),
    [progress?.courses],
  );
  const languageById = useMemo(
    () => new Map(languages.map((language) => [language.id, language.name])),
    [languages],
  );

  const filteredCourses = useMemo(() => {
    const normalizedQuery = query.trim().toLocaleLowerCase();
    const result = courses.filter((course) => {
      const courseProgress = progressByCourse.get(course.id);
      const percent = courseProgress?.percent ?? 0;
      const matchesQuery =
        !normalizedQuery ||
        course.title.toLocaleLowerCase().includes(normalizedQuery) ||
        course.description?.toLocaleLowerCase().includes(normalizedQuery) ||
        languageById.get(course.language_id)?.toLocaleLowerCase().includes(normalizedQuery);
      const matchesLanguage = languageId === "all" || course.language_id === languageId;
      const matchesStatus =
        status === "all" ||
        (status === "not-started" && percent === 0) ||
        (status === "in-progress" && percent > 0 && percent < 100) ||
        (status === "completed" && percent === 100);
      return matchesQuery && matchesLanguage && matchesStatus;
    });

    return result.sort((left, right) => {
      if (sort === "name") return left.title.localeCompare(right.title);
      if (sort === "progress") {
        return (progressByCourse.get(right.id)?.percent ?? 0) -
          (progressByCourse.get(left.id)?.percent ?? 0);
      }
      const resumeId = progress?.resume?.course_id;
      return Number(right.id === resumeId) - Number(left.id === resumeId);
    });
  }, [courses, languageById, languageId, progress?.resume?.course_id, progressByCourse, query, sort, status]);

  return (
    <div className="space-y-8">
      <header>
        <p className="page-kicker">Library</p>
        <h1 className="page-heading">All courses</h1>
        <p className="mt-2 text-muted-foreground">
          Browse full course outlines or continue from the next unfinished item.
        </p>
      </header>

      <Card>
        <CardContent className="grid gap-3 py-5 md:grid-cols-[minmax(15rem,1fr)_repeat(3,minmax(9rem,auto))]">
          <label className="relative">
            <span className="sr-only">Search courses</span>
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search courses or languages"
              className={`${fieldClass} w-full pl-9`}
            />
          </label>
          <select value={languageId} onChange={(event) => setLanguageId(event.target.value)} className={fieldClass} aria-label="Filter by language">
            <option value="all">All languages</option>
            {languages.map((language) => <option key={language.id} value={language.id}>{language.name}</option>)}
          </select>
          <select value={status} onChange={(event) => setStatus(event.target.value as StatusFilter)} className={fieldClass} aria-label="Filter by status">
            <option value="all">All statuses</option>
            <option value="not-started">Not started</option>
            <option value="in-progress">In progress</option>
            <option value="completed">Completed</option>
          </select>
          <select value={sort} onChange={(event) => setSort(event.target.value as SortOption)} className={fieldClass} aria-label="Sort courses">
            <option value="recent">Recently learned</option>
            <option value="progress">Highest progress</option>
            <option value="name">Course name</option>
          </select>
        </CardContent>
      </Card>

      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">{filteredCourses.length} courses</p>
      </div>

      {isLoading ? (
        <SkeletonCards count={6} />
      ) : filteredCourses.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center py-12 text-center">
            <BookOpen className="mb-3 size-6 text-muted-foreground" />
            <p className="font-medium">No matching courses</p>
            <p className="mt-1 text-sm text-muted-foreground">Try changing the search or filters.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {filteredCourses.map((course, index) => (
            <CourseCard
              key={course.id}
              course={course}
              courseProgress={progressByCourse.get(course.id)}
              index={index}
              language={languageById.get(course.language_id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
