# Use Case Stress Test : Explorer les limites du systeme


---

## 1. Scenario A : La question hors perimetre

**Sara :** "Mes etudiants ont du mal avec les design patterns. Comment gamifier ca ?"

### Ce qui devrait se passer
1. **Ontologie** → Le cours TIC321_OOP ne contient PAS de lecon sur les design patterns. Les 5 lecons sont : Java Basics, Classes & Objets, Constructors, Heritage, Polymorphisme.
2. Le systeme devrait detecter que la question est **hors perimetre du cours** et le signaler.

### Ce qui va probablement se passer
1. **Ontologie** → Pas de match sur "design patterns" dans les Lessons de TIC321.
2. **RAG** → Va quand meme retourner des chunks qui contiennent "pattern" ou "design" — probablement des passages sans rapport (ou le cours Coursera qui parle de game design patterns).
3. **LLM** → Va generer une recommandation comme si de rien n'etait, sans signaler que le sujet n'est pas dans le cours de Sara.

### Zone d'ombre exposee
- **Le systeme ne sait pas dire "je ne sais pas"** — il n'y a pas de mecanisme pour detecter qu'une question tombe en dehors du cours indexe.
- **Le RAG retourne toujours quelque chose** — meme si les chunks sont peu pertinents (score de similarite bas), le retriever retourne les top_k resultats quand meme.
- **Pas de seuil de pertinence** — le retriever fait `retrieve(question, top_k=3)` sans filtrer par score minimum.

### Amelioration identifiee
- Ajouter un seuil de score minimum dans le retriever (ex: score L2 > 1.5 → considerer comme non pertinent)
- Croiser avec l'ontologie : si aucun EducationalTopic ne matche la question, avertir l'utilisateur
- Ajouter une reponse type "Ce sujet ne semble pas faire partie de votre cours TIC321. Voulez-vous l'ajouter ?"

---

## 2. Scenario B : La question multilingue

**Sara :** "Comment rendre ma lecon sur l'heritage plus engageante ?" (en francais)

Puis enchaine avec :

**Sara :** "Can you give me more details about the badge system?" (en anglais)

### Ce qui devrait se passer
Le systeme gere les deux langues de maniere transparente grace au modele multilangue.

### Les problemes possibles

**Probleme 1 : La langue du contenu indexe**
- Si les supports de cours de Sara sont en anglais ("Lesson 4: Inheritance Slides"), le RAG doit quand meme matcher sur une question en francais.
- Le modele `paraphrase-multilingual-MiniLM-L12-v2` est concu pour ca, MAIS la qualite du matching cross-lingue est inferieure au matching mono-lingue.
- **Test a faire** : comparer les scores de `retrieve("heritage Java")` vs `retrieve("Java inheritance")` sur le meme contenu. Si l'ecart est trop grand, les recommandations seront de moins bonne qualite en francais.

**Probleme 2 : La langue de la reponse**
- Le LLM doit repondre dans la langue de la question. Mais si le prompt systeme est en anglais et les chunks RAG en anglais, le LLM va avoir tendance a repondre en anglais meme si Sara pose sa question en francais.
- **Pas encore de gestion de la langue dans le prompt** — il faudrait detecter la langue de la question et forcer la langue de la reponse.

**Probleme 3 : La langue de l'ontologie**
- Les entites de l'ontologie sont en anglais (ConstructorsTopic, InheritanceTopic)
- Les noms des documents sont en anglais ("Constructors Worked Examples")
- Si on fait une requete Cypher pour matcher "heritage" avec "InheritanceTopic", ca ne marchera pas sans mapping

### Zone d'ombre exposee
- Pas de detection automatique de la langue de l'utilisateur
- Pas de mapping francais ↔ anglais pour les termes techniques de l'ontologie
- Qualite du retrieval cross-lingue non testee quantitativement

---

## 3. Scenario C : L'incoherence ontologie ↔ RAG

**Sara :** "J'ai deja un quiz sur Java Basics, comment l'ameliorer ?"

