from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .api_utils.tt_simple_api import *
from .api_utils.h_index import *
from knowledge.forms import *
from django.core import serializers
from pprint import pprint
from datetime import datetime, date
import time
from django.db.models import Avg, Count, Min, Sum
from django.db.models import Q

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import nltk
nltk.download('punkt')
nltk.download('stopwords')

from difflib import SequenceMatcher

# Create your views here.

# Define important Publication Types for sorting
publication_types_options = ['Conference Paper', 'Book', 'Article', 'Review']
publication_types_options = sorted(publication_types_options)
publication_types_options.insert(0, 'All')
publication_types_options.append('Other')

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

            if 'test2' in request.POST:

                authors = Author.objects.all()

                for author in authors:

                    sync_scopus_docs(author.pk)
            
            if 'test' in request.POST:

                authors = Author.objects.prefetch_related(
                    'projects__areas',
                    'publications__author_set',
                    'publications__keywords',
                    'publications__areas',
                    'publications__publication_type',
                    'domains',
                    'current_affiliations',
                    'previous_affiliations'
                ).annotate(num_publications=Count('publications')).order_by('-num_publications')#[:20]

                erratum_id = PublicationType.objects.get(name='Erratum')

                matches = 0
                total = 0
                i = 1

                same_scopus = 0
                same_ciencia = 0
                same_doi = 0

                # Id's of iterated publications
                # We want to test A vs B. But then B vs A will be unnecessary
                iterated_pubs = []

                for author in authors:

                    if author.pk == 62:

                        publications = author.publications.all()
                        
                        for publication in publications:

                            if publication.publication_type != erratum_id:

                                iterated_pubs.append(publication.pk)

                                #print(publication.pk, end=' ')
                                #print("\n\nTesting \"" + publication.title + "\"")

                                # NAME TEST

                                # Lower case
                                name_a = publication.title.lower()

                                # Separate words. Example: 'system-on-chip' -> 'system on chip'
                                name_a = name_a.replace('-', ' ').replace('/', ' ').replace("'", ' ')

                                # Tokenize
                                # Won't exclude '16:9', 'systems-on-chip', 'ua.pt', ...
                                tokenized_a = word_tokenize(name_a)

                                # Remove non alphanumeric tokens
                                new_tokanized_a = []
                                for token in tokenized_a:
                                    if token.isalnum():
                                        new_tokanized_a.append(token)

                                # Remove stop words
                                stop_tokanized_a = []
                                stop_words = set(stopwords.words('english'))
                                for token in new_tokanized_a:
                                    if not token in stop_words:
                                        stop_tokanized_a.append(token)

                                a = " ".join(stop_tokanized_a)

                                for test in publications:
                                    if test.pk not in iterated_pubs and \
                                        publication.pk != test.pk and \
                                        test.publication_type != erratum_id and \
                                        test.publication_type == publication.publication_type:
                                        
                                        # NAME TEST

                                        # Lower case
                                        name_b = test.title.lower()

                                        # Separate words. Example: 'system-on-chip' -> 'system on chip', "CAMBADA'2008" -> 'CAMBADA 2008'
                                        name_b = name_b.replace('-', ' ').replace('/', ' ').replace("'", ' ')

                                        # Tokenize
                                        # Won't exclude '16:9', 'systems-on-chip', 'ua.pt', ...
                                        tokenized_b = word_tokenize(name_b)

                                        # Remove non alphanumeric tokens
                                        new_tokanized_b = []
                                        for token in tokenized_b:
                                            if token.isalnum():
                                                new_tokanized_b.append(token)

                                        # Remove stop words
                                        stop_tokanized_b = []
                                        stop_words = set(stopwords.words('english'))
                                        for token in new_tokanized_b:
                                            if not token in stop_words:
                                                stop_tokanized_b.append(token)

                                        b = " ".join(stop_tokanized_b)

                                        # https://www.educative.io/answers/what-is-sequencematcher-in-python
                                        match = SequenceMatcher(None, a, b).ratio()

                                        abstract_count = 0
                                        if publication.abstract != "":
                                            abstract_count += 1
                                        if test.abstract != "":
                                            abstract_count += 1
                                        
                                        f_same_scopus = False
                                        f_same_ciencia = False
                                        f_same_doi = False
                                        if publication.scopus_id == test.scopus_id and publication.scopus_id != None:
                                            same_scopus += 1
                                            f_same_scopus = True
                                        if publication.ciencia_id == test.ciencia_id and publication.ciencia_id != None:
                                            same_ciencia += 1
                                            f_same_ciencia = True
                                        if publication.doi == test.doi and publication.doi != None:
                                            same_doi += 1
                                            f_same_doi = True

                                        if match > 0.7:# and abstract_count == 0:# and match != 1:

                                            print()
                                            print(a)
                                            print(b)
                                            #print(match, publication.pk, test.pk)

                                            print()
                                            print(publication.publication_type.name + "s")
                                            print(publication.pk, "[{}]".format( str(publication.date) ), "("+str(len(publication.author_set.all()))+")", publication.title)
                                            print(publication.scopus_id, publication.ciencia_id, publication.doi, publication.from_scopus, publication.from_ciencia)
                                            print("vs")
                                            print(test.pk, "[{}]".format( str(test.date) ), "("+str(len(test.author_set.all()))+")", test.title)
                                            print(test.scopus_id, test.ciencia_id, test.doi, test.from_scopus, test.from_ciencia)
                                            print("\nMatch:", match)
                                            print("\n" + publication.abstract[:300])
                                            print("vs")
                                            print(test.abstract[:300])
                                            #print("\nSame? [y/n] ")
                                            #x = None
                                            #while(x != 'y' and x != 'n'):
                                            #    x = input()
                                            #if x == 'y':
                                            #    matches += 1
                                            matches += 1
                                        
                                        total += 1
                            
                print("\nmatches: " + str(matches) + " out of " + str(total))
                print("same_scopus: " + str(same_scopus) + " out of " + str(total))
                print("same_ciencia: " + str(same_ciencia) + " out of " + str(total))
                print("same_doi: " + str(same_doi) + " out of " + str(total))
                print()
                                        

                                        


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


            # Sync operations
            elif 'sync-scopus-docs' in request.POST:
                pk = request.POST['author_pk']
                sync_scopus_docs(pk)

            elif 'sync-scopus-author' in request.POST:
                pk = request.POST['author_pk']
                sync_scopus_author(pk)
                
            elif 'sync-ciencia' in request.POST:
                pk = request.POST['author_pk']
                sync_ciencia(pk)
            

            # Publications Chart
            elif 'publication-type' in request.POST:
                request.session['index-publication-type'] = request.POST['publication-type']
            elif 'publication-start' in request.POST:
                request.session['index-publication-start'] = int(request.POST['publication-start'])
            elif 'publication-end' in request.POST:
                request.session['index-publication-end'] = int(request.POST['publication-end'])

            # Projects Chart
            elif 'project-start' in request.POST:
                request.session['index-project-start'] = int(request.POST['project-start'])
            elif 'project-end' in request.POST:
                request.session['index-project-end'] = int(request.POST['project-end'])
        

        # Publications Chart
        # Moved to top of file
        #publication_types_options = ['All', 'Conference Paper', 'Book', 'Other']

        try:
            earliest_publication = Publication.objects.earliest('date')
            latest_publication = Publication.objects.latest('date')

            if not 'index-publication-type' in request.session:
                request.session['index-publication-type'] = "Conference Paper"
            if not 'index-publication-start' in request.session:
                request.session['index-publication-start'] = earliest_publication.date.year
            if not 'index-publication-end' in request.session:
                request.session['index-publication-end'] = latest_publication.date.year
            
            publication_start_range = list(reversed(range(earliest_publication.date.year, request.session['index-publication-end'] + 1)))
            publication_end_range = list(reversed(range(request.session['index-publication-start'], latest_publication.date.year + 1)))

        except Publication.DoesNotExist:
            earliest_publication = None
            latest_publication = None
            publication_start_range = None
            publication_end_range = None
        
        # Projects Chart
        try:
            earliest_project = Project.objects.earliest('date')
            latest_project = Project.objects.latest('date')

            if not 'index-project-start' in request.session:
                request.session['index-project-start'] = earliest_project.date.year
            if not 'index-project-end' in request.session:
                request.session['index-project-end'] = latest_project.date.year
            
            project_start_range = list(reversed(range(earliest_project.date.year, request.session['index-project-end'] + 1)))
            project_end_range = list(reversed(range(request.session['index-project-start'], latest_project.date.year + 1)))

        except Publication.DoesNotExist:
            earliest_project = None
            latest_project = None
            project_start_range = None
            project_end_range = None


        # Charts
    
        labels_publications, data_publications = documents_from_year_interval(
            'Publication',
            request.session['index-publication-start'],
            request.session['index-publication-end'],
            pub_type=request.session['index-publication-type'],
            pub_types=publication_types_options.copy()
        )
        labels_projects, data_projects = documents_from_year_interval(
            'Project',
            request.session['index-project-start'],
            request.session['index-project-end'],
        )
        
        authorform = AuthorForm()
        
        authors = Author.objects.prefetch_related(  
            'projects__areas',
            'publications__author_set',
            'publications__keywords',
            'publications__areas',
            'publications__publication_type',
            'domains',
            'current_affiliations',
            'previous_affiliations'
        ).annotate(num_publications=Count('publications')).order_by('-num_publications')#[:20]

        cnt_publications = Publication.objects.all().count()
        cnt_projects = Project.objects.all().count()
        cnt_keywords = Keyword.objects.all().count()
        cnt_areas = Area.objects.all().count()

        context = {
            'user': request.user,

            'authorform': authorform,

            'authors': authors,

            # Publications Chart
            'publication_types': publication_types_options,
            'publication_type': request.session['index-publication-type'],
            'publication_start': request.session['index-publication-start'],
            'publication_end': request.session['index-publication-end'],
            'publication_start_range': publication_start_range,
            'publication_end_range': publication_end_range,

            # Projects Chart
            'project_start': request.session['index-project-start'],
            'project_end': request.session['index-project-end'],
            'project_start_range': project_start_range,
            'project_end_range': project_end_range,

            # Stats
            'cnt_publications': cnt_publications,
            'cnt_projects': cnt_projects,
            'cnt_keywords': cnt_keywords,
            'cnt_areas': cnt_areas,

            # Charts data
            'labels_publications': labels_publications,
            'data_publications': data_publications,
            'total_data_publications': sum(data_publications),

            'labels_projects': labels_projects,
            'data_projects': data_projects,
            'total_data_projects': sum(data_projects),
        }
        
        return render(request, 'index.html', context)

    return redirect('login')

