import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  useCourse,
  useCourses,
  useCreateCourse,
  useCreateLanguage,
  useCreateLesson,
  useDeleteCourse,
  useDeleteLanguage,
  useDeleteLesson,
  useLanguages,
} from "@/features/content/hooks";
import { useSessionStore } from "@/store/session";

const inputClass =
  "flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring";

function ErrorText({ error }: { error: unknown }) {
  if (!error) return null;
  const message = error instanceof Error ? error.message : "Request failed";
  return <p className="text-sm text-destructive">{message}</p>;
}

function LanguagesSection() {
  const { data: languages = [] } = useLanguages();
  const create = useCreateLanguage();
  const remove = useDeleteLanguage();
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Languages</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <ul className="space-y-1">
          {languages.map((lang) => (
            <li key={lang.id} className="flex items-center justify-between text-sm">
              <span>
                {lang.name} <span className="text-muted-foreground">({lang.slug})</span>
              </span>
              <Button variant="ghost" size="sm" onClick={() => remove.mutate(lang.id)}>
                Delete
              </Button>
            </li>
          ))}
          {languages.length === 0 && <li className="text-sm text-muted-foreground">None yet.</li>}
        </ul>
        <form
          className="flex gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            create.mutate(
              { name, slug },
              {
                onSuccess: () => {
                  setName("");
                  setSlug("");
                },
              },
            );
          }}
        >
          <input className={inputClass} placeholder="Name" value={name} required
            onChange={(e) => setName(e.target.value)} />
          <input className={inputClass} placeholder="slug" value={slug} required
            onChange={(e) => setSlug(e.target.value)} />
          <Button type="submit" size="sm" disabled={create.isPending}>
            Add
          </Button>
        </form>
        <ErrorText error={create.error || remove.error} />
      </CardContent>
    </Card>
  );
}

function CoursesSection() {
  const { data: languages = [] } = useLanguages();
  const { data: courses = [] } = useCourses();
  const create = useCreateCourse();
  const remove = useDeleteCourse();
  const [languageId, setLanguageId] = useState("");
  const [title, setTitle] = useState("");
  const [slug, setSlug] = useState("");
  const [description, setDescription] = useState("");

  useEffect(() => {
    if (!languageId && languages.length) setLanguageId(languages[0].id);
  }, [languages, languageId]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Courses</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <ul className="space-y-1">
          {courses.map((course) => (
            <li key={course.id} className="flex items-center justify-between text-sm">
              <span>
                {course.title} <span className="text-muted-foreground">({course.slug})</span>
              </span>
              <Button variant="ghost" size="sm" onClick={() => remove.mutate(course.id)}>
                Delete
              </Button>
            </li>
          ))}
          {courses.length === 0 && <li className="text-sm text-muted-foreground">None yet.</li>}
        </ul>
        <form
          className="grid grid-cols-2 gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            create.mutate(
              { language_id: languageId, title, slug, description: description || null },
              { onSuccess: () => { setTitle(""); setSlug(""); setDescription(""); } },
            );
          }}
        >
          <select className={inputClass} value={languageId} onChange={(e) => setLanguageId(e.target.value)}>
            {languages.map((lang) => (
              <option key={lang.id} value={lang.id}>{lang.name}</option>
            ))}
          </select>
          <input className={inputClass} placeholder="Title" value={title} required
            onChange={(e) => setTitle(e.target.value)} />
          <input className={inputClass} placeholder="slug" value={slug} required
            onChange={(e) => setSlug(e.target.value)} />
          <input className={inputClass} placeholder="Description" value={description}
            onChange={(e) => setDescription(e.target.value)} />
          <Button type="submit" size="sm" disabled={create.isPending || !languageId}>
            Add course
          </Button>
        </form>
        <ErrorText error={create.error || remove.error} />
      </CardContent>
    </Card>
  );
}

function LessonsSection() {
  const { data: courses = [] } = useCourses();
  const [courseSlug, setCourseSlug] = useState<string>("");

  useEffect(() => {
    if (!courseSlug && courses.length) setCourseSlug(courses[0].slug);
  }, [courses, courseSlug]);

  const { data: course } = useCourse(courseSlug || undefined);
  const create = useCreateLesson(courseSlug || undefined);
  const remove = useDeleteLesson(courseSlug || undefined);
  const [title, setTitle] = useState("");
  const [slug, setSlug] = useState("");
  const [orderIndex, setOrderIndex] = useState("0");
  const [content, setContent] = useState("");

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Lessons</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <select className={inputClass} value={courseSlug} onChange={(e) => setCourseSlug(e.target.value)}>
          {courses.map((c) => (
            <option key={c.id} value={c.slug}>{c.title}</option>
          ))}
        </select>

        <ul className="space-y-1">
          {course?.lessons.map((lesson) => (
            <li key={lesson.id} className="flex items-center justify-between text-sm">
              <span>
                {lesson.order_index}. {lesson.title}
              </span>
              <Button variant="ghost" size="sm" onClick={() => remove.mutate(lesson.id)}>
                Delete
              </Button>
            </li>
          ))}
          {course && course.lessons.length === 0 && (
            <li className="text-sm text-muted-foreground">No lessons in this course.</li>
          )}
        </ul>

        <form
          className="grid grid-cols-2 gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            if (!course) return;
            create.mutate(
              {
                course_id: course.id,
                title,
                slug,
                order_index: Number(orderIndex) || 0,
                content,
              },
              { onSuccess: () => { setTitle(""); setSlug(""); setOrderIndex("0"); setContent(""); } },
            );
          }}
        >
          <input className={inputClass} placeholder="Title" value={title} required
            onChange={(e) => setTitle(e.target.value)} />
          <input className={inputClass} placeholder="slug" value={slug} required
            onChange={(e) => setSlug(e.target.value)} />
          <input className={inputClass} type="number" placeholder="Order" value={orderIndex}
            onChange={(e) => setOrderIndex(e.target.value)} />
          <input className={inputClass} placeholder="Content (markdown)" value={content}
            onChange={(e) => setContent(e.target.value)} />
          <Button type="submit" size="sm" disabled={create.isPending || !course} className="col-span-2">
            Add lesson
          </Button>
        </form>
        <ErrorText error={create.error || remove.error} />
      </CardContent>
    </Card>
  );
}

export function AdminPage() {
  const user = useSessionStore((s) => s.user);

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Admin</h1>
        <p className="text-muted-foreground">Manage languages, courses, and lessons.</p>
      </div>

      {!user?.isAdmin && (
        <Card className="border-amber-500/40">
          <CardContent className="py-4 text-sm text-muted-foreground">
            Your account is not an admin, so write actions will return 403. Grant admin with{" "}
            <code className="rounded bg-muted px-1">python -m scripts.set_admin {user?.email}</code>{" "}
            in the backend container, then sign out and back in.
          </CardContent>
        </Card>
      )}

      <LanguagesSection />
      <CoursesSection />
      <LessonsSection />
    </div>
  );
}
