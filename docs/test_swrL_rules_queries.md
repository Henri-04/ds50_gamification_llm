# SPARQL queries to test inferred axioms for SWRL rules

These queries are meant to be run **after** executing the SWRL workflow in Protégé:

1. `OWL+SWRL → Drools`
2. `Run Drools`
3. `Drools → OWL`
4. Save, close, and reopen the ontology if SPARQL does not immediately see the inferred axioms.

Common prefixes used in all queries:

```sparql
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX tgc: <http://www.hds.utc.fr/tgc/tbox#>
PREFIX tco: <http://www.hds.utc.fr/tco/tbox#>
```

---

## Rule 2 — RecommendResourceByTeacherObjective

**Inferred property tested:** `tgc:recommendedResource`

```sparql
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX tgc: <http://www.hds.utc.fr/tgc/tbox#>
PREFIX tco: <http://www.hds.utc.fr/tco/tbox#>

SELECT DISTINCT ?teacher ?resource ?course ?classroomObjective ?behaviouralObjective
WHERE {
  ?teacher tgc:recommendedResource ?resource .

  ?teacher tco:teaches ?course .
  ?classroomObjective tgc:concernsACourse ?course .
  ?classroomObjective tgc:concernsObjective ?behaviouralObjective .
  ?resource tgc:designedWithObjective ?behaviouralObjective .
}
```

---

## Rule 3 — RecommendResourceForExperiencedTeacher

**Inferred property tested:** `tgc:recommendedResource`

This query filters recommended resources for teachers whose gamification experience level is greater than 2.

```sparql
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX tgc: <http://www.hds.utc.fr/tgc/tbox#>
PREFIX tco: <http://www.hds.utc.fr/tco/tbox#>

SELECT DISTINCT ?teacher ?resource ?course ?classroomObjective ?behaviouralObjective ?gamificationExperience ?level
WHERE {
  ?teacher tgc:recommendedResource ?resource .

  ?teacher tco:teaches ?course .
  ?classroomObjective tgc:concernsACourse ?course .
  ?classroomObjective tgc:concernsObjective ?behaviouralObjective .
  ?resource tgc:designedWithObjective ?behaviouralObjective .

  ?teacher tgc:hasGamificationExperience ?gamificationExperience .
  ?gamificationExperience tgc:experienceLevel ?level .

  FILTER(?level > 2)
}
```

> Note: Rule 2 and Rule 3 both infer `tgc:recommendedResource`. SPARQL cannot directly tell which rule produced the axiom. This query checks that the inferred recommendations also satisfy Rule 3 conditions.

---

## Rule 4 — InferMoreExpertTeacher

**Inferred property tested:** `tgc:moreExpertThan`

```sparql
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX tgc: <http://www.hds.utc.fr/tgc/tbox#>
PREFIX tco: <http://www.hds.utc.fr/tco/tbox#>

SELECT DISTINCT ?expertTeacher ?lessExpertTeacher ?level1 ?level2
WHERE {
  ?expertTeacher tgc:moreExpertThan ?lessExpertTeacher .

  ?expertTeacher tgc:hasGamificationExperience ?geExp1 .
  ?lessExpertTeacher tgc:hasGamificationExperience ?geExp2 .

  ?geExp1 tgc:experienceLevel ?level1 .
  ?geExp2 tgc:experienceLevel ?level2 .

  FILTER(?level1 > ?level2)
}
```

---

## Rule 5A — InferSimilarDomainBySubjectArea

**Inferred property tested:** `tgc:hasSimilarDomain`

```sparql
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX tgc: <http://www.hds.utc.fr/tgc/tbox#>
PREFIX tco: <http://www.hds.utc.fr/tco/tbox#>

SELECT DISTINCT ?teacher1 ?teacher2 ?subjectArea
WHERE {
  ?teacher1 tgc:hasSimilarDomain ?teacher2 .

  ?teacher1 tgc:specializedIn ?subjectArea .
  ?teacher2 tgc:specializedIn ?subjectArea .

  FILTER(?teacher1 != ?teacher2)
}
```

> If this returns nothing while the conditions seem satisfied, check whether `differentFrom(?t1, ?t2)` is used in the SWRL rule. In OWL, individuals with different names are not automatically considered different. You may need to declare teachers as `Different Individuals` or use an `AllDifferent` axiom.

---

## Rule 5B — InferSimilarTeachingTopicByEducationalTopic

**Inferred property tested:** `tgc:hasSimilarTeachingTopic`

```sparql
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX tgc: <http://www.hds.utc.fr/tgc/tbox#>
PREFIX tco: <http://www.hds.utc.fr/tco/tbox#>

SELECT DISTINCT ?teacher1 ?teacher2 ?course1 ?course2 ?topic
WHERE {
  ?teacher1 tgc:hasSimilarTeachingTopic ?teacher2 .

  ?teacher1 tco:teaches ?course1 .
  ?teacher2 tco:teaches ?course2 .

  ?course1 tgc:hasEducationalTopic ?topic .
  ?course2 tgc:hasEducationalTopic ?topic .

  FILTER(?teacher1 != ?teacher2)
}
```

---

## Rule 6A — InferPotentialMentorBySimilarDomain

**Inferred property tested:** `tgc:potentialMentorOf`

This query checks mentor relations inferred through similar domain.