def author_detail_view(request, pk):

    if request.user.is_authenticated:

        #del request.session['publication-type']
        #del request.session['publication-start']
        #del request.session['publication-end']

        try:
            author = Author.objects.get(pk = pk)
        except Author.DoesNotExist:
            raise Http404('Author does not exist')

        if request.method == 'POST':
            
            # Publications Chart
            if 'publication-type' in request.POST:
                request.session['publication-type'] = request.POST['publication-type']
            elif 'publication-start' in request.POST:
                request.session['publication-start'] = int(request.POST['publication-start'])
            elif 'publication-end' in request.POST:
                request.session['publication-end'] = int(request.POST['publication-end'])

            # Projects Chart
            elif 'project-start' in request.POST:
                request.session['project-start'] = int(request.POST['project-start'])
            elif 'project-end' in request.POST:
                request.session['project-end'] = int(request.POST['project-end'])


        # Publications Chart
        # Moved to top of file
        #publication_types_options = ['All', 'Conference Paper', 'Book', 'Other']
        
        try:
            earliest_publication = Publication.objects.earliest('date')
            latest_publication = Publication.objects.latest('date')

            if not 'publication-type' in request.session:
                request.session['publication-type'] = "Conference Paper"
            if not 'publication-start' in request.session:
                request.session['publication-start'] = earliest_publication.date.year
            if not 'publication-end' in request.session:
                request.session['publication-end'] = latest_publication.date.year
            
            publication_start_range = list(reversed(range(earliest_publication.date.year, request.session['publication-end'] + 1)))
            publication_end_range = list(reversed(range(request.session['publication-start'], latest_publication.date.year + 1)))

        except Publication.DoesNotExist:
            earliest_publication = None
            latest_publication = None
            publication_start_range = None
            publication_end_range = None

        
        # Projects Chart
        
        try:
            earliest_project = Project.objects.earliest('date')
            latest_project = Project.objects.latest('date')

            if not 'project-start' in request.session:
                request.session['project-start'] = earliest_project.date.year
            if not 'project-end' in request.session:
                request.session['project-end'] = latest_project.date.year
            
            project_start_range = list(reversed(range(earliest_project.date.year, request.session['project-end'] + 1)))
            project_end_range = list(reversed(range(request.session['project-start'], latest_project.date.year + 1)))

        except Publication.DoesNotExist:
            earliest_project = None
            latest_project = None
            project_start_range = None
            project_end_range = None

        # Charts
    
        labels_publications, data_publications = documents_from_year_interval(
            'Publication',
            request.session['publication-start'],
            request.session['publication-end'],
            author=pk,
            pub_type=request.session['publication-type'],
            pub_types=publication_types_options.copy()
        )
        labels_projects, data_projects = documents_from_year_interval(
            'Project',
            request.session['project-start'],
            request.session['project-end'],
            author=pk
        )

        # Top stats

        publications = Publication.objects.filter(author__id=pk).prefetch_related(
            'keywords',
            'areas',
            'author_set'
        )
        projects = Project.objects.filter(author__id=pk).prefetch_related(
            'areas'
        )

        author_keywords = {}
        author_areas = {}
        collaborators = {}

        for publication in publications:

            for keyword in publication.keywords.all():
                if not keyword.name in author_keywords:
                    author_keywords[keyword.name] = 1
                else:
                    author_keywords[keyword.name] += 1

            for area in publication.areas.all():
                if not area.name in author_areas:
                    author_areas[area.name] = [1, 0]
                else:
                    author_areas[area.name][0] += 1
            
            for author in publication.author_set.all():
                if author.pk != pk:
                    if not author.pk in collaborators:
                        collaborators[author.pk] = [1, 0]
                    else:
                        collaborators[author.pk][0] += 1
        
        for project in projects:

            for area in project.areas.all():
                if not area.name in author_areas:
                    author_areas[area.name] = [0, 1]
                else:
                    author_areas[area.name][1] += 1
            
            for author in project.author_set.all():
                if author.pk != pk:
                    if not author.pk in collaborators:
                        collaborators[author.pk] = [0, 1]
                    else:
                        collaborators[author.pk][1] += 1
        
        sorted_author_keywords = dict(sorted(author_keywords.items(), key=lambda item: item[1], reverse=True))
        sorted_author_areas = dict(sorted(author_areas.items(), key=lambda item: item[1][0] + item[1][1], reverse=True))
        sorted_collaborators = dict(sorted(collaborators.items(), key=lambda item: item[1][0] + item[1][1], reverse=True))

        # Change id to actual object
        x = {}
        for key, value in sorted_collaborators.items():
            collaborator = Author.objects.get(pk=key)
            x[collaborator] = value

        context = {
            'user': request.user,

            'author': author,
            'publications': publications,
            'projects': projects,

            # Publications Chart
            'publication_types': publication_types_options,
            'publication_type': request.session['publication-type'],
            'publication_start': request.session['publication-start'],
            'publication_end': request.session['publication-end'],
            'publication_start_range': publication_start_range,
            'publication_end_range': publication_end_range,
            
            # Projects Chart
            'project_start': request.session['project-start'],
            'project_end': request.session['project-end'],
            'project_start_range': project_start_range,
            'project_end_range': project_end_range,

            # Stats
            'sorted_author_keywords': sorted_author_keywords,
            'sorted_author_areas': sorted_author_areas,
            'sorted_collaborators': x, # sorted_collaborators but with the actual objects

            # Charts data
            'labels_publications': labels_publications,
            'data_publications': data_publications,
            'total_data_publications': sum(data_publications),

            'labels_projects': labels_projects,
            'data_projects': data_projects,
            'total_data_projects': sum(data_projects),
        }

        return render(request, 'author_detail.html', context)

    return redirect('login')

