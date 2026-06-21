# `TCO:teaches` relations added to the TGC ontology

## Context

In the modified version of the ontology, `TCO:teaches` relations were added between teacher individuals and course individuals.

The property used is:

```ttl
TCO:teaches
```

with:

- **Domain**: `TCO:Teacher`
- **Range**: `TCO:Course`

The goal was to add these relations in a way that remains coherent with the information already present in the ontology, mainly:

- the teacher's specialization through `TGC:specializedIn`;
- the course domain through `TGC:has_SubjectArea`;
- the lessons already designed by some teachers through `TGC:designLesson`;
- the associated classroom objectives when they existed through `TGC:hasClassroomObjective`.

---

## Summary of added relations

| Teacher | Added relation | Justification |
|---|---|---|
| `TGC:Sara` | `TCO:teaches TGC:TIC321_OOP` | Sara is specialized in `TGC:ObjectOrientedProgramming`, and the course `TGC:TIC321_OOP` also has `TGC:ObjectOrientedProgramming` as its subject area. In addition, Sara had already designed several lessons from this course: `TGC:Lesson1_JavaBasics`, `TGC:Lesson2_ClassesAndObjects`, and `TGC:Lesson3_Constructors`. She also has two classroom objectives related to this course: `TGC:ClassroomObjective_JavaParticipation` and `TGC:ClassroomObjective_OOP_Motivation`. |
| `TGC:Adam` | `TCO:teaches TGC:TIC321_OOP` | Adam is specialized in `TGC:ObjectOrientedProgramming`, which matches the subject area of the course `TGC:TIC321_OOP`. He had also already designed the lesson `TGC:Lesson4_Inheritance`, which covers the topic `TGC:InheritanceTopic`, one of the educational topics of this course. |
| `TGC:Ethan` | `TCO:teaches TGC:TIC321_OOP` | Ethan is specialized in `TGC:ObjectOrientedProgramming`, like the course `TGC:TIC321_OOP`. Even though he did not have an explicitly designed lesson in the ontology, his specialization directly matches the course domain. |
| `TGC:Noah` | `TCO:teaches TGC:TIC321_OOP` | Noah is specialized in `TGC:ObjectOrientedProgramming`, like the course `TGC:TIC321_OOP`. He had also designed `TGC:Lesson5_Polymorphism`, which covers `TGC:PolymorphismTopic`, a topic attached to the course. |
| `TGC:Olivia` | `TCO:teaches TGC:TIC321_OOP` | Olivia is specialized in `TGC:ObjectOrientedProgramming`, which matches the subject area of `TGC:TIC321_OOP`. The relation is therefore coherent with her area of expertise, even without an explicitly designed lesson. |
| `TGC:Grace` | `TCO:teaches TGC:EDU410_GamificationForTeachers` | Grace is specialized in `TGC:GamificationDesign`, like the course `TGC:EDU410_GamificationForTeachers`. She had already designed `TGC:Lesson1_GamificationFundamentals`, which covers `TGC:GamificationFundamentalsTopic`, a topic of the course. She also has the objective `TGC:ClassroomObjective_Gamification_Exploration`, which concerns this course. |
| `TGC:Daniel` | `TCO:teaches TGC:EDU410_GamificationForTeachers` | Daniel is specialized in `TGC:GamificationDesign`, which is the subject area of the course `TGC:EDU410_GamificationForTeachers`. He had also designed `TGC:Lesson2_GameElementsSelection`, which covers `TGC:GameElementsSelectionTopic`, a topic of the course. |
| `TGC:Natalie` | `TCO:teaches TGC:EDU410_GamificationForTeachers` | Natalie is specialized in `TGC:GamificationDesign`, like the course `TGC:EDU410_GamificationForTeachers`. Even though no lesson designed by Natalie was indicated, her specialization justifies that she teaches this course. |
| `TGC:Chloe` | `TCO:teaches TGC:EDU420_InteractiveLearningDesign` | Chloe is specialized in `TGC:InteractiveLearningDesign`, which matches the subject area of the course `TGC:EDU420_InteractiveLearningDesign`. She had also designed `TGC:Lesson1_InteractiveLessonDesign`, covering `TGC:InteractiveLessonDesignTopic`, a topic of the course. |
| `TGC:Victor` | `TCO:teaches TGC:EDU420_InteractiveLearningDesign` | Victor is specialized in `TGC:InteractiveLearningDesign`, like the course `TGC:EDU420_InteractiveLearningDesign`. He had also designed `TGC:Lesson2_CollaborativeActivities`, which covers `TGC:CollaborativeActivityTopic`, a topic of the course. |
| `TGC:Clara` | `TCO:teaches TGC:SE240_UMLModeling` | Clara is specialized in `TGC:SoftwareEngineering`, like the course `TGC:SE240_UMLModeling`. She had already designed `TGC:Lesson1_UMLClassDiagrams`, which covers `TGC:UMLClassDiagramTopic`, a topic of the course. She also has `TGC:ClassroomObjective_UML_GroupLearning`, which concerns `TGC:SE240_UMLModeling`. |
| `TGC:Clara` | `TCO:teaches TGC:SE350_DesignPatterns` | Clara is specialized in `TGC:SoftwareEngineering`, and `TGC:SE350_DesignPatterns` also belongs to this domain. Even though her designed lesson is more directly related to UML, the course remains within her general area of expertise. |
| `TGC:EmmaTeacher` | `TCO:teaches TGC:SE240_UMLModeling` | EmmaTeacher is specialized in `TGC:SoftwareEngineering`, which matches the subject area of `TGC:SE240_UMLModeling`. No lesson explicitly designed by her was indicated, but the specialization is sufficient to keep the relation coherent. |
| `TGC:EmmaTeacher` | `TCO:teaches TGC:SE350_DesignPatterns` | EmmaTeacher is specialized in `TGC:SoftwareEngineering`, like the course `TGC:SE350_DesignPatterns`. The relation is coherent with her area of expertise. |
| `TGC:Henry` | `TCO:teaches TGC:SE240_UMLModeling` | Henry is specialized in `TGC:SoftwareEngineering`, like the course `TGC:SE240_UMLModeling`. Even though his designed lesson is related to design patterns, UML remains within the same `SoftwareEngineering` domain. |
| `TGC:Henry` | `TCO:teaches TGC:SE350_DesignPatterns` | Henry is specialized in `TGC:SoftwareEngineering`, like `TGC:SE350_DesignPatterns`. He had already designed `TGC:Lesson1_IntroDesignPatterns`, which covers `TGC:DesignPatternsTopic`, a topic of this course. |
| `TGC:Lucas` | `TCO:teaches TGC:SE240_UMLModeling` | Lucas is specialized in `TGC:SoftwareEngineering`, like `TGC:SE240_UMLModeling`. He had already designed `TGC:Lesson2_SequenceDiagrams`, which covers `TGC:SequenceDiagramTopic`, a topic of the course. |
| `TGC:Lucas` | `TCO:teaches TGC:SE350_DesignPatterns` | Lucas is specialized in `TGC:SoftwareEngineering`, like `TGC:SE350_DesignPatterns`. Even though his designed lesson is more directly related to sequence diagrams, the course remains coherent with his general domain. |
| `TGC:Sophie` | `TCO:teaches TGC:SE240_UMLModeling` | Sophie is specialized in `TGC:SoftwareEngineering`, like `TGC:SE240_UMLModeling`. Even though her designed lesson is more directly related to design patterns, UML belongs to the same specialization domain. |
| `TGC:Sophie` | `TCO:teaches TGC:SE350_DesignPatterns` | Sophie is specialized in `TGC:SoftwareEngineering`, like `TGC:SE350_DesignPatterns`. She had already designed `TGC:Lesson2_CreationalPatterns`, which covers `TGC:CreationalPatternsTopic`, a topic of the course. |

