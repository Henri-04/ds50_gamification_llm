# Ontology update — SWRL inference rules and teacher-course relations


**Date:** 2026-06-05  
**Ontology file:** `TGC_working_2026-06-05.owl`  

## Summary

This update adds teacher-course relations, new object properties, and SWRL inference rules to support resource recommendation, teacher similarity detection, and potential mentor inference.

## Context

This update extends the TGC ontology by adding teacher-course relations, new object properties, and SWRL inference rules.
The objective is to make the ontology able to infer recommendations, teacher similarities, and potential mentoring relations between teachers.

The SWRL rules were added in Protégé using the SWRLTab and Drools workflow:

1. `OWL + SWRL → Drools`
2. `Run Drools`
3. `Drools → OWL`
4. Save, close, and reopen the ontology when needed so that inferred axioms are visible in SPARQL queries.

## 1. Added teacher-course relations

Several `TCO:teaches` relations were added between teacher individuals and course individuals.

The property used is:

```ttl
TCO:teaches
```

with:

* Domain: `TCO:Teacher`
* Range: `TCO:Course`

These relations were added coherently with the information already present in the ontology, mainly:

* the teacher specialization through `TGC:specializedIn`;
* the course subject area;
* the lessons already designed by the teacher through `TGC:designLesson`;
* the classroom objectives already associated with the teacher or course when available.

The detailed list of added `TCO:teaches` relations and their justifications is documented in:
[03_added_teaches_relations.md](03_added_teaches_relations.md).

## 2. Added object properties

The following object properties were added to support the new inference rules:

| Property                      | Domain        | Range                  | Purpose                                                                                   |
| ----------------------------- | ------------- | ---------------------- | ----------------------------------------------------------------------------------------- |
| `TGC:recommendedResource`     | `TCO:Teacher` | `TGC:GamifiedResource` | Recommends a gamified resource to a teacher.                                              |
| `TGC:hasSimilarDomain`        | `TCO:Teacher` | `TCO:Teacher`          | Indicates that two teachers share a similar subject/domain.                               |
| `TGC:hasSimilarTeachingTopic` | `TCO:Teacher` | `TCO:Teacher`          | Indicates that two teachers teach courses linked to the same educational topic.           |
| `TGC:potentialMentorOf`       | `TCO:Teacher` | `TCO:Teacher`          | Indicates that a teacher can potentially mentor another teacher.                          |
| `TGC:hasSimilarProfile`       | `TCO:Teacher` | `TCO:Teacher`          | Indicates that two teachers have a similar profile based on player type and domain/topic. |

## 3. Added SWRL rules

Rules 2 to 7B were added to the ontology.

Rule 1 was not kept in the current test workflow because it did not return results during SPARQL testing.

### Rule 2 — RecommendResourceByTeacherObjective

Infers `TGC:recommendedResource` when a teacher teaches a course whose classroom objective concerns a behavioural objective, and a gamified resource is designed with the same behavioural objective.

### Rule 3 — RecommendResourceForExperiencedTeacher

Infers `TGC:recommendedResource` for teachers who satisfy the same conditions as Rule 2 and also have a gamification experience level greater than 2.

### Rule 4 — InferMoreExpertTeacher

Infers `TGC:moreExpertThan` when one teacher has a higher gamification experience level than another teacher.

### Rule 5A — InferSimilarDomainBySubjectArea

Infers `TGC:hasSimilarDomain` when two different teachers are specialized in the same subject area.

### Rule 5B — InferSimilarTeachingTopicByEducationalTopic

Infers `TGC:hasSimilarTeachingTopic` when two different teachers teach courses associated with the same educational topic.

### Rule 6A — InferPotentialMentorBySimilarDomain

Infers `TGC:potentialMentorOf` when a teacher is more experienced, shares the same space with another teacher, and has a similar domain.

### Rule 6B — InferPotentialMentorBySimilarTeachingTopic

Infers `TGC:potentialMentorOf` when a teacher is more experienced, shares the same space with another teacher, and has a similar teaching topic.

### Rule 7A — InferSimilarProfileByPlayerTypeAndTopic

Infers `TGC:hasSimilarProfile` when two teachers have the same player type and a similar teaching topic.

### Rule 7B — InferSimilarProfileByPlayerTypeAndDomain

Infers `TGC:hasSimilarProfile` when two teachers have the same player type and a similar domain.

## 4. Validation

After running the SWRL rules with Drools, new inferred axioms were generated in the ontology.

The inferred relations were tested using SPARQL queries for each inferred property:

* `TGC:recommendedResource`
* `TGC:moreExpertThan`
* `TGC:hasSimilarDomain`
* `TGC:hasSimilarTeachingTopic`
* `TGC:potentialMentorOf`
* `TGC:hasSimilarProfile`

The SPARQL queries used for validation are documented in:
[04_swrl_rules_validation_queries.md](04_swrl_rules_validation_queries.md).

## 5. Notes and limitations

* SPARQL queries can verify that inferred axioms exist, but they do not directly indicate which SWRL rule produced a given axiom when several rules infer the same property.
* Rules 2 and 3 both infer `TGC:recommendedResource`.
* Rules 6A and 6B both infer `TGC:potentialMentorOf`.
* Rules 7A and 7B both infer `TGC:hasSimilarProfile`.

## 6. Related documentation

This update is accompanied by the following documentation files:

- [01_swrl_rules_proposal.md](01_swrl_rules_proposal.md)
- [03_added_teaches_relations.md](03_added_teaches_relations.md)
- [04_swrl_rules_validation_queries.md](04_swrl_rules_validation_queries.md)

## 7. Commit summary

This commit updates the ontology by:

* adding coherent `TCO:teaches` relations between teachers and courses;
* adding new object properties needed for inference;
* adding SWRL rules 2 to 7B;
* running the rules through Drools;
* saving the inferred axioms into the ontology;
* validating the inferred relations with SPARQL queries.