### Ce qui devrait se passer
1. **Ontologie** → Confirme que GamifiedResource_JavaBasicsQuiz existe, lie a Lesson1_JavaBasics
2. **RAG** → Retourne le contenu de la lecon Java Basics pour comprendre ce que le quiz pourrait couvrir
3. **LLM** → Propose des ameliorations basees sur le contenu reel + le profil Socializer

### Le probleme
L'ontologie dit que le quiz existe. Mais :
- L'ontologie ne dit **rien** sur le contenu du quiz (quelles questions ? quel format ? combien de questions ?)
- Le RAG n'a pas indexe le quiz lui-meme (ce n'est pas un document de cours)
- Le LLM va donc inventer des ameliorations sans connaitre le quiz actuel

### Zone d'ombre exposee
- **Les GamifiedResources sont des boites noires** dans l'ontologie — on sait qu'elles existent mais pas ce qu'elles contiennent
- Le systeme ne peut pas distinguer entre "ameliorer un element existant" et "creer un nouvel element" sans connaitre le contenu de l'existant
- Les proprietes des GamifiedResources dans l'ontologie sont minimales : juste un nom et un type



---

## 4. Scenario D : La chaine de prerequis

**Sara :** "Je veux ajouter un defi de polymorphisme des la lecon 2, pour motiver les etudiants tot."

### Ce qui devrait se passer
1. **Ontologie** → Detecter que PolymorphismTopic est lie a Lesson5_Polymorphism, et que la chaine de prerequis est : Lesson1 → Lesson2 → Lesson3 → Lesson4 → Lesson5
2. Le systeme devrait **avertir** Sara que le polymorphisme presuppose l'heritage (Lesson4) qui presuppose les constructeurs (Lesson3) — donc l'introduire en Lesson2 est pedagogiquement incoherent.

### Ce qui va probablement se passer
1. **Ontologie** → Si la requete ne traverse pas explicitement les liens hasPreLesson, rien ne bloquera
2. **RAG** → Retournera des passages sur le polymorphisme
3. **LLM** → Generera joyeusement un defi de polymorphisme pour la lecon 2 sans voir le probleme

### Zone d'ombre exposee
- **Pas de regle SWRL** pour enforcer les prerequis. L'ontologie definit hasPreLesson mais aucune regle d'inference ne l'exploite.
- **La requete Neo4j doit etre intelligente** — il faut traverser le graphe de prerequis pour valider la coherence pedagogique. Qui ecrit cette requete ? Le LLM ? Un agent LangGraph dedie ?
- **Le LLM ne connait pas les contraintes de l'ontologie** sauf si on les met dans le prompt ou dans le contexte

### Amelioration identifiee
- Regle SWRL (tache Numidia) : "Si Topic X est couvert en Lesson N et que Lesson N hasPreLesson Lesson M, alors les concepts de Lesson M sont des prerequis de X"
- OU : Agent LangGraph "Validateur de coherence" qui verifie les prerequis avant de generer une recommandation

---

## 5. Scenario E : Le profil Socializer ignore

**Sara :** "Donne-moi un classement individuel avec des scores pour chaque etudiant, je veux creer de la competition."

### Ce qui devrait se passer
1. **Ontologie** → Sara est PlayerType Socializer. Ses objectifs sont Motivation et Participation (pas Competition).
2. Le systeme devrait nuancer : les classements individuels competitifs ne correspondent pas a son profil Socializer, et proposer des alternatives collaboratives.

### Ce qui va probablement se passer
Le LLM va obeir a la demande et proposer un leaderboard competitif sans prendre en compte le profil.

### Zone d'ombre exposee
- **Pas de regle "si Socializer alors privilegier collaboratif"** — c'est la fameuse regle SWRL manquante
- **Le profil est dans l'ontologie, la question est dans le chat** — comment le LLM sait-il que Sara est Socializer ? Il faut que l'agent ontologie injecte cette info dans le contexte du LLM
- **Conflit entre la demande explicite et le profil** — le systeme doit-il ignorer le profil si l'enseignant demande explicitement autre chose ? Ou doit-il signaler la contradiction ?