def documents_from_year_interval(doctype='Publication', start_year=date(1980, 1, 1), end_year=date.today(), author=None, pub_type='All', pub_types=[]):
    labels = []
    data = []
    cnt_year = start_year

    if 'All' in pub_types:
        pub_types.remove('All')
    if 'Other' in pub_types:
        pub_types.remove('Other')

    while(cnt_year <= end_year):
        labels.append(
            cnt_year
        )

        if doctype == 'Publication':
            publications = Publication.objects.filter(
                date__range=(
                    date(cnt_year, 1, 1),
                    date(cnt_year, 12, 31)
                )
            )

            # Author filter
            tmp_publications = publications.filter(author__id=author) if author != None else publications

            if pub_type == 'All':
                data.append( tmp_publications.count() )

            elif pub_type == 'Other':

                tmp2_publications = tmp_publications

                for i in pub_types: # Iterate important types like Conference Papers and reject them for this query (Therefore, others)
                    
                    if PublicationType.objects.filter(name=i).exists():
                        pub_type_id = PublicationType.objects.get(name=i)
                        tmp2_publications = tmp2_publications.filter(
                            ~Q(publication_type=pub_type_id)
                        )

                data.append( tmp2_publications.count() )

            else:
                try:
                    pub_type_id = PublicationType.objects.get(name=pub_type)
                    tmp2_publications = tmp_publications.filter(publication_type=pub_type_id)

                    data.append( tmp2_publications.count() )

                except PublicationType.DoesNotExist:
                    data.append( 0 )
                
                

        elif doctype == 'Project':
            projects = Project.objects.filter(
                date__range=(
                    date(cnt_year, 1, 1),
                    date(cnt_year, 12, 31)
                )
            )

            # Author filter
            tmp_projects = projects.filter(author__id=author) if author != None else projects
            data.append( tmp_projects.count() )

        cnt_year += 1

    return labels, data

