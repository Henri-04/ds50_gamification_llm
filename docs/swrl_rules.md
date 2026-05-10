# SWRL Rules Added to the TGC Ontology

**Last updated:** May 10, 2026  
**Ontology version:** TGC 1.0.0

## Overview

This document tracks the SWRL (Semantic Web Rule Language) rules added to `TGC_working.owl`.

- The original ontology file `TGC_original.owl` is kept unchanged
- All modifications are applied only to `TGC_working.owl`
- Rules are designed to infer new relationships based on existing semantic patterns

## Table of Contents

1. [Rule 1 — InferLessonTopicFromReusedResource](#rule-1--inferlessontopicfromreusedresource)
2. [Rule 2 — InferCourseTopicFromLesson](#rule-2--infercoursetopicfromlesson)

---

# Rule 1 — InferLessonTopicFromReusedResource

## Description

If a lesson reuses a gamified resource, and that resource has an educational topic, then the lesson covers that educational topic.

## SWRL Rule

```swrl
TCO:Lesson(?l)
^ TGC:GamifiedResource(?r)
^ TCO:reuseResource(?l, ?r)
^ TGC:EducationalTopic(?et)
^ TGC:hasEducationalTopic(?r, ?et)
-> TGC:CoversTopic(?l, ?et)
```

## Purpose

This rule propagates the educational topic from a gamified resource to the lesson that reuses it.

It extends the semantic propagation chain already present in the ontology:

```text
GameElement
→ BehaviouralObjective
→ EducationalTopic
→ GamifiedResource
→ Lesson
```

## Semantic Context

**Dependencies:**
- Requires `TCO:Lesson` class
- Requires `TGC:GamifiedResource` class
- Requires `TCO:reuseResource` object property
- Requires `TGC:EducationalTopic` class
- Requires `TGC:hasEducationalTopic` object property

**Output property:**
- `TGC:CoversTopic` — inferred property linking lessons to educational topics

## Expected Inference

### Before reasoning

```text
LessonX TCO:reuseResource ResourceY
ResourceY TGC:hasEducationalTopic TopicZ
```

### After reasoning

```text
LessonX TGC:CoversTopic TopicZ
```

---

# Rule 2 — InferCourseTopicFromLesson

## Description

If a course consists of a lesson, and that lesson covers an educational topic, then the course also has that educational topic.

## SWRL Rule

```swrl
TCO:Course(?c)
^ TCO:Lesson(?l)
^ TGC:EducationalTopic(?et)
^ TCO:consists_of(?c, ?l)
^ TGC:CoversTopic(?l, ?et)
-> TGC:hasEducationalTopic(?c, ?et)
````

## Purpose

This rule propagates educational topics from lessons to the course that contains them.

It extends the semantic propagation chain introduced by Rule 1:

```text
GamifiedResource
→ Lesson
→ Course
```

Together with Rule 1, it allows the ontology to infer the educational topics of a course from the gamified resources reused by its lessons.

## Semantic Context

**Dependencies:**

* Requires `TCO:Course` class
* Requires `TCO:Lesson` class
* Requires `TGC:EducationalTopic` class
* Requires `TCO:consists_of` object property
* Requires `TGC:CoversTopic` object property

**Output property:**

* `TGC:hasEducationalTopic` — inferred property linking courses to educational topics

## Expected Inference

### Before reasoning

```text
CourseX TCO:consists_of LessonY
LessonY TGC:CoversTopic TopicZ
```

### After reasoning

```text
CourseX TGC:hasEducationalTopic TopicZ
```

---

