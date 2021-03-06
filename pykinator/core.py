#!/usr/bin/env python

import requests


class Pykinator(object):

    language = 'en'
    server = 1
    no_of_questions = 10

    url_template = { # {}{} translate to language and server
      'session': ("http://api-{}{}.akinator.com/ws/new_session?partner=1"
                  "&player=desktopPlayer"),
      'answer': "http://api-{}{}.akinator.com/ws/answer",
      'guess': "http://api-{}{}.akinator.com/ws/list",
      'choice': "http://api-{}{}.akinator.com/ws/choice",
      'exclusion': "http://api-{}{}.akinator.com/ws/exclusion"
    }

    url = { } # populated at init combining language, server, and templates

    session = {
      'akinator': None,
      'guess': None
    }

    identification = {
      'session': None,
      'signature': None
    }

    guessed_wrong_once = False

    game_over = False
    guessing = False


    """
      inputs:
        * language (i.e. "en","fr")
        * server (1,2...) just a suggestion.
        * no_of_questions how many questions to ask before we make a guess
    """
    def __init__(self, language=None, server=None, no_of_questions=None):

        if language is not None:
            self.language = language

        if server is not None:
            self.server = server

        if no_of_questions is not None:
            self.no_of_questions = int(no_of_questions)


    def init(self):

        # which server is running?
        if not self._server_connection():
            skip_server = self.server # we already tried this
            for server in range(1,5): # test servers 1-4
                if skip_server == server: continue
                self.server = server
                if self._server_connection():
                    return
            raise ConnectionError("Can't connect to server, try again later")


    def _setup_urls(self):

        for template in self.url_template:
            self.url[template] = self.url_template[template].format(
              self.language, self.server)


    def _server_connection(self):

        self._setup_urls()

        try:
            session = requests.get(self.url['session'])
        except requests.exceptions.ConnectionError:
            return False

        if session.json()['completion'] == "OK":
            self.session['akinator'] = session
            return True

        return False


    def ans_to_string(self, ans: str):

        ans = ans.lower()
        if ans in ["yes", "y"]:
            return "0"
        elif ans in ["no", "n"]:
            return "1"
        elif ans in ["i", "idk", "i dont know", "i don't know"]:
            return "2"
        elif ans in ["probably", "p"]:
            return "3"
        elif ans in ["probably not", "pn"]:
            return "4"
        else:
            return "-1"


    def question(self):

        try:
            data = self.session['akinator'].json()
        except ValueError:
            raise("something went wrong fetching the session data")

        self.guessing = False

        params = data['parameters']
        if 'step_information' in params:
            params = params['step_information']

        steps = int(params['step']) + 1
        if steps > self.no_of_questions and not self.guessed_wrong_once:
            self.guessing = True
            return self.guess()

        return (
          'Question {}:\n{}\n'
          '"yes", "no", "idk", "probably", "probably not"'.format(
            str(steps),
            params['question']
          )
        )


    def start(self):

        self.init() # ensure we have a connection

        return self.question()


    def _set_params(self, response=None):

        data = self.session['akinator'].json()

        parameters = data['parameters']

        if 'identification' in parameters:
            identification = parameters['identification']
            self.identification['session'] = identification['session']
            self.identification['signature'] = identification['signature']

        if 'step_information' in parameters:
            parameters = parameters['step_information']

        params = {
          "session": self.identification['session'],
          "signature": self.identification['signature'],
          "step": parameters['step'],
        }

        if response is not None:
            params['answer'] = self.ans_to_string(response)

        return params


    def answer(self, response=''):

        params = self._set_params(response)

        self.session['akinator'] = requests.get(
          self.url['answer'], params=params)

        return self.question()


    def guess(self, answer=None):

        params = self._set_params()

        def element():
            data = self.session['guess'].json()
            return data['parameters']['elements'][0]['element']

        if self.session['guess'] is None:
            self.session['guess'] = requests.get(
              self.url['guess'], params=params)

            element = element()

            name, desc = [element[x] for x in ['name','description']]

            return "Is this your character? [yes/no]\n{}\n{}\n".format(
              name, desc)
        elif answer is not None:
            self.guessing = False
            answer = answer.lower()
            if answer in ["yes","y"]:
                data = self.session['guess'].json()
                params['element'] = element()['id']
                requests.get(self.url['choice'], params)
                self.game_over = True
                return "I guessed right! Thanks for playing."
            elif answer in ["no", "n"]:
                params['forward_answer'] = self.ans_to_string(answer)
                requests.get(self.url['exclusion'], params=params)
                self.guessed_wrong_once = True
                self.session['guess'] = None
                return "Let's continue..."

        return "I have no guesses to give..."


if __name__ == "__main__":

    pk = Pykinator(server=2)

    print(self.start())
    response = input("> ")

    while (not self.game_over):
        if response in ["quit","exit","q"]:
            print("goodbye.")
            sys.exit()

        if response in ["guess", "done"]:
            self.guessing = True
            print(self.guess())
            response = input("> ")
            continue

        if self.guessing:
            print(self.guess(response))
            continue
        
        print(self.answer(response))
        response = input("> ")
