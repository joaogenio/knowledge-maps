from django.db import models
import json

class bcolors:
    HEADER =	'\033[95m'
    OKBLUE =	'\033[94m'
    OKCYAN =	'\033[96m'
    OKGREEN =	'\033[92m'
    WARNING =	'\033[93m'
    FAIL =		'\033[91m'
    ENDC =		'\033[0m'
    BOLD =		'\033[1m'
    UNDERLINE = '\033[4m'

# Create your models here.

class Area(models.Model):
    code = models.IntegerField(
        primary_key = True,
    )
    name = models.CharField(
        max_length = 100
    )

    class Meta:
        ordering = ['-code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class Affiliation(models.Model):
    scopus_id = models.IntegerField(
        primary_key = True
    )
    parent = models.ForeignKey(
        'Affiliation',
        on_delete = models.SET_NULL,
        null = True
    )
    name = models.CharField(
        max_length = 200
    )

    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Author(models.Model):
    # NULL=TRUE IN TEXT FIELDS DOESNT MAKE SENSE

    scopus_id = models.IntegerField(
        null = True,
        blank = True
    )
    ciencia_id = models.CharField(
        max_length = 100,
        blank = True
    )
    orcid_id = models.CharField(
        max_length = 100,
        blank = True
    )

    # SCOPUS / CIENCIA
    name = models.CharField(
        max_length = 100,
        blank = True
    )
    domains = models.ManyToManyField(
        'Area',
        blank = True
    )
    publications = models.ManyToManyField(
        'Publication',
        blank = True
    )

    # SCOPUS
    name_list = models.TextField(
        default = "[]"
    )

    h_index = models.IntegerField(
        null = True,
        blank = True
    )

    citation_count = models.IntegerField(
        default = 0
    )
    cited_by_count = models.IntegerField(
        default = 0
    )

    current_affiliations = models.ManyToManyField(
        'Affiliation',
        related_name = 'Current',
        blank = True
    )
    previous_affiliations = models.ManyToManyField(
        'Affiliation',
        related_name = 'Previous',
        blank = True
    )

    # CIENCIA
    bio = models.TextField(
        blank = True
    )
    degrees = models.TextField(
        default = "[]"
    )
    distinctions = models.TextField(
        default = "[]"
    )
    projects = models.ManyToManyField(
        'Project',
        blank = True
    )

    # Indicates that author has been synced with Ciencia Vitae at least once
    synced_ciencia = models.BooleanField(
        default = False
    )

    class Meta:
        #ordering = ['-id']
        ordering = ['name']

        unique_together = [
            ['scopus_id', 'ciencia_id', 'orcid_id'],

            # COMMENTED BECAUSE MULTIPLE AUTHORS COULD HAVE 2 FIELDS BEING NULL

            # BUT STILL NEEDS TO BE ENFORCED IN A FORM / VIEW BECAUSE THIS
            # ALLOWS FOR THE SAME ID TO EXIST IN MULTIPLE AUTHORS (BECAUSE WE
            # NEED TO ALLOW NULL)

            #['scopus_id', 'ciencia_id'],
            #['ciencia_id', 'orcid_id'],
            #['scopus_id', 'orcid_id'],
        ]
    
    def __str__(self):
        return self.name if self.name != "" else str(self.id)
    
    def short_name(self):
        split = self.name.split(' ')
        first_name = split[0]
        last_name = split[-1]
        return f"{first_name} {last_name}"
    
    def load_name_list(self):
        return json.loads(self.name_list)
    
    def load_degrees(self):
        return json.loads(self.degrees)
    
    def load_distinctions(self):
        return json.loads(self.distinctions)
    
    def publications_abstract(self):
        cnt = 0
        for publication in self.publications.all():
            if publication.abstract != "":
                cnt += 1
        return cnt
    
    def publications_fulltext(self):
        cnt = 0
        for publication in self.publications.all():
            if publication.available:
                cnt += 1
        return cnt

class Publication(models.Model):
    scopus_id = models.CharField(           # WATCH OUT FOR THIS BEING A STRING CALLED 'None' IN THE FUTURE :p
        max_length = 100,
        null = True
    )
    ciencia_id = models.CharField(
        max_length = 100,
        null = True
    )
    doi = models.CharField(
        max_length = 100,
        null = True
    )

    # SCOPUS / CIENCIA
    title = models.CharField(
        max_length = 200
    )
    date = models.DateField()
    keywords = models.ManyToManyField(
        'Keyword'
    )
    publication_type = models.ForeignKey(
        'PublicationType',
        on_delete = models.CASCADE
    )

    from_scopus = models.BooleanField()
    from_ciencia = models.BooleanField()

    # SCOPUS
    available = models.BooleanField()
    clean_text = models.TextField(
        blank = True
    )
    abstract = models.TextField(
        blank = True
    )
    areas = models.ManyToManyField(
        'Area'
    )

    # CIENCIA
    # No need for this! We have the reverse relation of Author-publication!
    #authors = models.ManyToManyField(
    #    'Author'
    #)

    class Meta:
        ordering = ['-date', 'title']
        unique_together = [
            ['scopus_id', 'ciencia_id']
        ]
    
    def __str__(self):
        return "[{}] {}".format( str(self.date), self.title )
    
    def pretty(self):
        return "[{:<11}] [{:<8}] [{:<20}] [{} {}] [{:<16}] [{} {:2d} {:2d} {} {}] [{}] \n{}".format( ############################################################################################################
            str(self.scopus_id)[-11:],
            str(self.ciencia_id)[-8:],
            str(self.doi)[-20:],

            bcolors.FAIL+'SC'+bcolors.ENDC if self.from_scopus else '  ',
            bcolors.OKGREEN+'CV'+bcolors.ENDC if self.from_ciencia else '  ',

            self.publication_type.name[-16:],

            self.author_set.all().count(),
            self.keywords.all().count(),
            self.areas.all().count(),
            'Ab' if self.abstract != '' else '  ',
            'FT' if self.available else '  ',

            str(self.date),
            self.title
        )

    #def load_keywords(self):
    #    return json.loads(self.keywords) if self.keywords != None else None

class PublicationType(models.Model):
    name = models.CharField(
        max_length = 50,
        unique = True
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class Project(models.Model):
    name = models.CharField(
        primary_key = True,
        max_length = 200
    )
    desc = models.TextField(
        blank = True
    )
    date = models.DateField()
    areas = models.ManyToManyField(
        'Area'
    )

    class Meta:
        ordering = ['-date', 'name']

    def __str__(self):
        return "[{}] {}".format( str(self.date), self.name )

class Keyword(models.Model):
    name = models.CharField(
        primary_key = True,
        max_length = 100
    )

    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name