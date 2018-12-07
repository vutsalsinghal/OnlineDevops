from django.http \
    import request, \
    HttpRequest, HttpResponseServerError, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods
from decimal import Decimal
import random
import urllib.request
from bs4 import BeautifulSoup as bs
import re
from bs4 import BeautifulSoup
import requests
import lxml

from .models import Question, Grade, Quiz, CourseModule

site_hdr = "The DevOps Course"

DEF_NUM_RAND_QS = 10
DEF_MINPASS = 80


def get_filenm(mod_nm):
    return mod_nm + '.html'


def markingQuiz(user_answers, graded_answers):
    num_correct = 0

    for answered_question in user_answers:
        processed_answer = {}
        id_to_retrieve = next(iter(answered_question))
        original_question = get_object_or_404(Question, pk=id_to_retrieve)

        # Lets start building a dictionary
        # with the status for the particular questions.
        processed_answer['question'] = original_question.text
        processed_answer['correctAnswer'] = original_question.correct.lower()
        processed_answer['yourAnswer'] = answered_question[id_to_retrieve]

        correctanskey =\
            "answer{}".format(processed_answer['correctAnswer'].upper())
        youranskey =\
            "answer{}".format(processed_answer['yourAnswer'].upper())

        processed_answer['correctAnswerText'] =\
            getattr(original_question, correctanskey)
        processed_answer['yourAnswerText'] =\
            getattr(original_question, youranskey)

        # and now we are evaluating either as right or wrong...
        if answered_question[id_to_retrieve] ==\
                processed_answer['correctAnswer']:
            processed_answer['status'] = "right"
            num_correct += 1
        else:
            processed_answer['message'] = "Sorry, that's incorrect!"
            processed_answer['status'] = "wrong"
            # and store to ship to the Template.
        graded_answers.append(processed_answer)
    return num_correct


class SliderSlide:
    def __init__(self, img, link, index):
        self.img = img
        self.link = link
        self.index = index


def get_dynamicslideshow(request, site,site_hdr):
    try:
        # Set Feed Site and Headers
        url = "https://devops.com/feed/"
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

        # Fetch feed
        r = requests.get(url, headers=headers)

        # Set text from fetch to data to query.
        data = r.text

        # Using BeautifulSoup to parse data.
        soup = BeautifulSoup(data, 'lxml')

        # Getting Slide Image Source elements
        allImgTags = soup.find_all('img')

        slidePicsSource = []

        for img in allImgTags:
            slidePicsSource.append(img.get('src'))

        # Getting Slide Links
        # Find all <a> tags and <dictionary> tags
        allaTags = soup.find_all('a')
        allDescriptionTags = soup.find_all('description')

        descriptionWithImgTag = []
        indexOfImgTagInDescriptionList = []
        aTagList = []
        slidePicsLinkList = []

        slidePicsLink = []

        # Fetches Description tags which contain img tag
        for d in allDescriptionTags:
            descriptionWithImgTag.append(d.contents[0])

        # Fetch index to match links
        for i, d in enumerate(descriptionWithImgTag):
            if (d.name == 'img'):
                indexOfImgTagInDescriptionList.append(i)

        # Remove Devop home Links, seems to be one for every a Tag.
        for i, a in enumerate(allaTags):
            if (i % 2 == 0):
                aTagList.append(a)

        # Get <a> HREF Links based off dictionary index.
        for i, a in enumerate(aTagList):
            if (i + 1) in indexOfImgTagInDescriptionList:
                slidePicsLinkList.append(a.get('href'))

        # Assign links to active slide and sibling slides.
        for l in slidePicsLinkList:
                slidePicsLink.append(l)

        # Create and set SlideShowObject List
        SliderSlides = []

        for x in range(0, len(indexOfImgTagInDescriptionList)):
            SliderSlides.append(SliderSlide(slidePicsSource[x], slidePicsLink[x], x))

        return render(request,
                      site,
                      dict(header=site_hdr,
                           SliderSlides=SliderSlides
                           ))
    except Exception as e:
        return HttpResponseServerError(e.__cause__,
                                       e.__context__,
                                       e.__traceback__)


