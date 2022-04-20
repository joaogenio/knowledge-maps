from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .api_utils.tt_simple_api import *
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

        authorform = AuthorForm()

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

                    # Check if publication already exists
                    if Publication.objects.filter(scopus_id=scopus_id).exists():
                        publication = Publication.objects.get(scopus_id=scopus_id)
                    # Override
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

                    # KEYWORDS
                    publication.keywords = json.dumps(data_pub['doc_keywords'])

                    # DOCUMENT TEXT
                    publication.clean_text = data_pub['clean_text']
                    publication.abstract = data_pub['doc_abstract']

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
                author.name = data['author_name']
                author.name_list = json.dumps(data['author_name_list'])

                author.save()
                
            elif 'sync-ciencia' in request.POST:
                pk = request.POST['author_pk']
                author = Author.objects.get(pk=pk)
                data = ciencia_author(author.ciencia_id)

        authors = Author.objects.all()

        context = {
            'user': request.user,

            'authorform': authorform,

            'authors': authors,
        }
        return render(request, 'index.html', context)

    return redirect('login')