### Question pour l'equipe
Quelle est la politique quand la demande de l'enseignant contredit son profil ? Refus ? Avertissement ? Execution avec nuance ?

---

## 6. Scenario G : Plusieurs cours indexes

**Contexte :** On indexe le cours OOP de Sara ET le cours UML de Noah (SE240_UMLModeling existe aussi dans l'ontologie).

**Sara :** "Comment gamifier la lecon sur les diagrammes de classes ?"

### Le probleme
- "Diagrammes de classes" est un sujet couvert par le cours UML de Noah (Lesson1_UMLClassDiagrams dans l'ontologie)
- MAIS c'est aussi en lien avec la lecon 2 de Sara (ClassesAndObjects)
- Le RAG va retourner des chunks des DEUX cours
- Le LLM ne saura pas quel cours est pertinent pour Sara

### Zone d'ombre exposee
- **Le RAG ne sait pas a qui appartient quel cours** — tous les chunks sont dans le meme vectorstore sans distinction
- **L'ontologie sait** (Sara teaches TIC321, Noah teaches SE240) mais cette information ne descend pas jusqu'au retriever
- **Pas de session utilisateur** — le systeme ne sait pas que c'est Sara qui pose la question (sauf si l'agent ontologie l'identifie)

### Amelioration identifiee
- Partitionner le vectorstore par cours (collection ChromaDB par cours) ou filtrer par metadata
- L'agent ontologie identifie d'abord qui parle, recupère ses cours, et passe cette info au retriever

---

## 7. Scenario H : Le contenu du cours change

**Sara :** "J'ai ajoute une lecon 6 sur les exceptions, tu peux integrer ca dans le plan de gamification ?"

### Le probleme
1. L'ontologie ne contient pas de Lesson6 — il faudrait la creer
2. Le RAG n'a pas le contenu de cette lecon — il faudrait l'indexer
3. Le systeme n'a aucun mecanisme de mise a jour dynamique

### Zone d'ombre exposee
- **L'ontologie est statique** — pas d'API pour ajouter une lecon depuis le chat
- **Le RAG est statique** — une fois indexe, pas de mecanisme pour ajouter des documents a chaud
- **Pas de pipeline de mise a jour** — si Sara ajoute une lecon, quelqu'un doit manuellement modifier l'ontologie dans Protege ET re-indexer les documents

### Question pour l'equipe
Est-ce que c'est dans le scope du projet ? Probablement pas pour le MVP, mais le prof pourrait poser la question en soutenance.

---

## 9. Scenario I : Le LLM hallucine

**Sara :** "Quels exercices existent deja dans ma lecon 3 ?"

### Ce qui devrait se passer
1. **Ontologie** → Lesson3_Constructors reuseResource : ConstructorsSlides, ConstructorsExamples, GamifiedResource_ConstructorsChallenge
2. Le systeme liste ces 3 ressources avec leurs metadonnees (titre, duree, type)

### Le risque
- L'ontologie donne les noms : "Constructors Worked Examples" (18 min) et "Constructors Challenge"
- Mais elle ne donne pas le detail — le LLM va potentiellement **inventer** le contenu de ces exercices
- Il pourrait dire "votre exercice CompteBancaire dans ConstructorsChallenge..." alors qu'on ne sait pas du tout ce qu'il y a dans ce challenge

### Zone d'ombre exposee
- **Comment distinguer fait ontologique et generation LLM ?** — le systeme devrait clairement separer "voici ce que je sais de votre cours" (ontologie) et "voici ce que je vous recommande" (generation)
- **Pas de mecanisme anti-hallucination** — le LLM peut attribuer du contenu invente a des ressources reelles
- **Le RAG pourrait aider** si les ressources gamifiees etaient indexees — mais elles ne le sont pas

### Amelioration identifiee
- Ajouter dans le prompt LLM une instruction explicite : "Ne decris pas le contenu des ressources existantes sauf si tu as un passage RAG qui le confirme. Dis 'je n'ai pas acces au contenu de [ressource]' si necessaire."
- Prefixer les infos ontologiques avec [ONTOLOGIE] et les passages RAG avec [COURS] dans le contexte du LLM

---



