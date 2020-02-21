#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    sample-data-generator: generate vivo sample data of desired volume and complexity

    All options are set in the properties file, sdg.properties

    sample-data-generator.py writes the sample data to sample-data.ttl.  It writes one line to standard out summarizing
    it's work.  For example:

    vivo.mydomain.edu 1 University; 2 colleges; 5 departments; 273 people; 3317 works; 268377 triples in language en
    98.40 seconds

"""

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, XSD, SKOS
from numpy import random
import string
import re
import configparser
import time

__author__ = "Michael Conlon"
__copyright__ = "Copyright (c) 2020 Michael Conlon"
__license__ = "Apache-2"
__version__ = "0.1.4"

# globals

vivo = Namespace('http://vivoweb.org/ontology/core#')
bibo = Namespace('http://purl.org/ontology/bibo/')
vcard = Namespace('http://www.w3.org/2006/vcard/ns#')
skos = Namespace('http://www.w3.org/2004/02/skos/core#')
prov = Namespace('http://www.w3.org/ns/prov#')
obo = Namespace('http://purl.obolibrary.org/obo/')
owl = Namespace('http://www.w3.org/2002/07/owl#')
g = Graph()
ns = "http://vivo.mydomain.edu/individual/"
first_names = ["a", "b", "c"]
last_names = ["x", "y", "z"]
lorem = ['abcdefghijklmnopqrstuvwxyz']
lang = "en"
concept_uris = []
journal_uris = []
author_uris = set()
work_uris = []
site_dns = re.compile('^(?:https?:\/\/)?(?:[^@\n]+@)?(?:www\.)?([^:\/\n?]+)').match(ns)[1]
titles = []
work_types = [URIRef(bibo.AcademicArticle), URIRef(vivo.BlogPosting), URIRef(bibo.Book), URIRef(bibo.BookSection),
              URIRef(vivo.CaseStudy),
              URIRef(bibo.Chapter), URIRef(vivo.ConferencePaper), URIRef(vivo.ConferencePoster), URIRef(vivo.Database),
              URIRef(bibo.EditedBook), URIRef(vivo.EditorialArticle), URIRef(vivo.ExtensionDocument),
              URIRef(bibo.Film), URIRef(bibo.Letter), URIRef(vivo.Newsletter), URIRef(vivo.NewsRelease),
              URIRef(bibo.Patent), URIRef(bibo.Report), URIRef(vivo.Review), URIRef(obo.ERO_0000071),
              URIRef(vivo.Speech), URIRef(bibo.Thesis), URIRef(vivo.Video), URIRef(bibo.Webpage), URIRef(bibo.Website)]
work_type_cumulative_probabilities = []


def make_uri(tag):
    global ns
    uri = URIRef(ns + tag + str(random.randint(1000000, 9999999)))
    return uri


def make_orcid_uri():
    uri = URIRef('https://orcid.org/' + '-'.join([str(random.randint(1000, 9999)) for x in range(4)]))
    return uri


def add_university(self, label):
    u_uri = make_uri('university')
    self.add((u_uri, URIRef(RDF.type), URIRef(vivo.University)))
    self.add((u_uri, URIRef(RDFS.label), Literal(label, lang="en")))
    return u_uri


def add_college(self, label, uri):
    global lang
    c_uri = make_uri('college')
    self.add((c_uri, URIRef(RDF.type), URIRef(vivo.College)))
    self.add((c_uri, URIRef(RDFS.label), Literal(label, lang=lang)))
    self.add((c_uri, URIRef(obo.BFO_0000050), uri))
    return c_uri


def add_department(self, u, uri):
    global lang
    d_uri = make_uri('department')
    self.add((d_uri, URIRef(RDF.type), URIRef(vivo.AcademicDepartment)))
    self.add((d_uri, URIRef(RDFS.label), Literal(u, lang=lang)))
    self.add((d_uri, URIRef(obo.BFO_0000050), uri))
    return d_uri


def add_person(self, o_uri):
    global first_names
    global last_names
    global lang
    global titles

    given_name = first_names[random.randint(0, len(first_names) - 1)]
    additional_name = string.ascii_uppercase[random.randint(0, 25)] + '.'
    family_name = last_names[random.randint(0, len(last_names) - 1)]
    full_name = given_name + ' ' + additional_name + ' ' + family_name
    title = Literal(titles[random.randint(0, len(titles) - 1)], lang=lang)
    p_uri = make_uri('person')
    self.add((p_uri, URIRef(RDF.type), URIRef(vivo.FacultyMember)))
    self.add((p_uri, URIRef(RDFS.label), Literal(full_name, lang=lang)))
    self.add((p_uri, URIRef(vivo.overview), Literal(make_title() + make_title() + make_title(), lang=lang)))
    self.add((p_uri, URIRef(vivo.researcherId), Literal(str(random.randint(1000000, 9999999)), datatype=XSD.string)))
    self.add((p_uri, URIRef(vivo.scopusId), Literal(str(random.randint(1000000, 9999999)), datatype=XSD.string)))
    self.add((p_uri, URIRef(vivo.eraCommonsId), Literal(str(random.randint(1000000, 9999999)), datatype=XSD.string)))

    # add orcid

    orcid_uri = make_orcid_uri()
    self.add((p_uri, URIRef(vivo.orcidId), orcid_uri))
    self.add((orcid_uri, URIRef(RDF.type), URIRef(owl.Thing)))

    # add research areas for about half the people

    if random.randint(100) < 50:
        for ra in range(random.randint(5)):
            self.add((p_uri, URIRef(vivo.hasResearchArea), concept_uris[random.randint(0, len(concept_uris) - 1)]))

    # add a position

    pos_uri = make_uri('position')
    self.add((pos_uri, URIRef(RDF.type), URIRef(vivo.FacultyPosition)))
    self.add((pos_uri, URIRef(RDFS.label), title))
    self.add((pos_uri, URIRef(vivo.relates), p_uri))
    self.add((pos_uri, URIRef(vivo.relates), o_uri))
    self.add((pos_uri, URIRef(vivo.dateTimeInterval), self.add_date_interval(random.randint(1979, 2018), None)))

    # add a vcard with name parts, title, urls, email, phone

    v_uri = make_uri('vcard')
    self.add((p_uri, URIRef(obo.ARG_2000028), v_uri))
    self.add((v_uri, URIRef(RDF.type), URIRef(vcard.Individual)))

    vn_uri = make_uri('vcard-name')
    self.add((v_uri, URIRef(vcard.hasName), vn_uri))
    self.add((vn_uri, URIRef(RDF.type), URIRef(vcard.Name)))
    self.add((vn_uri, URIRef(vcard.givenName), Literal(given_name, lang=lang)))
    self.add((vn_uri, URIRef(vcard.additionalName), Literal(additional_name, lang=lang)))
    self.add((vn_uri, URIRef(vcard.familyName), Literal(family_name, lang=lang)))

    vt_uri = make_uri('vcard-title')
    self.add((v_uri, URIRef(vcard.hasTitle), vt_uri))
    self.add((vt_uri, URIRef(RDF.type), URIRef(vcard.Title)))
    self.add((vt_uri, URIRef(vcard.title), title))

    vu_uri = make_uri('vcard-url')
    self.add((v_uri, URIRef(vcard.hasURL), vu_uri))
    self.add((vu_uri, URIRef(RDF.type), URIRef(vcard.URL)))
    self.add((vu_uri, URIRef(vivo.rank), Literal('1', datatype=XSD.integer)))
    self.add((vu_uri, URIRef(RDFS.label), Literal('Home Page', lang=lang)))
    self.add((vu_uri, URIRef(vcard.url), Literal('http://www.google.com', datatype=XSD.anyUri)))
    vu_uri = make_uri('vcard-url')
    self.add((v_uri, URIRef(vcard.hasURL), vu_uri))
    self.add((vu_uri, URIRef(RDF.type), URIRef(vcard.URL)))
    self.add((vu_uri, URIRef(vivo.rank), Literal('2', datatype=XSD.integer)))
    self.add((vu_uri, URIRef(RDFS.label), Literal('Google Scholar', lang=lang)))
    self.add((vu_uri, URIRef(vcard.url), Literal('http://www.google.com', datatype=XSD.anyUri)))

    ve_uri = make_uri('vcard-email')
    self.add((v_uri, URIRef(vcard.hasEmail), ve_uri))
    self.add((ve_uri, URIRef(RDF.type), URIRef(vcard.Email)))
    self.add((ve_uri, URIRef(RDF.type), URIRef(vcard.Work)))
    self.add((ve_uri, URIRef(vcard.email), Literal((given_name[0] + additional_name[0] + family_name[0] +
                                                    str(random.randint(100000, 999999)) + '@' + site_dns).lower(),
                                                   datatype=XSD.string)))

    vtel_uri = make_uri('vcard-telephone')
    self.add((v_uri, URIRef(vcard.hasTelephone), vtel_uri))
    self.add((vtel_uri, URIRef(RDF.type), URIRef(vcard.Telephone)))
    self.add((vtel_uri, URIRef(vcard.telephone), Literal("+" + str(random.randint(1, 250)) + ' ' +
                                                            str(random.randint(100000000, 999999999)),
                                                            datatype=XSD.string)))

    return p_uri


def make_title():
    global lorem
    start = random.randint(0, len(lorem) / 2)
    length = random.randint(10, 100)
    title = lorem[start:start + length].strip(" ,.")
    title = title[1].upper() + title[2:]
    return title


def make_work_type():
    global work_types
    global work_type_cumulative_probabilities
    i = 0
    r = random.uniform(0., 1.)
    while r > work_type_cumulative_probabilities[i]:
        i += 1
    return work_types[i]


def add_work(self, p_uri):
    global lang
    global concept_uris
    global journal_uris
    global author_uris

    author_uris.add(p_uri)
    label = make_title()
    w_uri = make_uri('work')
    self.add((w_uri, URIRef(RDF.type), make_work_type()))
    self.add((w_uri, URIRef(RDFS.label), Literal(label, lang=lang)))
    self.add((w_uri, URIRef(bibo.doi),
              Literal(
                  "https://doi.org/10." + str(random.randint(1000, 9999)) + '/' + str(random.randint(100000, 999999)),
                  datatype=XSD.anyURI)))
    self.add((w_uri, URIRef(bibo.abstract),
              Literal(' '.join([make_title() for x in range(5)]), lang=lang)))
    self.add((w_uri, URIRef(vivo.hasPublicationVenue), journal_uris[random.randint(0, len(journal_uris) - 1)]))
    self.add((w_uri, URIRef(vivo.dateTimeValue), self.add_date(random.randint(1979, 2018))))
    self.add((w_uri, URIRef(bibo.volume), Literal(str(random.randint(1, 400)), datatype=XSD.string)))
    self.add((w_uri, URIRef(vivo.issue), Literal(str(random.randint(1, 48)), datatype=XSD.string)))
    start = random.randint(1, 500)
    end = start + random.randint(1, 50)
    self.add((w_uri, URIRef(bibo.start), Literal(str(start), datatype=XSD.string)))
    self.add((w_uri, URIRef(bibo.end), Literal(str(end), datatype=XSD.string)))

    # add authorship

    a_uri = make_uri('authorship')
    self.add((a_uri, URIRef(RDF.type), URIRef(vivo.Authorship)))
    self.add((a_uri, URIRef(vivo.relates), p_uri))
    self.add((a_uri, URIRef(vivo.relates), w_uri))
    self.add((a_uri, URIRef(vivo.rank), Literal(str(1), datatype=XSD.integer)))

    # add subject areas for about half the papers

    if random.randint(100) < 50:
        for ra in range(random.randint(5)):
            self.add((w_uri, URIRef(vivo.hasSubjectArea), concept_uris[random.randint(0, len(concept_uris) - 1)]))

    # add a vcard with url

    v_uri = make_uri('vcard')
    self.add((w_uri, URIRef(obo.ARG_2000028), v_uri))
    self.add((v_uri, URIRef(RDF.type), URIRef(vcard.Individual)))

    vu_uri = make_uri('vcard-url')
    self.add((v_uri, URIRef(vcard.hasURL), vu_uri))
    self.add((vu_uri, URIRef(RDF.type), URIRef(vcard.URL)))
    self.add((vu_uri, URIRef(vivo.rank), Literal('1', datatype=XSD.integer)))
    self.add((vu_uri, URIRef(RDFS.label), Literal('Full Text', lang=lang)))
    self.add((vu_uri, URIRef(vcard.url),
              Literal('https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5937161/', datatype=XSD.anyUri)))
    return w_uri


def add_coauthors(self, w_uri):
    global author_uris

    rank = 1

    # create additional stub authors for this work

    stub_uris = [make_uri('stub')]  # for x in range(max(1, random.poisson(4)))]
    for stub_uri in stub_uris:
        given_name = first_names[random.randint(0, len(first_names) - 1)]
        family_name = last_names[random.randint(0, len(last_names) - 1)]
        self.add((stub_uri, URIRef(RDF.type), URIRef(vcard.Kind)))
        vn_uri = make_uri('vcard-name')
        self.add((stub_uri, URIRef(vcard.hasName), vn_uri))
        self.add((vn_uri, URIRef(RDF.type), URIRef(vcard.Name)))
        self.add((vn_uri, URIRef(vcard.givenName), Literal(given_name, lang=lang)))
        self.add((vn_uri, URIRef(vcard.familyName), Literal(family_name, lang=lang)))

    # find the existing author

    query_string = """
        PREFIX vivo: <http://vivoweb.org/ontology/core#>
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        SELECT ?p
        WHERE {
          ?a vivo:relates <w_uri> .
          ?a a vivo:Authorship .
          ?a vivo:relates ?p .
          ?p a vivo:FacultyMember .
        }
        """

    query_string = query_string.replace('w_uri', w_uri)
    result = self.query(query_string)
    for row in result:
        p_uri = "%s" % row

    # select additional university authors for this work

    authors = []
    stop = False
    while not stop:
        authors = list(random.choice(list(author_uris), min(len(author_uris), random.poisson(3)), replace=False))
        if p_uri not in authors:
            stop = True

    authors = authors + stub_uris

    if len(authors) > 0:
        authors = random.choice(authors, len(authors), replace=False)  # shuffle the authors
        authors = [URIRef(x) for x in authors if isinstance(x, str)]

        for p_uri in authors:
            rank += 1
            a_uri = make_uri('authorship')
            self.add((a_uri, URIRef(RDF.type), URIRef(vivo.Authorship)))
            self.add((a_uri, URIRef(vivo.relates), p_uri))
            self.add((a_uri, URIRef(vivo.relates), w_uri))
            self.add((a_uri, URIRef(vivo.rank), Literal(str(rank), datatype=XSD.integer)))
    return


def add_date_interval(self, start, end):
    di_uri = make_uri('interval')
    self.add((di_uri, URIRef(RDF.type), URIRef(vivo.DateTimeInterval)))
    if start is not None:
        start_uri = self.add_date(start)
        self.add((di_uri, URIRef(vivo.start), start_uri))
    if end is not None:
        end_uri = self.add_date(end)
        self.add((di_uri, URIRef(vivo.end), end_uri))
    return di_uri


def add_date(self, year):
    d_uri = make_uri('date')
    self.add((d_uri, URIRef(RDF.type), vivo.DateTimeValue))
    self.add((d_uri, URIRef(vivo.dateTimePrecision), vivo.yearPrecision))
    self.add((d_uri, URIRef(vivo.dateTime), Literal("{}-01-01T00:00:00".format(year), datatype=XSD.dateTime)))
    return d_uri


Graph.add_university = add_university
Graph.add_college = add_college
Graph.add_department = add_department
Graph.add_person = add_person
Graph.add_work = add_work
Graph.add_date = add_date
Graph.add_date_interval = add_date_interval
Graph.add_coauthors = add_coauthors


def main():
    global ns
    global college_names
    global department_names
    global first_names
    global last_names
    global lorem
    global lang
    global concept_uris
    global journal_uris
    global titles
    global site_dns
    global work_uris
    global work_type_cumulative_probabilities

    start = time.time()
    config = configparser.ConfigParser()
    config.read("sdg.properties")
    ns = config.get("VIVO", "ns")
    site_dns = re.compile('^(?:https?:\/\/)?(?:[^@\n]+@)?(?:www\.)?([^:\/\n?]+)').match(ns)[1]
    first_names = config.get("SDG", "first_names").replace(" ", "").split(",")
    last_names = config.get("SDG", "last_names").replace(" ", "").split(",")
    titles = config.get("SDG", "titles").replace("  ", " ").split(",")
    titles = [x.strip() for x in titles]
    college_names = config.get("SDG", "college_names").replace("  ", " ").split(",")
    college_names = [x.strip() for x in college_names]
    department_names = config.get("SDG", "department_names").replace("  ", " ").split(",")
    department_names = [x.strip() for x in department_names]
    lorem = config.get("SDG", "lorem")
    lang = config.get("SDG", "lang")

    work_type_frequency = config.get("SDG", "work_type_frequency").replace("  ", " ").split(",")
    work_type_frequency_sum = sum([float(x) for x in work_type_frequency])
    work_type_probabilities = [float(x) / work_type_frequency_sum for x in work_type_frequency]
    work_type_cumulative_probabilities = []
    p = 0.
    for x in work_type_probabilities:
        p += x
        work_type_cumulative_probabilities.append(p)

    min_colleges_per_university = int(config.get("SDG", "min_colleges_per_university"))
    max_colleges_per_university = int(config.get("SDG", "max_colleges_per_university"))
    min_departments_per_college = int(config.get("SDG", "min_departments_per_college"))
    max_departments_per_college = int(config.get("SDG", "max_departments_per_college"))
    min_faculty_per_department = int(config.get("SDG", "min_faculty_per_department"))
    max_faculty_per_department = int(config.get("SDG", "Max_faculty_per_department"))
    min_works_per_faculty = int(config.get("SDG", "min_works_per_faculty"))
    max_works_per_faculty = int(config.get("SDG", "max_works_per_faculty"))

    n_colleges = 0
    n_departments = 0
    n_people = 0
    n_works = 0

    # add concepts, collect concept uris

    concepts = config.get("SDG", "concepts").replace("  ", " ").split(",")
    concepts = [x.strip() for x in concepts]
    for concept in concepts:
        c_uri = make_uri('concept')
        g.add((c_uri, URIRef(RDF.type), URIRef(SKOS.Concept)))
        g.add((c_uri, URIRef(RDFS.label), Literal(concept, lang=lang)))
        concept_uris.append(c_uri)

    # add journals, collect journal uris

    journals = config.get("SDG", "journals").replace("  ", " ").split(",")
    journals = [x.strip() for x in journals]
    for journal in journals:
        j_uri = make_uri('journal')
        g.add((j_uri, URIRef(RDF.type), URIRef(bibo.Journal)))
        g.add((j_uri, URIRef(RDFS.label), Literal(journal, lang=lang)))
        g.add((j_uri, URIRef(bibo.issn),
               Literal(str(random.randint(1000, 9999)) + '-' + str(random.randint(1000, 9999)), datatype=XSD.string)))
        journal_uris.append(j_uri)

    # generate a university with colleges and departments and people and scholarly works

    u_uri = g.add_university(config.get("SDG", "university_name"))

    for i in range(random.randint(min_colleges_per_university, max_colleges_per_university + 1)):
        c_uri = g.add_college(college_names[random.randint(0, len(college_names) - 1)], u_uri)
        n_colleges += 1

        for j in range(random.randint(min_departments_per_college, max_departments_per_college + 1)):
            d_uri = g.add_department(department_names[random.randint(0, len(department_names) - 1)], c_uri)
            n_departments += 1

            for k in range(random.randint(min_faculty_per_department, max_faculty_per_department + 1)):
                p_uri = g.add_person(d_uri)
                n_people += 1
                print("Adding person", n_people)

                # use numpy zipf to generate publication count.  numpy appears to be returning either an integer
                # or an an array with a single element.  Regardless, convert to int

                a = min(random.zipf(1.8, 1) + random.zipf(1.7, 1), max_works_per_faculty)
                if not isinstance(a, int):
                    a = int(a[0])

                for w in range(random.randint(min_works_per_faculty, a)):
                    w_uri = g.add_work(p_uri)
                    work_uris.append(w_uri)
                    n_works += 1

    print("People", n_people, "Works", n_works)

    # once all the authors and works are created, add co-authors and co-author stubs

    nw_uri = 0
    for w_uri in work_uris:
        nw_uri += 1
        g.add_coauthors(w_uri)
        if nw_uri % 10 == 0:
            print("Adding coauthors for work", nw_uri)

    f = open("sample-data.ttl", "w")
    print(g.serialize(format="ttl").decode('utf-8'), file=f)
    stop = time.time()
    print(site_dns, "1 University;", n_colleges, "colleges;", n_departments, "departments;", n_people, "people;",
          n_works,
          "works;", len(g), "triples in language", lang, "{:.2f} seconds".format(stop - start))
    return


if __name__ == "__main__":
    main()
