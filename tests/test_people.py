"""
Tests de la recommandation de personnes (aucune clé API : 100 % SPARQL sur
l'ontologie enrichie). Les faits assertés s'appuient sur les relations inférées
présentes dans l'ontologie (potentialMentorOf, hasSimilarProfile/Domain).
"""

from src.agent.people import gather_people, format_people_reco, recommend_people


def test_sara_has_mentors_in_her_domain():
    data = gather_people("Sara")
    assert data["mentors"], "Sara devrait avoir au moins un mentor potentiel"
    sara_domain = "ObjectOrientedProgramming"
    # Un mentor est proposé dans le même domaine que Sara.
    assert all(c["specialization"] == sara_domain for c in data["mentors"])
    # Chaque fiche mentor est exploitable (nom + niveau de gamification).
    for c in data["mentors"]:
        assert c["name"]
        assert c["gamification_level"] is not None


def test_sara_has_similar_peers():
    data = gather_people("Sara")
    assert data["peers"], "Sara devrait avoir au moins un pair au profil similaire"


def test_mentor_not_listed_as_peer():
    data = gather_people("Sara")
    mentor_ids = {c["id"] for c in data["mentors"]}
    peer_ids = {c["id"] for c in data["peers"]}
    assert mentor_ids.isdisjoint(peer_ids)


def test_unknown_teacher_returns_empty():
    data = gather_people("PersonneInexistante")
    assert data == {"mentors": [], "peers": []}


def test_format_lists_mentors_and_names():
    text = format_people_reco("Sara", gather_people("Sara"))
    assert "Mentors" in text
    assert "Sara" in text


def test_format_handles_no_recommendation():
    text = format_people_reco("X", {"mentors": [], "peers": []})
    assert "Aucune personne" in text


def test_recommend_people_node_sets_final_answer():
    state = recommend_people({"teacher": "Sara"})
    assert state["final_answer"]
    assert state["people_recommendations"]["mentors"]
    assert state["final_answer"] == state["recommendation"]