def get_quiz(request, mod_nm):

    #  Returns list of Randomized Questions
    # :param: mod_nm
    # :return: header, list() containing randomized questions, mod_nm
    try:
        questions = Question.objects.filter(module=mod_nm)
        num_questions = questions.count()
        rand_qs = []
        num_qs_to_randomize = DEF_NUM_RAND_QS

        if num_questions > 0:
            # we have to fetch numq from here:
            quizzes = Quiz.objects.filter(module=mod_nm)
            # we should log if we get count > 1 here!
            for quiz in quizzes:
                # we should have only 1 if any!
                num_qs_to_randomize = quiz.numq
                break
            if num_questions >= num_qs_to_randomize:
                    rand_qs = random.sample(list(questions),
                                            num_qs_to_randomize)
            else:
                    rand_qs = random.sample(list(questions),
                                            num_questions)

        return render(request, get_filenm(mod_nm),
                      {'header': site_hdr, 'questions': rand_qs,
                       'mod_nm': mod_nm})

        # And if we crashed along the way - we crash gracefully...
    except Exception as e:
        return HttpResponseServerError(e.__cause__,
                                       e.__context__,
                                       e.__traceback__)


# def index(request: request) -> object:
#     return render(request, 'index.html', {'header': site_hdr})

def index(request: request) -> object:
    return get_dynamicslideshow(request, 'index.html', site_hdr)


def about(request: request) -> object:
    return render(request, 'about.html', {'header': site_hdr})


def gloss(request: request) -> object:
    return render(request, 'glossary.html', {'header': site_hdr})


def teams(request: request) -> object:
    return render(request, 'teams.html', {'header': site_hdr})


def basics(request: request) -> object:
    return get_quiz(request, 'basics')


def build(request: request) -> object:
    return get_quiz(request, 'build')


def cloud(request: request) -> object:
    return get_quiz(request, 'cloud')


def comm(request: request) -> object:
    return get_quiz(request, 'comm')


def flow(request: request) -> object:
    return get_quiz(request, 'flow')


def incr(request: request) -> object:
    return get_quiz(request, 'incr')


def infra(request: request) -> object:
    return get_quiz(request, 'infra')


def micro(request: request) -> object:
    return get_quiz(request, 'micro')


def monit(request: request) -> object:
    return get_quiz(request, 'monit')


def no_quiz(request: request) -> object:
    return get_quiz(request, 'no_quiz')


def secur(request: request) -> object:
    return get_quiz(request, 'secur')


def suite(request: request) -> object:
    return get_quiz(request, 'suite')


def sum(request: request) -> object:
    return get_quiz(request, 'sum')


def test(request: request) -> object:
    return get_quiz(request, 'test')


def work(request: request) -> object:
    return get_quiz(request, 'work')


def search(request: request) -> object:
    return get_quiz(request, 'search')


@require_http_methods(["GET", "POST"])
def parse_search(request) -> object:

    def crawl_index(url):
        with urllib.request.urlopen(url) as response:
            html = response.read()
            html = bs(html, "html.parser")
            lst = bs.find_all(html, "a")
            url_lst = []
            for i in lst:
                web_url = i["href"]
                if "/devops/" in web_url:
                    url_lst.append(web_url)
            return url_lst

    def search_page(url_lst, query):
        result = []
        for i in url_lst:
            content_url = url + i
            with urllib.request.urlopen(content_url) as res:

                html = res.read()
                html = bs(html, "html.parser")
                strings = html.body.strings
                title = html.h1
                if title is None:
                    title = i.split("/")[-1]
                else:
                    title = re.sub("[\n]", "", title.string).strip()
                for i in strings:
                    i = re.sub("\n", " ", i)
                    if query in i.lower():
                        dic = {
                            "url": content_url,
                            "page": title,
                            "content": i
                        }
                        result.append(dic)
        return result

    url = "http://www.thedevopscourse.com"

    try:
        header = "The DevOps Course"
        path = request.get_full_path()
        query = path.split("query=")[1]
        if("+") in query:
            query = " ".join(query.split("+")).lower()
        else:
            query = query.lower()

        data = search_page(crawl_index(url), query)

        return render(request,
                      'search.html', dict(data=data,
                                          header=header,
                                          query=query))
    except Exception as e:
        return HttpResponseServerError(e.__cause__,
                                       e.__context__,
                                       e.__traceback__)


