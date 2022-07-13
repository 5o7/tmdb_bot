from bs4 import BeautifulSoup
from googlesearch import search
import requests
import json
import praw
import time

# Two variables to hold user credentials and an instance of the website

creds = {"client_id": "xxxxxxx",
         "client_secret": "xxxxxxx",
         "password": "xxxxxxx",
         "user_agent": "Provide movie info",
         "username": "tmdb_bot"}

reddit = praw.Reddit(client_id=creds["client_id"],
                     client_secret=creds["client_secret"],
                     password=creds["password"],
                     user_agent=creds["user_agent"],
                     username=creds["username"])

# Variables for tracking and testing

tags_given = 0
postspersub = 1
cinesub = "xxxxxxx"

# a loop to run a block of code every fifteen minutes

while True:

    # A list called subreddits to hold website communities

    subreddits = []
    subreddits.append("5o7bot")
    subreddits.append("moviesuggestions")
    subreddits.append("fullforeignmovies")
    subreddits.append("fullscifimovies")
    subreddits.append("ijustwatched")
    subreddits.append("movieposterporn")
    subreddits.append("internetarchivemovies")
    subreddits.append("fullmoviesonyoutube")
    subreddits.append("fulltvshowsonyoutube")
    subreddits.append("cineshots")

    # Make a list called submissions to store new submissions from movie subs

    submissions = []
    checked = []

    for subreddit in subreddits:
        for submission in reddit.subreddit(subreddit).__getattribute__("new")(limit=postspersub):

            # Check if the submission is in the checked list

            if not any(x in submission.title for x in checked):

                # Add the submission to the checked list and the submissions list

                checked.append(submission.title)

                # Exclude submissions with these words in the title

                catch_words = ["Weekly", "Monthly", "Announcement", "Features", "Spencer", "Resurrections"]
                if not any(x in submission.title for x in catch_words):

                    # Check if self has commented in the submission

                    task_complete = False
                    for comment in submission.comments:
                        if comment.author == "tmdb_bot":
                            task_complete = True
                            break

                    if not task_complete:

                        # Only get suggesting flair from MovieSuggestions

                        if submission.subreddit == "moviesuggestions":
                            if submission.link_flair_text == "SUGGESTING":
                                if submission.author != "jFalner":
                                    submissions.append(submission)
                                else:
                                    print("jFalner posted")
                        else:
                            submissions.append(submission)

    # A loop to examine each item in the submissions list

    for submission in submissions:

        # Reset variables

        query = search_results = imdb_id = tmdb_page = soup = source = genres = ""
        title = release = runtime = overview = genres = director = dp = ""
        actors = tag_line = vote_average = vote_count = content_rating = ""

        # Prepare a query from the submission title and add imdb

        query = submission.title
        if ")" in query:
            query = query.split(")")
            query = query[0] + (") imdb")
        else:
            query = query + " imdb"

        # Change ampersands to "and"

        if "&" in query:
            query = query.replace("&", "and")

        # Get the imdb id with google

        try:
            for i in search(query, tld="com", num=6, stop=6, pause=2):
                if "https://www.imdb.com/title/tt" in i:
                    imdb_url = str(i)
                    if len(imdb_url) == 37:
                        imdb_id = imdb_url.replace("https://www.imdb.com/title/", "")
                        imdb_id = imdb_id.replace("/", "")
                        break

            # Use imdb id to get the movie's tmdb webpage

            tmdb_page = "https://api.themoviedb.org/3/movie/" + imdb_id + \
                        "?api_key=xxxxxxx&append_to_response=credits"


            # Convert The Movie Database API page into a dictionary

            source = requests.get(tmdb_page).text
            soup = BeautifulSoup(source, 'lxml')
            soup = soup.p.text
            soup = json.loads(soup)

            # for k, v in soup.items():
            #     print("-"*30)
            #     print(k, v)

            # Extract info

            title = soup["title"]
            release = soup["release_date"]
            release = release.split("-")
            release = "(" + release[0] + ")"

            tmdb_page2 = "https://api.themoviedb.org/3/movie/" + imdb_id + \
                         "?api_key=xxxxxxx&append_to_response=releases"
            source2 = requests.get(tmdb_page2).text
            soup2 = BeautifulSoup(source2, 'lxml')
            soup2 = soup2.p.text
            soup2 = json.loads(soup2)
            for i in soup2["releases"]["countries"]:
                if i["iso_3166_1"] == "US":
                    content_rating = i["certification"]

            runtime = soup["runtime"]

            hours = runtime // 60
            minutes = runtime % 60
            runtime = "{}:{}".format(hours, minutes)
            runtime = str(runtime)

            tag_line = soup["tagline"]
            overview = soup["overview"]

            vote_average = soup["vote_average"]
            star_number = vote_average
            vote_average = str(vote_average)
            vote_average = vote_average.replace(".", "")

            star_number = int(star_number)
            stars = ""
            for i in range(0, 10):
                type(i)
                if i <= star_number:
                    stars = stars + "★"
                else:
                    stars = stars + "☆"

            vote_count = soup["vote_count"]
            vote_count = "{:,}".format(vote_count)
            vote_count = str(vote_count)

            for key in soup["credits"]["crew"]:
                if key["job"] == "Director":
                    director = key["name"]
                    break

            for key in soup["credits"]["crew"]:
                if key["job"] == "Director of Photography":
                    dp = key["name"]
                    break

            for i in range(0, 3):
                actors = actors + ", " + soup["credits"]["cast"][i]["name"]
            actors = actors[1:]

            tmdb_url = "[TMDB](https://www.themoviedb.org/movie/" + str(soup["id"]) + ")"

            for key in soup["genres"]:
                genres = genres + " | " + key["name"]
            genres = genres[3:]
            genres = "*" + genres + "*"

            entry = "##" + title + " " + release + " " + content_rating + "  \n"

            if len(tag_line) > 0:
                entry = entry + "*" + tag_line +  "*  \n"

            entry = entry + ">!" + overview + "!<  \n" + genres + "  \n"
            entry = entry + "Director: " + director + "  \n"

            if submission.subreddit == cinesub and len(dp) > 0:
                entry = entry + "Cinematographer: " + dp + "  \n"

            entry = entry + "Actors: " + actors + "  \n"
            entry = entry + "Rating: " + stars + " " + vote_average + "% with " + \
                vote_count + " votes" + "  \n"
            entry = entry + "Runtime: " + runtime + "  \n"
            entry = entry + tmdb_url
            submission.reply(entry)
            print(entry)

        except:
            pass

    time.sleep(900)