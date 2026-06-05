# Proposed SWRL Rules for the TGC Ontology

This document summarizes the proposed SWRL rules for recommending gamified resources and inferring teacher similarity / mentoring relations in the TGC ontology.

Protégé version : 5-6.4 
---

## Rule 1 — Recommend a motivation resource based on ProgressBar for Socializer + Sequential learners

### Objective

This rule recommends a gamified resource to a teacher when the teacher teaches a course whose audience contains a learner with:

- player type: `TGC:Socializer`;
- understanding pole: `TGC:Sequential`;
- and when the resource contains a `TGC:ProgressBar` relevant to the behavioural objective `TGC:Motivation`.

### Property created

`TGC:recommendedResource`

- **Domain:** `TCO:Teacher`
- **Range:** `TGC:GamifiedResource`

The recommendation is made **to the teacher**, not directly to the learner. The learner profile is used as a criterion for the recommendation.

### SWRL

```swrl
TCO:Teacher(?t)
^ TCO:Course(?c)
^ TCO:Learner(?l)
^ TGC:Audience(?a)
^ TGC:ClassroomObjective(?o)
^ TCO:teaches(?t, ?c)
^ TCO:hasClassroomObjective(?t, ?o)
^ TGC:concernsACourse(?o, ?c)
^ TGC:hasTargetAudience(?c, ?a)
^ TGC:isComposedOf(?a, ?l)
^ TGC:hasPlayerType(?l, TGC:Socializer)
^ TGC:hasUnderstandingPole(?l, TGC:Sequential)
^ TGC:GamifiedResource(?r)
^ TGC:containsGameElement(?r, ?ge)
^ TGC:ProgressBar(?ge)
^ TGC:relevantToObjective(?ge, TGC:Motivation)
->
TGC:recommendedResource(?t, ?r)
```

---

## Rule 2 — Recommend a gamified resource based on the teacher's behavioural objective

"Cette règle recommande une ressource gamifiée lorsque l’un de ses éléments de jeu est pertinent pour l’objectif comportemental visé par l’enseignant."

title : RecommendResourceByTeacherObjective

### Objective

This rule is a generalization of Rule 1. It recommends a gamified resource when the resource is designed with the same behavioural objective as the classroom objective associated with the course taught by the teacher.

This rule relies on the existing relation:

```swrl
TGC:designedWithObjective(?r, ?bo)
```

This relation may already be asserted in the ontology or inferred by another SWRL rule such as:

```swrl
TGC:GamifiedResource(?r)
^ TGC:GameElementResource(?ge)
^ TGC:BehaviouralObjective(?bo)
^ TGC:containsGameElement(?r, ?ge)
^ TGC:relevantToObjective(?ge, ?bo)
->
TGC:designedWithObjective(?r, ?bo)
```

### SWRL

```swrl
TCO:Teacher(?t)
^ TCO:Course(?c)
^ TCO:teaches(?t, ?c)
^ TGC:ClassroomObjective(?co)
^ TGC:BehaviouralObjective(?bo)
^ TGC:concernsObjective(?co, ?bo)
^ TGC:concernsACourse(?co, ?c)
^ TGC:GamifiedResource(?r)
^ TGC:designedWithObjective(?r, ?bo)
->
TGC:recommendedResource(?t, ?r)
```

---

## Rule 3 — Recommend resources to teachers with strong gamification experience
"Cette règle recommande aux enseignants ayant une forte expérience en gamification des ressources gamifiées adaptées à leurs objectifs comportementaux."

title : RecommendResourceForExperiencedTeacher

### Objective

This rule recommends a gamified resource to a teacher only if:

- the resource is designed with the behavioural objective targeted by the course/classroom objective;
- the teacher has a sufficient gamification experience level.

### SWRL

```swrl
TCO:Teacher(?t)
^ TCO:Course(?c)
^ TCO:teaches(?t, ?c)
^ TGC:ClassroomObjective(?co)
^ TGC:BehaviouralObjective(?bo)
^ TGC:concernsObjective(?co, ?bo)
^ TGC:concernsACourse(?co, ?c)
^ TGC:GamifiedResource(?r)
^ TGC:designedWithObjective(?r, ?bo)
^ TGC:GamificationExperience(?geExp)
^ TGC:hasGamificationExperience(?t, ?geExp)
^ TGC:experienceLevel(?geExp, ?level)
^ swrlb:greaterThan(?level, 2)
->
TGC:recommendedResource(?t, ?r)
```