def add_publication(author, scopus_id, ciencia_id, doi, title, date, \
    keywords, publication_type, from_scopus, from_ciencia, \
    available, clean_text, abstract, areas):

    debug_text = "\nSC {} ;; CV {} ;; DOI {} ;; {} ;; {} ;; SC {} ;; CV {} ;; AB {}".format(
        scopus_id,
        ciencia_id,
        doi,
        date,
        title,
        from_scopus,
        from_ciencia,
        available
    )
    
    merge = False
    reason = ''

    for test in author.publications.all():

        # test -> The publication that we are 'testing' against.
        # if the 'test' publication already has the info that we're trying to add,
        # we need to merge the data from both publications (onto the existing one, that being 'test').

        # Same pub. type (Yes)
        # We only want to merge publications from the same type.
        # If there's a Conference Paper and an Article about the same thing, we want to keep them
        # for counting/statistic purposes.
        if publication_type == test.publication_type:

            # Same scopus_id (Yes)
            if scopus_id != None and scopus_id == test.scopus_id:
                
                merge = True
                reason = 'same scopus'

                # Verifying that there's no different 'id info' between the 2 publications.
                # Example: They have the same 'scopus_id', but then specify different "doi"s.

                # Long code to make it understandable (only first time).

                # None and !None
                if test.ciencia_id == None and ciencia_id != None:
                    # Add new info to the test publication.
                    test.ciencia_id = ciencia_id
                # !None and None
                elif test.ciencia_id != None and ciencia_id == None:
                    # Only test publication . Do nothing.
                    pass
                # None and None
                elif test.ciencia_id == None and ciencia_id == None:
                    # Neither of them provide info. Do nothing.
                    pass
                # !None and !None
                else: # test.ciencia_id != None and ciencia_id != None:
                    if test.ciencia_id != ciencia_id:
                        # They provide different info. There may be no way to handle this merge.
                        # Same 'scopus_id' but different 'ciencia_id'
                        print(debug_text)
                        print("\n  -1-  I N C O N S I S T E N C Y  --\n")
                        print("SC {} ;; CV {} ;; DOI {} ;; {} ;; {} ;; SC {} ;; CV {} ;; AB {} ;; [{}]".format(test.scopus_id,test.ciencia_id,test.doi,test.date,test.title,test.from_scopus,test.from_ciencia,test.available,test.pk))
                        
                        reason += ' different ciencia'
                        #merge = False
                        #continue
                    else:
                        # They already provide the same info (!None info).
                        pass

                if test.doi == None and doi != None:
                    test.doi = doi
                elif test.doi != None and doi != None:
                    if test.doi != doi:
                        # Same 'scopus_id' but different 'doi'
                        print(debug_text)
                        print("\n  -2-  I N C O N S I S T E N C Y  --\n")
                        print("SC {} ;; CV {} ;; DOI {} ;; {} ;; {} ;; SC {} ;; CV {} ;; AB {} ;; [{}]".format(test.scopus_id,test.ciencia_id,test.doi,test.date,test.title,test.from_scopus,test.from_ciencia,test.available,test.pk))
                        
                        reason += ' different doi'
                        #merge = False
                        #continue
                
                debug_text += "\n                    SAME SCOPUS_ID"
                break
            else:

                # Same ciencia_id (Yes)
                if ciencia_id != None and ciencia_id == test.ciencia_id:

                    merge = True
                    reason = 'same ciencia'

                    if test.scopus_id == None and scopus_id != None:
                        test.scopus_id = scopus_id
                    elif test.scopus_id != None and scopus_id != None:
                        if test.scopus_id != scopus_id:
                            # Same 'ciencia_id' but different 'scopus_id'
                            print(debug_text)
                            print("\n  -3-  I N C O N S I S T E N C Y  --\n")
                            print("SC {} ;; CV {} ;; DOI {} ;; {} ;; {} ;; SC {} ;; CV {} ;; AB {} ;; [{}]".format(test.scopus_id,test.ciencia_id,test.doi,test.date,test.title,test.from_scopus,test.from_ciencia,test.available,test.pk))
                            
                            reason += ' different scopus'
                            #merge = False
                            #continue

                    if test.doi == None and doi != None:
                        test.doi = doi
                    elif test.doi != None and doi != None:
                        if test.doi != doi:
                            # Same 'ciencia_id' but different 'doi'
                            print(debug_text)
                            print("\n  -4-  I N C O N S I S T E N C Y  --\n")
                            print("SC {} ;; CV {} ;; DOI {} ;; {} ;; {} ;; SC {} ;; CV {} ;; AB {} ;; [{}]".format(test.scopus_id,test.ciencia_id,test.doi,test.date,test.title,test.from_scopus,test.from_ciencia,test.available,test.pk))
                            
                            reason += ' different doi'
                            #merge = False
                            #continue
                    
                    debug_text += "\n                    SAME CIENCIA_ID"
                    break
                else:

                    # Same doi (Yes)
                    if doi != None and doi == test.doi:

                        merge = True
                        reason = 'same doi'

                        if test.scopus_id == None and scopus_id != None:
                            test.scopus_id = scopus_id
                        elif test.scopus_id != None and scopus_id != None:
                            if test.scopus_id != scopus_id:
                                # Same 'doi' but different 'scopus_id'
                                print(debug_text)
                                print("\n  -5-  I N C O N S I S T E N C Y  --\n")
                                print("SC {} ;; CV {} ;; DOI {} ;; {} ;; {} ;; SC {} ;; CV {} ;; AB {} ;; [{}]".format(test.scopus_id,test.ciencia_id,test.doi,test.date,test.title,test.from_scopus,test.from_ciencia,test.available,test.pk))

                                reason += ' different scopus'
                                #merge = False
                                #continue

                        if test.ciencia_id == None and ciencia_id != None:
                            test.ciencia_id = ciencia_id
                        elif test.ciencia_id != None and ciencia_id != None:
                            if test.ciencia_id != ciencia_id:
                                # Same 'doi' but different 'ciencia_id'
                                print(debug_text)
                                print("\n  -6-  I N C O N S I S T E N C Y  --\n")
                                print("SC {} ;; CV {} ;; DOI {} ;; {} ;; {} ;; SC {} ;; CV {} ;; AB {} ;; [{}]".format(test.scopus_id,test.ciencia_id,test.doi,test.date,test.title,test.from_scopus,test.from_ciencia,test.available,test.pk))
                                
                                reason += ' different ciencia'
                                #merge = False
                                #continue
                        
                        debug_text += "\n                    SAME DOI"
                        break
                    else:

                        # Title processing
                        pass

    if merge:

        debug_text += "\nSC {} ;; CV {} ;; DOI {} ;; {} ;; {} ;; SC {} ;; CV {} ;; AB {} ;; [{}]".format(test.scopus_id,test.ciencia_id,test.doi,test.date,test.title,test.from_scopus,test.from_ciencia,test.available,test.pk)
        print(debug_text)

        # The 3 main fields are already taken care of
        # (scopus_id, ciencia_id, doi)

        if from_scopus:
            test.title = title
            test.date = date
            test.from_scopus = True
            test.available = available
            test.clean_text = clean_text
            test.abstract = abstract

            # Merge areas
            for area in areas:
                test.areas.add(area)

        else:
            test.from_ciencia = True

        # Merge keywords
        for keyword in keywords:
            test.keywords.add(keyword)
        
        test.save()
        author.publications.add(test)
        author.save()

        return reason
    
    else:

        print("", end=".")

        if from_scopus:
            from_scopus = True
            from_ciencia = False
            available = available
            clean_text = clean_text
            abstract = abstract
        else:
            from_scopus = False
            from_ciencia = True
            available = False
            clean_text = ""
            abstract = ""

        publication = Publication(
            scopus_id = scopus_id,
            ciencia_id = ciencia_id,
            doi = doi,
            title = title,
            date = date,
            publication_type = publication_type,

            from_scopus = from_scopus,
            from_ciencia = from_ciencia,
            available = available,
            clean_text = clean_text,
            abstract = abstract
        )
        publication.save()

        for keyword in keywords:
            publication.keywords.add(keyword)
        
        if from_scopus:

            for area in areas:
                publication.areas.add(area)
        
        publication.save()
        author.publications.add(publication)
        author.save()

        return 'new'