def grade_quiz(request: HttpRequest()) -> list:
    """
    Returns list of Questions user answered as right / wrong
    :param request: request as HttpRequest()
    :return: list() of dict() containing question, right/wrong, correct answer
    """
    try:
        num_rand_qs = DEF_NUM_RAND_QS
        # First, we process only when form is POSTed...
        if request.method == 'POST':
            graded_answers = []
            user_answers = []
            form_data = request.POST
            num_correct = 0

            # get only post fields containing user answers...
            for key, value in form_data.items():
                if key.startswith('_'):
                    proper_id = str(key).strip('_')
                    user_answers.append({proper_id: value})

            # forces user to answer all quiz questions,
            # redirects to module page if not completed
            # TODO: keep previously selected radio buttons
            # checked instead of clearing form
            mod_nm = form_data['submit']

            questions = Question.objects.filter(module=mod_nm)
            questions_count = questions.count()

            quizzes = Quiz.objects.filter(module=mod_nm)
            # we should log if we get count > 1 here!
            for quiz in quizzes:
                num_rand_qs = quiz.numq
                show_answers = quiz.show_answers
                break

            num_ques_of_quiz = min(questions_count, num_rand_qs)

            # Number of randomized questions from get_quiz.
            num_qs_to_check = num_ques_of_quiz

            # Function to mark quiz
            num_correct = markingQuiz(user_answers, graded_answers)

            # Calculating quiz score
            correct_pct = Decimal((num_correct / num_qs_to_check) * 100)
            curr_quiz = Quiz.objects.get(module=mod_nm)

            curr_module = None
            quiz_name = 'Quiz'
            navigate_links = {}
            modules = CourseModule.objects.filter(module=mod_nm)
            # we should log if we get count > 1 here!
            for this_module in modules:
                curr_module = this_module
                break

            # No matter if user passes or fails,
            # show link to next module if it exists
            if curr_module is not None:
                quiz_name = curr_module.title
                navigate_links = {
                    'next': 'devops:'
                    + curr_module.next_module
                    if curr_module.next_module
                    else
                    False
                }
                # If user fails, show link to previous module
                if (correct_pct < curr_quiz.minpass):
                    navigate_links['previous'] = 'devops:' + mod_nm

            # now we are ready to record quiz results...
            if request.user.username != '':
                Grade.objects.create(participant=request.user,
                                     score=correct_pct.real,
                                     quiz=curr_quiz,
                                     quiz_name=mod_nm)

            # ok, all questions processed, lets render results...
            return render(request,
                          'graded_quiz.html',
                          dict(graded_answers=graded_answers,
                               num_ques=num_qs_to_check,
                               num_correct=num_correct,
                               correct_pct=int(correct_pct),
                               quiz_name=quiz_name,
                               show_answers=show_answers,
                               navigate_links=navigate_links,
                               header=site_hdr))

        # If it is PUT, DELETE etc. we say we dont do that...
        else:
            raise HttpResponseBadRequest("ERROR: Method not allowed")

    # And if we crashed along the way - we crash gracefully...
    except Exception as e:
        return HttpResponseServerError(e.__cause__,
                                       e.__context__,
                                       e.__traceback__)