```sparql
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX tgc: <http://www.hds.utc.fr/tgc/tbox#>
PREFIX tco: <http://www.hds.utc.fr/tco/tbox#>

SELECT DISTINCT ?mentor ?mentee ?level ?subjectArea
WHERE {
  ?mentor tgc:potentialMentorOf ?mentee .

  ?mentor tgc:moreExpertThan ?mentee .
  ?mentor tgc:sharesSpaceWith ?mentee .
  ?mentor tgc:hasSimilarDomain ?mentee .

  ?mentor tgc:hasGamificationExperience ?geExp .
  ?geExp tgc:experienceLevel ?level .
  FILTER(?level > 2)

  ?mentor tgc:specializedIn ?subjectArea .
  ?mentee tgc:specializedIn ?subjectArea .

  FILTER(?mentor != ?mentee)
}
```

---

## Rule 6B — InferPotentialMentorBySimilarTeachingTopic

**Inferred property tested:** `tgc:potentialMentorOf`

This query checks mentor relations inferred through similar teaching topic.

```sparql
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX tgc: <http://www.hds.utc.fr/tgc/tbox#>
PREFIX tco: <http://www.hds.utc.fr/tco/tbox#>

SELECT DISTINCT ?mentor ?mentee ?level ?course1 ?course2 ?topic
WHERE {
  ?mentor tgc:potentialMentorOf ?mentee .

  ?mentor tgc:moreExpertThan ?mentee .
  ?mentor tgc:sharesSpaceWith ?mentee .
  ?mentor tgc:hasSimilarTeachingTopic ?mentee .

  ?mentor tgc:hasGamificationExperience ?geExp .
  ?geExp tgc:experienceLevel ?level .
  FILTER(?level > 2)

  ?mentor tco:teaches ?course1 .
  ?mentee tco:teaches ?course2 .

  ?course1 tgc:hasEducationalTopic ?topic .
  ?course2 tgc:hasEducationalTopic ?topic .

  FILTER(?mentor != ?mentee)
}
```

> Note: Rule 6A and Rule 6B both infer `tgc:potentialMentorOf`. SPARQL cannot directly tell which rule produced the axiom. These queries check that the inferred mentor relation satisfies the conditions of each rule.

---

## Rule 7A — InferSimilarProfileByPlayerTypeAndTopic

**Inferred property tested:** `tgc:hasSimilarProfile`

This query checks similar profiles inferred through same player type and similar teaching topic.

```sparql
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX tgc: <http://www.hds.utc.fr/tgc/tbox#>
PREFIX tco: <http://www.hds.utc.fr/tco/tbox#>

SELECT DISTINCT ?teacher1 ?teacher2 ?playerType ?course1 ?course2 ?topic
WHERE {
  ?teacher1 tgc:hasSimilarProfile ?teacher2 .
  ?teacher1 tgc:hasSimilarTeachingTopic ?teacher2 .

  ?teacher1 tgc:hasPlayerType ?playerType .
  ?teacher2 tgc:hasPlayerType ?playerType .

  ?teacher1 tco:teaches ?course1 .
  ?teacher2 tco:teaches ?course2 .

  ?course1 tgc:hasEducationalTopic ?topic .
  ?course2 tgc:hasEducationalTopic ?topic .

  FILTER(?teacher1 != ?teacher2)
}
```

---

## Rule 7B corrigée — InferSimilarProfileByPlayerTypeAndDomain

**Inferred property tested:** `tgc:hasSimilarProfile`

This query checks similar profiles inferred through same player type and similar domain.

```sparql
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX tgc: <http://www.hds.utc.fr/tgc/tbox#>
PREFIX tco: <http://www.hds.utc.fr/tco/tbox#>

SELECT DISTINCT ?teacher1 ?teacher2 ?playerType ?subjectArea
WHERE {
  ?teacher1 tgc:hasSimilarProfile ?teacher2 .
  ?teacher1 tgc:hasSimilarDomain ?teacher2 .

  ?teacher1 tgc:hasPlayerType ?playerType .
  ?teacher2 tgc:hasPlayerType ?playerType .

  ?teacher1 tgc:specializedIn ?subjectArea .
  ?teacher2 tgc:specializedIn ?subjectArea .

  FILTER(?teacher1 != ?teacher2)
}
```

> Note: Rule 7A and Rule 7B both infer `tgc:hasSimilarProfile`. SPARQL cannot directly tell which rule produced the axiom. These queries check that the inferred similar profile relation satisfies the conditions of each rule.

---

## Minimal queries for quick checks

Use these if you only want to verify whether the inferred properties exist.

```sparql
PREFIX tgc: <http://www.hds.utc.fr/tgc/tbox#>

SELECT DISTINCT ?teacher ?resource
WHERE {
  ?teacher tgc:recommendedResource ?resource .
}
```

```sparql
PREFIX tgc: <http://www.hds.utc.fr/tgc/tbox#>

SELECT DISTINCT ?t1 ?t2
WHERE {
  ?t1 tgc:moreExpertThan ?t2 .
}
```

```sparql
PREFIX tgc: <http://www.hds.utc.fr/tgc/tbox#>

SELECT DISTINCT ?t1 ?t2
WHERE {
  ?t1 tgc:hasSimilarDomain ?t2 .
}
```

```sparql
PREFIX tgc: <http://www.hds.utc.fr/tgc/tbox#>

SELECT DISTINCT ?t1 ?t2
WHERE {
  ?t1 tgc:hasSimilarTeachingTopic ?t2 .
}
```

```sparql
PREFIX tgc: <http://www.hds.utc.fr/tgc/tbox#>

SELECT DISTINCT ?mentor ?mentee
WHERE {
  ?mentor tgc:potentialMentorOf ?mentee .
}
```

```sparql
PREFIX tgc: <http://www.hds.utc.fr/tgc/tbox#>

SELECT DISTINCT ?t1 ?t2
WHERE {
  ?t1 tgc:hasSimilarProfile ?t2 .
}
```