def sync_scopus_docs(pk):
    author = Author.objects.get(pk=pk)
    
    
    data = scopus_author_docs(author.scopus_id)

    #with open(str(pk)+'.json', encoding="utf-8") as fh:
    #    data = json.load(fh)
    
    new = 0
    s_sc = 0
    s_sc_d_cv = 0
    s_sc_d_doi = 0
    s_cv = 0
    s_cv_d_sc = 0
    s_cv_d_doi = 0
    s_doi = 0
    s_doi_d_sc = 0
    s_doi_d_cv = 0

    for data_pub in data:

        # MANDATORY FIELDS
        title = data_pub['doc_title']
        date = datetime.strptime(data_pub['doc_date'], "%Y-%m-%d").date()
        available = data_pub['available']

        # TYPE (MANDATORY)
        doc_type = data_pub['doc_type'].title()
        if PublicationType.objects.filter(name=doc_type).exists():
            publication_type = PublicationType.objects.get(name=doc_type)
        else:
            publication_type = PublicationType(name=doc_type)
            publication_type.save()

        # ID'S
        scopus_id = data_pub['doc_scopus_id']
        doi = data_pub['doc_doi']

        # KEYWORDS
        keywords = []

        for name in data_pub['doc_keywords']:
            name = ' '.join(elem[0].upper() + elem[1:] for elem in name.split())
            name = ' '.join(elem[0].upper() + elem[1:] for elem in name.split('-'))
            # Check keyword
            if Keyword.objects.filter(name=name).exists():
                keyword = Keyword.objects.get(name=name)
            else:
                keyword = Keyword(
                    name = name
                )
                keyword.save()
            keywords.append(keyword)

        # DOCUMENT TEXT
        clean_text = data_pub['clean_text']

        abst = data_pub['doc_abstract']
        abstract = abst if abst != None else ""

        # AREAS
        areas = []

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
            areas.append(area)

        reason = add_publication(
            author = author,
            scopus_id = scopus_id,
            ciencia_id = None,
            doi = doi,
            title = title,
            date = date,
            keywords = keywords,
            publication_type = publication_type,
            from_scopus = True, # SCOPUS
            from_ciencia = False,
            available = available,
            clean_text = clean_text,
            abstract = abstract,
            areas = areas
        )

        reason_F2 = " ".join( reason.split(' ')[:2] )
        reason_L2 = " ".join( reason.split(' ')[2:] )
        print(reason, "---", reason_F2, "---", reason_L2)
        if reason == 'new':
            new += 1
        elif reason_F2 == 'same scopus':
            s_sc += 1
            if reason_L2 == 'different ciencia':
                s_sc_d_cv += 1
            elif reason_L2 == 'different doi':
                s_sc_d_doi += 1
        elif reason_F2 == 'same ciencia':
            s_cv += 1
            if reason_L2 == 'different scopus':
                s_cv_d_sc += 1
            elif reason_L2 == 'different doi':
                s_cv_d_doi += 1
        elif reason_F2 == 'same doi':
            s_doi += 1
            if reason_L2 == 'different scopus':
                s_doi_d_sc += 1
            elif reason_L2 == 'different ciencia':
                s_doi_d_cv += 1
    
    print()
    print('new       '  , new)
    print()
    print('s_sc      '  , s_sc)
    print('  s_sc_d_cv ', s_sc_d_cv)
    print('  s_sc_d_doi', s_sc_d_doi)
    print()
    print('s_cv      '  , s_cv)
    print('  s_cv_d_sc ', s_cv_d_sc)
    print('  s_cv_d_doi', s_cv_d_doi)
    print()
    print('s_doi     '  , s_doi)
    print('  s_doi_d_sc', s_doi_d_sc)
    print('  s_doi_d_cv', s_doi_d_cv)