### Alternative threshold

```swrl
swrlb:greaterThanOrEqual(?level, 3)
```

instead of:

```swrl
swrlb:greaterThan(?level, 2)
```

---

## Rule 4 — Infer that one teacher is more expert than another
"Cette règle infère qu’un enseignant est plus expert qu’un autre lorsque son niveau d’expérience en gamification est supérieur."

title : InferMoreExpertTeacher

### Objective

This rule infers that a teacher is more expert than another teacher when their gamification experience level is higher.

### Property created

`TGC:moreExpertThan`

- **Domain:** `TCO:Teacher`
- **Range:** `TCO:Teacher`

### SWRL

```swrl
TCO:Teacher(?t1)
^ TCO:Teacher(?t2)
^ TGC:GamificationExperience(?geExp1)
^ TGC:GamificationExperience(?geExp2)
^ TGC:hasGamificationExperience(?t1, ?geExp1)
^ TGC:hasGamificationExperience(?t2, ?geExp2)
^ TGC:experienceLevel(?geExp1, ?level1)
^ TGC:experienceLevel(?geExp2, ?level2)
^ swrlb:greaterThan(?level1, ?level2)
->
TGC:moreExpertThan(?t1, ?t2)
```

### Comment

This rule compares two teachers through their associated `TGC:Gamification_Experience` individuals.

---

## Rule 5 — Infer similarity between teachers based on domain or teaching topic
"Cette règle infère que deux enseignants ont un domaine similaire lorsqu’ils sont spécialisés dans le même topic."

Two variants are proposed because they do not express exactly the same level of similarity.

---

### Rule 5A — Similarity based on `TGC:SubjectArea`

title : InferSimilarDomainBySubjectArea

#### Objective

This rule infers that two teachers have a similar domain when they are specialized in the same subject area.

#### Property created

`TGC:hasSimilarDomain`

- **Domain:** `TCO:Teacher`
- **Range:** `TCO:Teacher`

#### SWRL

```swrl
TCO:Teacher(?t1)
^ TCO:Teacher(?t2)
^ TGC:subjectArea(?sa)
^ TGC:specializedIn(?t1, ?sa)
^ TGC:specializedIn(?t2, ?sa)
^ differentFrom(?t1, ?t2)
->
TGC:hasSimilarDomain(?t1, ?t2)
```

#### Comment

This version is broader. It checks whether two teachers share the same general subject area, such as InteractiveLearningDesigne, ObjectOrientedProgramming, SoftwareEngineering, etc.

---

### Rule 5B — Similarity based on `TGC:EducationalTopic`

title : InferSimilarTeachingTopicByEducationalTopic

#### Objective

This rule infers that two teachers have a similar teaching topic when they teach courses associated with the same educational topic.

#### Required property

`TGC:hasSimilarTeachingTopic`

- **Domain:** `TCO:Teacher`
- **Range:** `TCO:Teacher`

#### SWRL

```swrl
TCO:Teacher(?t1)
^ TCO:Teacher(?t2)
^ TCO:Course(?c1)
^ TCO:Course(?c2)
^ TGC:EducationalTopic(?et)
^ TCO:teaches(?t1, ?c1)
^ TCO:teaches(?t2, ?c2)
^ TGC:hasEducationalTopic(?c1, ?et)
^ TGC:hasEducationalTopic(?c2, ?et)
^ differentFrom(?t1, ?t2)
->
TGC:hasSimilarTeachingTopic(?t1, ?t2)
```

#### Comment

This version is more precise than Rule 5A because it compares the actual educational topics associated with the courses taught by the teachers.

---

## Rule 6 — Infer a potential mentor relationship between teachers
"Cette règle propose un enseignant X comme mentor potentiel de Y lorsqu’il est plus expérimenté, partage le même espace et enseigne le même topic."

### Objective

This rule proposes teacher `?t1` as a potential mentor of teacher `?t2` when:

- `?t1` is more expert than `?t2`;
- `?t1` has a sufficient gamification experience level;
- both teachers share the same collaborative space;
- both teachers have a similar domain or teaching topic.

### Property created

`TGC:potentialMentorOf`

- **Domain:** `TCO:Teacher`
- **Range:** `TCO:Teacher`

