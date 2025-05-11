# import tools

from bs4 import BeautifulSoup
import requests
import json
import praw
import time

# credentials for accessing reddit and tmdb api

creds = {"client_id": "XXX",
         "client_secret": "XXX",
         "password": "XXX",
         "user_agent": "Provide movie info",
         "username": "5o7bot"}

reddit = praw.Reddit(client_id=creds["client_id"],
                     client_secret=creds["client_secret"],
                     password=creds["password"],
                     user_agent=creds["user_agent"],
                     username=creds["username"])

tmdb_key = "XXX"

# variables, one to track how many comments are made and an arbitrary limit on posts per subreddit

entry_number = 0
postspersub = 10

# this loop runs once every 20 minutes

while True:

    # gather subreddits into a list called subreddits

    subreddits = []
    subreddits.append("moviesuggestions")
    subreddits.append("fullforeignmovies")
    subreddits.append("fullscifimovies")
    subreddits.append("ijustwatched")
    subreddits.append("movieposterporn")
    subreddits.append("internetarchivemovies")
    subreddits.append("fullmoviesonyoutube")
    subreddits.append("fulltvshowsonyoutube")
    subreddits.append("cineshots")

    # filter through the collected submissions and put them in a list called submissions

    submissions = []

    # the checked list will include everything collected and be used to re-doing stuff

    checked = []

    # a for loop is the filter that scans everything and places good candidates into the submissions list

    for subreddit in subreddits:
        for submission in reddit.subreddit(subreddit).__getattribute__("new")(limit=postspersub):

            # if it has not been checked already, continue

            if not any(x in submission.title for x in checked):
                checked.append(submission.title)

                # don't include items with specific words in the submission title

                catch_words = ["Weekly", "Monthly", "Announcement", "Features", "Spencer", "Resurrections"]
                if not any(x in submission.title for x in catch_words):

                    # this is how you keep from making duplicate comments in the same submission

                    task_complete = False
                    for comment in submission.comments:
                        if comment.author == "5o7bot":
                            task_complete = True
                            break

                    if not task_complete:

                        # this subreddit requires info for posts with a specific flair

                        if submission.subreddit == "moviesuggestions":
                            if submission.link_flair_text == "SUGGESTING":
                                submissions.append(submission)
                        else:

                            # if the submission meets all the requirements, add it to the list

                            submissions.append(submission)

    for submission in submissions:

        # "try:", will run the following code until the "except:" - It won't break the loop

        try:

            # parsing text to collect the movie title and year from the submission title

            query = submission.title.split(")")[0] + (")")
            query_title = query.split("(")[0][:-1].replace(" ", "%20")
            query_year = query.split("(")[1][:-1]

            # a dictionary (a data package) of 3 things

            params = {
                "api_key": tmdb_key,
                "query": query_title,
                "year": query_year
            }

            # response contains a string, it uses the requests tool search tmdb with their api

            response = requests.get("https://api.themoviedb.org/3/search/movie", params=params)

            # data contains the result of turning a string, response, into a dictionary data type

            data = response.json()

            # movie contains the zeroth item in a section called results from data

            movie = data["results"][0]

            # movie_id collects the tmdb id from movie - movie is a dictionary - movie_id, a string

            movie_id = movie["id"]

            # url is made to contain the url using the movie id - it is a string

            url = f"https://www.themoviedb.org/movie/{movie_id}"

            # use the tmdb id to make 2 calls for chunks of data for one movie - store them is soup and soup2

            base_string = "https://api.themoviedb.org/3/movie/"
            tmdb_data1 = base_string + movie_id + "?api_key=" + tmdb_key + "&append_to_response=credits"
            source = requests.get(tmdb_data1).text
            soup = BeautifulSoup(source, 'lxml')
            soup = soup.p.text
            soup = json.loads(soup)

            tmdb_data2 = base_string + movie_id + "?api_key=" + tmdb_key + "&append_to_response=releases"
            source2 = requests.get(tmdb_data2).text
            soup2 = BeautifulSoup(source2, 'lxml')
            soup2 = soup2.p.text
            soup2 = json.loads(soup2)

            # soup and soup 2 are dictionaries, parse them using basic python commands,
            # use variables to store the collected data

            title = soup['original_title']
            content_rating =""
            for i in soup2["releases"]["countries"]:
                if i["iso_3166_1"] == "US":
                    content_rating = i["certification"]
            date = soup['release_date'].split("-")[0]
            tagline = soup['tagline']
            genres = ""
            for i in soup['genres']:
                genres = genres + " | " +i['name']
            genres = genres[3:]
            overview = soup['overview']
            stars = ""
            for i in soup['credits']["cast"][:5]:
                stars = stars + ", " +i['name']
            stars = stars[2:]
            director = ""
            for key in soup["credits"]["crew"]:
                if key["job"] == "Director":
                    director = key["name"]
                    break
            dop = ""
            for key in soup["credits"]["crew"]:
                if key["job"] == "Director of Photography":
                    dop = key["name"]
                    break
            runtime = soup["runtime"]

            # prepare an entry for the submission

            entry = "##" + title + " " + date + " " + content_rating + "\n   " + tagline + "  \n>>!" + overview + "!<\n   \n"
            entry = entry + genres + "  \nDirector: " + director + "  \nDirector of Photography: " + dop
            entry = entry + "  \nActors: " + stars + "  \nRuntime: " + str(soup["runtime"]) + " min  \n[TMDB](" + url + ")  \n"
            entry = entry + ">*I am a bot. This information was sent automatically. If it is faulty, please reply to this comment.*"

            # print the entry into the output console

            print(entry)

            # send the entry to reddit using their api

            submission.reply(entry)

            # chalk one up and print some info into the output console

            entry_number += 1
            print(submission.title + "\nentry: " + str(entry_number))

        except:
            pass

    # take a nap

    time.sleep(1200)