def sync_scopus_author(pk):
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

def sync_ciencia(pk):
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

    new = 0
    s_sc = 0
    s_sc_d_cv = 0
    s_sc_d_doi = 0
    s_cv = 0
    s_cv_d_sc = 0
    s_cv_d_doi = 0
    s_doi = 0
    s_doi_d_sc = 0
    s_doi_d_cv = 0

    for data_publication in data['publications']:

        ciencia_id = data_publication['ciencia_id']
        scopus_id = str(data_publication['scopus_id']).split('-')[-1]
        doi = data_publication['doi']
        title = data_publication['title']
        date = datetime.strptime(data_publication['date'], "%Y-%m-%d").date()

        # TYPE (MANDATORY)
        doc_type = data_publication['type'].title()
        doc_type = 'Article' if doc_type == 'Journal Article' else doc_type
        if PublicationType.objects.filter(name=doc_type).exists():
            publication_type = PublicationType.objects.get(name=doc_type)
        else:
            publication_type = PublicationType(name=doc_type)
            publication_type.save()

        available = False

        if scopus_id == 'None':
            scopus_id = None
        
        keywords = []

        for name in data_publication['keywords']:
            # Example: a-b cd -> A-b Cd
            name = ' '.join(elem[0].upper() + elem[1:] if elem != '' else '' for elem in name.split())
            # Example: A-b Cd -> A-B Cd
            name = ' '.join(elem[0].upper() + elem[1:] if elem != '' else '' for elem in name.split('-'))
            # Check keyword
            if Keyword.objects.filter(name=name).exists():
                keyword = Keyword.objects.get(name=name)
            else:
                keyword = Keyword(
                    name = name
                )
                keyword.save()
            keywords.append(keyword)

        areas = []

        reason = add_publication(
            author = author,
            scopus_id = scopus_id,
            ciencia_id = ciencia_id,
            doi = doi,
            title = title,
            date = date,
            keywords = keywords,
            publication_type = publication_type,
            from_scopus = False,
            from_ciencia = True, # CIENCIA
            available = None,
            clean_text = None,
            abstract = None,
            areas = areas
        )

        reason_F2 = " ".join( reason.split(' ')[:2] )
        reason_L2 = " ".join( reason.split(' ')[2:] )
        print(reason, "---", reason_F2, "---", reason_L2)
        if reason == 'new':
            new += 1
        elif reason_F2 == 'same scopus':
            s_sc += 1
            if reason_L2 == 'different ciencia':
                s_sc_d_cv += 1
            elif reason_L2 == 'different doi':
                s_sc_d_doi += 1
        elif reason_F2 == 'same ciencia':
            s_cv += 1
            if reason_L2 == 'different scopus':
                s_cv_d_sc += 1
            elif reason_L2 == 'different doi':
                s_cv_d_doi += 1
        elif reason_F2 == 'same doi':
            s_doi += 1
            if reason_L2 == 'different scopus':
                s_doi_d_sc += 1
            elif reason_L2 == 'different ciencia':
                s_doi_d_cv += 1

    print()
    print('new       '  , new)
    print()
    print('s_sc      '  , s_sc)
    print('  s_sc_d_cv ', s_sc_d_cv)
    print('  s_sc_d_doi', s_sc_d_doi)
    print()
    print('s_cv      '  , s_cv)
    print('  s_cv_d_sc ', s_cv_d_sc)
    print('  s_cv_d_doi', s_cv_d_doi)
    print()
    print('s_doi     '  , s_doi)
    print('  s_doi_d_sc', s_doi_d_sc)
    print('  s_doi_d_cv', s_doi_d_cv)

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



