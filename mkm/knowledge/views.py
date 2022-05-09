from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .api_utils.tt_simple_api import *
from .api_utils.h_index import *
from knowledge.forms import *
from django.core import serializers
from pprint import pprint
from datetime import datetime

# Create your views here.

def login_view(request):

    if not request.user.is_authenticated:

        # If authentication fails, report error
        auth_fail = False

        if request.method == 'POST':

            if 'username' in request.POST:

                username = request.POST['username']
                password = request.POST['password']
                user = authenticate(request, username=username, password=password)
                
                if user is not None:
                    login(request, user)
                    return redirect('index')
                    
                else:
                    auth_fail = True
        
        context = {'auth_fail': auth_fail}
        return render(request, 'login.html', context)

    else: # User is authenticated

        if request.method == 'POST':

            if 'logout' in request.POST:
                
                logout(request)
                return redirect('login')

        return redirect('index')
    
def index_view(request):

    if request.user.is_authenticated:

        if request.method == 'POST':

            if 'add-author' in request.POST:
                authorform = AuthorForm(request.POST)
                if authorform.is_valid():
                    clean = authorform.cleaned_data
                    author = Author(
                        scopus_id = clean['scopus_id'],
                        ciencia_id = clean['ciencia_id'],
                        orcid_id = clean['orcid_id']
                    )
                    author.save()
            
            if 'delete_author' in request.POST:
                pk = request.POST['author_pk']
                author = Author.objects.get(pk=pk)
                author.delete()

            elif 'sync-scopus-docs' in request.POST:
                pk = request.POST['author_pk']
                author = Author.objects.get(pk=pk)
                data = scopus_author_docs(author.scopus_id)

                for data_pub in data:

                    # MANDATORY FIELDS
                    title = data_pub['doc_title']
                    date = datetime.strptime(data_pub['doc_date'], "%Y-%m-%d").date()
                    available = data_pub['available']

                    # TYPE (MANDATORY)
                    doc_type = data_pub['doc_type']
                    if PublicationType.objects.filter(name=doc_type).exists():
                        publication_type = PublicationType.objects.get(name=doc_type)
                    else:
                        publication_type = PublicationType(name=doc_type)
                        publication_type.save()

                    # ID'S
                    scopus_id = data_pub['doc_scopus_id']
                    doi = data_pub['doc_doi']

                    # Check if publication with scopus id already exists
                    if Publication.objects.filter(scopus_id=scopus_id).exists():
                        publication = Publication.objects.get(scopus_id=scopus_id)
                        # Override
                        publication.title = title
                        publication.date = date
                        publication.available = available
                        publication.publication_type = publication_type
                        publication.scopus_id = scopus_id
                        publication.doi = doi
                        print("Case X: Already a scopus doc. Overwrite.")
                    else:
                        publication = Publication(
                            title = title,
                            date = date,
                            available = available,
                            publication_type = publication_type,
                            scopus_id = scopus_id,
                            doi = doi
                        )
                        publication.save()
                        print("Case Y: New doc.")

                    # KEYWORDS
                    publication.keywords = json.dumps(   list(   set( json.loads(publication.keywords) + data_pub['doc_keywords'] )   )   )

                    # DOCUMENT TEXT
                    publication.clean_text = data_pub['clean_text']

                    abst = data_pub['doc_abstract']
                    publication.abstract = abst if abst != None else ""

                    # AREAS
                    for data_area in data_pub['doc_areas']:
                        code = data_area['area_code']
                        name = data_area['area_name']

                        # Check area
                        if Area.objects.filter(code=code).exists():
                            area = Area.objects.get(code=code)
                        else:
                            area = Area(
                                code = code,
                                name = name
                            )
                            area.save()
                        publication.areas.add(area)
                
                    publication.save()
                    author.publications.add(publication)
                
                author.save()

            elif 'sync-scopus-author' in request.POST:
                pk = request.POST['author_pk']
                author = Author.objects.get(pk=pk)
                data = scopus_author(author.scopus_id)
                author.h_index = scopus_h_index(author.scopus_id)

                # DOMAINS
                for data_area in data['author_areas']:
                    code = data_area['area_code']
                    name = data_area['area_name']

                    # Check area
                    if Area.objects.filter(code=code).exists():
                        area = Area.objects.get(code=code)
                    else:
                        area = Area(
                            code = code,
                            name = name
                        )
                        area.save()
                    author.domains.add(area)

                # CITATIONS
                author.citation_count = data['author_citation_count']
                author.cited_by_count = data['author_cited_by_count']

                # CURRENT AFFILIATIONS
                for data_affiliation in data['author_current_affiliation_list']:
                    affiliation_id = data_affiliation['affiliation_id']
                    name = data_affiliation['affiliation_name']
                    parent = data_affiliation['affiliation_parent']

                    # Check affiliation
                    if Affiliation.objects.filter(scopus_id=affiliation_id).exists():
                        affiliation = Affiliation.objects.get(scopus_id=affiliation_id)
                    else:
                        affiliation = Affiliation(
                            scopus_id = affiliation_id,
                            name = name,
                        )

                    # Check parent
                    if Affiliation.objects.filter(scopus_id=parent).exists():
                        parent_affiliation = Affiliation.objects.get(scopus_id=parent)
                        affiliation.parent = parent_affiliation
                    
                    affiliation.save()
                    author.current_affiliations.add(affiliation)
                
                # PREVIOUS AFFILIATIONS
                for data_affiliation in data['author_previous_affiliation_list']:
                    affiliation_id = data_affiliation['affiliation_id']
                    name = data_affiliation['affiliation_name']
                    parent = data_affiliation['affiliation_parent']

                    # Check affiliation
                    if Affiliation.objects.filter(scopus_id=affiliation_id).exists():
                        affiliation = Affiliation.objects.get(scopus_id=affiliation_id)
                    else:
                        affiliation = Affiliation(
                            scopus_id = affiliation_id,
                            name = name,
                        )

                    # Check parent
                    if Affiliation.objects.filter(scopus_id=parent).exists():
                        parent_affiliation = Affiliation.objects.get(scopus_id=parent)
                        affiliation.parent = parent_affiliation
                    
                    affiliation.save()
                    author.previous_affiliations.add(affiliation)

                # NAMES
                # Ciência has the best names
                if author.name == "":
                    author.name = data['author_name']
                author.name_list = json.dumps(data['author_name_list'])

                author.save()
                
            elif 'sync-ciencia' in request.POST:
                pk = request.POST['author_pk']
                author = Author.objects.get(pk=pk)
                data = ciencia_author(author.ciencia_id)

                # DOMAINS
                for data_domain in data['domains']:
                    code = data_domain['code']
                    name = data_domain['name']

                    # Check area
                    if Area.objects.filter(code=code).exists():
                        area = Area.objects.get(code=code)
                    else:
                        area = Area(
                            code = code,
                            name = name
                        )
                        area.save()
                    author.domains.add(area)
                
                # PUBLICATIONS
                case_a = 0
                case_b = 0
                case_c = 0
                for data_publication in data['publications']:

                    ciencia_id = data_publication['ciencia_id']
                    scopus_id = str(data_publication['scopus_id']).split('-')[-1]
                    doi = data_publication['doi']
                    title = data_publication['title']
                    date = datetime.strptime(data_publication['date'], "%Y-%m-%d").date()

                    # TYPE (MANDATORY)
                    doc_type = data_publication['type']
                    if PublicationType.objects.filter(name=doc_type).exists():
                        publication_type = PublicationType.objects.get(name=doc_type)
                    else:
                        publication_type = PublicationType(name=doc_type)
                        publication_type.save()

                    available = False

                    has_scopus_id = False
                    ciencia_id_exists = False

                    # Check if this has a scopus id
                    if scopus_id != 'None':
                        scopus_id = int(scopus_id)

                        # Check if publication already exists as scopus doc
                        if Publication.objects.filter(scopus_id=scopus_id).exists():
                            publication = Publication.objects.get(scopus_id=scopus_id)
                            publication.ciencia_id = ciencia_id
                            has_scopus_id = True
                            # Don't override existing scopus fields
                            #print("Case A: Already a scopus doc. Don't overwrite scopus fields.")
                            case_a += 1

                    # If this doesn't have a scopus id, then it's a Ciência exclusive
                    if ciencia_id != None and not has_scopus_id:
                        if Publication.objects.filter(ciencia_id=ciencia_id).exists():
                            publication = Publication.objects.get(ciencia_id=ciencia_id)
                            # Override existing ciencia fields
                            publication.title = title
                            publication.date = date
                            publication.available = available
                            publication.publication_type = publication_type
                            publication.scopus_id = scopus_id
                            publication.doi = doi
                            publication.ciencia_id = ciencia_id
                            ciencia_id_exists = True
                            #print("Case B: Already a ciencia doc.")
                            case_b += 1
                    
                    if not has_scopus_id and ciencia_id_exists == False:
                        # Create new publication
                        publication = Publication(
                            title = title,
                            date = date,
                            available = available,
                            publication_type = publication_type,
                            scopus_id = scopus_id,
                            doi = doi,
                            ciencia_id = ciencia_id
                        )
                        publication.save()
                        #print("Case C: New doc.")
                        case_c += 1
                    
                    # Doesn't make sense! If the author exists, then this publication will eventually be added to him/her.
                    # This is adding authors to publications (Publication-author relationship) when what we
                    # actually want is to add publications to authors (Author-publication relationship)

                    #for ciencia_id in data_publication['authors']:
                    #    if Author.objects.filter(ciencia_id=ciencia_id).exists() and ciencia_id != None:
                    #        author = Author.objects.get(ciencia_id=ciencia_id)
                    #        publication.authors.add(author)

                    publication.keywords = json.dumps(   list(   set( json.loads(publication.keywords) + data_publication['keywords'] )   )   )

                    publication.save()

                    author.publications.add(publication)
                    author.save()

                print(case_a, ": Already a scopus doc. Don't overwrite scopus fields.")
                print(case_b, ": Already a ciencia doc.")
                print(case_c, ": New doc.")

                # NAME
                # Some names come uppercased. This can uppercase wrong names but
                # still, it's better than all uppercase.
                author.name = data['name'].title()
                
                # INFO
                author.bio = data['bio']
                author.degrees = json.dumps(data['degrees'])
                author.distinctions = json.dumps(data['distinctions'])

                # PROJECTS
                for data_project in data['projects']:
                    name = data_project['name']
                    date = datetime.strptime(data_project['year'], "%Y").date()

                    # Check project
                    if Project.objects.filter(name=name).exists():
                        project = Project.objects.get(name=name)
                    else:
                        project = Project(
                            name = name,
                            date = date
                        )
                        project.save()
                    
                    desc = data_project['desc']
                    project.desc = desc if desc != None else ""

                    # Project areas
                    for data_area in data_project['areas']:
                        code = data_area['code']
                        name = data_area['name']

                        # Check area
                        if Area.objects.filter(code=code).exists():
                            area = Area.objects.get(code=code)
                        else:
                            area = Area(
                                code = code,
                                name = name
                            )
                            area.save()
                        project.areas.add(area)
                    
                    project.save()
                    author.projects.add(project)

                author.synced_ciencia = True
                author.save()

        authorform = AuthorForm()

        authors = Author.objects.all()

        context = {
            'user': request.user,

            'authorform': authorform,

            'authors': authors,
        }
        return render(request, 'index.html', context)

    return redirect('login')

# PUBLICACOES "REPETIDAS"
# KEYWORDS "REPETIDAS"
# JUNTAR AREAS E KEYWORDS?
# KEYWORDS NUMA CLASSE?
# PROJS DESC AREAS