---

### Rule 6A — Mentor recommendation based on similar domain

title: InferPotentialMentorBySimilarDomain

```swrl
TCO:Teacher(?t1)
^ TCO:Teacher(?t2)
^ TGC:GamificationExperience(?geExp1)
^ TGC:hasGamificationExperience(?t1, ?geExp1)
^ TGC:experienceLevel(?geExp1, ?level1)
^ swrlb:greaterThan(?level1, 2)
^ TGC:moreExpertThan(?t1, ?t2)
^ TGC:sharesSpaceWith(?t1, ?t2)
^ TGC:hasSimilarDomain(?t1, ?t2)
->
TGC:potentialMentorOf(?t1, ?t2)
```

### Rule 6B — Mentor recommendation based on similar teaching topic

title: InferPotentialMentorBySimilarTeachingTopic

```swrl
TCO:Teacher(?t1)
^ TCO:Teacher(?t2)
^ TGC:GamificationExperience(?geExp1)
^ TGC:hasGamificationExperience(?t1, ?geExp1)
^ TGC:experienceLevel(?geExp1, ?level1)
^ swrlb:greaterThan(?level1, 2)
^ TGC:moreExpertThan(?t1, ?t2)
^ TGC:sharesSpaceWith(?t1, ?t2)
^ TGC:hasSimilarTeachingTopic(?t1, ?t2)
->
TGC:potentialMentorOf(?t1, ?t2)
```

### Comment

Rule 6A is broader because it relies on the general subject area.  
Rule 6B is stricter because it relies on the educational topic associated with the taught courses.

---

## Rule 7 — Infer similar teacher profiles based on player type and domain/topic
"Cette règle infère une similarité entre enseignants lorsqu’ils ont le même player type et sont spécialisés dans le même topic."

### Objective

This rule infers a profile similarity between two teachers when they have the same player type and share either:

- a similar teaching topic; or
- the same subject area.

### Required property

`TGC:hasSimilarProfile`

- **Domain:** `TCO:Teacher`
- **Range:** `TCO:Teacher`

---

### Rule 7A — Similar profile based on player type and similar teaching topic

title : InferSimilarProfileByPlayerTypeAndTopic
```swrl
TCO:Teacher(?t1)
^ TCO:Teacher(?t2)
^ TGC:PlayerType(?pt)
^ TGC:hasPlayerType(?t1, ?pt)
^ TGC:hasPlayerType(?t2, ?pt)
^ TGC:hasSimilarTeachingTopic(?t1, ?t2)
->
TGC:hasSimilarProfile(?t1, ?t2)
```

### Rule 7B — Similar profile based on player type and subject area

title : InferSimilarProfileByPlayerTypeAndDomain

```swrl
TCO:Teacher(?t1)
^ TCO:Teacher(?t2)
^ TGC:PlayerType(?pt)
^ TGC:hasPlayerType(?t1, ?pt)
^ TGC:hasPlayerType(?t2, ?pt)
^ TGC:hasSimilarDomain(?t1, ?t2)
->
TGC:hasSimilarProfile(?t1, ?t2)
```

### Comment

Rule 7A is more precise if `hasSimilarTeachingTopic` is inferred using Rule 5B.  
Rule 7B is broader and directly uses `specializedIn` with `SubjectArea`.
---

## Summary of proposed new properties

| Property | Domain | Range | Purpose |
|---|---|---|---|
| `TGC:recommendedResource` | `TCO:Teacher` | `TGC:GamifiedResource` | Recommends a gamified resource to a teacher. |
| `TGC:moreExpertThan` | `TCO:Teacher` | `TCO:Teacher` | Indicates that one teacher has a higher gamification experience level than another. |
| `TGC:hasSimilarDomain` | `TCO:Teacher` | `TCO:Teacher` | Indicates that two teachers share the same general subject area. |
| `TGC:hasSimilarTeachingTopic` | `TCO:Teacher` | `TCO:Teacher` | Indicates that two teachers teach courses linked to the same educational topic. |
| `TGC:potentialMentorOf` | `TCO:Teacher` | `TCO:Teacher` | Indicates that one teacher can potentially mentor another. |
| `TGC:hasSimilarProfile` | `TCO:Teacher` | `TCO:Teacher` | Indicates that two teachers have a similar profile based on player type and domain/topic. |

---