---

## Turtle version of the added triples

```ttl
TGC:Sara TCO:teaches TGC:TIC321_OOP .
TGC:Adam TCO:teaches TGC:TIC321_OOP .
TGC:Ethan TCO:teaches TGC:TIC321_OOP .
TGC:Noah TCO:teaches TGC:TIC321_OOP .
TGC:Olivia TCO:teaches TGC:TIC321_OOP .

TGC:Grace TCO:teaches TGC:EDU410_GamificationForTeachers .
TGC:Daniel TCO:teaches TGC:EDU410_GamificationForTeachers .
TGC:Natalie TCO:teaches TGC:EDU410_GamificationForTeachers .

TGC:Chloe TCO:teaches TGC:EDU420_InteractiveLearningDesign .
TGC:Victor TCO:teaches TGC:EDU420_InteractiveLearningDesign .

TGC:Clara TCO:teaches TGC:SE240_UMLModeling .
TGC:Clara TCO:teaches TGC:SE350_DesignPatterns .
TGC:EmmaTeacher TCO:teaches TGC:SE240_UMLModeling .
TGC:EmmaTeacher TCO:teaches TGC:SE350_DesignPatterns .
TGC:Henry TCO:teaches TGC:SE240_UMLModeling .
TGC:Henry TCO:teaches TGC:SE350_DesignPatterns .
TGC:Lucas TCO:teaches TGC:SE240_UMLModeling .
TGC:Lucas TCO:teaches TGC:SE350_DesignPatterns .
TGC:Sophie TCO:teaches TGC:SE240_UMLModeling .
TGC:Sophie TCO:teaches TGC:SE350_DesignPatterns .
```

---

## Note

For teachers who already had a `TGC:designLesson` relation, priority was given to the course that contains the topic of that lesson.

For teachers without an explicitly designed lesson, the coherence between their `TGC:specializedIn` value and the course `TGC:has_SubjectArea` value was used.

In the case of the `TGC:SoftwareEngineering` domain, two courses belong to the same subject area:

- `TGC:SE240_UMLModeling`;
- `TGC:SE350_DesignPatterns`.

Software Engineering teachers were therefore linked to both courses, except when a more precise justification already existed through a designed lesson.
